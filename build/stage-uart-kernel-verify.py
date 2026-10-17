"""Remove exact returned update trigger; stage one read-only verification boot."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys,shutil
from attempt_archive import verify_saved
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/uart-kernel-verify-private'
TARGET='retro/uart-kernel-verify1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/'build'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def artifacts():
 q=json.loads((OUT/'qualification.json').read_text());assert q['passed'] and len(q['checks'])==10
 for n,h in q['sources'].items():assert digest(ROOT/'build'/n)==h,n
 for n,h in q['payload_hashes'].items():assert digest(OUT/n)==h,n
 assert digest(OUT/'init')==q['init_sha256'] and digest(OUT/'armed')==q['marker_sha256'];return q
def stage(card,payload,init,marker,update_hash,atomic,health,verify,inject=lambda _:None):
 target=card/TARGET;normal=card/'retro/init';trigger=card/'retro/update/Code.bkp';old=normal.read_bytes()
 assert sha256(old).hexdigest()=='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7' and not target.exists() and not list((card/'retro').rglob('armed'))
 if trigger.exists():assert digest(trigger)==update_hash
 health('before')
 if trigger.exists():trigger.unlink()
 target.mkdir()
 try:
  for n,data in payload.items():assert Path(n).name==n;atomic(target/n,data)
  inject('payload');verify();health('payload')
  atomic(normal,init);inject('init');atomic(target/'armed',marker);inject('marker');verify();health('armed')
 except BaseException:
  health('before-rollback')
  if (target/'armed').exists():assert (target/'armed').read_bytes()==marker;(target/'armed').unlink()
  assert normal.read_bytes() in (old,init);atomic(normal,old)
  # Keep owned partial staging. Never reintroduce a firmware update trigger.
  raise
def main(archive):
 q=artifacts();fix=load('install-uart-fix.py');iq=json.loads((OUT/'staging-qualification.json').read_text());assert iq['passed'] and iq['installer_sha256']==digest(Path(__file__)) and iq['qualification_sha256']==digest(OUT/'qualification.json')
 assert not fix.git('status','--porcelain');commit=fix.git('rev-parse','HEAD');assert commit==fix.git('rev-parse','origin/codex/snes-mvp-foundation')
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());assert a['fat_clean'] and a['card_writes']==o['card_writes']==0;verify_saved(archive,a)
 entries=a['all_retro_files']+o['files'];card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\')
 for e in entries:
  assert digest(card/e['path'])==e['sha256'],e['path']
  if e['stored']:assert digest(archive/e['path'])==e['sha256']
 assert shutil.disk_usage(card).free>64*1024*1024
 installed=json.loads((ROOT/'evidence/2026-10-16/uart-kernel1/installation.json').read_text());assert a['known_update_sha256']==installed['package_sha256']
 payload={n:(OUT/n).read_bytes() for n in q['payload_hashes']};payload['qualification.json']=(OUT/'qualification.json').read_bytes()
 protected={e['path']:e['sha256'] for e in entries if e['path'] not in ('retro/init','retro/update/Code.bkp')}
 def verify():
  for n,h in protected.items():assert digest(card/n)==h,n
  for n,b in payload.items():assert (card/TARGET/n).read_bytes()==b,n
  assert (card/'retro/init').read_bytes() in ((ROOT/'device-evidence/uart-kernel-firmware1/normal-init').read_bytes(),(OUT/'init').read_bytes())
  assert not (card/'retro/update/Code.bkp').exists()
 stage(card,payload,(OUT/'init').read_bytes(),(OUT/'armed').read_bytes(),installed['package_sha256'],fix.atomic,lambda label:fix.health(archive,'kernel-verify-'+label),verify)
 assert (card/'retro/init').read_bytes()==(OUT/'init').read_bytes() and (card/TARGET/'armed').read_bytes()==(OUT/'armed').read_bytes()
 report={'version':'uart-kernel-verify1','source_commit':commit,'archive':archive.name,'one_shot_verification_armed':True,'known_update_trigger_removed':True,'removed_trigger_sha256':installed['package_sha256'],'protected_existing_files':len(protected),'init_sha256':q['init_sha256'],'normal_init_restore_sha256':installed['normal_init_sha256'],'marker_sha256':q['marker_sha256'],'payload_hashes':{n:sha256(b).hexdigest() for n,b in payload.items()},'clean_FAT':True,'flash_writes':False,'module_loads':False,'no_full_backup':True,'physical_measurement':'PENDING'}
 (archive/'verification-installation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
