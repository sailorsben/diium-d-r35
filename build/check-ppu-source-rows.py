"""Dependency/canary oracle and original-command exactness for isolated rows."""
from pathlib import Path
import json,os,runpy,shutil,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ppu-refinements-private-v4'
def main():
 code='''#include <stdint.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "demand-visible-private-v3/core/source/a7_tile.h"
static unsigned long long counts[32];
#define PP_ADD(n,v) (counts[n]+=(v))
static unsigned d35_palette_epoch=1;
#define D35_SOURCE_IMPLEMENTATION
#include "ppu-source-rows.h"
int main(void){uint8_t tile[64] __attribute__((aligned(64)));uint16_t colors[16],out[8],expected[8];unsigned seed=4,cases=0;
 for(unsigned t=0;t<2000;t++){
  for(unsigned j=0;j<64;j++){seed=seed*1664525u+1013904223u;tile[j]=(seed>>16)&15;}
  for(unsigned j=0;j<16;j++){seed=seed*1664525u+1013904223u;colors[j]=seed;}
  d35_source_tile_changed(tile);++d35_palette_epoch;
  for(unsigned row=0;row<8;row++)for(unsigned flip=0;flip<2;flip++)for(unsigned repeat=0;repeat<3;repeat++){
   uint8x8_t idx=vld1_u8(tile+row*8);if(flip)idx=vrev64_u8(idx);
   for(unsigned j=0;j<8;j++)expected[j]=colors[tile[row*8+(flip?7-j:j)]];
   vst1q_u16(out,d35_source_color(tile+row*8,colors,4,idx,d35_palette(colors,4),flip));
   assert(!memcmp(out,expected,sizeof(out)));cases++;
  }
 }
 /* Two mutable owners, cross-epoch reuse and wrap are explicit boundaries. */
 d35_palette_epoch=0xffffffff;d35_source_clear();d35_palette_epoch=1;
 tile[0]=5;colors[5]=0x1234;d35_source_tile_changed(tile);
 vst1q_u16(out,d35_source_color(tile,colors,4,vld1_u8(tile),d35_palette(colors,4),0));assert(out[0]==0x1234);
 assert(counts[22]>0&&counts[23]>0&&counts[25]>0);
 printf("PASS: %u source-row dependency cases, tile writes/palette changes/reverse/warm hits/collisions/epoch wrap\\n",cases);return 0;}
'''
 src=OUT/'source-rows-check.c';src.write_text(code,newline='\n')
 libs=['-Lbuild/sysroot/lib','-Wl,--no-as-needed']+['-l:'+n for n in ('libm-2.30.so','libc-2.30.so','libgcc_s.so.1')]
 exe=OUT/'source-rows-check'
 subprocess.run(['arm-linux-gnueabihf-gcc','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-O3','-std=gnu99','-Wall','-Wextra','-Werror','-no-pie','-nostdlib','-Ibuild','/usr/arm-linux-gnueabihf/lib/crt1.o',str(src),*libs,'-o',str(exe)],check=True)
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 with (OUT/'source-rows-check.log').open('x') as f:subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(exe)],env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=90)
 print((OUT/'source-rows-check.log').read_text(),end='',flush=True)
 review=OUT/'row-review';review.mkdir()
 for label in ('rows-v2','rows-v2-counted'):
  (review/label).mkdir();shutil.copy2(OUT/label/'snes9x2005_plus_libretro.so',review/label/'snes9x2005_plus_libretro.so')
 for name in ('compare','frozen.json'):shutil.copy2(OUT/name,review/name)
 (review/'seams.json').write_text(json.dumps({'passed':True,'cache_dependency_oracle':(OUT/'source-rows-check.log').read_text().strip()})+'\n')
 m=runpy.run_path(str(ROOT/'build/qualify-ppu-refinements.py'));g=m['main'].__globals__;g['OUT']=review;g['LABELS']=('rows-v2','rows-v2-counted')
 g['FIELDS']+=('reserved19','reserved20','reserved21','source_hits','source_misses','source_queries','source_invalidation_visits')
 m['main']()
if __name__=='__main__':main()
