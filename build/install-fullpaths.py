"""I:-only owned measurement install; archive/hash/FAT protected, never production."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fullpaths-private-v2'
MARKER=b'SNES fullpaths1 five-core A7 measurement, every frame, two orders; experimental\n'
spec=importlib.util.spec_from_file_location('fullpaths_guard',ROOT/'build/package-snes-1.19.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
def digest(p):return sha256(p.read_bytes()).hexdigest()
def health(archive,name):
 r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True);(archive/name).write_text(r.stdout+r.stderr,encoding='utf-8')
 assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
def install(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());q=json.loads((OUT/'verification.json').read_text());plan=json.loads((OUT/'plan.json').read_text())
 assert a['fat_clean'] and a['card_writes']==0 and q['passed'] and q['archive']==archive.name
 assert q['measurement_only'] and q['native_client_qualified'] and q['wrapper_qualified'] and not q['production_gate_passed'] and not q['frameskip']
 assert q['authorization']==plan['authorization']=='Stage an automated test on I: to measure the actual A7 savings for these three paths, separately and combined. Keep every frame and log whether we have enough headroom.'
 card=Path('I:/').resolve();old=card/'retro/snes-mvp';target=card/'retro/snes-fullpaths1'
 assert str(card).lower() in ('i:/','i:\\') and target.resolve().is_relative_to(card) and not target.exists()
 assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for name,h in q[group].items():assert digest(ROOT/name)==h,name
 for e in a['all_retro_files']:assert digest(card/e['path'])==e['sha256'],e['path']
 for name,h in guard.BOOT_EXPECTED.items():assert digest(card/name)==h,name
 assert digest(card/'retro/init')==guard.baseline.HOOK
 assert digest(card/'retro/snes-mvp/plus-a7.so')=='80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'
 health(archive,'chkdsk-before-fullpaths.txt')
 payload={n:OUT/n for n in ('ability-suite','launch.sh','ROM-PATH.txt','plan.json')}
 payload.update({'suite-identity.json':OUT/'verification.json','TEST-ME.txt':ROOT/'docs/snes-fullpaths-test.txt'})
 for folder in ('cores','cases'):
  for p in (OUT/folder).rglob('*'):
   if p.is_file():payload[folder+'/'+p.relative_to(OUT/folder).as_posix()]=p
 assert len([n for n in payload if n.endswith('.state')])==50
 assert shutil.disk_usage(card).free>sum(p.stat().st_size for p in payload.values())+256*1024*1024
 protected={e['path']:e['sha256'] for e in a['all_retro_files'] if e['path']!='retro/snes-mvp/launch.sh'}
 original=(old/'launch.sh').read_bytes();marker=old/'armed';created=[];dispatch=False
 target.mkdir();(target/'saves').mkdir()
 def verify():
  for name,h in protected.items():assert digest(card/name)==h,name
  for name,p in payload.items():assert digest(target/name)==digest(p),name
 try:
  for name,p in payload.items():
   dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);guard.atomic(dest,p.read_bytes(),target);created.append(dest)
  verify();health(archive,'chkdsk-after-fullpaths-payload.txt')
  guard.atomic(old/'launch.sh',(OUT/'dispatch.sh').read_bytes(),old);dispatch=True
  guard.atomic(marker,MARKER,old);assert marker.read_bytes()==MARKER
  assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/snes-mvp/armed']
  health(archive,'chkdsk-after-fullpaths-arm.txt');verify()
  assert (old/'launch.sh').read_bytes()==(OUT/'dispatch.sh').read_bytes()
 except Exception:
  health(archive,'chkdsk-before-fullpaths-rollback.txt')
  if marker.exists():assert marker.read_bytes()==MARKER;marker.unlink()
  if dispatch:guard.atomic(old/'launch.sh',original,old)
  assert target.resolve().is_relative_to(card) and target.name=='snes-fullpaths1'
  for p in reversed(created):assert p.resolve().is_relative_to(target);p.unlink()
  for p in sorted((p for p in target.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):assert p.resolve().is_relative_to(target);p.rmdir()
  target.rmdir();raise
 proof={'version':q['version'],'card':'I:','archive':archive.name,'one_shot_armed':True,'fat_checks_clean':True,'measurement_only':True,'production_gate_passed':False,'hardware_result':'PENDING','frameskip':False,'runs':100,'variants':plan['variants'],'contexts':10,'original_retro_files_protected':len(protected),'original_progress_unchanged':True,'production_binaries_unchanged':True,'payload_files':len(payload),'payload_hashes':{n:digest(p) for n,p in payload.items()},'dispatch_sha256':digest(old/'launch.sh')}
 (archive/'fullpaths-installation.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='payload_hashes'},indent=2))
if __name__=='__main__':install(Path(sys.argv[1]))
