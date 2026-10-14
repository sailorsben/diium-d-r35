"""Explicit-install-only I: automatic spell test, separate and one-shot."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-spells-private-v1'
MARKER=b'SNES demand-spells1 automatic18-context test, all frames; experimental\n'
spec=importlib.util.spec_from_file_location('spell_card_guard',ROOT/'build/package-snes-1.19.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
def digest(p):return sha256(p.read_bytes()).hexdigest()
def health(archive,name):
 r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True);(archive/name).write_text(r.stdout+r.stderr,encoding='utf-8')
 assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());q=json.loads((OUT/'verification.json').read_text());ready=json.loads((OUT/'ready.json').read_text())
 assert a['fat_clean'] and a['card_writes']==0 and q['passed'] and q['native_client_qualified'] and q['wrapper_qualified']
 assert q['measurement_only'] and not q['production_gate_passed'] and not q['frameskip']
 assert not git('status','--porcelain') and git('branch','--show-current')=='codex/snes-mvp-foundation'
 commit=git('rev-parse','HEAD');assert commit==git('rev-parse','origin/codex/snes-mvp-foundation')
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for name,h in q[group].items():assert digest(ROOT/name if group=='source_hashes' else OUT/name)==h,name
 for name,h in ready['additional_sources'].items():assert digest(ROOT/name)==h,name
 assert ready['verification_sha256']==digest(OUT/'verification.json')
 card=Path('I:/').resolve();target=card/'retro/snes-demand-spells1';old=card/'retro/snes-mvp'
 assert str(card).lower() in ('i:/','i:\\') and target.resolve().is_relative_to(card) and not target.exists()
 assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
 for e in a['all_retro_files']:assert digest(card/e['path'])==e['sha256'],e['path']
 for name,h in guard.BOOT_EXPECTED.items():assert digest(card/name)==h,name
 assert digest(card/'retro/init')==guard.baseline.HOOK
 assert digest(old/'plus-a7.so')=='80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'
 rom=card/'002/Final Fantasy VI.zip';rom_hash=digest(rom)
 assert rom_hash=='f61af2bd9e3f9b6a2bd543fb176af0b81fd9e5ba4ea0fa0f453371ccb45d3911'
 health(archive,'chkdsk-before-demand-spells.txt')
 payload={n:(OUT/n).read_bytes() for n in q['payload_hashes'] if n!='dispatch.sh'}
 payload['suite-identity.json']=(OUT/'verification.json').read_bytes();payload['TEST-ME.txt']=(ROOT/'docs/snes-demand-spells-test.txt').read_bytes()
 assert shutil.disk_usage(card).free>sum(map(len,payload.values()))+512*1024*1024
 protected={e['path']:e['sha256'] for e in a['all_retro_files'] if e['path']!='retro/snes-mvp/launch.sh'}
 original=(old/'launch.sh').read_bytes();marker=old/'armed';created=[];dispatch=False;target.mkdir()
 def verify():
  for n,h in protected.items():assert digest(card/n)==h,n
  for n,raw in payload.items():assert (target/n).read_bytes()==raw,n
  assert digest(rom)==rom_hash
 try:
  for n,raw in payload.items():
   dest=target/n;dest.parent.mkdir(parents=True,exist_ok=True);guard.atomic(dest,raw,target);created.append(dest)
  verify();health(archive,'chkdsk-after-demand-spells-payload.txt')
  guard.atomic(old/'launch.sh',(OUT/'dispatch.sh').read_bytes(),old);dispatch=True
  guard.atomic(marker,MARKER,old)
  assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/snes-mvp/armed'] and marker.read_bytes()==MARKER
  health(archive,'chkdsk-after-demand-spells-arm.txt');verify()
 except Exception:
  health(archive,'chkdsk-before-demand-spells-rollback.txt')
  if marker.exists():assert marker.read_bytes()==MARKER;marker.unlink()
  if dispatch:guard.atomic(old/'launch.sh',original,old)
  assert target.resolve().is_relative_to(card) and target.name=='snes-demand-spells1'
  for dest in reversed(created):assert dest.resolve().is_relative_to(target);dest.unlink()
  for folder in sorted((p for p in target.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):assert folder.resolve().is_relative_to(target);folder.rmdir()
  target.rmdir();raise
 proof={'version':q['version'],'source_commit':commit,'archive':archive.name,'card':'I:','one_shot_armed':True,'clean_FAT':True,
 'protected_files':len(protected),'production_gate_passed':False,'physical_result':'PENDING','ROM_unchanged':True,'original_progress_unchanged':True,
 'payload_hashes':{n:sha256(raw).hexdigest() for n,raw in payload.items()},'dispatch_sha256':digest(old/'launch.sh')}
 (archive/'demand-spells-installation.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
