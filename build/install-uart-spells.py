"""Install persistent correction and separately owned identical FFVI retest."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,shutil,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/uart-spells-private'
MARKER=b'SNES draw-order48 identical retest with persistent UART fix1\n'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/'build'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(archive):
 fix=load('install-uart-fix.py');q=json.loads((OUT/'qualification.json').read_text())
 assert q['epochs']==48 and q['unchanged_plan_runner_cores_states_inputs'] and len(q['qualification'])==4
 for n,h in q['sources'].items():assert digest(ROOT/n)==h,n
 for n,h in q['payloads'].items():assert digest(OUT/n)==h,n
 old=ROOT/'build/draw-order-test-private-v1';oq=json.loads((old/'verification.json').read_text())
 assert digest(old/'verification.json')==q['baseline_suite_verification_sha256']
 for n in q['unchanged_payloads']:assert digest(OUT/n)==oq['payload_hashes'][n],n
 archive=archive.resolve();assert archive.is_relative_to((ROOT/'device-evidence').resolve())
 a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
 card=Path('I:/').resolve();target=card/'retro/snes-draw-uart1';trigger=card/'retro/snes-mvp'
 assert str(card).lower() in ('i:/','i:\\') and not target.exists()
 assert shutil.disk_usage(card).free>sum((OUT/n).stat().st_size for n in q['payloads'])+512*1024*1024
 # Complete preflight/activation of the persistent fix using this fresh archive.
 fix.main(archive)
 fq=fix.artifacts();assert digest(card/'retro/init')==fq['payloads']['init']
 for n,h in fq['payloads'].items():assert digest(card/'retro/uart-fix1'/n if n!='init' else card/'retro/init')==h,n
 assert not list((card/'retro').rglob('armed'))
 baseline_dispatch=(trigger/'launch.sh').read_bytes();protected={e['path']:e['sha256'] for e in a['all_retro_files'] if e['path'] not in ('retro/init','retro/snes-mvp/launch.sh')}
 target.mkdir();payload={n:(OUT/n).read_bytes() for n in q['payloads'] if n!='dispatch.sh'}
 payload['uart-retest-qualification.json']=(OUT/'qualification.json').read_bytes()
 def verify():
  for n,h in protected.items():assert digest(card/n)==h,n
  assert digest(card/'retro/init')==fq['payloads']['init']
  for n,b in payload.items():assert (target/n).read_bytes()==b,n
  assert digest(card/'002/Final Fantasy VI.zip')==fix.ROM
 try:
  for n,b in payload.items():
   p=target/n;assert p.resolve().is_relative_to(target.resolve());p.parent.mkdir(parents=True,exist_ok=True);fix.atomic(p,b)
  verify();fix.health(archive,'retest-payload')
  fix.atomic(trigger/'launch.sh',(OUT/'dispatch.sh').read_bytes())
  fix.atomic(trigger/'armed',MARKER)
  assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/snes-mvp/armed']
  assert (trigger/'armed').read_bytes()==MARKER
  verify();fix.health(archive,'retest-armed')
 except BaseException:
  fix.health(archive,'retest-before-rollback')
  if (trigger/'armed').exists():assert (trigger/'armed').read_bytes()==MARKER;(trigger/'armed').unlink()
  assert (trigger/'launch.sh').read_bytes() in (baseline_dispatch,(OUT/'dispatch.sh').read_bytes())
  fix.atomic(trigger/'launch.sh',baseline_dispatch)
  # Retain the persistent fix and any unarmed retest staging for inspection.
  raise
 report={'version':'uart-spells1','source_commit':fix.git('rev-parse','HEAD'),'archive':archive.name,
 'target':target.relative_to(card).as_posix(),'one_shot_armed':True,'persistent_UART_enabled':True,
 'init_sha256':digest(card/'retro/init'),'payload_hashes':{n:sha256(b).hexdigest() for n,b in payload.items()},
 'dispatch_sha256':digest(trigger/'launch.sh'),'marker_sha256':sha256(MARKER).hexdigest(),
 'protected_prior_files':len(protected),'ROM_progress_and_old_test_evidence_preserved':True,
 'baseline_physical_analysis_sha256':q['baseline_physical_analysis_sha256'],'physical_result':'PENDING','FAT_clean':True}
 (archive/'uart-spells-installation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
