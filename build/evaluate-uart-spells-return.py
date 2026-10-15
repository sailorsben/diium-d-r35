"""Strict archived UART/FFVI return and matched same-epoch pre/post comparison.

No device writes. Reuses the frozen physical reporter's acceptance rules; raw
valid-prefix CPU/wall and cumulative PCM reserve are recomputed independently.
"""
from pathlib import Path
from hashlib import sha256
import argparse,csv,importlib.util,json,re,runpy,statistics
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def rows(p):return list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')))
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/'build'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def status(p):
 s=dict(x.split('=',1) for x in p.read_text().split())
 for n in ['result','irq','attached','calls','added','writes','full','empty_stop','stopped','urgent','fallback','fault','bypass','fifo','head','tail','rx','tx','frame','parity','overrun','brk','cap']:s[n]=int(s[n])
 assert s['result']==0 and s['irq']==19 and s['attached']==1 and s['fifo']==8 and s['cap']==0
 assert s['fault']==s['bypass']==0 and 0<=s['head']<4096 and 0<=s['tail']<4096
 assert s['calls']==sum(s[n] for n in ['added','fallback','fault'])%2**32
 assert s['added']==sum(s[n] for n in ['writes','full','empty_stop','stopped'])%2**32
 return s
def epoch_metrics(d):
 session=kv(d/'last-session.txt');framepath=d/'frames.csv'
 assert kv(framepath).get('#mock')=='0','Mock telemetry cannot qualify a physical return'
 data=rows(framepath);prefix={};pa=pv=0
 for i,r in enumerate(data):
  ca,cv=int(r['audio_worker_cpu_ns']),int(r['video_worker_cpu_ns'])
  if int(r['frame'])!=i or r['pointer_valid']!='1' or ca<pa or cv<pv or int(r['pace_wait_ns'])>int(r['step_ns']):break
  prefix[i]={'thread_CPU_ns':int(r['main_step_cpu_ns'])+ca-pa+cv-pv,'core_CPU_ns':int(r['cpu_ns']),
    'wall_service_ns':int(r['step_ns'])-int(r['pace_wait_ns']),'step_ns':int(r['step_ns']),'pace_ns':int(r['pace_wait_ns'])}
  pa,pv=ca,cv
 pcm=kv(d/'pcm-full.txt');sync=[];first_invalid=None
 boundary=int(session['pcm_boundary_frames']);buffer=int(session['pcm_buffer_frames'])
 transactions=list(re.finditer(r'seq=(\d+) ns=(\d+) op=(\S+) arg=(\d+) result=(-?\d+) state=(\d+) queued=(\d+) appl=(\d+) hw=(\d+) epoch=(\d+) xfer=(\d+)',(d/'pcm-full.txt').read_text()))
 assert len(transactions)==int(pcm['entries_total'])-int(pcm['retained_from'])
 for m in transactions:
  seq,t,op,arg,rc,state,q,appl,hw,ep,xfer=m.groups()
  if op!='SYNC_OK' or state!='3':continue
  r={n:int(v) for n,v in [('seq',seq),('ns',t),('queued',q),('appl',appl),('hw',hw),('epoch',ep),('xfer',xfer)]}
  if not(boundary>0 and r['appl']%boundary==r['xfer']%boundary and (r['appl']-r['hw'])%boundary==r['queued'] and r['queued']<=buffer):first_invalid=r['seq'];break
  sync.append(r)
 cumulative=None
 if sync:
  first,last=sync[0],sync[-1];assert len({r['epoch'] for r in sync})==1
  produced=(last['xfer']-first['xfer'])%boundary;consumed=(last['hw']-first['hw'])%boundary
  assert last['queued']-first['queued']==produced-consumed
  cumulative={'seconds':(last['ns']-first['ns'])/1e9,'initial_reserve':first['queued'],'last_valid_reserve':last['queued'],
   'change_frames':produced-consumed,'produced_growth':produced,'HW_growth':consumed,'identity_exact':True}
 head=kv(d/'headroom.txt')
 return prefix,{'valid_CPU_prefix_calls':len(prefix),'completed_calls':int(session['runs']),
  'minimum_valid_reserve_frames':min((r['queued'] for r in sync),default=None),'first_invalid_sync':first_invalid,
  'retained_from':int(pcm['retained_from']),'cumulative_reserve':cumulative,
  'scaled':int(session['display_scaled']),'flipped':int(session['display_flipped']),
  'reported_xruns':int(session['xrun_count']),'write_errors':int(session['write_errors']),
  'service_deadline_overruns':int(head['deadline_overruns']),'service_margin_overruns':int(head['margin_overruns']),
  'warm20percent_headroom':head['sampled_warm_20_percent_headroom'],
  'frequency_values_khz':sorted({int(r[n]) for r in data for n in ['freq_before_khz','freq_after_khz']})}
def paired(old,new,indices):
 indices=list(indices);complete=all(i in old and i in new for i in indices)
 common=[i for i in indices if i in old and i in new]
 return {'requested_calls':len(indices),'common_calls':len(common),'complete':complete,
  'saving_ms':{n:statistics.mean(old[i][n]-new[i][n] for i in common)/1e6 if common and complete else None for n in ['thread_CPU_ns','core_CPU_ns','wall_service_ns','step_ns','pace_ns']}}
def platform(p):
 sections=[]
 for block in p.read_text().split('Platform snapshot ')[1:]:
  irq=re.search(r'^\s*19:\s*(\d+)\s',block,re.M);up=re.search(r'^(\d+\.\d+)\s+\d+\.\d+\s*$',block,re.M)
  cpu=re.search(r'^cpu\s+([0-9 ]+)$',block,re.M)
  sections.append({'label':block.splitlines()[0],'IRQ19':int(irq[1]) if irq else None,'uptime':float(up[1]) if up else None,'CPU_ticks':[int(x) for x in cpu[1].split()] if cpu else None})
 return sections
def main(archive,live=False):
 archive=archive.resolve();assert archive.is_relative_to((ROOT/'device-evidence').resolve())
 a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
 for e in a['all_retro_files']:assert digest(archive/e['path'])==e['sha256'],e['path']
 instpath=ROOT/'evidence/2026-10-15/uart-spells1/installation.json';inst=json.loads(instpath.read_text())
 base=archive/inst['target'];assert (base/'last-launch').read_bytes()==load('install-uart-spells.py').MARKER
 assert not list((archive/'retro').rglob('armed')) and not (archive/'retro/update/Code.bkp').exists()
 for n,h in inst['payload_hashes'].items():assert digest(base/n)==h,n
 assert digest(archive/'retro/snes-mvp/launch.sh')==inst['dispatch_sha256']
 assert digest(archive/'retro/init')==inst['init_sha256']
 fqpath=ROOT/'evidence/2026-10-15/uart-fix1/qualification.json';fq=json.loads(fqpath.read_text())
 fipath=ROOT/'evidence/2026-10-15/uart-fix1/installation.json';fi=json.loads(fipath.read_text())
 assert fi['source_commit']==inst['source_commit'] and digest(archive/'retro/uart-fix1/qualification.json')==fi['qualification_sha256']
 assert digest(archive/'retro/uart-fix1/original-init')=='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
 for n,h in fq['payloads'].items():assert digest(archive/'retro/init' if n=='init' else archive/'retro/uart-fix1'/n)==h,n
 assert not (archive/'retro/uart-fix1/disabled').exists()
 before,after=status(base/'uart-before.txt'),status(base/'uart-after.txt')
 deltas={n:(after[n]-before[n])%2**32 for n in ['calls','added','writes','full','empty_stop','stopped','urgent','fallback','fault','bypass','rx','tx','frame','parity','overrun','brk']}
 assert deltas['calls']>0
 boot=(archive/'retro/uart-fix1/latest-boot.log').read_text();assert 'helper_exit=0 ' in boot and 'start_result=0 attached=1' in boot
 baseline_analysis_path=ROOT/'evidence/2026-10-14/draw-order-return/analysis.json'
 assert digest(baseline_analysis_path)==inst['baseline_physical_analysis_sha256']
 baseline_analysis=json.loads(baseline_analysis_path.read_text());oldarchive=ROOT/'device-evidence'/baseline_analysis['archive'];old=oldarchive/'retro/snes-draw-order1'
 for n,h in baseline_analysis['inputs'].items():assert digest(ROOT/n)==h,n
 oldinst=json.loads((ROOT/'evidence/2026-10-14/draw-order/installation.json').read_text())
 for n,h in oldinst['payload_hashes'].items():assert digest(old/n)==h,n
 # Full old/new plan/runner/core/state/input identity, not similar labels.
 assert (base/'plan.json').read_bytes()==(old/'plan.json').read_bytes()
 retq=json.loads((base/'uart-retest-qualification.json').read_text())
 for n in retq['unchanged_payloads']:assert (base/n).read_bytes()==(old/n).read_bytes(),n
 prior=json.loads((ROOT/'device-evidence'/inst['archive']/'archive.json').read_text());changed=[];unchanged=0
 for e in prior['all_retro_files']:
  if e['path'] in ['retro/init','retro/snes-mvp/launch.sh']:continue
  if digest(archive/e['path'])==e['sha256']:unchanged+=1
  else:changed.append(e['path'])
 assert not [n for n in changed if n!='retro/swapfile'],changed
 guard=load('package-snes-1.19.py')
 for n,h in guard.BOOT_EXPECTED.items():assert digest(archive/n)==h,n
 ROM=None
 if live:
  card=Path('I:/');assert not list((card/'retro').rglob('armed'))
  for n,h in {**guard.BOOT_EXPECTED,'retro/init':inst['init_sha256'],'retro/snes-mvp/launch.sh':inst['dispatch_sha256']}.items():assert digest(card/n)==h,n
  for n,h in inst['payload_hashes'].items():assert digest(card/inst['target']/n)==h,n
  for n,h in fq['payloads'].items():assert digest(card/'retro/init' if n=='init' else card/'retro/uart-fix1'/n)==h,n
  assert (card/'retro/uart-fix1/latest-boot.log').read_bytes()==(archive/'retro/uart-fix1/latest-boot.log').read_bytes()
  assert not (card/'retro/uart-fix1/disabled').exists()
  for n in ['uart-before.txt','uart-after.txt','suite-result.txt','startup.log']:assert (card/inst['target']/n).read_bytes()==(base/n).read_bytes(),n
  ROM=digest(card/'002/Final Fantasy VI.zip');assert ROM==load('install-uart-fix.py').ROM
 reporter=ROOT/'build/draw-order-test-private-v1/report.py';analyze=runpy.run_path(str(reporter))['analyze']
 newreport=analyze(base,False);oldreport=analyze(old,False)
 plan=json.loads((base/'plan.json').read_text());epochs=[];inputs={};groups={};frame_records={}
 for run,nr,orr in zip(plan['runs'],newreport['epochs'],oldreport['epochs']):
  assert run['run']==nr['run']==orr['run']
  nd,od=base/f"run-{run['run']:03d}",old/f"run-{run['run']:03d}"
  nf,nm=epoch_metrics(nd);of,om=epoch_metrics(od)
  frame_records[run['run']]=nf
  warm=sorted(i for i in set(nf)&set(of) if i>=120)
  m=paired(of,nf,warm);fixed={label:paired(of,nf,span) for label,span in [('early',range(120,240)),('earlier_heavy',range(384,416)),('late_heavy',range(496,536 if run['fixture']==1 else 542))]}
  windows=[warm[j:j+16] for j in range(max(0,len(warm)-15)) if warm[j+15]-warm[j]==15]
  saves=[statistics.mean(of[i]['thread_CPU_ns']-nf[i]['thread_CPU_ns'] for i in w)/1e6 for w in windows]
  epoch={**run,'before_status':orr['status'],'after_status':nr['status'],'before':om,'after':nm,'warm_common':m,'fixed':fixed,
   'worst_common16_CPU_saving_ms':min(saves) if saves else None,'best_common16_CPU_saving_ms':max(saves) if saves else None,
   'before_worst16_CPU_ms':orr['worst16_recorded_threads_CPU_mean_ms'],'after_worst16_CPU_ms':nr['worst16_recorded_threads_CPU_mean_ms']}
  epochs.append(epoch)
  key=run['block']+'/'+run['variant'];groups.setdefault(key,[]).append(epoch)
  for d in [nd,od]:
   for n in ['frames.csv','last-session.txt','pcm-full.txt','headroom.txt','animation.csv','result.txt','begin.txt']:inputs[(d/n).relative_to(ROOT).as_posix()]=digest(d/n)
 summary={}
 for key,es in groups.items():
  summary[key]={'runs':len(es),'before_clean':sum(e['before_status']=='CLEAN_BOUNDED_WINDOW' for e in es),'after_clean':sum(e['after_status']=='CLEAN_BOUNDED_WINDOW' for e in es),
   'median_warm_common_thread_CPU_saving_ms':statistics.median(e['warm_common']['saving_ms']['thread_CPU_ns'] for e in es),
   'median_warm_common_wall_service_saving_ms':statistics.median(e['warm_common']['saving_ms']['wall_service_ns'] for e in es),
   'minimum_reserve_before':min(e['before']['minimum_valid_reserve_frames'] for e in es),'minimum_reserve_after':min(e['after']['minimum_valid_reserve_frames'] for e in es)}
 suite=kv(base/'suite-result.txt');assert suite['runs']==suite['planned']=='48' and suite['stopped']=='0'
 assert len(epochs)==48 and [e['before_status'] for e in epochs]==[e['status'] for e in baseline_analysis['epochs']]
 log=(base/'startup.log').read_text();assert 'display worker joined' in log and 'FreeVFB returned' in log
 for p in [archive/'archive.json',instpath,fqpath,fipath,baseline_analysis_path,reporter,Path(__file__),base/'uart-before.txt',base/'uart-after.txt',base/'runtime-platform.txt',base/'suite-result.txt',base/'startup.log',archive/'retro/uart-fix1/latest-boot.log']:
  inputs[p.relative_to(ROOT).as_posix()]=digest(p)
 newplatform,oldplatform=platform(base/'runtime-platform.txt'),platform(old/'runtime-platform.txt')
 def IRQrate(s):
  assert len(s)==2 and s[1]['uptime']>s[0]['uptime'] and s[1]['IRQ19']>=s[0]['IRQ19']
  return (s[1]['IRQ19']-s[0]['IRQ19'])/(s[1]['uptime']-s[0]['uptime'])
 oldrate,newrate=IRQrate(oldplatform),IRQrate(newplatform)
 within=[{'repeat':repeat,'raw_minus_draw_order':paired(frame_records[raw],frame_records[draw],range(120,1200))} for repeat,raw,draw in [(2,39,40),(3,44,43)]]
 result={'version':'uart-spells1-return','archive':archive.name,'mock':False,'card_writes':0,'fat_clean':True,
  'archive_files':len(a['all_retro_files']),'archive_bytes':sum(e['bytes'] for e in a['all_retro_files']),
  'installed_test_payloads_verified':len(inst['payload_hashes']),'protected_prior_files_unchanged':unchanged,'changed_prior_files':changed,
  'ROM_live_sha256':ROM,'UART_before':before,'UART_after':after,'UART_deltas':deltas,'UART_boot_attach_success':True,
  'runtime_platform':newplatform,'old_runtime_platform':oldplatform,'IRQ19_rate_before':oldrate,'IRQ19_rate_after':newrate,'IRQ19_reduction_percent':100*(1-newrate/oldrate),
  'within_corrected_boot_Quasar_pricing':within,
  'suite':suite,'before_clean':sum(e['before_status']=='CLEAN_BOUNDED_WINDOW' for e in epochs),'after_clean':sum(e['after_status']=='CLEAN_BOUNDED_WINDOW' for e in epochs),
  'groups':summary,'epochs':epochs,'marker_consumed':True,'persistent_UART_next_boot':True,'one_shot_rearmed':False,
  'production_gate':False,'inputs':inputs,'limits':['Historical different-boot comparison; not a randomized within-boot UART A/B.','Thread CPU does not independently price IRQ execution; wall and reserve remain essential.','PCM reserve is vendor logical accounting before first pointer drift; no independent DAC/speaker proof.','No sustained full-FIFO or mixed-RX event is inferred from a passing RAM fixture.']}
 (archive/'uart-spells-return.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ['archive','before_clean','after_clean','UART_deltas','runtime_platform','groups','suite']},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--verify-live',action='store_true');a=p.parse_args();main(a.archive,a.verify_live)
