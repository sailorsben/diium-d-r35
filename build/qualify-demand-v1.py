"""Every frame's raw graphics/PCM, geometry and periodic normalized state.
Work census is a separate build; no QEMU timings enter the evidence."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json,os,subprocess,sys,statistics
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-private-v1'
FIELDS=('dma_spans','dma_bytes','dma_old_flags','dma_flags','ring_old_copies','ring_copies',
 'zero_palettes','obj_invalidation_avoided','no_recipient_scanlines','geometry_produced_bands',
 'geometry_reused_bands','geometry_write_bytes','geometry_read_bytes','geometry_full_tiles',
 'geometry_edges','geometry_fallbacks','direct_frames','output_promotions','aux_migration_bytes',
 'output_fallbacks','geometry_16_bands','geometry_bg0','geometry_bg1','geometry_bg2','geometry_bg3',
 'geometry_window_bands','geometry_main_cells','geometry_sub_cells','palette_last_reuse','palette_lookup','reserved30','reserved31')
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert sys.argv[1:] in ([],['--peaks']);peaks=bool(sys.argv[1:]);name='peaks' if peaks else 'qualification'
 assert not (OUT/(name+'.json')).exists();logs=OUT/name;logs.mkdir()
 plan=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text())
 cases=[c for c in plan['cases'] if not peaks or c['seq'] in (1,8)]
 assert [c['seq'] for c in cases if c['name'] in ('METEOR','QUASAR')]==[1,8]
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 def run(job):
  variant,label,c=job;core=OUT/variant/label/'snes9x2005_plus_libretro.so';log=logs/f"{variant}-{label}-{c['seq']:03d}.log"
  args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'compare'),
   str(ROOT/'build/common-band-private-v3/plus-a7.so'),str(core),str(ROOT/'build/plus-a7-out/ff6.sfc'),
   str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),
   str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
  reused=False
  prior=OUT/'peaks'/log.name
  if not peaks and prior.exists() and 'PASS 1200 calls' in prior.read_text():
   log=prior;reused=True
  else:
   with log.open('x') as f:subprocess.run(args,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=480)
  txt=log.read_text();assert 'PASS 1200 calls' in txt
  rows=[list(map(int,l[7:].split(','))) for l in txt.splitlines() if l.startswith('DEMAND ')]
  assert len(rows)==1200 and [r[0] for r in rows]==list(range(1200)) and all(len(r)==33 for r in rows)
  sums={k:sum(r[j+1] for r in rows) for j,k in enumerate(FIELDS)}
  if label=='counted-core':
   if variant in ('dma','combined'):assert sums['dma_spans']>0 and sums['dma_old_flags']>sums['dma_flags']
   if variant in ('small','combined'):assert sums['zero_palettes']>0 and sums['ring_old_copies']>sums['ring_copies']
   if variant in ('geometry','combined'):assert sums['geometry_reused_bands']>0
   if variant in ('output','combined'):assert sums['direct_frames']>0
  heavy=None
  if c['seq'] in (1,8):
   indexes=range(384,416) if c['seq']==1 else range(496,530)
   heavy={k:statistics.mean(rows[i][j+1] for i in indexes) for j,k in enumerate(FIELDS)}
  print('PASS',variant,label,c['seq'],c['name'],'1200 raw graphics/PCM + geometry/state',flush=True)
  return {'variant':variant,'label':label,'case':c['seq'],'name':c['name'],'calls':1200,
   'core_sha256':digest(core),'log_sha256':digest(log),'reused_completed_peak_replay':reused,'work_total':sums,'heavy_mean':heavy}
 variants=('dma','small','geometry','output','combined')
 jobs=[(v,l,c) for v in variants for l in ('core','counted-core') for c in cases]
 with ThreadPoolExecutor(max_workers=3) as pool:proof=list(pool.map(run,jobs))
 # Frozen originals were never build targets. Check all bytes, not just ELFs.
 frozen=json.loads((OUT/'frozen.json').read_text())
 assert all(digest(ROOT/p)==h for p,h in frozen.items())
 data={'passed':True,'calls':len(proof)*1200,'comparisons':proof,'raw_bytes_compared':True,
  'graphics_PCM_geometry_each_call':True,'normalized_state_every':30,'frozen_files_verified':len(frozen),
  'reference_sha256':digest(ROOT/'build/common-band-private-v3/plus-a7.so'),
  'A7_savings_measured':False,'QEMU_timings_used':False,'card_access':False,'production_gate_passed':False}
 (OUT/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
 print('PASS',data['calls'],'new candidate calls; all',len(frozen),'frozen files remain exact',flush=True)
if __name__=='__main__':main()
