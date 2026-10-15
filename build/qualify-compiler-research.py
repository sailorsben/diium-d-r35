"""Check semantic equivalence of compiler counterfactuals, not their speed."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import json,os,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/compiler-research-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 assert not (OUT/'qualification.json').exists();(OUT/'exact').mkdir()
 cases=[c for c in json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text())['cases'] if c['seq'] in (1,8,17)]
 labels=['combined','combined-one','combined-flag-local','combined-apu-boundary']
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 def run(job):
  label,c=job;core=OUT/label/'snes9x2005_plus_libretro.so';p=OUT/f"exact/{label}-{c['seq']:03d}.log"
  args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(ROOT/'build/ppu-refinements-private-v4/compare'),str(ROOT/'build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so'),str(core),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
  with p.open('x') as f:subprocess.run(args,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
  assert 'PASS 1200 calls' in p.read_text();print('PASS compiler control',label,c['name'],flush=True)
  return {'label':label,'case':c['name'],'calls':1200,'core_sha256':digest(core),'log_sha256':digest(p)}
 with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,[(l,c) for l in labels for c in cases]))
 for n,h in json.loads((OUT/'frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 (OUT/'qualification.json').write_text(json.dumps({'passed':True,'calls':14400,'normalized_state_every':30,'results':results,'A7_time_claim':False,'card_access':False},indent=2)+'\n')
if __name__=='__main__':main()
