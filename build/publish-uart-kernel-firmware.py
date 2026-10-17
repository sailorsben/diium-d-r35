"""Publish only metadata for the direct kernel correction; no private firmware."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
DEST=ROOT/'evidence/2026-10-16/uart-kernel1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(phase,archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');s=importlib.util.spec_from_file_location('stage',ROOT/'build/stage-uart-kernel-firmware.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);p,q,*_=m.artifacts()
 iq=json.loads((m.OUT/'staging-qualification.json').read_text());assert iq['passed'] and iq['installer_sha256']==digest(ROOT/'build/stage-uart-kernel-firmware.py') and iq['qualification_sha256']==digest(m.OUT/'qualification.json')
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();data=json.loads(raw)
 for e in data['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 if phase in ('qualified','qualified-v2'):
  a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());assert a['fat_clean'] and a['card_writes']==o['card_writes']==0
  suffix='-v2' if phase=='qualified-v2' else ''
  values=[('preparation'+suffix+'.json',p,m.OUT/'preparation.json'),('qualification'+suffix+'.json',{**q,'staging_transaction':iq,'archive':archive.name,'archive_manifest_sha256':digest(archive/'archive.json'),'outside_manifest_sha256':digest(archive/'outside-retro.json'),'all_existing_files_hashed':len(a['all_retro_files'])+len(o['files']),'new_sparse_content_bytes':a['new_content_bytes']+o['new_content_bytes'],'no_full_backup':True,'publication_sources':{n:digest(ROOT/'build'/n) for n in ['archive-uart-kernel.py','stage-uart-kernel-firmware.py','check-uart-kernel-stage.py','verify-uart-kernel-card.py','publish-uart-kernel-firmware.py','check-uart-kernel-boot-heap.py']}},m.OUT/'qualification.json')]
 elif phase=='installed':
  heap=m.OUT/'boot-heap-qualification.json';h=json.loads(heap.read_text());assert h['passed'] and h['heap_bytes']==65536 and h['zImage_sha256']==p['files']['zImage.bin']['sha256'] and h['probe_source_sha256']==digest(ROOT/'build/check-uart-kernel-boot-heap.py')
  values=[(name,json.loads(path.read_text()),path) for name,path in [('installation.json',archive/'uart-kernel-installation.json'),('live-verification.json',archive/'uart-kernel-live-verification.json'),('boot-heap-qualification.json',heap),('withdrawn-stage.json',archive/'uart-kernel-staging-withdrawn.json')]]
 else:raise ValueError(phase)
 DEST.mkdir(exist_ok=True)
 for name,value,source in values:
  dest=DEST/name;assert not dest.exists();dest.write_text(json.dumps(value,indent=2)+'\n');data['entries'].append({'source':source.relative_to(ROOT).as_posix(),'published':dest.relative_to(ROOT).as_posix(),'source_sha256':digest(source),'published_sha256':digest(dest),'bytes':dest.stat().st_size,'normalized':value!=json.loads(source.read_text())})
 manifest.write_bytes((json.dumps(data,indent=2)+'\n').replace('\n','\r\n' if b'\r\n' in raw else '\n').encode());print('Published',phase,'metadata; prior evidence preserved')
if __name__=='__main__':main(sys.argv[1],Path(sys.argv[2]))
