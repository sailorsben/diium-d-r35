"""Install the qualified runner-only focus diagnostic on the exact returned1.19 card."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import importlib.util,json,subprocess
ROOT=Path(__file__).resolve().parent.parent
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/'build'/file)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def digest(p):return sha256(p.read_bytes()).hexdigest()
installer=module('focus_baseline','package-snes-1.19.py')
def health(archive,name):
 r=subprocess.run(['chkdsk','D:'],capture_output=True,text=True)
 (archive/name).write_text(r.stdout,encoding='utf-8')
 assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
def install():
 card=Path('D:/').resolve();assert str(card).lower() in ('d:/','d:\\')
 target=card/'retro/snes-mvp';out=ROOT/'build/snes-focus-out'
 q=json.loads((out/'verification.json').read_text());assert q['passed'] and not q['hardware_qualified']
 for key in ('source_hashes','check_artifact_hashes'):
  for name,wanted in q[key].items():assert digest(ROOT/name)==wanted,name
 assert digest(out/'snes-mvp')==q['binary_sha256']
 old=json.loads((ROOT/'releases/snes-mvp-1.19/manifest.json').read_text())
 assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
 for name,key in [('snes-mvp','binary_sha256'),('plus-a7.so','core_sha256'),('launch.sh','wrapper_sha256')]:
  assert digest(target/name)==old[key],name
 assert q['core_sha256']==old['core_sha256'] and q['wrapper_sha256']==old['wrapper_sha256']
 for name,wanted in installer.BOOT_EXPECTED.items():assert digest(card/name)==wanted,name
 assert digest(card/'retro/init')==installer.baseline.HOOK
 archive=installer.collector.collect(card)
 health(archive,'chkdsk-before-focus.txt')
 collected=json.loads((archive/'collection.json').read_text());lab=json.loads((archive/'lab-collection.json').read_text())
 protected={e['card_path']:e['sha256'] for e in collected['copied_and_hash_verified']
            if e['card_path'] not in ('retro/snes-mvp/snes-mvp','retro/snes-mvp/TEST-ME.txt')}
 protected.update({'retro/platform-lab/'+e['relative_path']:e['sha256'] for e in lab['copied']})
 protected.update(installer.BOOT_EXPECTED)
 for folder in (card/'retro').glob('spi-readback*'):
  if folder.is_dir():
   for p in folder.rglob('*'):
    if p.is_file():protected[p.relative_to(card).as_posix()]=digest(p)
 payload={'snes-mvp':(out/'snes-mvp').read_bytes(),'TEST-ME.txt':(ROOT/'docs/snes-focus-1-test.txt').read_bytes()}
 original={n:(target/n).read_bytes() for n in payload};changed=[];marker=target/'armed'
 try:
  for name,raw in payload.items():installer.atomic(target/name,raw,target);changed.append(name)
  for name,raw in payload.items():assert (target/name).read_bytes()==raw,name
  for name,wanted in protected.items():assert digest(card/name)==wanted,name
  health(archive,'chkdsk-after-focus-payload.txt')
  assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
  armed=b'SNES-focus-1 runner diagnostics; unchanged1.19 core one-shot\n'
  installer.atomic(marker,armed,target)
  assert marker.read_bytes()==armed
  assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/snes-mvp/armed']
  for name,wanted in protected.items():assert digest(card/name)==wanted,name
  for name,raw in payload.items():assert (target/name).read_bytes()==raw,name
  health(archive,'chkdsk-after-focus-arm.txt')
 except Exception:
  # Restore only through a clean card gate; preserve evidence if health fails.
  health(archive,'chkdsk-before-focus-rollback.txt')
  if marker.exists():assert marker.read_bytes()==armed;marker.unlink()
  for name in reversed(changed):installer.atomic(target/name,original[name],target)
  raise
 proof={'version':'1.19-focus1','installed_utc':datetime.now(timezone.utc).isoformat(),
  'archive_before_writes':archive.name,'binary_sha256':q['binary_sha256'],
  'core_sha256':q['core_sha256'],'wrapper_sha256':q['wrapper_sha256'],
  'only_runner_and_test_instructions_replaced':True,'unchanged_files_verified':len(protected),
  'core_states_sram_stock_vesper_init_labs_readers_preserved':True,'all_three_fat_checks_clean':True,
  'only_snes_marker_armed':True,'firmware_trigger_absent':True,
  'audio_render_and_pacing_policy_unchanged':True,'hardware_profile':'pending physical Bio Blast capture'}
 (archive/'focus-installation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(proof,indent=2))
if __name__=='__main__':install()
