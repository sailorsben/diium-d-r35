"""Actual original renderer oracle and real-core resolution/state seams."""
from pathlib import Path
from hashlib import sha256
import json, os, shutil, subprocess, sys

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/draw-order-private-v1'
FLAGS='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'

def digest(p):return sha256(p.read_bytes()).hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')

def build(label,extra=''):
 target=OUT/label;shutil.copy2(OUT/'boundary/source/apu_blargg.o',target/'source/apu_blargg.o')
 args=['make','-j3','platform=unix','USE_BLARGG_APU=1','LOAD_FROM_MEMORY=1','GIT_VERSION=" 7f3528e"','CC=arm-linux-gnueabihf-gcc '+FLAGS+' '+extra,
 'SHARED=-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T',
 'LDFLAGS=-L../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1']
 with (OUT/(label+'-build.log')).open('x') as f:subprocess.run(args,cwd=target,stdout=f,stderr=subprocess.STDOUT,check=True)
 assert digest(target/'source/apu_blargg.o')==digest(OUT/'boundary/source/apu_blargg.o')

def compile_check(source,name):
 libs=['-Lbuild/sysroot/lib','-Wl,--no-as-needed','-l:libdl-2.30.so','-l:libz.so.1','-l:libpthread-2.30.so','-l:librt-2.30.so','-l:libm-2.30.so','-l:libc-2.30.so','-l:libgcc_s.so.1','-l:ld-2.30.so']
 subprocess.run(['arm-linux-gnueabihf-gcc',*FLAGS.split(),'-DUSE_BLARGG_APU','-O2','-std=gnu99','-Wall','-Wextra','-Werror','-no-pie','-nostdlib',
 '-Ibuild','-I'+str(OUT),'-Ibuild/snes9x2005/libretro-common/include','/usr/arm-linux-gnueabihf/lib/crt1.o',str(source),*libs,'-o',str(OUT/name)],cwd=ROOT,check=True)

def main():
 for label in ('boundary','priority'):
  target=OUT/(label+'-probe');assert not target.exists();shutil.copytree(OUT/label,target,ignore=shutil.ignore_patterns('*.o','*.so'))
  p=target/'source/gfx.c';s='static unsigned d35_order_probe_hits;\n'+p.read_text()
  if label=='priority':
   anchor='         if (order_top)\n         {';assert s.count(anchor)==1;s=s.replace(anchor,anchor+'\n            d35_order_probe_hits++;')
  write(p,s+'\n#include "draw-order-render-probe.h"\n');shutil.copy2(ROOT/'build/draw-order-render-probe.h',target/'source/draw-order-render-probe.h')
  p=target/'link.T';write(p,p.read_text().replace('global:','global: d35_order_probe; d35_order_probe_hits_read;'))
  build(label+'-probe')
 compile_check(ROOT/'build/draw-order-render-check.c','render-check')
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 with (OUT/'render-check.log').open('x') as f:
  subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(OUT/'render-check'),
  str(OUT/'boundary-probe/snes9x2005_plus_libretro.so'),str(OUT/'priority-probe/snes9x2005_plus_libretro.so'),str(ROOT/'build/plus-a7-out/ff6.sfc')],
  env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
 print((OUT/'render-check.log').read_text(),flush=True)
 code=(ROOT/'build/prepare-demand-transitions.py').read_text().replace("OUT=ROOT/'build/demand-final-private-v2'","OUT=ROOT/'build/draw-order-private-v1'")
 code=code.replace("ROOT/'build/common-band-private-v3/core'","OUT/'boundary'").replace("OUT/'core'","OUT/'priority'")
 ns={'__file__':str(ROOT/'build/prepare-demand-transitions.py'),'__name__':'draw_order_transition_prepare'}
 exec(compile(code,'draw_order_transition_prepare','exec'),ns);old=sys.argv;sys.argv=[old[0],'--deterministic']
 try:ns['main']()
 finally:sys.argv=old
 build('transition-fixed-reference');build('transition-fixed-candidate','-DD35_DEMAND_COUNT')
 compile_check(OUT/'transition-fixed-compare.c','transition-fixed-compare')
 code=(ROOT/'build/qualify-demand-transitions.py').read_text().replace("OUT=ROOT/'build/demand-final-private-v2'","OUT=ROOT/'build/draw-order-private-v1'")
 ns={'__file__':str(ROOT/'build/qualify-demand-transitions.py'),'__name__':'draw_order_transitions'}
 exec(compile(code,'draw_order_transitions','exec'),ns);old=sys.argv;sys.argv=[old[0],'--deterministic']
 try:ns['main']()
 finally:sys.argv=old
 (OUT/'seams.json').write_text(json.dumps({'passed':True,'original_renderer_probe':(OUT/'render-check.log').read_text().strip(),
 'resolution_state_transitions':json.loads((OUT/'transitions-fixed.json').read_text()),'A7_performance_evidence':False},indent=2)+'\n')

if __name__=='__main__':main()
