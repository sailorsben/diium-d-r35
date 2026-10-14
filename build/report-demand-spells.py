"""Archive-only per-effect completion, reserve and matched aggregate CPU review."""
from pathlib import Path
from hashlib import sha256
import csv,json,re,statistics,sys
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l) if p.exists() else {}
def rows(p):return list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')))
def analyze(base,allow_mock=False):
 plan=json.loads((base/'plan.json').read_text());assert plan['version']=='1.19-demand-spells1' and not plan['frameskip']
 reports=[];records={}
 for run in plan['runs']:
  d=base/f"run-{run['run']:03d}";path=d/'frames.csv'
  if not path.exists():reports.append({**run,'status':'MISSING'});continue
  metadata=kv(path);mock=metadata['#mock']=='1'
  assert allow_mock or not mock,'Mock telemetry is not physical evidence'
  data=rows(path);session=kv(d/'last-session.txt');head=kv(d/'headroom.txt');end=kv(d/'result.txt');anim=kv(d/'animation.csv')
  identity=session.get('core_crc32')==plan['cores'][run['variant']]['crc32'] and session.get('build_version')==plan['version']
  complete=len(data)==1200 and [int(r['frame']) for r in data]==list(range(1200)) and session.get('runs')==session.get('video_submitted')=='1200' and session.get('held')==session.get('video_dupes')=='0' and not session.get('error') and end.get('runner_rc')=='0'
  complete=complete and end.get('audio_worker_joined')==end.get('display_idle')=='1'
  PCM_ok=head.get('final_PCM_software_accounting_exact')=='1' and head.get('final_remaining')==head.get('final_cleared')==head.get('final_audio_error')=='0'
  effect=int(anim.get('#matching_property_samples','0'))>0
  prefix={};previous_a=previous_v=0;valid=True
  for row in data:
   a,v=int(row['audio_worker_cpu_ns']),int(row['video_worker_cpu_ns'])
   sane=int(row['pointer_valid'])==1 and a>=previous_a and v>=previous_v and int(row['pace_wait_ns'])<=int(row['step_ns'])
   valid=valid and sane
   if valid:
    row['recorded_thread_CPU_ns']=int(row['main_step_cpu_ns'])+a-previous_a+v-previous_v
    prefix[int(row['frame'])]=row
   previous_a,previous_v=a,v
  warm=[r for i,r in prefix.items() if i>=plan['warmup_calls']]
  windows=[warm[i:i+16] for i in range(max(0,len(warm)-15))]
  worst=max(windows,key=lambda w:statistics.mean(int(r['recorded_thread_CPU_ns']) for r in w)) if windows else []
  worst_mean=statistics.mean(int(r['recorded_thread_CPU_ns']) for r in worst) if worst else None
  pcm=kv(d/'pcm-full.txt');sync=[];pointer_faults=[]
  if (d/'pcm-full.txt').exists():
   pattern=r'seq=(\d+) ns=(\d+) op=(\S+) arg=(\d+) result=(-?\d+) state=(\d+) queued=(\d+) appl=(\d+) hw=(\d+) epoch=(\d+) xfer=(\d+)'
   boundary=int(session.get('pcm_boundary_frames','0'));buffer=int(session.get('pcm_buffer_frames','0'))
   for m in re.finditer(pattern,(d/'pcm-full.txt').read_text()):
    seq,ns,op,arg,result,state,queued,appl,hw,epoch,xfer=m.groups()
    if op=='SYNC_OK' and int(state)==3:
     good=boundary>0 and int(appl)%boundary==int(xfer)%boundary and (int(appl)-int(hw))%boundary==int(queued) and int(queued)<=buffer
     if good:sync.append({'seq':int(seq),'ns':int(ns),'queued':int(queued),'epoch':int(epoch),'xfer':int(xfer)})
     else:pointer_faults.append(int(seq))
  trace_complete=pcm.get('retained_from')=='0'
  status='NOT_PHYSICAL' if mock else 'CLEAN_BOUNDED_WINDOW' if identity and complete and PCM_ok and effect and valid and trace_complete and not pointer_faults else 'INVALID_OR_INCOMPLETE'
  reports.append({**run,'status':status,'identity_verified':identity,'complete_window':complete,'effect_properties_observed':effect,
   'PCM_final_accounting_exact':PCM_ok,'all_frame_pointer_samples_valid':valid,'valid_CPU_prefix_calls':len(prefix),
   'PCM_trace_retained_from':pcm.get('retained_from'),'complete_PCM_trace':trace_complete,'invalid_running_sync_sequences':pointer_faults,
   'valid_running_sync_samples':len(sync),'minimum_valid_running_pointer_reserve_frames':min((r['queued'] for r in sync),default=None),
   'worst16_valid_CPU_frames':[int(r['frame']) for r in worst],'worst16_recorded_threads_CPU_mean_ms':worst_mean/1e6 if worst_mean is not None else None,
   'worst16_remaining_to_deadline_ms':(plan['period_ns']-worst_mean)/1e6 if worst_mean is not None else None,
   'worst16_remaining_to20percent_ms':(plan['target_ns']-worst_mean)/1e6 if worst_mean is not None else None,
   'final_direct_submitted':int(data[-1]['direct_submitted']) if data else None,'final_copied_payload_bytes':int(data[-1]['copied_payload_bytes']) if data else None,
   'core_error':session.get('error'),'PCM_failure':pcm.get('failure'),'production_gate_passed':False})
  records[(run['fixture'],run['repeat'],run['variant'])]=prefix
 comparisons=[]
 for fixture in (1,8):
  for repeat in range(2):
   ref=records.get((fixture,repeat,'reference'),{});new=records.get((fixture,repeat,'demand'),{})
   both=sorted(set(ref)&set(new));warm=[i for i in both if i>=plan['warmup_calls']]
   # Select the reference's heaviest retained16-call interval, then match exact indices.
   windows=[warm[i:i+16] for i in range(max(0,len(warm)-15)) if warm[i+15]-warm[i]==15]
   chosen=max(windows,key=lambda w:statistics.mean(int(ref[j]['recorded_thread_CPU_ns']) for j in w)) if windows else []
   saving=statistics.mean(int(ref[j]['recorded_thread_CPU_ns'])-int(new[j]['recorded_thread_CPU_ns']) for j in chosen)/1e6 if chosen else None
   comparisons.append({'fixture':fixture,'repeat':repeat,'matched_common_calls':len(both),'reference_heavy_matched_frames':chosen,'mean_recorded_thread_CPU_saving_ms':saving,
    'interpretation':'whole combination, observers included; retained prefix only; cannot price each optimization'})
 return {'version':plan['version'],'physical_result':not allow_mock,'epochs':reports,'matched_Meteor_Quasar':comparisons,'production_gate_passed':False,
 'limits':['Frame-property matches are bounded observed branches, not proof of every conditional outcome.','A complete bounded window needs separate effect/recovery interpretation and physical panel/speaker observation.',
 'Distinct measured thread CPU omits other processes/kernel work and post-last-sample worker residuals; headroom remains provisional.','Pointer consistency is not independent kernel correctness; full trace loss or drift prevents reserve acceptance.',
 'Only Meteor/Quasar have matched controls; no per-optimization prices or timer calibration subtraction.']}
if __name__=='__main__':
 root=Path(sys.argv[1]).resolve();mock='--mock-qualification' in sys.argv
 if not mock:
  assert (root/'archive.json').exists(),'Use a strict return archive'
  archive=json.loads((root/'archive.json').read_text());assert archive['fat_clean'] and archive['card_writes']==0
  for e in archive['all_retro_files']:assert sha256((root/e['path']).read_bytes()).hexdigest()==e['sha256'],e['path']
  root=root/'retro/snes-demand-spells1'
  plan=json.loads((root/'plan.json').read_text())
  for name,identity in plan['cores'].items():assert sha256((root/f'cores/{name}.so').read_bytes()).hexdigest()==identity['sha256']
 result=analyze(root,mock);out=root/'spell-analysis.json';out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'analysis':str(out),'epochs':len(result['epochs']),'physical':result['physical_result'],'production_gate_passed':False}))
