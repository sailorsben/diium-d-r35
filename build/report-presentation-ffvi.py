"""Archive-bound FFVI acceptance and matched valid-prefix report. No live writes."""
from pathlib import Path
from hashlib import sha256
import argparse,csv,json,re,statistics
def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l) if p.exists() else {}
def rows(p):return list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')))
def analyze(base,plan,allow_mock=False):
 reports=[];prefixes={};any_mock=False
 supervisor=kv(base/'supervisor.txt');summary=kv(base/'suite-result.txt')
 safe_teardown=supervisor.get('forced')=='0' and supervisor.get('reaped')=='1' and summary.get('board_closed')=='1'
 for run in plan['runs']:
  d=base/f"run-{run['run']:03d}";s=kv(d/'last-session.txt');begin=kv(d/'begin.txt');end=kv(d/'result.txt')
  if not s or not (d/'frames.csv').exists():reports.append({**run,'status':'MISSING'});continue
  mock=s.get('mock_backend')=='1';any_mock|=mock;assert allow_mock or not mock,'Mock telemetry is not physical evidence'
  f=rows(d/'frames.csv');trace=kv(d/'pcm-full.txt');head=kv(d/'headroom.txt');anim=kv(d/'animation.csv')
  correct=all(begin.get(k)==str(run[k]) for k in ('fixture','policy','repeat','load_ms'))
  complete=len(f)==1200 and [int(x['frame']) for x in f]==list(range(1200)) and s.get('runs')==s.get('rendered_frames')=='1200' and end.get('runner_rc')=='0' and not s.get('error')
  rendered=int(s.get('rendered_frames','0'));submitted=int(s.get('video_submitted','0'));skipped=int(s.get('presentation_skipped','0'))
  video=rendered==submitted+skipped and int(s.get('display_scaled','-1'))==int(s.get('display_flipped','-1'))==submitted and s.get('video_dupes')==s.get('held')=='0'
  video=video and (run['policy']!=0 or skipped==0) and (not f or int(f[-1]['rendered'])==rendered and int(f[-1]['skipped'])==skipped)
  pcm=head.get('final_PCM_software_accounting_exact')=='1' and head.get('final_remaining')==head.get('final_cleared')==head.get('final_audio_error')=='0'
  effect=int(anim.get('#matching_property_samples','0'))>0
  boundary=int(s.get('pcm_boundary_frames','0'));buffer=int(s.get('pcm_buffer_frames','0'));running=[];bad=[];valid_trace=True
  pattern=r'seq=(\d+) ns=(\d+) op=(\S+) arg=(\d+) result=(-?\d+) state=(\d+) queued=(\d+) appl=(\d+) hw=(\d+) epoch=(\d+) xfer=(\d+)'
  parsed=list(re.finditer(pattern,(d/'pcm-full.txt').read_text())) if (d/'pcm-full.txt').exists() else []
  trace_complete=trace.get('retained_from')=='0' and len(parsed)==int(trace.get('entries_total','-1'))
  for m in parsed:
   seq,ns,op,arg,result,state,q,appl,hw,epoch,xfer=m.groups()
   if int(result)<0 and int(result) not in (-11,-4):valid_trace=False
   if op=='SYNC_OK' and state=='3':
    good=boundary>0 and int(appl)%boundary==int(xfer)%boundary and (int(appl)-int(hw))%boundary==int(q) and int(q)<=buffer
    if not good:valid_trace=False;bad.append(int(seq))
    if valid_trace:running.append({'seq':int(seq),'ns':int(ns),'queued':int(q),'epoch':int(epoch)})
  prefix={};previous_a=previous_v=0;valid=True
  for row in f:
   a,v=int(row['audio_worker_cpu_ns']),int(row['video_worker_cpu_ns']);b=int(s.get('pcm_boundary_frames','0'))
   sane=b>0 and int(row['appl'])%b==int(row['xfer'])%b and (int(row['appl'])-int(row['hw']))%b<=buffer
   valid=valid and sane and row['pointer_valid']=='1' and a>=previous_a and v>=previous_v and int(row['pace_wait_ns'])<=int(row['step_ns'])
   if valid:prefix[int(row['frame'])]={**row,'threads_cpu_ns':int(row['main_step_cpu_ns'])+a-previous_a+v-previous_v}
   previous_a,previous_v=a,v
  loads=int(f[-1]['load_events']) if f else 0;expected_loads=7 if run['load_ms'] else 0
  joins=end.get('audio_worker_joined')==end.get('display_idle')=='1'
  accepted=not mock and correct and complete and video and pcm and effect and valid and valid_trace and trace_complete and bool(running) and loads==expected_loads and joins and safe_teardown
  reports.append({**run,'status':'NOT_PHYSICAL' if mock else 'CLEAN_BOUNDED_WINDOW' if accepted else 'INVALID_OR_INCOMPLETE',
   'complete_window':complete,'video_accounting':video,'rendered':rendered,'submitted':submitted,'skipped':skipped,
   'PCM_final_exact':pcm,'complete_trace':trace_complete,'valid_PCM_prefix_observations':len(running),'invalid_running_sequences':bad,
   'minimum_valid_reserve_frames':min((x['queued'] for x in running),default=None),'expected_effect_observed':effect,
   'valid_CPU_prefix_calls':len(prefix),'load_events':loads,'core_error':s.get('error'),'production_gate':False})
  prefixes[run['run']]=prefix
 comparisons=[]
 for fixture in range(18):
  for load in ([0,24,48] if fixture==0 else [0]):
   group=[r for r in plan['runs'] if r['fixture']==fixture and r['load_ms']==load]
   by_repeat={r['repeat']:r for r in group}
   for a,b in ((0,1),(3,2)):
    if a not in by_repeat or b not in by_repeat:continue
    ref,new=by_repeat[a],by_repeat[b];x,y=prefixes.get(ref['run'],{}),prefixes.get(new['run'],{})
    common=[i for i in sorted(set(x)&set(y)) if i>=120]
    comparisons.append({'fixture':fixture,'load_ms':load,'control_run':ref['run'],'candidate_run':new['run'],'common_warm_valid_calls':len(common),
      'mean_recorded_threads_CPU_saving_ms':statistics.mean(x[i]['threads_cpu_ns']-y[i]['threads_cpu_ns'] for i in common)/1e6 if common and not any_mock else None,
      'interpretation':'Matched valid frame indices; observers included, wall waits are not CPU saving; no physical promotion from prefix alone.'})
 return {'version':'presentation-ffvi1','physical':not any_mock,'safe_teardown':safe_teardown,'epochs':reports,'comparisons':comparisons,'production_gate':False,
         'limits':['Manual panel/input/speaker acceptance remains required.','Final recovery must be analyzed from complete valid raw reserve history and executed-load frame times; sampled minima are not continuous minima.','Failed/censored prefixes do not pass a1200-frame window.']}
def main():
 p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--mock',action='store_true');p.add_argument('--installation',type=Path);a=p.parse_args()
 if a.mock:
  root=a.archive.resolve();plan=json.loads((root.parent/'plan.json').read_text())
 else:
  archive=a.archive.resolve();meta=json.loads((archive/'archive.json').read_text());assert meta['fat_clean'] and meta['card_writes']==0
  for e in meta['all_retro_files']:assert digest(archive/e['path'])==e['sha256']
  assert a.installation is not None,'Use the frozen installation receipt'
  installed=json.loads(a.installation.read_text());assert installed['version']=='presentation-ffvi1'
  target=archive/'retro/snes-presentation-ffvi1'
  for n,h in installed['payload_hashes'].items():assert digest(target/n)==h,n
  assert digest(target/'launch.sh')==installed['payload_hashes']['launch.sh']
  runs=list((target/'results').glob('run-*'));assert len(runs)==1,'Select the exact returned run explicitly if repeated'
  root=runs[0];plan=json.loads((target/'plan.json').read_text())
 result=analyze(root,plan,a.mock);out=root/'presentation-analysis.json';out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'epochs':len(result['epochs']),'accepted':sum(r['status']=='CLEAN_BOUNDED_WINDOW' for r in result['epochs']),'physical':result['physical'],'report':str(out)}))
if __name__=='__main__':main()
