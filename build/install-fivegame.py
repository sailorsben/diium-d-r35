"""Authorized separate matched five-game one-shot. Archive/FAT/hash/clean-push gates."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,shutil,sys
from attempt_archive import verify_saved
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fivegame-physical-private-v1'
MARKER=b'Matched five-game presentation policy 20 epochs once\n'
TARGET='retro/snes-fivegame1'
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
 fix=load('install-uart-fix.py');q=json.loads((OUT/'verification.json').read_text())
 iq=json.loads((OUT/'installation-qualification.json').read_text())
 assert q['passed'] and q['measurement_only'] and not q['production_gate'] and len(q['actual_epochs'])==20
 assert iq['passed'] and iq['installer_sha256']==digest(Path(__file__)) and iq['qualification_sha256']==digest(OUT/'verification.json')
 for n,h in q['source_hashes'].items():assert digest(ROOT/n)==h,n
 for n,h in q['payload_hashes'].items():assert digest(OUT/n)==h,n
 for n,h in q['proof_hashes'].items():assert digest(OUT/n)==h,n
 assert digest(OUT/'abi.txt')==q['ABI_sha256']
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
 # UART boot init and all UART files remain protected, never rewritten.
 uq=json.loads((ROOT/'build/uart-fix-private/qualification.json').read_text())
 assert digest(card/'retro/init')==uq['payloads']['init']
 for n,h in uq['payloads'].items():
  if n!='init':assert digest(card/'retro/uart-fix1'/n)==h,n
 assert not (card/'retro/uart-fix1/disabled').exists()
 for n,h in load('package-snes-1.19.py').BOOT_EXPECTED.items():assert digest(card/n)==h,n
 assert digest(card/'002/Final Fantasy VI.zip')==fix.ROM
 health=lambda label:fix.health(archive,'fivegame-'+label)
 health('before')
 payload={n:(OUT/n).read_bytes() for n in q['payload_hashes'] if n!='dispatch.sh'}
 payload['verification.json']=(OUT/'verification.json').read_bytes()
 payload['installation-qualification.json']=(OUT/'installation-qualification.json').read_bytes()
 assert shutil.disk_usage(card).free>sum(map(len,payload.values()))+512*1024*1024
 protected={e['path']:e['sha256'] for e in entries if e['path']!='retro/snes-mvp/launch.sh'}
 def verify():
  for n,h in protected.items():assert digest(card/n)==h,n
  for n,b in payload.items():assert (card/TARGET/n).read_bytes()==b,n
 old=stage(card,payload,(OUT/'dispatch.sh').read_bytes(),fix.atomic,health,verify)
 assert (card/'retro/snes-mvp/launch.sh').read_bytes()==(OUT/'dispatch.sh').read_bytes()
 report={'version':'fivegame1','source_commit':commit,'archive':archive.name,'clean_FAT':True,
 'one_shot_armed':True,'physical_result':'PENDING','persistent_UART_preserved':True,
 'protected_existing_files':len(protected),'all_existing_files_hashed':len(entries),
 'archive_storage_policy':a.get('storage_policy','legacy-full-copy'),
 'only_changed_existing_file':'retro/snes-mvp/launch.sh','previous_dispatch_sha256':sha256(old).hexdigest(),
 'dispatch_sha256':digest(card/'retro/snes-mvp/launch.sh'),'marker_sha256':sha256(MARKER).hexdigest(),
 'payload_hashes':{n:sha256(b).hexdigest() for n,b in payload.items()}}
 (archive/'fivegame-installation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
