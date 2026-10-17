"""Authorized separate matched five-game one-shot. Archive/FAT/hash/clean-push gates."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,shutil,sys
from attempt_archive import verify_saved
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fivegame-kernel-private-v1'
MARKER=b'Matched five-game kernel UART 20 epochs once\n'
TARGET='retro/snes-fivegame-kernel1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def load(n):
 spec=importlib.util.spec_from_file_location(n,ROOT/'build'/n);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def stage(card,payload,dispatch,atomic,health,verify,inject=lambda _:None):
 target=card/TARGET;mvp=card/'retro/snes-mvp';old=(mvp/'launch.sh').read_bytes()
 assert not target.exists() and not list((card/'retro').rglob('armed'))
 target.mkdir()
 try:
  for n,b in payload.items():
   path=Path(n);assert not path.is_absolute() and '..' not in path.parts
   p=target/path;p.parent.mkdir(parents=True,exist_ok=True);atomic(p,b)
  inject('payload');verify();health('payload')
  atomic(mvp/'launch.sh',dispatch);inject('dispatcher')
  atomic(target/'armed',MARKER);inject('target_marker')
  atomic(mvp/'armed',MARKER);inject('mvp_marker')
  verify();health('armed')
  assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==sorted(['retro/snes-mvp/armed',TARGET+'/armed'])
 except BaseException:
  health('before-rollback')
  for p in (target/'armed',mvp/'armed'):
   if p.exists():assert p.read_bytes()==MARKER;p.unlink()
  assert (mvp/'launch.sh').read_bytes() in (old,dispatch)
  atomic(mvp/'launch.sh',old)
  # Retain partial owned staging for inspection. Never remove prior content.
  raise
 return old
def main(archive):
 fix=load('install-uart-fix.py');q=json.loads((OUT/'qualification.json').read_text())
 iq=json.loads((OUT/'installation-qualification.json').read_text())
 assert q['passed'] and q['measurement_only'] and not q['production_gate'] and len(q['previous_actual_epochs'])==20
 assert iq['passed'] and iq['installer_sha256']==digest(Path(__file__)) and iq['qualification_sha256']==digest(OUT/'qualification.json')
 for n,h in q['sources'].items():assert digest(ROOT/n)==h,n
 for n,h in q['payload_hashes'].items():assert digest(OUT/n)==h,n
 assert digest(ROOT/'build/fivegame-physical-private-v1/verification.json')==q['previous_qualification_sha256']
 assert digest(ROOT/'evidence/2026-10-16/uart-kernel-verification/powered-return.json')==q['kernel_physical_receipt_sha256']
 assert not fix.git('status','--porcelain') and fix.git('branch','--show-current')=='codex/snes-mvp-foundation'
 commit=fix.git('rev-parse','HEAD');assert commit==fix.git('rev-parse','origin/codex/snes-mvp-foundation')
 archive=archive.resolve();assert archive.is_relative_to((ROOT/'device-evidence').resolve())
 a=json.loads((archive/'archive.json').read_text());extra=json.loads((archive/'outside-retro.json').read_text())
 assert a['fat_clean'] and a['card_writes']==extra['card_writes']==0
 card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\')
 assert not list((card/'retro').rglob('armed')) and not list(card.rglob('Code.bkp'))
 entries=a['all_retro_files']+extra['files']
 verify_saved(archive,a)
 for e in extra['files']:
  if extra.get('schema') is None or e['stored']:assert digest(archive/e['path'])==e['sha256'],e['path']
 for e in entries:assert digest(card/e['path'])==e['sha256'],e['path']
 # Verified firmware owns UART; normal init and all old UART artifacts protected.
 assert digest(card/'retro/init')=='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
 for n,h in load('package-snes-1.19.py').BOOT_EXPECTED.items():assert digest(card/n)==h,n
 physical=json.loads((ROOT/'evidence/2026-10-16/uart-kernel-verification/powered-return.json').read_text());assert physical['two_pass_flash_exact'] and physical['idle_IRQ_flood_acceptance_passed']
 assert digest(card/'002/Final Fantasy VI.zip')==fix.ROM
 health=lambda label:fix.health(archive,'fivegame-'+label)
 health('before')
 payload={n:(OUT/n).read_bytes() for n in q['payload_hashes'] if n!='dispatch.sh'}
 payload['qualification.json']=(OUT/'qualification.json').read_bytes()
 payload['installation-qualification.json']=(OUT/'installation-qualification.json').read_bytes()
 assert shutil.disk_usage(card).free>sum(map(len,payload.values()))+512*1024*1024
 protected={e['path']:e['sha256'] for e in entries if e['path']!='retro/snes-mvp/launch.sh'}
 def verify():
  for n,h in protected.items():assert digest(card/n)==h,n
  for n,b in payload.items():assert (card/TARGET/n).read_bytes()==b,n
 old=stage(card,payload,(OUT/'dispatch.sh').read_bytes(),fix.atomic,health,verify)
 assert (card/'retro/snes-mvp/launch.sh').read_bytes()==(OUT/'dispatch.sh').read_bytes()
 report={'version':'fivegame-kernel1','source_commit':commit,'archive':archive.name,'clean_FAT':True,
 'one_shot_armed':True,'physical_result':'PENDING','kernel_UART_preserved':True,'normal_init_sha256':digest(card/'retro/init'),'target':TARGET,'no_full_backup':True,
 'kernel_verification_receipt_sha256':q['kernel_physical_receipt_sha256'],
 'protected_existing_files':len(protected),'all_existing_files_hashed':len(entries),
 'archive_storage_policy':a.get('storage_policy','legacy-full-copy'),
 'only_changed_existing_file':'retro/snes-mvp/launch.sh','previous_dispatch_sha256':sha256(old).hexdigest(),
 'dispatch_sha256':digest(card/'retro/snes-mvp/launch.sh'),'marker_sha256':sha256(MARKER).hexdigest(),
 'payload_hashes':{n:sha256(b).hexdigest() for n,b in payload.items()}}
 (archive/'fivegame-kernel-installation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
