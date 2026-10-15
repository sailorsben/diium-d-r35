"""Strict archive-only draw-order/control assessment; optional read-only I: check."""
from pathlib import Path
from hashlib import sha256
import csv,json,re,runpy,statistics,sys
ROOT=Path(__file__).resolve().parent.parent

def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def rows(p):return list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')))

def main(archive,live=False):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
 base=archive/'retro/snes-draw-order1'
 reporter_path=ROOT/'build/draw-order-test-private-v1/report.py'
 report=runpy.run_path(str(reporter_path))['analyze'](base,False)
 (base/'spell-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
 source=ROOT/'build/evaluate-demand-spells-return.py';code=source.read_text().replace('demand-spells','draw-order')
 code=code.replace("suite['runs']=='40'","suite['runs']=='48'")
 code=code.replace("r['variant']=='demand']","r['variant']=='demand' and r['run']<36]")
 code=code.replace("'interim_user_observations':'Grand Train, Ultima and Pearl seemed to work; Meteor did not seem complete. Observations occurred during the suite, not an independent full40-epoch visual review.'",
 "'interim_user_observations':'User saw no obvious crash through Carbunkl and reported the middle run struggling. Middle of each pricing triple is draw-order; exact epoch/effect of that observation not independently established.'")
 ns={'__file__':str(Path(__file__).resolve()),'__name__':'draw_order_return'}
 exec(compile(code,'draw_order_return','exec'),ns);ns['main'](archive,live)
 target=archive/'draw-order-return-evaluation.json';result=json.loads(target.read_text())
 apu_path=ROOT/'evidence/2026-10-14/draw-order/APU-audit.json';apu=json.loads(apu_path.read_text())
 assert apu['passed'] and apu['APU_object_byte_identical'] and apu['SPC_DSP_function_sizes_identical']
 records={};inputs=[source,reporter_path,apu_path]
 for epoch in result['epochs']:
  d=base/f"run-{epoch['run']:03d}";frames=rows(d/'frames.csv');s=kv(d/'last-session.txt')
  valid={};pa=pv=0
  for i,r in enumerate(frames):
   ca,cv=int(r['audio_worker_cpu_ns']),int(r['video_worker_cpu_ns'])
   if int(r['frame'])!=i or r['pointer_valid']!='1' or ca<pa or cv<pv or int(r['pace_wait_ns'])>int(r['step_ns']):break
   r['threads_cpu']=int(r['main_step_cpu_ns'])+ca-pa+cv-pv;pa,pv=ca,cv;valid[i]=r
  records[(epoch['fixture'],epoch['repeat'],epoch['variant'])]=valid
  pcm=d/'pcm-full.txt';meta=kv(pcm);boundary=int(s['pcm_boundary_frames']);buffer=int(s['pcm_buffer_frames'])
  transactions=list(re.finditer(r'seq=(\d+) ns=(\d+) op=(\S+) arg=(\d+) result=(-?\d+) state=(\d+) queued=(\d+) appl=(\d+) hw=(\d+) epoch=(\d+) xfer=(\d+)',pcm.read_text()))
  assert len(transactions)==int(meta['entries_total'])-int(meta['retained_from'])
  sync=[]
  for m in transactions:
   seq,t,op,arg,rc,state,q,appl,hw,ep,xfer=m.groups()
   if op!='SYNC_OK' or state!='3':continue
   if not(boundary>0 and int(appl)%boundary==int(xfer)%boundary and (int(appl)-int(hw))%boundary==int(q) and int(q)<=buffer):break
   sync.append(dict(ns=int(t),queued=int(q),hw=int(hw),xfer=int(xfer),epoch=int(ep)))
  cumulative=None
  if sync:
   first,last=sync[0],sync[-1];assert len({r['epoch'] for r in sync})==1
   produced=(last['xfer']-first['xfer'])%boundary;consumed=(last['hw']-first['hw'])%boundary
   assert last['queued']-first['queued']==produced-consumed
   cumulative={'prefix_seconds':(last['ns']-first['ns'])/1e9,'initial_reserve_frames':first['queued'],'last_valid_reserve_frames':last['queued'],
    'reserve_change_frames':produced-consumed,'accepted_growth_frames':produced,'HW_growth_frames':consumed,'accounting_identity_exact':True}
  epoch['valid_prefix_reserve_min_frames']=min((r['queued'] for r in sync),default=None)
  epoch['cumulative_valid_running_reserve']=cumulative
  epoch['valid_CPU_prefix_calls']=len(valid)
  epoch['scaled']=int(s['display_scaled']);epoch['flipped']=int(s['display_flipped'])
  head=kv(d/'headroom.txt')
  epoch['warm_20percent_headroom']=head['sampled_warm_20_percent_headroom']
  epoch['conservative_service_deadline_overruns']=int(head['deadline_overruns'])
  epoch['conservative_service_margin_overruns']=int(head['margin_overruns'])
  epoch['conservative_service_max_ns']=int(head['service_max_ns'])
  if epoch['status']=='CLEAN_BOUNDED_WINDOW':assert epoch['scaled']==epoch['flipped']==1200
  inputs += [d/n for n in ('frames.csv','last-session.txt','headroom.txt','pcm-full.txt','animation.csv','result.txt','begin.txt')]
 comparisons=[]
 for fixture in (1,8):
  for repeat in (2,3):
   for refname,newname,label in [('reference','boundary','boundary_vs_raw'),('boundary','demand','priority_vs_boundary'),('reference','demand','priority_vs_raw')]:
    ref,new=records[(fixture,repeat,refname)],records[(fixture,repeat,newname)]
    common=sorted(set(ref)&set(new));warm=[i for i in common if i>=120]
    fixed={}
    for name,wanted in [('early',range(120,240)),('earlier_heavy',range(384,416)),('late_heavy',range(496,536 if fixture==1 else 542))]:
     selected=[i for i in wanted if i in ref and i in new];complete=len(selected)==len(wanted)
     fixed[name]={'requested_calls':len(wanted),'common_valid_calls':len(selected),'all_frames_valid_in_both':complete,
      'thread_CPU_saving_ms':statistics.mean(ref[i]['threads_cpu']-new[i]['threads_cpu'] for i in selected)/1e6 if complete else None,
      'core_CPU_saving_ms':statistics.mean(int(ref[i]['cpu_ns'])-int(new[i]['cpu_ns']) for i in selected)/1e6 if complete else None}
    windows=[warm[i:i+16] for i in range(max(0,len(warm)-15)) if warm[i+15]-warm[i]==15]
    changes=[(statistics.mean(ref[j]['threads_cpu']-new[j]['threads_cpu'] for j in w)/1e6,w) for w in windows]
    comparisons.append({'fixture':fixture,'repeat':repeat,'comparison':label,'common_valid_calls':len(common),'warm_common_calls':len(warm),
     'warm_common_thread_CPU_saving_ms':statistics.mean(ref[i]['threads_cpu']-new[i]['threads_cpu'] for i in warm)/1e6 if warm else None,
     'warm_common_core_CPU_saving_ms':statistics.mean(int(ref[i]['cpu_ns'])-int(new[i]['cpu_ns']) for i in warm)/1e6 if warm else None,
     'worst_common16_saving_ms':min(changes)[0] if changes else None,'best_common16_saving_ms':max(changes)[0] if changes else None,'fixed_intervals':fixed})
 result['all_common_valid_comparisons']=comparisons
 result['clean_all_epochs']=sum(e['status']=='CLEAN_BOUNDED_WINDOW' for e in result['epochs'])
 result['nominally_complete_but_invalid']=[e['run'] for e in result['epochs'] if e['completed_calls']==1200 and e['status']!='CLEAN_BOUNDED_WINDOW']
 result['APU_compiler_output_stable']=apu['APU_object_byte_identical']
 result['limits'] += ['All-common windows and fixed intervals accompany reference-selected peaks; no selective peak-only speed claims.',
  'Shared APU object fixes compilation but linked layout and other LTO output can differ; pricing is aggregate build cost.',
  'Cumulative reserve is vendor logical accounting over the complete retained running prefix before first pointer drift.']
 result['inputs'].update({p.relative_to(ROOT).as_posix():digest(p) for p in inputs})
 target.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'clean_regression_windows':result['clean_demand_windows'],'cases_clean_both':result['cases_clean_both'],'unresolved':result['unresolved_contexts'],
  'clean_all_epochs':result['clean_all_epochs'],'comparisons':comparisons,'archive':archive.name},indent=2))

if __name__=='__main__':main(Path(sys.argv[1]),'--verify-live' in sys.argv)
