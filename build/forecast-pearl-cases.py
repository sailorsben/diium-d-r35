"""Conditional planning table for failed contexts actually staged on I:.
No card access or measured A7 price is inferred from the offline populations.
"""
from pathlib import Path
from hashlib import sha256
from importlib.util import spec_from_file_location,module_from_spec
import json,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert sys.argv[1:] in ([],['--publish'])
 prediction=json.loads((ROOT/'evidence/2026-10-13/full-fidelity-paths/prediction.json').read_text())
 staged=json.loads((ROOT/'evidence/2026-10-13/fullpaths-measurement/plan.json').read_text())
 q=json.loads((ROOT/'evidence/2026-10-13/pearl-workback/sub-qualified.json').read_text())
 cases=[];controls=[]
 for context in staged['contexts']:
  c=next(c for c in prediction['cases'] if c['case']==context['fixture'])
  if not c['physical_fixture_failed']:controls.append(c['name']);continue
  log=ROOT/f"build/pearl-sub-private-v2/both/exact/{c['case']:03d}-census.log"
  proof=next(r for r in q['exact_comparisons'] if r['kind']=='both' and r['label']=='census' and r['case']==c['case'])
  assert digest(log)==proof['log_sha256']
  a=[list(map(int,l[6:].split(','))) for l in log.read_text().splitlines() if l.startswith('PEARL ')]
  assert len(a)==1200 and [r[0] for r in a]==list(range(1200))
  h=statistics.mean(sum(a[i][1+(plane*6+bg)*24+20] for plane in range(2) for bg in range(5)) for i in c['tail_frames'])
  sub=statistics.mean(a[i][333] for i in c['tail_frames'])
  # Transfer the explicit Pearl subscreen/DSP judgments by eligible work only.
  # This is a new assumption across effects, not an empirical calibration.
  old_other=sum(c['new_subscreen_fast_rows_mean'].values())*300/4166+c['DSP_mean']['zero_envelope']*200/1372.25
  staged_range=[c['removed']['renderer_entries']*e+old_other for e in (21.2210366,23.5372807)]
  latest_range=[(h+sub)*u for u in (.3,.4)]
  total=[x+y for x,y in zip(staged_range,latest_range)]
  step=[c['baseline_step_us']-total[1],c['baseline_step_us']-total[0]]
  cases.append({'fixture':c['case'],'name':c['name'],'baseline_version':'ability2','baseline_step_us':c['baseline_step_us'],'aligned_frames':c['tail_frames'],'log_sha256':digest(log),'early_removed_calls':h,'sole_sub_calls':sub,'staged_planning_saving_us':staged_range,'latest_planning_saving_us':latest_range,'total_planning_saving_us':total,'conditional_service_step_us':step,'entire_range_below_deadline':step[1]<prediction['period_us'],'entire_range_below_20pct_target':step[1]<prediction['proposed_total_step_target_us']})
 result={'staged_version':staged['version'],'latest_paths_installed':False,'A7_new_prices_measured':False,'scenario_is_confidence_interval':False,'all_frames_retained':True,'card_access':False,'deadline_us':prediction['period_us'],'target_20pct_us':prediction['proposed_total_step_target_us'],'assumptions':['Historical fixed-row restart-bundle transfer range; not isolated entry prices.','Transfer Pearl judgment of300us/4166 eligible subscreen rows and200us/1372.25 omitted interpolations to other contexts; unmeasured and uncertain.','New early/sub calls each save0.30 to0.40us net; illustrative price scenarios, not a measured or bounded range.','Other added costs/interactions b=0; subtract measured b from saving.','Saved CPU translates into failed-tail service reduction; tail means are not complete-effect or worst-case guarantees.'],'cases':cases,'completed_controls_without_new_headroom_claim':controls,'control_limit':'Healthy paced wall duration cannot be reduced into an active-service prediction without intentional-wait accounting.'}
 out=ROOT/'build/pearl-sub-private-v2/forecast-cases.json';out.write_text(json.dumps(result,indent=2)+'\n')
 if sys.argv[1:]:
  spec=spec_from_file_location('publish',ROOT/'build/publish-snes-1.19.py');m=module_from_spec(spec);spec.loader.exec_module(m)
  manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();prior=json.loads(raw)['entries']
  for e in prior:assert digest(ROOT/e['published'])==e['published_sha256']
  dest=ROOT/'evidence/2026-10-13/pearl-workback/forecast-cases.json';assert not dest.exists();dest.write_bytes(m.public_text(out.read_bytes()))
  manifest.write_bytes(m.append_manifest(raw,[{'source':out.relative_to(ROOT).as_posix(),'published':dest.relative_to(ROOT).as_posix(),'source_sha256':digest(out),'published_sha256':digest(dest)}]))
  assert json.loads(manifest.read_bytes())['entries'][:len(prior)]==prior
 for c in cases:print(c['name'],*[f'{v/1000:.2f}' for v in [c['baseline_step_us'],*c['total_planning_saving_us'],*c['conditional_service_step_us']]])
if __name__=='__main__':main()
