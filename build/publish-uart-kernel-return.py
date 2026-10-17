"""Publish sparse preservation/boot observation and probe metadata only."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
from attempt_archive import verify_saved
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main(phase,archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');a=read(archive/'archive.json');o=read(archive/'outside-retro.json');assert a['fat_clean'] and a['card_writes']==o['card_writes']==0;verify_saved(archive,a)
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();m=json.loads(raw)
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 if phase=='collected':
  installed=read(ROOT/'evidence/2026-10-16/uart-kernel1/installation.json');before=ROOT/'device-evidence'/installed['archive'];old={e['path']:e['sha256'] for e in read(before/'archive.json')['all_retro_files']};now={e['path']:e['sha256'] for e in a['all_retro_files']};changes={n:{'before':h,'after':now.get(n)} for n,h in old.items() if now.get(n)!=h}
  assert set(changes)=={'retro/init','retro/update/Code.bkp','retro/swapfile'} and set(now)==set(old)
  assert now['retro/init']==installed['normal_init_sha256'] and now['retro/update/Code.bkp']==installed['package_sha256']
  assert {e['path']:e['sha256'] for e in o['files']}=={e['path']:e['sha256'] for e in read(before/'outside-retro.json')['files']}
  report={'version':'uart-kernel1-boot-return','archive':archive.name,'archive_manifest_sha256':digest(archive/'archive.json'),'outside_manifest_sha256':digest(archive/'outside-retro.json'),'installation_sha256':digest(ROOT/'evidence/2026-10-16/uart-kernel1/installation.json'),'user_observation':'Flash worked; both Vesper screens and stock launcher came up.','physical_boot_user_accepted':True,'exact_flash_image_verified':False,'fresh_UART_IRQ_measurement_available':False,'all_files_hashed':len(now)+len(o['files']),'unchanged_preinstall_files':len(old)+len(o['files'])-len(changes),'expected_changes':changes,'all_saves_prior_evidence_and_stock_files_exact':True,'outside_files_unchanged':len(o['files']),'no_full_backup':True,'new_sparse_content_bytes':a['new_content_bytes']+o['new_content_bytes'],'card_writes':0,'FAT_clean':True,'known_update_trigger_present':a['update_trigger_present'],'next_step':'Remove exact trigger after archive/FAT/hash gates; one read-only two-pass SPI/IRQ verification boot required.'}
  dest=ROOT/'evidence/2026-10-16/uart-kernel1/boot-return.json';values=[(dest,report,archive/'archive.json')]
 else:
  s=importlib.util.spec_from_file_location('stage',ROOT/'build/stage-uart-kernel-verify.py');stage=importlib.util.module_from_spec(s);s.loader.exec_module(stage);q=stage.artifacts();iq=read(stage.OUT/'staging-qualification.json');assert iq['passed'] and iq['installer_sha256']==digest(ROOT/'build/stage-uart-kernel-verify.py') and iq['qualification_sha256']==digest(stage.OUT/'qualification.json')
  base=ROOT/'evidence/2026-10-16/uart-kernel-verification';base.mkdir(exist_ok=True)
  if phase=='qualified':values=[(base/'qualification.json',{**q,'staging_transaction':iq,'publication_sources':{n:digest(ROOT/'build'/n) for n in ['collect-uart-kernel-return.py','stage-uart-kernel-verify.py','check-uart-kernel-verify-stage.py','verify-uart-kernel-probe-card.py','publish-uart-kernel-return.py']},'archive':archive.name},stage.OUT/'qualification.json')]
  elif phase=='installed':values=[(base/name,read(path),path) for name,path in [('installation.json',archive/'verification-installation.json'),('live-verification.json',archive/'verification-live-check.json')]]
  else:raise ValueError(phase)
 for dest,value,source in values:
  assert not dest.exists();dest.write_text(json.dumps(value,indent=2)+'\n');m['entries'].append({'source':source.relative_to(ROOT).as_posix(),'published':dest.relative_to(ROOT).as_posix(),'source_sha256':digest(source),'published_sha256':digest(dest),'bytes':dest.stat().st_size,'normalized':True})
 manifest.write_bytes((json.dumps(m,indent=2)+'\n').replace('\n','\r\n' if b'\r\n' in raw else '\n').encode());print('Published',phase,'metadata; all prior public hashes retained')
if __name__=='__main__':main(sys.argv[1],Path(sys.argv[2]))
