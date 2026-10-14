"""Count eligibility failures in the isolated second observer; no device timing."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import os,subprocess,json
R=Path.cwd();O=R/'build/shared-geometry-private-v2';(O/'exact').mkdir()
plan=json.loads((R/'build/ability-regression-private-v1/plan.json').read_text())
def run(c):
 p=O/f"exact/{c['seq']:03d}.log"
 args=['qemu-arm','-cpu','cortex-a7','-L',str(R/'build/sysroot'),str(O/'compare'),str(R/'build/common-band-private-v3/plus-a7.so'),str(O/'core/snes9x2005_plus_libretro.so'),str(R/'build/plus-a7-out/ff6.sfc'),str(R/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),str(R/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
 with p.open('x') as f:subprocess.run(args,env={**os.environ,'LD_LIBRARY_PATH':str(R/'build/sysroot/lib')},stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
 rows=[list(map(int,l[7:].split(','))) for l in p.read_text().splitlines() if l.startswith('SHARED ')]
 indices=range(384,416) if c['seq']==1 else range(496,530)
 means=[sum(rows[i][j+1] for i in indices)/len(indices) for j in range(16)]
 print(c['name'],means,flush=True)
 return {'fixture':c['seq'],'means':means,'calls':1200,'exact':True}
with ThreadPoolExecutor(max_workers=2) as pool:cases=list(pool.map(run,[c for c in plan['cases'] if c['seq'] in (1,8)]))
(O/'eligibility.json').write_text(json.dumps({'cases':cases,'counter7':'BG0 visits','counter8':'nonmode1','counter9':'non8x8','counter10':'unsupported_batch','counter11':'not_both_enabled','counter12':'clip_count_nonzero','counter13':'window2_target','counter14':'main_clip_count1_fullwidth','counter15':'sub_clip_count1_fullwidth'},indent=2)+'\n')
