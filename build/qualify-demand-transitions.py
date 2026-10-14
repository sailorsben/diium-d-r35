from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import os,json,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-final-private-v2'
def main():
 assert sys.argv[1:] in ([],[''],['--deterministic']);fixed=sys.argv[1:]==['--deterministic'];prefix='transition-fixed' if fixed else 'transition'
 dest='transitions-fixed' if fixed else 'transitions';assert not (OUT/(dest+'.json')).exists();(OUT/dest).mkdir()
 names=('midframe_mode5','midframe_mode6','midframe_interlace','midframe_239','midframe_pseudohires','initial_hires_fallback','state_load_cycles')
 def run(kind):
  log=OUT/f'{dest}/{kind}.log';args=['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/(prefix+'-compare')),str(OUT/(prefix+'-reference')/'snes9x2005_plus_libretro.so'),str(OUT/(prefix+'-candidate')/'snes9x2005_plus_libretro.so'),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(ROOT/'build/ability-regression-private-v1/cases/001/scene.state'),str(ROOT/'build/ability-regression-private-v1/cases/001/input.txt'),'19','1200',str(kind)]
  with log.open('x') as f:subprocess.run(args,cwd=ROOT,env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')},stdout=f,stderr=subprocess.STDOUT,check=True,timeout=480)
  txt=log.read_text();assert 'PASS 1200 calls' in txt;rows=[list(map(int,l[7:].split(','))) for l in txt.splitlines() if l.startswith('DEMAND ')]
  assert len(rows)==1200;direct=sum(r[17] for r in rows);promote=sum(r[18] for r in rows);fallback=sum(r[20] for r in rows)
  if kind in (1,2,3,5):assert promote>0
  if kind==6:assert fallback>0
  if kind in (4,7):assert direct>0
  print('PASS real-core',names[kind-1],direct,'direct',promote,'promotions',fallback,'fallbacks',flush=True)
  return {'kind':names[kind-1],'calls':1200,'direct_frames':direct,'promotions':promote,'fallbacks':fallback,'raw_graphics_PCM_state_match':True,'log_sha256':sha256(log.read_bytes()).hexdigest()}
 with ThreadPoolExecutor(max_workers=3) as pool:proof=list(pool.map(run,range(1,8)))
 (OUT/(dest+'.json')).write_text(json.dumps({'passed':True,'calls':8400,'cases':proof,'synthetic_register_writes':True,'common_fixture_HDMA_base_reset':fixed,'final_core_HDMA_changed':False,'ignored_emulated_fields':False,'ROM_modified':False,'A7_performance_evidence':False},indent=2)+'\n')
if __name__=='__main__':main()
