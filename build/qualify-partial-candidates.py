"""Finite original-ROM qualification; same game states/inputs, every output."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import json,os,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
SELECTIVE=sys.argv[1:]==['--selective']
assert sys.argv[1:] in ([],['--selective'])
OUT=ROOT/('build/partial-selective-private-v1' if SELECTIVE else 'build/partial-candidates-private-v1')
NAMES=('selective',) if SELECTIVE else ('local','sparse')
def main():
 assert not (OUT/'qualification.json').exists();(OUT/'exact').mkdir()
 plan=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text());env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 def run(job):
  name,c=job;core=OUT/f'{name}/snes9x2005_plus_libretro.so';log=OUT/f"exact/{c['seq']:03d}-{name}.log"
  args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'compare'),str(ROOT/'build/plus-a7-out/plus-a7.so'),str(core),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/scene.state"),str(ROOT/f"build/ability-regression-private-v1/cases/{c['seq']:03d}/input.txt"),str(c['observed_effect_id']),'1200']
  with log.open('x') as f:subprocess.run(args,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
  assert 'PASS 1200 calls' in log.read_text();print(c['name'],name,'exact1200',flush=True)
  return {'case':c['seq'],'name':c['name'],'variant':name,'calls':1200,'passed':True,'core_sha256':sha256(core.read_bytes()).hexdigest(),'log_sha256':sha256(log.read_bytes()).hexdigest()}
 with ThreadPoolExecutor(max_workers=2) as pool:proof=list(pool.map(run,[(n,c) for n in NAMES for c in plan['cases'] if c['seq'] in (0,1,8)]))
 result={'passed':True,'comparisons':proof,'calls':len(proof)*1200,'A7_timings_measured':False,'QEMU_timings_used':False,'frameskip':False,'card_access':False,'production_gate_passed':False};(OUT/'qualification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(proof)*1200,'exact original-output calls; no A7 performance claim')
if __name__=='__main__':main()
