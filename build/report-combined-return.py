"""Read archived native A7 crossover; no unit-price inference or calibration."""
from pathlib import Path
import csv,json,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
def kv(p):return dict(s.split('=',1) for s in p.read_text().splitlines() if '=' in s) if p.exists() else {}
def rows(p):return list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')))
def distribution(a):
 s=sorted(a)
 return {k:v/1000 for k,v in {'mean':statistics.mean(s),'median':statistics.median(s),'p05':s[(len(s)-1)*5//100],'p95':s[(len(s)-1)*95//100],'p99':s[(len(s)-1)*99//100],'max':s[-1]}.items()} if s else None
def analyze(archive):
 assert (archive/'archive.json').exists();base=archive/'retro/snes-combined1';plan=json.loads((base/'plan.json').read_text())
 assert plan['version']=='1.19-combined1' and plan['measurement_only'] and not plan['frameskip']
 records={};reports=[]
 for run in plan['runs']:
  folder=base/f"run-{run['run']:03d}";path=folder/'frames.csv'
  if not path.exists():reports.append({**run,'status':'MISSING'});continue
  h=kv(path);assert h['#mock']=='0','Mock/QEMU cannot supply A7 performance evidence'
  assert h['#suite']==plan['version']
  data=rows(path);head=kv(folder/'headroom.txt');session=kv(folder/'last-session.txt');end=kv(folder/'result.txt');anim=kv(folder/'animation.csv')
  previous=(0,0);valid=True;d={}
  for r in data:
   a,v=int(r['audio_worker_cpu_ns']),int(r['video_worker_cpu_ns']);step,wait=int(r['step_ns']),int(r['pace_wait_ns'])
   sane=a>=previous[0] and v>=previous[1] and wait<=step and int(r['pointer_valid'])!=0
   valid&=sane;r['service_proxy_ns']=step-(wait if wait<=step else 0)+max(0,a-previous[0])+max(0,v-previous[1]);previous=(a,v);d[int(r['frame'])]=r
  raw_service=[r['service_proxy_ns'] for r in d.values()]
  final_service=list(raw_service)
  if final_service:final_service[-1]+=int(head.get('post_last_sample_audio_CPU_ns',0))+int(head.get('post_last_sample_video_CPU_ns',0))
  identity=session.get('core_crc32')==plan['cores'][run['variant']]['crc32'] and session.get('build_version')==plan['version']
  complete=len(d)==1200 and list(d)==list(range(1200)) and session.get('runs')==session.get('video_submitted')==session.get('display_flipped')=='1200' and session.get('held')=='0' and not session.get('error') and end.get('runner_rc')=='0' and end.get('audio_worker_joined')==end.get('display_idle')=='1'
  final_ok=head.get('physical')=='1' and head.get('final_worker_counters_valid')==head.get('final_PCM_software_accounting_exact')=='1' and head.get('final_remaining')==head.get('final_cleared')==head.get('final_audio_error')=='0' and head.get('invalid_accounting')=='0'
  observed=int(anim.get('#matching_property_samples','0'))>0
  status='INVALID_OR_INCOMPLETE' if not(identity and complete and valid and final_ok and observed) else 'NOT_MET' if max(final_service)>plan['target_ns'] else 'MET_IN_RECORDED_SERVICE_PROXY_PENDING_EFFECT_RECOVERY_REVIEW'
  reports.append({**run,'status':status,'identity_verified':identity,'every_frame_completed':complete,'PCM_worker_accounting_valid':valid and final_ok,'expected_properties_observed':observed,'rows':len(data),'frequency_values_khz':sorted({int(r[k]) for r in data for k in ('freq_before_khz','freq_after_khz')}),'pin':h.get('#pin'),'restore':h.get('#restore'),'service_proxy_us':distribution(final_service),'headroom':head,'native_generated':session.get('native_audio_frames'),'last_error':session.get('error'),'production_gate_passed':False})
  records[(run['fixture'],run['repeat'],run['variant'])]=d
 targets={c['case']:c['tail_frames'] for c in json.loads((ROOT/'evidence/2026-10-13/full-fidelity-paths/prediction.json').read_text())['cases']};comparisons=[]
 for c in plan['cases']:
  for repeat in range(2):
   for before,after in (('baseline','prior'),('baseline','combined'),('prior','combined')):
    a=records.get((c['seq'],repeat,before),{});b=records.get((c['seq'],repeat,after),{});wanted=targets[c['seq']];common=[i for i in wanted if i in a and i in b]
    result={'fixture':c['seq'],'name':c['name'],'repeat':repeat,'before':before,'after':after,'wanted_frames':wanted,'common_frames':common,'aligned_interval_complete':wanted==common}
    if common:
     for metric in ('cpu_ns','wall_ns','step_ns','service_proxy_ns'):result[metric+'_saving_us']=distribution([int(a[i][metric])-int(b[i][metric]) for i in common])
     service=[b[i]['service_proxy_ns'] for i in common];result['candidate_service_proxy_us']=distribution(service);result['mean_deadline_margin_us']=(plan['period_ns']-statistics.mean(service))/1000;result['mean_20_percent_margin_us']=(plan['target_ns']-statistics.mean(service))/1000
    comparisons.append(result)
 result={'suite':plan['version'],'runs':reports,'matched_comparisons':comparisons,'production_gate_passed':False,'frameskip':False,'observers_included':True,'limitations':['Conservative wall plus worker CPU may double-count overlap.','Final unobserved worker CPU is charged to last sampled call; cleanup drain wall is reported separately.','Full effect/recovery reserve and physical frame delivery must be reviewed before production acceptance.','Missing frames, pointer drift, undrained/discarded PCM, final errors and incomplete intervals cannot pass.','New A7 comparison is whole-combination saving, not isolated per-entry prices.']}
 out=archive/'combined-analysis';out.mkdir(exist_ok=True);(out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 r=analyze(Path(sys.argv[1]).resolve());print(json.dumps({'runs':len(r['runs']),'comparisons':len(r['matched_comparisons']),'production_gate_passed':False}))
