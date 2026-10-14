"""Freeze and publish measurement readiness after actual-controller qualification."""
from pathlib import Path
from hashlib import sha256
import json,runpy,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ppu-test-private-v1'
DEST=ROOT/'evidence/2026-10-14/ppu-test'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not DEST.exists() and not (OUT/'ready.json').exists()
 q=json.loads((OUT/'verification.json').read_text());assert q['passed'] and len(q['actual_epochs'])==56
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for n,h in q[group].items():assert digest(ROOT/n if group=='source_hashes' else OUT/n)==h,n
 shutil.copy2(OUT/'plan.json',OUT/'mock/plan.json')
 reporter=runpy.run_path(str(OUT/'report.py'));a=reporter['analyze'](OUT/'mock',True)
 assert len(a['epochs'])==56 and all(r['status']=='NOT_PHYSICAL' and r['identity_verified'] and r['complete_window'] and r['PCM_final_accounting_exact'] and r['effect_properties_observed'] for r in a['epochs'])
 assert len(a['matched_Meteor_Quasar'])==16
 try:reporter['analyze'](OUT/'mock',False)
 except AssertionError:pass
 else:raise AssertionError('Physical reporter accepted mock data')
 sources=[OUT/n for n in ('build.sh','qualify.py','install.py','report.py','TEST-ME.txt')]+[ROOT/'build/finalize-ppu-test.py']
 ready={'ready':True,'measurement_only':True,'production_gate_passed':False,'installed':False,'armed':False,
  'verification_sha256':digest(OUT/'verification.json'),'additional_sources':{p.relative_to(ROOT).as_posix():digest(p) for p in sources},
  'reporter_mock_rejection_passed':True,'actual_epochs':56,'calls':67200,'core_exactness':'reused only by exact qualified ordinary core hashes',
  'authorization':'Explicit Arm I for measurement after PPU fixes; prices unknown, no production promotion',
  'prediction':'Final combination must improve matched valid tail/recovery costs and prevent reserve/pointer collapse; failure or negative isolated saving rejects the candidate. Residual deficit is unknown pending this measurement.'}
 (OUT/'ready.json').write_text(json.dumps(ready,indent=2)+'\n')
 manifest=ROOT/'evidence/manifest.json';m=json.loads(manifest.read_text())
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 DEST.mkdir(parents=True)
 for name in ('plan.json','ready.json','verification.json'):
  src=OUT/name;p=DEST/name;shutil.copy2(src,p)
  m['entries'].append({'source':src.relative_to(ROOT).as_posix(),'published':p.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(p),'bytes':p.stat().st_size,'normalized':False})
 manifest.write_text(json.dumps(m,indent=2)+'\n')
 print('PASS56-epoch controller/reporter with physical mock rejection; published ready metadata only')
if __name__=='__main__':main()
