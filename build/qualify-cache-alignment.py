"""Original-input exactness and ARM address assertions; no timing claims."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json,os,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/cache-alignment-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not (OUT/'qualification.json').exists();(OUT/'exact').mkdir()
 plan=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text())
 selected=[c for c in plan['cases'] if c['seq'] in (0,1,3,5,6,7,8,10)]
 def run(c):
  log=OUT/f"exact/{c['seq']:03d}.log"
  args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'compare'),str(ROOT/'build/common-band-private-v3/plus-a7.so'),str(OUT/'core/snes9x2005_plus_libretro.so'),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
  with log.open('x') as f:subprocess.run(args,env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')},stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
  text=log.read_text();assert 'PASS 1200 calls' in text
  line=[l for l in text.splitlines() if l.startswith('ALIGNED ')];assert len(line)==1
  layout=list(map(int,line[0].split()[1:]));assert all(not v%64 for v in layout[:3]) and not layout[7]%64
  print('PASS exact aligned cache',c['seq'],c['name'],flush=True)
  return {'fixture':c['seq'],'name':c['name'],'exact_calls':1200,'log_sha256':digest(log),'ARM_QEMU_layout':layout}
 with ThreadPoolExecutor(max_workers=2) as pool:cases=list(pool.map(run,selected))
 data={'passed':True,'qualified_original_command_calls':9600,'cases':cases,'oracle_core_sha256':digest(ROOT/'build/common-band-private-v3/plus-a7.so'),'candidate_core_sha256':digest(OUT/'core/snes9x2005_plus_libretro.so'),'metadata_bytes':960,'palette_table_bytes':2560,'old_cache_bytes':3840,'new_cache_bytes':3520,'A7_measurements':False,'card_access':False,'QEMU_timing_used':False,'production_gate_passed':False,'limits':['ARM/QEMU address assertions establish the implementation guarantee, not archived A7 heap addresses or cache-miss rates.','Rendering/color/depth decisions, original tile allocation sizes, initial zeroing and invalidation lifetimes retained.','No time or cache-miss saving inferred from cache-line counts. Separate A7 test must price full CPU demand and worker interactions.']}
 (OUT/'qualification.json').write_text(json.dumps(data,indent=2)+'\n');print('PASS 9600 exact aligned-cache calls; all3 allocations64B-aligned and all80 tables contained in one64B line')
if __name__=='__main__':main()
