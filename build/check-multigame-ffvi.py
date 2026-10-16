"""Preserve all18 original FFVI contexts after the shared HDMA correction."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/multigame-fixes-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 tag='-'+sys.argv[1] if len(sys.argv)>1 else '';assert tag in ('','-v2');d=OUT/('ffvi'+tag);d.mkdir();source=(ROOT/'build/presentation-runtime-private-v1/compare.c').read_text();assert 'dc[32]' in source;source=source.replace('dc[32]','dc[40]');(d/'compare.c').write_text(source)
 flags=['arm-linux-gnueabihf-gcc','-DUSE_BLARGG_APU','-std=gnu99','-O2','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-Wall','-Wextra','-Werror','-no-pie','-nostdlib','-Ibuild','-Ibuild/demand-private-v1','-Ibuild/snes9x2005/libretro-common/include','/usr/arm-linux-gnueabihf/lib/crt1.o',str(d/'compare.c'),'-Lbuild/sysroot/lib','-Wl,--no-as-needed','-l:libdl-2.30.so','-l:libz.so.1','-l:libc-2.30.so','-l:libgcc_s.so.1','-o',str(d/'compare')]
 with (d/'build.log').open('w') as f:subprocess.run(flags,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
 plan=json.loads((ROOT/'build/ability-regression-private-v1/plan.json').read_text());q=['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib'];core=OUT/'core/snes9x2005_plus_libretro.so';ref=OUT/'reference/snes9x2005_plus_libretro.so'
 def run(case):
  folder=ROOT/f"build/ability-regression-private-v1/cases/{case['seq']:03d}";log=d/f"case-{case['seq']:03d}.log"
  with log.open('w') as f:r=subprocess.run(q+[str(d/'compare'),str(ref),str(core),str(ROOT/'build/plus-a7-out/ff6.sfc'),str(folder/'scene.state'),str(folder/'input.txt'),str(case['observed_effect_id']),'1200'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=480)
  text=log.read_text();passed=r.returncode==0 and 'PASS 1200 calls: exact graphics/PCM/state' in text;print('FFVI',case['name'],passed,flush=True);return {'case':case['seq'],'name':case['name'],'passed':passed,'returncode':r.returncode,'calls':1200,'log_sha256':digest(log),'log_tail':text.splitlines()[-2:]}
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,plan['cases']))
 (OUT/('ffvi'+tag+'-result.json')).write_text(json.dumps({'physical':False,'candidate_sha256':digest(core),'reference_sha256':digest(ref),'cases':results,'generated_compare_sha256':digest(d/'compare.c'),'source_sha256':digest(Path(__file__))},indent=2)+'\n')
if __name__=='__main__':main()
