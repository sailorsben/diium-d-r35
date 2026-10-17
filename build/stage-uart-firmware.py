"""Stage authorized UART firmware on I: using the normal vendor trigger only."""
from pathlib import Path
from hashlib import sha256
import importlib.util,io,json,os,sys,zipfile
from attempt_archive import verify_saved
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'device-evidence/uart-firmware1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/'build'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def artifacts():
 p=json.loads((OUT/'preparation.json').read_text());q=json.loads((OUT/'qualification.json').read_text())
 assert q['all_checks_passed'] and len(q['checks'])==35 and q['preparation_sha256']==digest(OUT/'preparation.json')
 for n,h in q['sources'].items():assert digest(ROOT/n)==h,n
 for n,v in p['files'].items():assert digest(OUT/n)==v['sha256'],n
 assert digest(ROOT/p['baseline_path'])==p['baseline_sha256']
 assert digest(OUT/'execution.txt')==q['execution_sha256']
 package=(OUT/'fixture-compatible.bkp').read_bytes();assert package[:3]==b'WQW'
 with zipfile.ZipFile(io.BytesIO(package[3:])) as z:
  assert z.namelist()==['SPI_ROM.bin'] and z.testzip() is None and z.read('SPI_ROM.bin')==(OUT/'candidate.bin').read_bytes()
 old=load('install-uart-fix.py').artifacts();assert old['payloads']['launch.sh']==digest(ROOT/'build/launch-uart-fix.sh')
 return p,q,package,(OUT/'card-launch.sh').read_bytes()
def stage(card,package,compat,atomic,health,verify,inject=lambda _:None):
 hook=card/'retro/uart-fix1/launch.sh';trigger=card/'retro/update/Code.bkp';old=hook.read_bytes()
 assert not trigger.exists() and not list((card/'retro').rglob('armed'))
 assert old==(ROOT/'build/launch-uart-fix.sh').read_bytes()
 health('before')
 try:
  atomic(hook,compat);inject('compat');verify();health('compat')
  atomic(trigger,package);inject('trigger');verify();health('armed')
 except BaseException:
  # Never attempt restoration against a damaged filesystem.
  health('before-rollback')
  if trigger.exists():assert trigger.read_bytes()==package;trigger.unlink()
  assert hook.read_bytes() in (old,compat);atomic(hook,old)
  raise
def main(archive):
 p,q,package,compat=artifacts();fix=load('install-uart-fix.py')
 iq=json.loads((OUT/'staging-qualification.json').read_text());assert iq['passed'] and iq['installer_sha256']==digest(Path(__file__)) and iq['qualification_sha256']==digest(OUT/'qualification.json')
 assert not fix.git('status','--porcelain');commit=fix.git('rev-parse','HEAD');assert commit==fix.git('rev-parse','origin/codex/snes-mvp-foundation')
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());outside=json.loads((archive/'outside-retro.json').read_text());assert a['fat_clean'] and a['card_writes']==outside['card_writes']==0
 verify_saved(archive,a)
 entries=a['all_retro_files']+outside['files'];card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\')
 assert not list(card.rglob('Code.bkp')) and not list((card/'retro').rglob('armed'))
 for e in entries:
  assert digest(card/e['path'])==e['sha256'],e['path']
  if e['stored']:assert digest(archive/e['path'])==e['sha256']
 uq=fix.artifacts();assert digest(card/'retro/init')==uq['payloads']['init']
 for n,h in uq['payloads'].items():
  if n!='init':assert digest(card/'retro/uart-fix1'/n)==h,n
 assert not (card/'retro/uart-fix1/disabled').exists()
 assert digest(card/'retro/vrtemu')==p['vendor_sha256']
 assert os.stat(card).st_dev and __import__('shutil').disk_usage(card).free>len(package)+512*1024*1024
 protected={e['path']:e['sha256'] for e in entries if e['path']!='retro/uart-fix1/launch.sh'}
 def verify():
  for n,h in protected.items():assert digest(card/n)==h,n
  assert (card/'retro/uart-fix1/launch.sh').read_bytes()==compat
  trigger=card/'retro/update/Code.bkp'
  if trigger.exists():assert trigger.read_bytes()==package
 stage(card,package,compat,fix.atomic,lambda label:fix.health(archive,'firmware1-'+label),verify)
 report={'version':'uart-firmware1','source_commit':commit,'archive':archive.name,'armed_vendor_update':True,'package_sha256':p['package_sha256'],'package_bytes':len(package),'candidate_sha256':p['candidate_sha256'],'expected_after_vendor_sha256':p['expected_after_vendor_sha256'],
 'only_changed_existing_file':'retro/uart-fix1/launch.sh','old_hook_sha256':digest(ROOT/'build/launch-uart-fix.sh'),'card_hook_sha256':digest(OUT/'card-launch.sh'),'only_added_file':'retro/update/Code.bkp','protected_existing_files':len(protected),'clean_FAT':True,'no_emulator_test_armed':True,'no_full_backup_created':True,'physical_update':'PENDING'}
 (archive/'uart-firmware-installation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
