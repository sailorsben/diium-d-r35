"""Publish source-bound metadata only; preserve prior published evidence bytes."""
from pathlib import Path
from hashlib import sha256
import json,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fivegame-physical-private-v1'
DEST=ROOT/'evidence/2026-10-16/fivegame'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(phase,archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 q=json.loads((OUT/'verification.json').read_text());assert q['passed']
 iq=json.loads((OUT/'installation-qualification.json').read_text());assert iq['passed']
 assert iq['installer_sha256']==digest(ROOT/'build/install-fivegame.py') and iq['qualification_sha256']==digest(OUT/'verification.json')
 for group,base in ((q['source_hashes'],ROOT),(q['payload_hashes'],OUT),(q['proof_hashes'],OUT)):
  for n,h in group.items():assert digest(base/n)==h,n
 manifest=ROOT/'evidence/manifest.json';newline='\r\n' if b'\r\n' in manifest.read_bytes() else '\n';m=json.loads(manifest.read_text())
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 if phase=='qualified':
  report=json.loads((archive/'archive.json').read_text());extra=json.loads((archive/'outside-retro.json').read_text())
  files=report['all_retro_files']+extra['files']
  metadata={**q,'all_existing_files_hashed':len(files),'inventoried_bytes':sum(e['bytes'] for e in files),
   'archive_storage_policy':report.get('storage_policy','legacy-full-copy'),
   'new_content_bytes':sum(e.get('new_content_bytes',e['bytes']) for e in files),'FAT_clean':report['fat_clean'],
   'installation_transaction':iq,'archive':archive.name,'archive_manifest_sha256':digest(archive/'archive.json'),
   'outside_retro_manifest_sha256':digest(archive/'outside-retro.json'),
   'publication_sources':{n:digest(ROOT/'build'/n) for n in ('archive-presentation-extra.py','check-fivegame-install.py','install-fivegame.py','report-fivegame.py','verify-fivegame-card.py','publish-fivegame.py')},
   'prior_published_hashes_verified':len(m['entries'])}
  values=[('qualification.json',metadata,OUT/'verification.json')]
 elif phase=='installed':
  report=archive/'fivegame-installation.json';readback=archive/'fivegame-live-verification.json'
  values=[('installation.json',json.loads(report.read_text()),report),('live-verification.json',json.loads(readback.read_text()),readback)]
 else:raise ValueError(phase)
 DEST.mkdir(parents=True,exist_ok=True)
 for name,value,source in values:
  p=DEST/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n')
  m['entries'].append({'source':source.relative_to(ROOT).as_posix(),'published':p.relative_to(ROOT).as_posix(),
   'source_sha256':digest(source),'published_sha256':digest(p),'bytes':p.stat().st_size,'normalized':value!=json.loads(source.read_text())})
 manifest.write_bytes((json.dumps(m,indent=2)+'\n').replace('\n',newline).encode())
 print('Published',phase,'metadata; prior evidence preserved')
if __name__=='__main__':main(sys.argv[1],Path(sys.argv[2]))
