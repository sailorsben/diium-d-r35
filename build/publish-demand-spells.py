"""Freeze the ready test and publish hashes/qualification, never fixture bytes."""
from pathlib import Path
from hashlib import sha256
import json,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-spells-private-v1'
DEST=ROOT/'evidence/2026-10-14/demand-spells'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 q=json.loads((OUT/'verification.json').read_text());assert q['passed'] and not q['installed'] and not q['armed']
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for n,h in q[group].items():assert digest(ROOT/n if group=='source_hashes' else OUT/n)==h,n
 analysis=json.loads((OUT/'mock/spell-analysis.json').read_text())
 assert analysis['physical_result']==False and len(analysis['epochs'])==40 and all(r['status']=='NOT_PHYSICAL' for r in analysis['epochs'])
 sources=[ROOT/'build'/n for n in ('report-demand-spells.py','install-demand-spells.py','publish-demand-spells.py','check-demand-spells-reporter.py')]
 sources += [ROOT/'docs/snes-demand-spells-test.txt',ROOT/'docs/snes-demand-spells.md']
 ready={'version':q['version'],'ready':True,'installed':False,'armed':False,'card_writes':0,'verification_sha256':digest(OUT/'verification.json'),
 'additional_sources':{p.relative_to(ROOT).as_posix():digest(p) for p in sources},
 'qualification':q,'reporter_mock_guard_qualified':True,'physical_performance':'PENDING'}
 assert not (OUT/'ready.json').exists();(OUT/'ready.json').write_text(json.dumps(ready,indent=2)+'\n')
 assert not DEST.exists();DEST.mkdir()
 mpath=ROOT/'evidence/manifest.json';m=json.loads(mpath.read_text())
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 for n,h in json.loads((ROOT/'build/demand-visible-private-v3/frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 for name,src in [('ready.json',OUT/'ready.json'),('plan.json',OUT/'plan.json')]:
  dest=DEST/name;shutil.copy2(src,dest);assert digest(dest)==digest(src)
  m['entries'].append({'source':src.relative_to(ROOT).as_posix(),'published':dest.relative_to(ROOT).as_posix(),
   'source_sha256':digest(src),'published_sha256':digest(dest),'bytes':dest.stat().st_size,'normalized':False})
 mpath.write_text(json.dumps(m,indent=2)+'\n')
 print('Published ready40-epoch test receipts; all prior evidence/frozen inputs exact; no card writes')
if __name__=='__main__':main()
