"""Exact offline output and aligned eliminated work; never A7 timings."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import json,os,subprocess,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/pearl-paths-private-v1'
BASE=ROOT/'build/ability-regression-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return [list(map(int,l[6:].split(','))) for l in p.read_text().splitlines() if l.startswith('PEARL ')]
def qualify(OUT=OUT,kinds=('earlyz','flat','both')):
 assert not (OUT/'qualification.json').exists()
 plan=json.loads((BASE/'plan.json').read_text());env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 ref=ROOT/'build/plus-a7-out/plus-a7.so';rom=ROOT/'build/plus-a7-out/ff6.sfc'
 assert digest(ref)=='80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'
 for kind in kinds:(OUT/kind/'exact').mkdir()
 def run(job):
  kind,label,c=job;d=OUT/kind;core=d/('plus-a7.so' if label=='ordinary' else 'counted-core/snes9x2005_plus_libretro.so');exe=d/('compare' if label=='ordinary' else 'census-compare');log=d/f"exact/{c['seq']:03d}-{label}.log"
  with log.open('x') as f:subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(exe),str(ref),str(core),str(rom),str(BASE/f"cases/{c['seq']:03d}/scene.state"),str(BASE/f"cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200'],env=env,check=True,stdout=f,stderr=subprocess.STDOUT,timeout=180)
  assert 'PASS 1200 calls' in log.read_text();print(kind,label,c['seq'],c['name'],'exact',flush=True)
  if label=='census':assert [r[0] for r in read(log)]==list(range(1200))
  return {'kind':kind,'label':label,'case':c['seq'],'calls':1200,'passed':True,'core_sha256':digest(core),'log_sha256':digest(log)}
 with ThreadPoolExecutor(max_workers=2) as pool:proof=list(pool.map(run,[(kind,label,c) for kind in kinds for label in ('ordinary','census') for c in plan['cases']]))
 tail=list(range(399,415));before=read(ROOT/'build/pearl-work-private-v1/holy.log');pop=[]
 for kind in kinds:
  after=read(OUT/kind/'exact/000-census.log');layers=[]
  for plane in range(2):
   for bg in range(5):
    off=(plane*6+bg)*24+1
    fields=('full_calls','clipped_calls','row_visits','fully_depth_hidden_rows','active_rows','full_mask_rows','active_pixels','overwritten_pixels','math_rows')
    layers.append({'plane':plane,'layer':bg,'before':{k:statistics.mean(before[i][off+j] for i in tail) for j,k in enumerate(fields)},'after':{k:statistics.mean(after[i][off+j] for i in tail) for j,k in enumerate(fields)},'pre_depth_preambles_removed':statistics.mean(after[i][off+20] for i in tail),'pre_depth_rows_removed':statistics.mean(after[i][off+21] for i in tail),'flat_band_rows':statistics.mean(after[i][off+17] for i in tail),'flat_band_expansions':statistics.mean(after[i][off+18] for i in tail)})
  pop.append({'kind':kind,'tail_frames':tail,'layers':layers,'sole_sub_opaque_rows':statistics.mean(after[i][331] for i in tail),'sole_sub_transparent_rows':statistics.mean(after[i][332] for i in tail),'sole_sub_calls':statistics.mean(after[i][333] for i in tail),'A7_saving_measured':False})
 q={'passed':True,'card_writes':0,'frameskip':False,'production_gate_passed':False,'A7_saving_measured':False,'QEMU_timings_used':False,'exact_comparisons':proof,'aligned_Pearl_work':pop,'new_calls':len(proof)*1200,'baseline_census_core_sha256':digest(ROOT/'build/pearl-work-private-v1/plus-a7.so'),'baseline_census_log_sha256':digest(ROOT/'build/pearl-work-private-v1/holy.log'),'limits':['No returned fullpaths data used.','Bounded sole-layer 2bpp subscreen and optional main-depth rejection; fallback elsewhere.' if 'sub' in kinds else 'Bounded Mode1 single-layer 2bpp flat band and ordinary main-depth rejection; fallback everywhere else.','Removed counts do not establish A7 saving or universal behavior.']}
 (OUT/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print(f'PASS {len(kinds)} isolated prototypes, ordinary/census exactness, aligned Pearl work; no hardware timing',flush=True)
if __name__=='__main__':
 assert len(sys.argv)==1 or sys.argv[1:]==['sub']
 if len(sys.argv)>1:qualify(ROOT/'build/pearl-sub-private-v2',('sub','both'))
 else:qualify()
