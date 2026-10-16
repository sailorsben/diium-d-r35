"""Run recorded cold-boot button sequences, retaining private visual checkpoints."""
from pathlib import Path
import json,subprocess
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/multigame-fixes-private-v1'
# Libretro masks: Start=8, A=100, B=1, Right=80, Y=2.
PLAN={
 0:[[600,0],[8,8],[180,0],[8,256],[1800,0],[8,256],[300,0],[60,128],[8,1],[300,0]],
 1:[[600,0],[8,8],[180,0],[8,256],[6000,0],[6000,0],[8,8],[600,0]],
 2:[[600,0],[8,8],[180,0],[8,256],[180,0],[8,8],[180,0],[8,256],[180,0],[8,8],[300,1]],
 3:[[1400,0],[8,8],[600,0],[8,8],[600,0],[8,8],[1200,0],[8,8],[600,0]],
 4:[[1200,0],[8,8],[300,0],[8,8],[600,0],[8,256],[600,0],[600,130]]}
def run(i):
 d=OUT/f'play-{i}';d.mkdir();commands=''.join(f'{n} {mask:x}\n' for n,mask in PLAN[i]);(d/'inputs.txt').write_text(commands)
 q=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib',str(OUT/'explore'),str(OUT/'core/snes9x2005_plus_libretro.so'),str(ROOT/f'build/multigame-private-v3/game-{i}.sfc'),str(d)]
 with (d/'run.log').open('w') as f:r=subprocess.run(q,cwd=ROOT,input=commands,text=True,stdout=f,stderr=subprocess.STDOUT,timeout=300)
 print('PLAY',i,r.returncode,flush=True);return {'game':i,'returncode':r.returncode,'inputs':PLAN[i]}
def main():
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,range(5)))
 (OUT/'exploration.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':main()
