"""Original clipped C oracle, NEON arithmetic oracle and stock window starts."""
from pathlib import Path
import json,os,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ppu-refinements-private-v4'
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def main():
 assert not (OUT/'seams.json').exists()
 # Compile the unchanged scalar oracle and new actual clipped entry points.
 source=(ROOT/'build/fused-toolbox-private-v2/tile-check.c').read_text()
 source=source.replace('"fused-toolbox-private-v2/core/source/','"ppu-refinements-private-v4/combined-counted/source/')
 source=source.replace('uint16_t DirectColourMaps[8][256];','uint16_t DirectColourMaps[8][256];\nunsigned long long d35_ppu[32];')
 source=source.replace('clipped_fn draw[]={batch_0,batch_1,batch_2,batch_3,batch_4,batch_5,batch_6};','clipped_fn draw[]={DrawClippedTile16,DrawClippedTile16Add,DrawClippedTile16Add1_2,DrawClippedTile16Sub,DrawClippedTile16Sub1_2,DrawClippedTile16FixedAdd1_2,DrawClippedTile16FixedSub1_2};')
 source=source.replace('    fprintf(stderr,"PASS:', '    for(unsigned p=0;p<32;p++)fprintf(stderr,"PPU[%u]=%llu\\n",p,d35_ppu[p]);\n    fprintf(stderr,"PASS:')
 write(OUT/'tile-check.c',source)
 windows='''#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef unsigned char bool;
#define false 0
static unsigned long long stats[32];
#define PP_ADD(n,v) (stats[n]+=(v))
#include "ppu-window-start.h"
int main(void){unsigned cases=0,seed=41;struct{uint16_t Pos;bool Value;}Windows[7];
 for(unsigned t=0;t<4000;t++){
  unsigned position=0;
  for(unsigned j=0;j<7;j++){seed=seed*1664525u+1013904223u;position+=(seed>>24)%61;Windows[j].Pos=position;Windows[j].Value=(seed>>8)&1;}
  if(t%4==0){Windows[0].Pos=0;Windows[0].Value=1;Windows[1].Pos=256;}
  if(t%4==1)Windows[0].Pos=1000;
  struct d35_obj_lookup q;D35_OBJ_PREPARE(q,Windows);
  for(int X=-7;X<256;X++){
   int WinIdx=0,NextPos=-1000;bool WinStat=1;
'''
 gfx=(ROOT/'build/demand-visible-private-v3/core/source/gfx.c').read_text()
 start=gfx.index('               for (; WinIdx < 7 && Windows[WinIdx].Pos <= X; WinIdx++);')
 end=gfx.index('               NextPos = (WinIdx < 7) ? Windows[WinIdx].Pos : 1000;',start)+len('               NextPos = (WinIdx < 7) ? Windows[WinIdx].Pos : 1000;')
 windows+=gfx[start:end]+'''
   int ni=0,nn=-1000;bool nv=1;D35_OBJ_START(q,Windows,X,ni,nv,nn);
   assert(ni==WinIdx&&nv==WinStat&&nn==NextPos);cases++;
  }
 }
 printf("PASS: %u actual-stock window starts, simple/empty/complex/degenerated boundaries\\n",cases);
 return 0;}
'''
 write(OUT/'window-check.c',windows)
 subprocess.run(['gcc','-O2','-std=gnu99','-Wall','-Wextra','-Werror','-Ibuild',str(OUT/'window-check.c'),'-o',str(OUT/'window-check')],check=True)
 r=subprocess.run([str(OUT/'window-check')],check=True,capture_output=True,text=True)
 write(OUT/'window-check.log',r.stdout);print(r.stdout,end='')
 math='''#include <stdint.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include "ppu-refinements-private-v4/combined-counted/source/a7_tile.h"
#include "ppu-refinements-private-v4/combined-counted/source/a7_ppu_stats.h"
unsigned long long d35_ppu[32];
#include "ppu-refinements-private-v4/combined-counted/source/a7_ppu_math.h"
int main(void){unsigned seed=42,cases=0;uint16_t colors[16],sub[8],a[10],b[10];uint8_t depth[10],expected[10],idx[8],sd[8],mask[8];
 for(unsigned t=0;t<4096;t++){
  for(unsigned j=0;j<16;j++){seed=seed*1664525u+1013904223u;colors[j]=seed;}
  for(unsigned j=0;j<8;j++){seed=seed*1664525u+1013904223u;sub[j]=seed;idx[j]=(seed>>16)&15;sd[j]=(seed>>24)%4;}
  uint16_t fixed=(seed>>7);
  for(unsigned m=1;m<7;m++)for(unsigned flip=0;flip<2;flip++)for(unsigned bits=1;bits<256;bits++){
   if(__builtin_popcount(bits)>2)continue;
   for(unsigned j=0;j<10;j++){a[j]=b[j]=0x1234;depth[j]=expected[j]=77;}
   uint16_t input[8];for(unsigned j=0;j<8;j++){mask[j]=bits&(1u<<j)?255:0;input[j]=colors[idx[flip?7-j:j]];}
   uint16_t vector[8];vst1q_u16(vector,d35_blend(vld1q_u16(input),vld1_u8(sd),sub,fixed,m,vld1_u8(mask)));
   for(unsigned j=0;j<8;j++)if(mask[j]){b[j+1]=vector[j];expected[j+1]=29;}
   assert(d35_sparse_math(a+1,depth+1,idx,colors,vget_lane_u64(vreinterpret_u64_u8(vld1_u8(mask)),0),flip,29,sd,sub,fixed,m));
   assert(!memcmp(a,b,sizeof(a))&&!memcmp(depth,expected,sizeof(depth)));cases++;
  }
 }
 printf("PASS: %u sparse math cases vs actual NEON, all6 math modes/fixed/sub/mixed/flips/canaries\\n",cases);return 0;}
'''
 write(OUT/'math-check.c',math)
 libs=['-Lbuild/sysroot/lib','-Wl,--no-as-needed']+['-l:'+n for n in ('libz.so.1','libm-2.30.so','libc-2.30.so','libgcc_s.so.1')]
 flags=['-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-fno-stack-protector','-D_TIME_BITS=32','-D_FILE_OFFSET_BITS=32','-O3','-std=gnu99','-Wall','-Wextra','-Werror','-Wno-sign-compare','-Wno-unused-function','-Wno-misleading-indentation','-Wno-implicit-fallthrough','-no-pie','-nostdlib','-Ibuild','-Ibuild/snes9x2005/libretro-common/include','/usr/arm-linux-gnueabihf/lib/crt1.o']
 env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')}
 for name,extra in [('tile-reference',['-DUSE_BLARGG_APU']),('tile-candidate',['-DUSE_BLARGG_APU','-DD35_CLIPPING_CANDIDATE','-DD35_TEST_POLICY=0']),('math',[])]:
  src=OUT/('math-check.c' if name=='math' else 'tile-check.c');exe=OUT/(name+'-check')
  subprocess.run(['arm-linux-gnueabihf-gcc',*flags,*extra,str(src),*libs,'-o',str(exe)],check=True)
  with (OUT/(name+'.crc')).open('x') as f,(OUT/(name+'.log')).open('x') as e:subprocess.run(['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),str(exe)],env=env,stdout=f,stderr=e,check=True,timeout=180)
 assert (OUT/'tile-reference.crc').read_bytes()==(OUT/'tile-candidate.crc').read_bytes()
 txt=(OUT/'tile-candidate.log').read_text();assert any('PPU[%d]='%j in txt and int(txt.split('PPU[%d]='%j)[1].splitlines()[0])>0 for j in range(1,8))
 result={'passed':True,'stock_window':r.stdout.strip(),'clipped_original_C_exact':True,'math':(OUT/'math.crc').read_text().strip(),'physical_timing':False}
 write(OUT/'seams.json',json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
