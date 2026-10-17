"""Arm exact pre-kernel Wings2 rollback and restore proven card UART boot."""
from pathlib import Path
import importlib.util,json,sys,shutil
from attempt_archive import digest,verify_saved
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'device-evidence/battery-rollback1'
NORMAL='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
def load(name):
 s=importlib.util.spec_from_file_location(name,ROOT/'build'/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def stage(card,init,launch,package,atomic,health,verify,inject=lambda _:None):
 ip=card/'retro/init';lp=card/'retro/uart-fix1/launch.sh';trigger=card/'retro/update/Code.bkp';oldinit=ip.read_bytes();oldlaunch=lp.read_bytes()
 assert not trigger.exists() and not list(card.rglob('armed'))
 health('before')
 try:
  atomic(lp,launch);inject('launch');atomic(ip,init);inject('init');verify();health('hooks')
  atomic(trigger,package);inject('trigger');verify();health('armed')
 except BaseException:
  health('before-rollback')
  if trigger.exists():assert trigger.read_bytes()==package;trigger.unlink()
  assert ip.read_bytes() in (oldinit,init) and lp.read_bytes() in (oldlaunch,launch)
  atomic(ip,oldinit);atomic(lp,oldlaunch);raise
 return oldinit,oldlaunch
def main(archive):
 q=json.loads((OUT/'qualification.json').read_text());assert q['passed'] and len(q['checks'])==11
 for n,h in q['sources'].items():assert digest(ROOT/n)==h,n
 assert digest(OUT/'execution.txt')==q['execution_sha256'];iq=json.loads((OUT/'staging-qualification.json').read_text());assert iq['passed'] and iq['installer_sha256']==digest(Path(__file__)) and iq['qualification_sha256']==digest(OUT/'qualification.json')
 module=ROOT/'build/uart-fix-private/package';payload={n:(module/n).read_bytes() for n in q['card_UART_payloads']}
 for n,h in q['card_UART_payloads'].items():assert digest(module/n)==h,n
 package=(ROOT/q['package_path']).read_bytes();assert digest(ROOT/q['package_path'])==q['package_sha256']
 fix=load('install-uart-fix.py');assert not fix.git('status','--porcelain');commit=fix.git('rev-parse','HEAD');assert commit==fix.git('rev-parse','origin/codex/snes-mvp-foundation')
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());assert a['fat_clean'] and a['card_writes']==o['card_writes']==0;verify_saved(archive,a)
 entries=a['all_retro_files']+o['files'];card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\')
 assert not list(card.rglob('Code.bkp')) and not list(card.rglob('armed')) and not (card/'retro/uart-fix1/disabled').exists()
 for e in entries:assert digest(card/e['path'])==e['sha256'],e['path']
 assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}=={e['path'] for e in entries}
 assert digest(card/'retro/init')==NORMAL
 assert digest(card/'retro/uart-fix1/launch.sh') in (q['card_UART_payloads']['launch.sh'],digest(ROOT/'device-evidence/uart-firmware1/card-launch.sh'))
 for n in ['d35_uart_tx.ko','uart-fix-boot']:assert digest(card/'retro/uart-fix1'/n)==q['card_UART_payloads'][n],n
 assert digest(card/'retro/vrtemu')=='8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
 assert shutil.disk_usage(card).free>len(package)+64*1024*1024
 changed={'retro/init','retro/uart-fix1/launch.sh'};protected={e['path']:e['sha256'] for e in entries if e['path'] not in changed}
 def verify():
  for n,h in protected.items():assert digest(card/n)==h,n
  assert (card/'retro/init').read_bytes()==payload['init'] and (card/'retro/uart-fix1/launch.sh').read_bytes()==payload['launch.sh']
  if (card/'retro/update/Code.bkp').exists():assert (card/'retro/update/Code.bkp').read_bytes()==package
 oldinit,oldlaunch=stage(card,payload['init'],payload['launch.sh'],package,fix.atomic,lambda label:fix.health(archive,'battery-rollback-'+label),verify)
 result={'version':'battery-kernel-rollback1','source_commit':commit,'archive':archive.name,'armed_vendor_update':True,'package_sha256':q['package_sha256'],'package_bytes':len(package),'candidate_sha256':q['candidate_sha256'],'expected_after_vendor_sha256':q['expected_after_vendor_sha256'],'restored_kernel_sha256':q['restored_kernel_sha256'],'card_UART_payloads':q['card_UART_payloads'],'prior_init_sha256':__import__('hashlib').sha256(oldinit).hexdigest(),'prior_UART_wrapper_sha256':__import__('hashlib').sha256(oldlaunch).hexdigest(),'changed_existing_files':sorted(changed),'added_update_file':'retro/update/Code.bkp','protected_existing_files':len(protected),'all_existing_files':len(entries),'FAT_clean':True,'no_emulator_test_armed':True,'no_full_backup':True,'physical_rollback':'PENDING','battery_result':'UNPROVEN'}
 (archive/'battery-rollback-installation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
