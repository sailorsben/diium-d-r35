"""Freeze a concrete offline-qualified diagnostic without installing it."""
from pathlib import Path
from hashlib import sha256
import json,runpy,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/current-pc-profile-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not (OUT/'ready.json').exists()
 q=json.loads((OUT/'verification.json').read_text());assert q['passed'] and len(q['actual_epochs'])==4
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for n,h in q[group].items():assert digest(ROOT/n if group=='source_hashes' else OUT/n)==h,n
 shutil.copy2(OUT/'plan.json',OUT/'mock/plan.json')
 m=runpy.run_path(str(ROOT/'build/analyze-main-pc.py'));r=m['analyze'](OUT/'mock',True)
 assert not r['physical'] and len(r['runs'])==2 and all(x['selected_samples']>0 and x['selection']=='mock_frames_without_physical_validity' for x in r['runs'])
 try:m['analyze'](OUT/'mock',False)
 except AssertionError:pass
 else:raise AssertionError('Physical PC analyzer accepted mock')
 (OUT/'mock/main-pc-analysis.json').write_text(json.dumps(r,indent=2)+'\n')
 files=[ROOT/'build'/n for n in ('main-pc-sampler.h','check-main-pc-sampler.c','check-main-pc-sampler.sh','analyze-main-pc.py','install-current-pc-profile.py','finalize-current-pc-profile.py')]
 files += [OUT/n for n in ('main-pc-sampler.h','build.sh','qualify.py')]+[ROOT/'docs/snes-pc-profile-test.txt']
 ready={'version':'1.19-pc-profile1','ready':True,'installed':False,'armed':False,'card_writes':0,'measurement_only':True,'production_gate_passed':False,
  'verification_sha256':digest(OUT/'verification.json'),'additional_sources':{p.relative_to(ROOT).as_posix():digest(p) for p in files},
  'same_exact_core_both_variants':True,'raw_core_sha256':'1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8',
  'controller_calls':4800,'host_and_ARM_sampler_lifecycle_checked':True,'actual_native_PCM_sampler_checked':True,'physical_mock_rejection':True,
  'A7_timer_support_verified':False,'A7_function_time_distribution_measured':False,'installation_authorized_by_this_receipt':False,
  'limits':['Host/ARM-QEMU checks establish sampling/lifecycle only.','Timer delivery coalesces; no invented1ms resolution or overrun weighting.','A7 main-thread ownership remains pending this actual diagnostic return.']}
 (OUT/'ready.json').write_text(json.dumps(ready,indent=2)+'\n')
 print('PASS local PC diagnostic/controller/native/reporter; concrete ready packet, not installed or armed')
if __name__=='__main__':main()
