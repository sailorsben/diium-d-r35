"""Read archived physical crossover; same-frame differences, no clock calibration."""
from pathlib import Path
import csv,json,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
def rows(p):return list(csv.DictReader(s for s in p.read_text().splitlines() if not s.startswith('#')))
def kv(p):return dict(s.split('=',1) for s in p.read_text().splitlines() if '=' in s)
def quantile(values,p):
 a=sorted(values);return a[int((len(a)-1)*p)] if a else None
def service(r,previous):
 a,v=int(r['audio_worker_cpu_ns']),int(r['video_worker_cpu_ns']);pa,pv=previous
 return int(r['step_ns'])-int(r['pace_wait_ns'])+max(0,a-pa)+max(0,v-pv),(a,v)
def analyze(archive):
 base=archive/'retro/snes-fullpaths1';plan=json.loads((base/'plan.json').read_text());assert plan['measurement_only'] and not plan['frameskip']
 assert (archive/'archive.json').exists();records={};run_reports=[]
 for run in plan['runs']:
  folder=base/f"run-{run['run']:03d}";path=folder/'frames.csv'
  if not path.exists():run_reports.append({**run,'status':'MISSING'});continue
  header=kv(path);data=rows(path);assert header['#mock']=='0','QEMU/null backend is not physical evidence'
  previous=(0,0);d={}
  for r in data:
   active,previous=service(r,previous);r['service_proxy_ns']=active;d[int(r['frame'])]=r
  records[(run['fixture'],run['repeat'],run['variant'])]=d
  h=kv(folder/'headroom.txt') if (folder/'headroom.txt').exists() else {}
  session=kv(folder/'last-session.txt') if (folder/'last-session.txt').exists() else {}
  identity=session.get('core_crc32')==plan['cores'][run['variant']]['crc32'] and session.get('build_version')==plan['version']
  every=session.get('runs')==session.get('video_submitted')==session.get('display_flipped')=='1200' and session.get('held')=='0' and not session.get('error')
  # Cold frames stay in the all-call verdict; final peripheral service remains
  # a separate boundary, so neither this nor the warm flag is production proof.
  all_service=[int(r['service_proxy_ns']) for r in d.values()]
  accounting=bool(d) and all(int(r['pointer_valid']) and int(r['pace_wait_ns'])<=int(r['step_ns']) for r in d.values())
  verdict='INVALID_OR_INCOMPLETE' if not(identity and every and accounting and len(d)==1200) else 'NOT_MET' if max(all_service)>plan['target_ns'] else 'MET_IN_RECORDED_CALLS_PENDING_FINAL_WORKER_AND_RECOVERY_REVIEW'
  run_reports.append({**run,'rows':len(data),'failed':header.get('#failed'),'headroom':h,'identity_verified':identity,'every_frame_reported':every,'all_recorded_call_20_percent_headroom':verdict,'all_recorded_call_max_service_proxy_us':max(all_service)/1000 if all_service else None,'native_generated':int(data[-1]['native_generated']) if data else 0,'frequency_values_khz':sorted({int(r[k]) for r in data for k in ('freq_before_khz','freq_after_khz')}),'pin':header.get('#pin'),'restore':header.get('#restore')})
 targets={c['case']:c['tail_frames'] for c in json.loads((ROOT/'evidence/2026-10-13/full-fidelity-paths/prediction.json').read_text())['cases']}
 comparisons=[]
 for c in plan['cases']:
  for repeat in range(2):
   baseline=records.get((c['seq'],repeat,'baseline'),{});deltas={}
   for variant in ('fixed','subscreen','dsp','combined'):
    candidate=records.get((c['seq'],repeat,variant),{});wanted=targets[c['seq']];common=[i for i in wanted if i in baseline and i in candidate]
    out={'fixture':c['seq'],'name':c['name'],'repeat':repeat,'variant':variant,'wanted_frames':wanted,'common_frames':common,'aligned_interval_complete':common==wanted}
    if common:
     # Terminal failed rows are retained separately; a partial overlap cannot pass.
     for metric in ('cpu_ns','wall_ns','step_ns','service_proxy_ns'):
      vals=[int(baseline[i][metric])-int(candidate[i][metric]) for i in common]
      out[metric+'_saving_us']={'mean':statistics.mean(vals)/1000,'median':statistics.median(vals)/1000,'p05':quantile(vals,.05)/1000,'p95':quantile(vals,.95)/1000}
     deltas[variant]=out['cpu_ns_saving_us']['mean']
     active=[int(candidate[i]['service_proxy_ns']) for i in common]
     out['candidate_service_proxy_mean_us']=statistics.mean(active)/1000
     out['candidate_service_proxy_p95_us']=quantile(active,.95)/1000
     out['candidate_service_proxy_max_us']=max(active)/1000
     out['mean_deadline_margin_us']=(plan['period_ns']-statistics.mean(active))/1000
     out['mean_20_percent_margin_us']=(plan['target_ns']-statistics.mean(active))/1000
    comparisons.append(out)
   if len(deltas)==4:comparisons.append({'fixture':c['seq'],'repeat':repeat,'CPU_combination_extra_vs_sum_us':deltas['combined']-sum(deltas[v] for v in ('fixed','subscreen','dsp')),'interpretation':'interaction and run variability, not additive unit prices'})
 result={'suite':plan['version'],'runs':run_reports,'matched_comparisons':comparisons,'production_gate_passed':False,'observers_included':True,'frameskip':False,'limitations':['Proxy conservatively double counts some worker CPU; frequency may be unexposed.','Finite samples and tail means do not certify every spell or worst-case hardware capacity.','Completed warm sample flag requires independent effect/recovery, pointer, frame, quota and reserve review.']}
 out=archive/'fullpaths-analysis';out.mkdir(exist_ok=True);(out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'retained_runs':len(records),'comparisons':len(comparisons),'output':str(out/'analysis.json')},indent=2))
 return result
if __name__=='__main__':analyze(Path(sys.argv[1]).resolve())
