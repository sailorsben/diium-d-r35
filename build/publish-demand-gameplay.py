"""Publish metadata and hashes only; private binaries/progress remain local."""
from pathlib import Path
from hashlib import sha256
import json,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-gameplay-private-v1'
DEST=ROOT/'evidence/2026-10-14/demand-gameplay'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(phase):
 q=json.loads((OUT/'verification.json').read_text());assert q['passed']
 archive=ROOT/'device-evidence'/q['archive'];a=json.loads((archive/'archive.json').read_text())
 for n,h in q['payload_hashes'].items():assert digest(OUT/n)==h,n
 for n,h in q['source_hashes'].items():assert digest(ROOT/n)==h,n
 for n,h in q['proof_hashes'].items():assert digest(OUT/n)==h,n
 # The old frozen input manifest includes the original/reference trees.
 frozen=ROOT/'build/demand-visible-private-v3/frozen.json'
 for n,h in json.loads(frozen.read_text()).items():assert digest(ROOT/n)==h,n
 DEST.mkdir(parents=True,exist_ok=True)
 if phase=='qualified':
  report={**q,'archive_files':len(a['all_retro_files']),'archive_bytes':sum(e['bytes'] for e in a['all_retro_files']),
   'strict_archive_sha256':digest(archive/'archive.json'),'all_prior_frozen_hashes_verified':True,
   'card_writes':0,'physical_result':'PENDING','install_status':'qualified; not yet installed'}
  target=DEST/'qualification.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
 elif phase=='installed':
  report=json.loads((archive/'demand-gameplay-installation.json').read_text())
  target=DEST/'installation.json';assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
 else:raise ValueError(phase)
 mpath=ROOT/'evidence/manifest.json';m=json.loads(mpath.read_text())
 assert not any(e['published']==target.relative_to(ROOT).as_posix() for e in m['entries'])
 m['entries'].append({'source':('build/demand-gameplay-private-v1/verification.json' if phase=='qualified' else (archive/'demand-gameplay-installation.json').relative_to(ROOT).as_posix()),
 'published':target.relative_to(ROOT).as_posix(),'source_sha256':digest(OUT/'verification.json' if phase=='qualified' else archive/'demand-gameplay-installation.json'),
 'published_sha256':digest(target),'bytes':target.stat().st_size,'normalized':phase=='qualified'})
 mpath.write_text(json.dumps(m,indent=2)+'\n')
 print(json.dumps({'phase':phase,'archived_files':len(a['all_retro_files']),'published':str(target),'prior_artifacts_preserved':True}))
if __name__=='__main__':main(sys.argv[1])
