"""Publish hash-bound firmware metadata only; never vendor images or private saves."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'device-evidence/uart-firmware1'
DEST=ROOT/'evidence/2026-10-16/uart-firmware1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(phase,archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 s=importlib.util.spec_from_file_location('stage',ROOT/'build/stage-uart-firmware.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);p,q,_,_=m.artifacts()
 iq=json.loads((OUT/'staging-qualification.json').read_text());assert iq['passed'] and iq['installer_sha256']==digest(ROOT/'build/stage-uart-firmware.py') and iq['qualification_sha256']==digest(OUT/'qualification.json')
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();entries=json.loads(raw)
 for e in entries['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 if phase=='qualified':
  a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());assert a['fat_clean'] and a['card_writes']==o['card_writes']==0
  values=[('preparation.json',p,OUT/'preparation.json'),('qualification.json',{**q,'staging_transaction':iq,'archive':archive.name,'archive_manifest_sha256':digest(archive/'archive.json'),'outside_manifest_sha256':digest(archive/'outside-retro.json'),'all_existing_files_hashed':len(a['all_retro_files'])+len(o['files']),'new_sparse_content_bytes':a['new_content_bytes']+o['new_content_bytes'],'no_full_backup':True,
   'publication_sources':{n:digest(ROOT/'build'/n) for n in ['stage-uart-firmware.py','check-uart-firmware-stage.py','verify-uart-firmware-card.py','publish-uart-firmware.py']}},OUT/'qualification.json')]
 elif phase=='installed':
  files=[('installation.json',archive/'uart-firmware-installation.json'),('live-verification.json',archive/'uart-firmware-live-verification.json')];values=[(n,json.loads(p.read_text()),p) for n,p in files]
 else:raise ValueError(phase)
 DEST.mkdir(exist_ok=True)
 for name,value,source in values:
  dest=DEST/name;assert not dest.exists();dest.write_text(json.dumps(value,indent=2)+'\n')
  entries['entries'].append({'source':source.relative_to(ROOT).as_posix(),'published':dest.relative_to(ROOT).as_posix(),'source_sha256':digest(source),'published_sha256':digest(dest),'bytes':dest.stat().st_size,'normalized':value!=json.loads(source.read_text())})
 manifest.write_bytes((json.dumps(entries,indent=2)+'\n').replace('\n','\r\n' if b'\r\n' in raw else '\n').encode());print('Published',phase,'metadata; all prior evidence hashes preserved')
if __name__=='__main__':main(sys.argv[1],Path(sys.argv[2]))
