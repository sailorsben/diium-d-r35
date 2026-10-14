"""I:-only guarded separate experimental gameplay one-shot; stock stays exact."""
from pathlib import Path
from hashlib import sha256
import importlib.util, json, shutil, subprocess, sys, zipfile
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-gameplay-private-v1'
MARKER=b'SNES demand-gameplay1 experimental manual qualification; separate core/saves\n'
spec=importlib.util.spec_from_file_location('demand_card_guard',ROOT/'build/package-snes-1.19.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
def digest(p):return sha256(p.read_bytes()).hexdigest()
def health(archive,name):
 r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True)
 (archive/name).write_text(r.stdout+r.stderr,encoding='utf-8')
 assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def install(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());q=json.loads((OUT/'verification.json').read_text())
 assert a['fat_clean'] and a['card_writes']==0 and q['passed'] and q['archive']==archive.name
 assert q['manual_controls'] and not q['forced_replay'] and not q['production_gate_passed']
 assert q['authorization']=='User explicitly requested Push it to I: after the offline candidate was completed.'
 assert q['native_client_qualified'] and q['wrapper_qualified']
 assert not git('status','--porcelain') and git('branch','--show-current')=='codex/snes-mvp-foundation'
 commit=git('rev-parse','HEAD');assert commit==git('rev-parse','origin/codex/snes-mvp-foundation')
 card=Path('I:/').resolve();old=card/'retro/snes-mvp';target=card/'retro/snes-demand-gameplay1'
 assert str(card).lower() in ('i:/','i:\\') and target.resolve().is_relative_to(card) and not target.exists()
 assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
 for n,h in q['source_hashes'].items():assert digest(ROOT/n)==h,n
 for n,h in q['payload_hashes'].items():assert digest(OUT/n)==h,n
 for n,h in q['proof_hashes'].items():assert digest(OUT/n)==h,n
 for e in a['all_retro_files']:assert digest(card/e['path'])==e['sha256'],e['path']
 for n,h in guard.BOOT_EXPECTED.items():assert digest(card/n)==h,n
 assert digest(card/'retro/init')==guard.baseline.HOOK
 assert digest(old/'plus-a7.so')=='80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'
 rom=card/'002/Final Fantasy VI.zip';rom_hash=digest(rom)
 with zipfile.ZipFile(rom) as game:
  assert any(sha256(game.read(n)).hexdigest()=='0f51b4fca41b7fd509e4b8f9d543151f68efa5e97b08493e4b2a0c06f5d8d5e2' for n in game.namelist() if not n.endswith('/'))
 health(archive,'chkdsk-before-demand-gameplay.txt')
 payload={n:(OUT/n).read_bytes() for n in q['payload_hashes'] if n!='dispatch.sh'}
 payload['suite-identity.json']=(OUT/'verification.json').read_bytes()
 payload['TEST-ME.txt']=(ROOT/'docs/snes-demand-gameplay-test.txt').read_bytes()
 assert shutil.disk_usage(card).free>sum(map(len,payload.values()))+256*1024*1024
 protected={e['path']:e['sha256'] for e in a['all_retro_files'] if e['path']!='retro/snes-mvp/launch.sh'}
 original=(old/'launch.sh').read_bytes();marker=old/'armed';created=[];dispatch=False
 target.mkdir()
 def verify():
  assert digest(rom)==rom_hash
  for n,h in protected.items():assert digest(card/n)==h,n
  for n,raw in payload.items():assert (target/n).read_bytes()==raw,n
 try:
  for n,raw in payload.items():
   dest=target/n;dest.parent.mkdir(parents=True,exist_ok=True);guard.atomic(dest,raw,target);created.append(dest)
  verify();health(archive,'chkdsk-after-demand-gameplay-payload.txt')
  guard.atomic(old/'launch.sh',(OUT/'dispatch.sh').read_bytes(),old);dispatch=True
  guard.atomic(marker,MARKER,old);assert marker.read_bytes()==MARKER
  assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/snes-mvp/armed']
  health(archive,'chkdsk-after-demand-gameplay-arm.txt');verify()
  assert (old/'launch.sh').read_bytes()==(OUT/'dispatch.sh').read_bytes()
 except Exception:
  health(archive,'chkdsk-before-demand-gameplay-rollback.txt')
  if marker.exists():assert marker.read_bytes()==MARKER;marker.unlink()
  if dispatch:guard.atomic(old/'launch.sh',original,old)
  assert target.resolve().is_relative_to(card) and target.name=='snes-demand-gameplay1'
  for dest in reversed(created):assert dest.resolve().is_relative_to(target);dest.unlink()
  for folder in sorted((p for p in target.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):assert folder.resolve().is_relative_to(target);folder.rmdir()
  target.rmdir();raise
 proof={'version':q['version'],'card':'I:','archive':archive.name,'source_commit':commit,'one_shot_armed':True,
 'fat_checks_clean':True,'experimental_qualification':True,'production_gate_passed':False,'A7_saving_measured':False,
 'original_retro_files_protected':len(protected),'original_progress_unchanged':True,'new_test_saves_separate':True,
 'production_binaries_unchanged':True,'original_ROM_zip_sha256':rom_hash,'payload_hashes':{n:sha256(raw).hexdigest() for n,raw in payload.items()},
 'dispatch_sha256':digest(old/'launch.sh'),'physical_gameplay_result':'PENDING'}
 (archive/'demand-gameplay-installation.json').write_text(json.dumps(proof,indent=2)+'\n')
 print(json.dumps(proof,indent=2))
if __name__=='__main__':install(Path(sys.argv[1]))
