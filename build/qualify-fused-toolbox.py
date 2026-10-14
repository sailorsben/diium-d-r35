"""Qualify all18 original command contexts; count work without measuring time."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import os,json,subprocess,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
V2=sys.argv[1:]==['--v2']
assert sys.argv[1:] in ([],['--v2'])
OUT=ROOT/('build/fused-toolbox-private-v2' if V2 else 'build/fused-toolbox-private-v1')
FIELDS=('ordinary_bands','sole_bands','policy_samples','four_bpp_prefix_tiles','two_bpp_prefix_tiles','prefix_depth_loads','fully_hidden_tile_returns','prefix_hidden_rows','first_visible_depth_reused','normal_depth_loads','index_row_loads','reserved11','reserved12','reserved13','blank_returns','cold_fallbacks','sparse_one','sparse_two','ordinary_active_rows','ordinary_partial_dense_rows','ordinary_opaque_rows','sole_rows','sole_opaque_rows','sole_partial_dense_rows','sole_sparse_rows','sole_palette_materializations','ordinary_palette_materializations','reserved27','reserved28','reserved29','reserved30','four_bpp_hidden_policy_samples')
if V2:FIELDS=tuple({'reserved11':'depth_policy_vetoes','reserved27':'prefix_rows_skipped_before_visible','reserved28':'band_cells','reserved29':'two_bpp_prefix_depth_loads','reserved30':'four_bpp_prefix_depth_loads'}.get(x,x) for x in FIELDS)
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not (OUT/'qualification.json').exists();(OUT/'exact').mkdir()
 plan=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text());pred=json.loads((ROOT/'evidence/2026-10-13/full-fidelity-paths/prediction.json').read_text());tails={c['case']:c['tail_frames'] for c in pred['cases']};env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 def run(job):
  label,c=job;core=OUT/('plus-a7.so' if label=='ordinary' else 'counted-core/snes9x2005_plus_libretro.so');exe=OUT/('compare' if label=='ordinary' else 'census-compare');log=OUT/f"exact/{c['seq']:03d}-{label}.log"
  args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(exe),str(ROOT/'build/plus-a7-out/plus-a7.so'),str(core),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
  with log.open('x') as f:subprocess.run(args,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
  assert 'PASS 1200 calls' in log.read_text();counts=None
  if label=='census':
   rows=[list(map(int,l[6:].split(','))) for l in log.read_text().splitlines() if l.startswith('FUSED ')];assert len(rows)==1200 and [x[0] for x in rows]==list(range(1200)) and all(len(x)==33 for x in rows)
   if c['seq'] in tails:counts={k:statistics.mean(rows[i][1+j] for i in tails[c['seq']]) for j,k in enumerate(FIELDS)}
  print(label,c['seq'],c['name'],'exact1200',flush=True)
  return {'case':c['seq'],'name':c['name'],'label':label,'calls':1200,'passed':True,'core_sha256':digest(core),'log_sha256':digest(log),'heavy_counts':counts}
 with ThreadPoolExecutor(max_workers=2) as pool:proof=list(pool.map(run,[(label,c) for label in ('ordinary','census') for c in plan['cases']]))
 q={'passed':True,'calls':len(proof)*1200,'comparisons':proof,'every_frame':True,'frameskip':False,'A7_savings_measured':False,'QEMU_timings_used':False,'card_access':False,'production_gate_passed':False,'limits':['Graphics and PCM compared each call; normalized state checkpoints every30 calls.','Work counts include interactions; no microsecond prices inferred.','Policy affects implementation work, never eligibility or output.']}
 (OUT/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print('PASS',q['calls'],'original-output calls; no A7 timing')
if __name__=='__main__':main()
