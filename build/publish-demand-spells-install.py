"""Publish verified installation metadata; preserve frozen preparation receipts."""
from pathlib import Path
from hashlib import sha256
import json,shutil,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-spells-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 source=archive/'demand-spells-installation.json';r=json.loads(source.read_text())
 assert r['one_shot_armed'] and r['clean_FAT'] and r['original_progress_unchanged'] and r['ROM_unchanged'] and not r['production_gate_passed']
 assert r['dispatch_sha256']==digest(OUT/'dispatch.sh')
 q=json.loads((OUT/'verification.json').read_text());ready=json.loads((OUT/'ready.json').read_text())
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for n,h in q[group].items():assert digest(ROOT/n if group=='source_hashes' else OUT/n)==h,n
 for n,h in ready['additional_sources'].items():assert digest(ROOT/n)==h,n
 assert ready['verification_sha256']==digest(OUT/'verification.json')
 for n,h in r['payload_hashes'].items():
  src=ROOT/'docs/snes-demand-spells-test.txt' if n=='TEST-ME.txt' else OUT/'verification.json' if n=='suite-identity.json' else OUT/n
  assert digest(src)==h,n
 mpath=ROOT/'evidence/manifest.json';m=json.loads(mpath.read_text())
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 for n,h in json.loads((ROOT/'build/demand-visible-private-v3/frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 target=ROOT/'evidence/2026-10-14/demand-spells/installation.json';assert not target.exists();shutil.copy2(source,target)
 assert digest(target)==digest(source)
 m['entries'].append({'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
 'source_sha256':digest(source),'published_sha256':digest(target),'bytes':target.stat().st_size,'normalized':False})
 mpath.write_text(json.dumps(m,indent=2)+'\n')
 print(json.dumps({'armed':True,'payload_files':len(r['payload_hashes']),'protected_files':r['protected_files'],'prior_evidence_and_frozen_artifacts_exact':True}))
if __name__=='__main__':main(Path(sys.argv[1]))
