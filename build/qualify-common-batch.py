"""Original-output qualification and per-effect shared-work census. No A7 time."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import json,os,subprocess,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/('build/common-band-private-v3' if sys.argv[1:]==['band3'] else 'build/common-band-private-v2' if sys.argv[1:]==['band'] else 'build/common-batch-private-v1')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return [list(map(int,l[6:].split(','))) for l in p.read_text().splitlines() if l.startswith('PEARL ')]
def main():
 assert not (OUT/'qualification.json').exists() and not (OUT/'exact').exists();(OUT/'exact').mkdir()
 plan=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text())
 old=json.loads((ROOT/'evidence/2026-10-13/pearl-workback/sub-qualified.json').read_text())
 pred=json.loads((ROOT/'evidence/2026-10-13/full-fidelity-paths/prediction.json').read_text())
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 def run(job):
  label,c=job;core=OUT/('plus-a7.so' if label=='ordinary' else 'counted-core/snes9x2005_plus_libretro.so');exe=OUT/('compare' if label=='ordinary' else 'census-compare');log=OUT/f"exact/{c['seq']:03d}-{label}.log"
  args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(exe),str(ROOT/'build/plus-a7-out/plus-a7.so'),str(core),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
  with log.open('x') as f:subprocess.run(args,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
  assert 'PASS 1200 calls' in log.read_text()
  if label=='census':assert [r[0] for r in read(log)]==list(range(1200))
  print(label,c['seq'],c['name'],'exact',flush=True)
  return {'case':c['seq'],'name':c['name'],'label':label,'calls':1200,'passed':True,'core_sha256':digest(core),'log_sha256':digest(log)}
 with ThreadPoolExecutor(max_workers=2) as pool:proof=list(pool.map(run,[(label,c) for label in ('ordinary','census') for c in plan['cases']]))
 fields=('attempts','cold_fallback','blank_handled','warm_nonblank_calls','rows','active_rows','opaque_rows','partial_rows','palette_materializations','palette_reuse_rows','fixed_operand_queries','plain_rows','math_rows','inactive_rows','early_hidden_calls','band_calls')
 cases=[]
 for c in pred['cases']:
  bpath=ROOT/f"build/pearl-sub-private-v2/both/exact/{c['case']:03d}-census.log"
  bproof=next(r for r in old['exact_comparisons'] if r['kind']=='both' and r['label']=='census' and r['case']==c['case'])
  assert digest(bpath)==bproof['log_sha256']
  a=read(OUT/f"exact/{c['case']:03d}-census.log");b=read(bpath);tail=c['tail_frames']
  means={name:statistics.mean(a[i][337+j] for i in tail) for j,name in enumerate(fields)}
  # Count former full-tile renderer entries for warm nonblank or blank work.
  # Early rejects are a separately qualified path and are not a new saving.
  eliminated=means['warm_nonblank_calls']+means['blank_handled']
  cases.append({'case':c['case'],'name':c['name'],'failed_A7_baseline':c['physical_fixture_failed'],'tail_frames':tail,'common':means,'new_indirect_calls_removed':eliminated,'before_full_tile_calls':statistics.mean(sum(b[i][1+(p*6+bg)*24] for p in range(2) for bg in range(5)) for i in tail),'A7_saving_measured':False})
 receipt={'passed':True,'calls':len(proof)*1200,'exact':proof,'cases':cases,'card_access':False,'every_frame':True,'A7_savings_measured':False,'QEMU_timings_used':False,'production_gate_passed':False,'baseline':'qualified Pearl both v2, already including fullpaths combination; comparison oracle original1.19','limits':['CPU time and frequency not measured.','The candidate adds runtime mode selection, cache guards, context state and possible spills.','Palette reuse counts are row reuse events, not all new savings: the old code already reused within a tile.','Only valid indexed full tiles use the common path; original converter/clipped/unsupported fallbacks remain.']}
 (OUT/'qualification.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PASS 43200 exact original-command calls; shared-work census is not A7 timing',flush=True)
if __name__=='__main__':
 assert sys.argv[1:] in ([],['band'],['band3']);main()
