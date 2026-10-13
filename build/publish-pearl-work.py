"""Publish bounded work/correctness evidence. Never raw state/ROM, A7 prices or installs."""
from pathlib import Path
from hashlib import sha256
from importlib.util import spec_from_file_location,module_from_spec
import json,statistics
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return [list(map(int,l[6:].split(','))) for l in p.read_text().splitlines() if l.startswith('PEARL ')]
def main():
 out=ROOT/'build/pearl-sub-private-v2';first=ROOT/'build/pearl-paths-private-v1'
 qs=[json.loads((p/'qualification.json').read_text()) for p in (first,out)]
 assert all(q['passed'] and not q['A7_saving_measured'] and not q['production_gate_passed'] for q in qs)
 for p,q in zip((first,out),qs):
  for proof in q['exact_comparisons']:
   log=p/proof['kind']/f"exact/{proof['case']:03d}-{proof['label']}.log"
   assert digest(log)==proof['log_sha256'] and 'PASS 1200 calls' in log.read_text()
   core=p/proof['kind']/('plus-a7.so' if proof['label']=='ordinary' else 'counted-core/snes9x2005_plus_libretro.so')
   assert digest(core)==proof['core_sha256']
 shape=ROOT/'build/pearl-shapes-private-v1/holy.log';base=ROOT/'build/pearl-work-private-v1/holy.log'
 a=read(shape);assert len(a)==1200 and 'PASS 1200 calls' in shape.read_text()
 means={str(j):statistics.mean(a[i][j+1] for i in range(399,415)) for j in range(310,327)}
 seams=[first/'clipping-exact.log',first/'clipping-candidate.log',first/'flat-check.log',out/'clipping-exact.log',out/'clipping-candidate.log']
 assert all('PASS' in p.read_text() for p in seams)
 need=4310.0389-1000;h=4763;s=4569
 prediction={'A7_measured':False,'production_gate_passed':False,'prior_staged_combination_saving_us':1000,'prior_is_judgment':True,'total_required_us':4310.0389,'conditional_remaining_us':need,'early_successful_calls':h,'sole_sub_calls':s,'inequality':'4763*h + 4569*s - b >= 4310.0389 - P; microseconds, P is measured staged combined saving when available','equal_net_unit_threshold_us':need/(h+s),'early_only_threshold_us':need/h,'sole_sub_only_threshold_us':need/s,'equal_net_with_250us_other_cost':(need+250)/(h+s),'scenarios':[{'h_us':x,'s_required_us_if_b_zero':(need-h*x)/s} for x in (0,.2,.35,.5)],'limits':['Counts and original-output equality are offline evidence, not A7 time.','Threshold assumes prior P=1000us; replace with staged A7 combined result.','No guarantee of 20 percent headroom or universal coverage.','No card reads/writes or changed staged payloads.']}
 shapes={'passed_exact_1200_calls':True,'log_sha256':digest(shape),'tail_frames':list(range(399,415)),'means':means,'schema':{'310':'sole_BG3_sub_scanlines','311':'those_with_8x8_2bpp_tiles','312':'only_BG3_enabled','313':'ordinary_geometry','314':'no_effective_clip','320':'flat_helper_attempts','321':'map_mismatch_returns','322':'nonuniform_plane_returns','323':'flat_helper_successes','324':'same_index_sub_rows','325':'same_color_sub_rows','326':'opaque_sub_rows'},'conclusion':'16x16, opaque but no uniform full rows; flat path does not activate'}
 proof={'passed':True,'ordinary_command_replay_calls':sum(q['new_calls'] for q in qs),'original_command_contexts':18,'variants':['early_depth','flat_band_inactive','early_depth_plus_flat_inactive','sole_sub','early_depth_plus_sole_sub'],'counted_and_counterfree':True,'base_census_calls':1200,'shape_probe_calls':1200,'independent_depth_cases':64512,'independent_sole_sub_cases':2304,'independent_flat_cases':258048,'flat_rejection_cases':4,'seam_logs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'text':p.read_text()} for p in seams],'negative_results':['BG1/BG2 shared-producer eligibility is zero for Pearl.','Flat band passes oracle but never activates in Pearl.','Sub v1 output mismatch at frame264 from generated dangling else; corrected in v2.','Initial census export visibility and nested sysroot path failed before qualification.','Legacy overlay runner lacks required symbols in these cores: startup failures, no 406-overlay coverage claimed.'],'card_writes':0,'A7_saving_measured':False,'production_gate_passed':False}
 frozen=json.loads((ROOT/'build/fullpaths-private-v2/verification.json').read_text());checked={}
 for key in ('source_hashes','payload_hashes','proof_hashes'):
  for name,expected in frozen[key].items():assert digest(ROOT/name)==expected,name
  checked[key]=len(frozen[key])
 proof['staged_local_identity_unchanged']=checked
 spec=spec_from_file_location('publish',ROOT/'build/publish-snes-1.19.py');m=module_from_spec(spec);spec.loader.exec_module(m)
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();prior=json.loads(raw)['entries']
 for e in prior:assert digest(ROOT/e['published'])==e['published_sha256']
 public=ROOT/'evidence/2026-10-13/pearl-workback';assert not public.exists();public.mkdir();entries=[]
 for name,data in [('paths-qualified.json',qs[0]),('sub-qualified.json',qs[1]),('shapes.json',shapes),('prediction.json',prediction),('verification.json',proof)]:
  src=out/('public-'+name);src.write_text(json.dumps(data,indent=2)+'\n');dest=public/name;dest.write_bytes(m.public_text(src.read_bytes()))
  entries.append({'source':src.relative_to(ROOT).as_posix(),'published':dest.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(dest)})
 manifest.write_bytes(m.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(prior)]==prior
 print('Published five bounded receipts;',proof['ordinary_command_replay_calls'],'exact calls;',checked,'frozen identities checked; old',len(prior),'entries preserved; A7 gate false')
if __name__=='__main__':main()
