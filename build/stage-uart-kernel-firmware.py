"""Replace only the known staged module update with the qualified kernel fix."""
from pathlib import Path
from hashlib import sha256
import importlib.util,io,json,sys,zipfile,shutil
from attempt_archive import verify_saved
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'device-evidence/uart-kernel-firmware1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/'build'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def artifacts():
 p=json.loads((OUT/'preparation.json').read_text());q=json.loads((OUT/'qualification.json').read_text());assert q['passed'] and len(q['checks'])==26 and q['preparation_sha256']==digest(OUT/'preparation.json')
 for n,h in q['sources'].items():assert digest(ROOT/n)==h,n
 for n,v in p['files'].items():assert digest(OUT/n)==v['sha256'],n
 assert digest(OUT/'execution.txt')==q['execution_sha256']
 package=(OUT/'fixture-compatible.bkp').read_bytes();assert package[:3]==b'WQW'
 with zipfile.ZipFile(io.BytesIO(package[3:])) as z:assert z.testzip() is None and z.namelist()==['SPI_ROM.bin'] and z.read('SPI_ROM.bin')==(OUT/'candidate.bin').read_bytes()
 old=(ROOT/'device-evidence/uart-firmware1/fixture-compatible.bkp').read_bytes();receipt=json.loads((ROOT/'evidence/2026-10-16/uart-firmware1/installation.json').read_text());assert sha256(old).hexdigest()==receipt['package_sha256']
 oldinit=(ROOT/'build/uart-fix-private/package/init').read_bytes();assert sha256(oldinit).hexdigest()=='24280b658d52702848901df258c9e3e9c4a1c4ba876cdad03534bee67d0343fe'
 return p,q,package,(OUT/'normal-init').read_bytes(),old,oldinit
def stage(card,package,normal,old,oldinit,atomic,health,verify,inject=lambda _:None):
 init=card/'retro/init';trigger=card/'retro/update/Code.bkp'
 assert init.read_bytes()==oldinit and trigger.read_bytes()==old and not list((card/'retro').rglob('armed'))
 health('before')
 try:
  atomic(init,normal);inject('init');verify();health('init')
  atomic(trigger,package);inject('trigger');verify();health('armed')
 except BaseException:
  health('before-rollback')
  assert trigger.read_bytes() in (old,package);atomic(trigger,old)
  assert init.read_bytes() in (oldinit,normal);atomic(init,oldinit)
  raise
def main(archive):
 p,q,package,normal,old,oldinit=artifacts();fix=load('install-uart-fix.py');iq=json.loads((OUT/'staging-qualification.json').read_text());assert iq['passed'] and iq['installer_sha256']==digest(Path(__file__)) and iq['qualification_sha256']==digest(OUT/'qualification.json')
 assert not fix.git('status','--porcelain') and fix.git('branch','--show-current')=='codex/snes-mvp-foundation';commit=fix.git('rev-parse','HEAD');assert commit==fix.git('rev-parse','origin/codex/snes-mvp-foundation')
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');a=json.loads((archive/'archive.json').read_text());outside=json.loads((archive/'outside-retro.json').read_text());assert a['fat_clean'] and a['card_writes']==outside['card_writes']==0
 verify_saved(archive,a);entries=a['all_retro_files']+outside['files'];card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\')
 assert list(card.rglob('Code.bkp'))==[card/'retro/update/Code.bkp'] and not list((card/'retro').rglob('armed'))
 for e in entries:
  assert digest(card/e['path'])==e['sha256'],e['path']
  if e['stored']:assert digest(archive/e['path'])==e['sha256']
 assert digest(card/'retro/vrtemu')=='8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
 assert not (card/'retro/uart-fix1/disabled').exists() and shutil.disk_usage(card).free>len(package)+512*1024*1024
 changed={'retro/init','retro/update/Code.bkp'};protected={e['path']:e['sha256'] for e in entries if e['path'] not in changed}
 def verify():
  for n,h in protected.items():assert digest(card/n)==h,n
  assert (card/'retro/init').read_bytes()==normal and (card/'retro/update/Code.bkp').read_bytes() in (old,package)
 stage(card,package,normal,old,oldinit,fix.atomic,lambda label:fix.health(archive,'kernel1-'+label),verify)
 result={'version':'uart-kernel1','source_commit':commit,'archive':archive.name,'armed_vendor_update':True,'package_sha256':p['package_sha256'],'package_bytes':len(package),'candidate_sha256':p['candidate_sha256'],'expected_after_vendor_sha256':p['expected_after_vendor_sha256'],'normal_init_sha256':digest(OUT/'normal-init'),'superseded_package_sha256':sha256(old).hexdigest(),'only_changed_files':sorted(changed),'protected_existing_files':len(protected),'clean_FAT':True,'no_emulator_test_armed':True,'runtime_UART_loader_invoked':False,'full_backup_created':False,'physical_boot':'PENDING'}
 receipt=archive/'uart-kernel-installation.json'
 if receipt.exists():
  assert (archive/'uart-kernel-staging-withdrawn.json').exists()
  previous=archive/'uart-kernel-installation-withdrawn.json';assert not previous.exists();receipt.rename(previous)
 receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
