"""Two bounded original-ROM cases, exact output and per-layer populations."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import os,subprocess,json,statistics
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/source-sharing-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not (OUT/'qualification.json').exists();(OUT/'exact').mkdir()
 plan=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text())
 def run(c):
  log=OUT/f"exact/{c['seq']:03d}.log"
  args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'compare'),str(ROOT/'build/common-band-private-v3/plus-a7.so'),str(OUT/'core/snes9x2005_plus_libretro.so'),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
  with log.open('x') as f:subprocess.run(args,env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')},stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
  text=log.read_text();assert 'PASS 1200 calls' in text
  rows=[list(map(int,l[5:].split(','))) for l in text.splitlines() if l.startswith('ARCH ')];assert [r[0] for r in rows]==list(range(1200))
  assert not any(r[93] or r[94] or r[95] for r in rows)
  indices=range(384,416) if c['seq']==1 else range(496,530)
  layers={name:{field:statistics.mean(rows[i][97+bg*3+k] for i in indices) for k,field in enumerate(('sub_requests','main_requests','matching_main_requests'))} for bg,name in enumerate(('BG0','BG1','BG2','BG3','OBJ'))}
  result={'fixture':c['seq'],'name':c['name'],'exact_calls':1200,'log_sha256':digest(log),'peak_layer_means':layers,'no_source_table_overflow':True,'no_unsupported_layout':True,'exact_original_output':True}
  print(c['name'],layers,flush=True);return result
 with ThreadPoolExecutor(max_workers=2) as pool:cases=list(pool.map(run,[c for c in plan['cases'] if c['seq'] in (1,8)]))
 data={'passed':True,'observer_only':True,'qualified_original_command_calls':2400,'cases':cases,'candidate_core_sha256':digest(OUT/'core/snes9x2005_plus_libretro.so'),'A7_measurements':False,'QEMU_timings_used':False,'limits':['Warm nonblank ordinary full-tile2/4bpp requests only; clipped/scaled/Mode7 paths excluded.','Same redraw, layer, destination, decoded-row pointer, palette pointer and HFlip.','Source-key set retains earlier overlapping OBJ requests; a match is source identity, not a visible or cheap consumer.','No source-sharing optimization or A7 saving measured.']}
 (OUT/'qualification.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':main()
