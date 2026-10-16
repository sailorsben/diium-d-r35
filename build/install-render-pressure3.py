"""Explicit-install-only ROM-free lab on I:. Archive first; not invoked by build."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/render-pressure3-private'
MARKER=b'Render pressure3 ROM-free77-phase device lab\n'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/'build'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(archive):
 fix=load('install-uart-fix.py');q=json.loads((OUT/'qualification.json').read_text());prep=json.loads((OUT/'preparation.json').read_text())
 assert q['passed'] and q['controller_mock_phases']==prep['phases']==77 and q['mock_rejected_as_physical'] and q['load_sweeps_on_light_workload']
 assert digest(OUT/'controller-qualification.json')==q['controller_qualification_sha256']
 fault=json.loads((OUT/'fault-qualification.json').read_text());assert fault['passed'] and fault['qualification_sha256']==digest(OUT/'qualification.json') and fault['wrapper_sha256']==q['payloads']['launch.sh']
 assert fault['source_sha256']==digest(ROOT/'build/check-render-pressure3-faults.py')
 assert digest(OUT/'preparation.json')==q['preparation_sha256']
 for group in ['sources','local_compile_dependencies']:
  for n,h in q[group].items():assert digest(ROOT/n)==h,n
 for n,h in q['payloads'].items():assert digest(OUT/n)==h,n
 assert not fix.git('status','--porcelain') and fix.git('branch','--show-current')=='codex/snes-mvp-foundation'
 commit=fix.git('rev-parse','HEAD');assert commit==fix.git('rev-parse','origin/codex/snes-mvp-foundation')
 archive=archive.resolve();assert archive.is_relative_to((ROOT/'device-evidence').resolve());a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
 card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\');target=card/'retro/render-pressure3';mvp=card/'retro/snes-mvp';assert not target.exists()
 assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
 for e in a['all_retro_files']:assert digest(card/e['path'])==e['sha256'],e['path']
 guard=load('package-snes-1.19.py')
 for n,h in guard.BOOT_EXPECTED.items():assert digest(card/n)==h,n
 assert digest(card/'retro/init')=='24280b658d52702848901df258c9e3e9c4a1c4ba876cdad03534bee67d0343fe'
 assert digest(card/'002/Final Fantasy VI.zip')==fix.ROM
 fix.health(archive,'pressure-before');payload={n:(OUT/n).read_bytes() for n in q['payloads'] if n!='dispatch.sh'}
 payload['qualification.json']=(OUT/'qualification.json').read_bytes();assert shutil.disk_usage(card).free>sum(map(len,payload.values()))+512*1024*1024
 protected={e['path']:e['sha256'] for e in a['all_retro_files'] if e['path']!='retro/snes-mvp/launch.sh'};old=(mvp/'launch.sh').read_bytes();target.mkdir()
 def verify():
  for n,h in protected.items():assert digest(card/n)==h,n
  for n,b in payload.items():assert (target/n).read_bytes()==b,n
 try:
  for n,b in payload.items():fix.atomic(target/n,b)
  verify();fix.health(archive,'pressure-payload')
  fix.atomic(mvp/'launch.sh',(OUT/'dispatch.sh').read_bytes());fix.atomic(target/'armed',MARKER);fix.atomic(mvp/'armed',MARKER)
  assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/render-pressure3/armed','retro/snes-mvp/armed']
  verify();fix.health(archive,'pressure-armed')
 except BaseException:
  fix.health(archive,'pressure-before-rollback')
  for marker in [target/'armed',mvp/'armed']:
   if marker.exists():assert marker.read_bytes()==MARKER;marker.unlink()
  assert (mvp/'launch.sh').read_bytes() in (old,(OUT/'dispatch.sh').read_bytes());fix.atomic(mvp/'launch.sh',old);raise
 report={'version':'render-pressure3','source_commit':commit,'archive':archive.name,'one_shot_armed':True,'clean_FAT':True,'persistent_UART_preserved':True,
 'payload_hashes':{n:sha256(b).hexdigest() for n,b in payload.items()},'dispatch_sha256':digest(mvp/'launch.sh'),'marker_sha256':sha256(MARKER).hexdigest(),'physical_result':'PENDING','ROM_required':False}
 (archive/'render-pressure-installation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
