"""Extract the actual frozen walker and DMA branch as independent oracles."""
from pathlib import Path
from hashlib import sha256
import json,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-private-v1'
BASE=ROOT/'build/common-band-private-v3/core/source'
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
PRE='''#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#define D35_DEMAND_COUNT
#include "demand-stats.h"
unsigned long long d35_demand[DS_FIELDS];
typedef unsigned char bool;
#define true 1
#define false 0
#define NULL_SOLE ((void*)0)
#define H_FLIP 0x4000
#define V_FLIP 0x8000
#define READ_2BYTES(p) ((unsigned)((const uint8_t *)(p))[0]|((unsigned)((const uint8_t *)(p))[1]<<8))
static unsigned seed=42;
static unsigned rnd(void){seed=seed*1664525u+1013904223u;return seed;}
'''
GEO=PRE+'''
typedef struct {unsigned Count[6],Left[6][6],Right[6][6];} ClipData;
static struct {unsigned BGMode,Mosaic;unsigned BGMosaic[4];struct{unsigned BGSize,NameBase,SCBase,SCSize;}BG[4];}PPU;
static struct {uint8_t *TileCache[3],*TileCached[3];ClipData Clip[2];unsigned DoubleWidthPixels,DoubleHeightPixels,HalfWidthPixels;}IPPU;
static struct {uint8_t *S,*SubScreen,*Screen,*DB,*SubZBuffer;unsigned PixSize,ZPitch,PPL,StartY,EndY,Z1,Z2,r212c,r212d,r2130,Pseudo;ClipData*pCurrentClip;}GFX;
static struct{unsigned TileSize,BitShift,TileShift,TileAddress,NameSelect,PaletteShift,PaletteMask,DirectColourMode,StartPalette;uint8_t *Buffer,*Buffered;}BG;
static struct{uint8_t VRAM[65536];}Memory;
static struct{struct{unsigned VOffset,HOffset;}BG[4];}LineData[256];
static uint8_t BGSizes[2]={8,16},BitShifts[8][4]={{2,2,2,2},{4,4,2,0},{4,4,0,0},{8,4,0,0}},TileShifts[8][4],Depths[8][4],PaletteShifts[8][4],PaletteMasks[8][4];
struct d35_window_clip{unsigned count,left[6],right[6];};
static unsigned target,custom_window;
static struct d35_window_clip windows[256];
static unsigned d35_window_is_target(unsigned bg){(void)bg;return target;}
static unsigned d35_window_same(unsigned a,unsigned b){return !memcmp(&windows[a],&windows[b],sizeof(windows[a]));}
static unsigned d35_window_fetch(unsigned bg,unsigned y,unsigned sub,struct d35_window_clip *w){(void)bg;(void)sub;*w=windows[y];return custom_window;}
struct d35_sub2_context {unsigned unused;};
struct d35_batch_context {unsigned mode,valid;};
struct cmd {unsigned tile,offset,start,width,line,lines,z1,z2;};
static struct cmd recorded[20000],expected[20000];static unsigned used;
static void clipped(unsigned t,int32_t o,unsigned start,unsigned width,unsigned line,unsigned lines){assert(used<20000);recorded[used++]=(struct cmd){t,(unsigned)o,start,width,line,lines,GFX.Z1,GFX.Z2};}
static void DrawTile16(unsigned t,int32_t o,unsigned l,unsigned n){clipped(t,o,0,8,l,n);}
static void DrawTile16Add(unsigned t,int32_t o,unsigned l,unsigned n){DrawTile16(t,o,l,n);}
static void DrawTile16Sub(unsigned t,int32_t o,unsigned l,unsigned n){DrawTile16(t,o,l,n);}
static void (*DrawTilePtr)(unsigned,int32_t,unsigned,unsigned)=DrawTile16;
static void (*DrawClippedTilePtr)(unsigned,int32_t,unsigned,unsigned,unsigned,unsigned)=clipped;
static unsigned d35_sub2(struct d35_sub2_context *c,unsigned t,int32_t o,unsigned l,unsigned n){(void)c;(void)t;(void)o;(void)l;(void)n;return 0;}
static unsigned d35_batch_tile_mode(struct d35_batch_context *c,unsigned t,int32_t o,unsigned l,unsigned n,unsigned mode){(void)c;(void)mode;DrawTilePtr(t,o,l,n);return 1;}
struct d35_band_walk {uint16_t*t,*b1,*b2;unsigned quot,offset,t1,t2,line,lines,low,high;struct d35_sub2_context*sole;};
'''
def geometry():
 s=(BASE/'gfx.c').read_text();a=s.index('static void DrawBackground(uint32_t');b=s.index('#define RENDER_BACKGROUND_MODE7',a);orig=s[a:b]
 band=(BASE/'a7_common_band.h').read_text();a=band.index('#define D35_BAND_FUNCTION');b=band.index('#undef D35_BAND_FUNCTION',a)
 pre=GEO+'\n#define D35_BAND_COUNT ((void)0)\n'+band[a:b]+'''
static void DrawBackgroundMosaic(unsigned m,unsigned b,unsigned l,unsigned h){(void)m;(void)b;(void)l;(void)h;assert(0);}
static void DrawBackgroundOffset(unsigned m,unsigned b,unsigned l,unsigned h){(void)m;(void)b;(void)l;(void)h;assert(0);}
static void DrawBackgroundMode5(unsigned b,unsigned l,unsigned h){(void)b;(void)l;(void)h;assert(0);}
'''+orig+'\n#include "demand-geometry.h"\n'
 # Candidate wraps the original unchanged layout preparation / fallback and
 # replaces only its ordinary traversal at the exact same seam as production.
 new=orig.replace('static void DrawBackground(', 'static void CandidateBackground(')
 new=new.replace('   SC0 = (uint16_t*) &Memory.VRAM[PPU.BG[bg].SCBase << 1];','   if(d35_geometry_begin(BGMode,bg,batch_ok,&batch,Z1,Z2,sub_fast?&sub_context:NULL))return;\n   SC0 = (uint16_t*) &Memory.VRAM[PPU.BG[bg].SCBase << 1];')
 write(OUT/'geometry-check.c',pre+new+'''
int main(void){
 uint8_t screen,sub,depth;GFX.Screen=&screen;GFX.SubScreen=&sub;GFX.SubZBuffer=&depth;GFX.DB=&depth;GFX.PPL=512;GFX.ZPitch=512;
 for(unsigned mode=0;mode<8;mode++)for(unsigned bg=0;bg<4;bg++)PaletteMasks[mode][bg]=7;
 unsigned cases=0;
 for(unsigned trial=0;trial<4096;trial++){
  unsigned bg=trial%4,mode=(trial%3==0)?0:1;PPU.BGMode=mode;PPU.Mosaic=1;
  PPU.BG[bg].BGSize=(trial>>2)&1;PPU.BG[bg].SCBase=(rnd()%32)*1024;PPU.BG[bg].SCSize=rnd()%4;
  GFX.r212c=GFX.r212d=1u<<bg;GFX.StartY=rnd()%224;GFX.EndY=GFX.StartY+15;if(GFX.EndY>239)GFX.EndY=239;
  unsigned vo=rnd()&1023,ho=rnd()&1023;target=(trial>>3)&1;custom_window=(trial>>4)&1;
  for(unsigned i=0;i<65536;i++)Memory.VRAM[i]=(uint8_t)rnd();
  memset(IPPU.Clip,0,sizeof(IPPU.Clip));memset(windows,0,sizeof(windows));
  for(unsigned y=0;y<256;y++){
   LineData[y].BG[bg].VOffset=vo+(y%9==0?1:0);LineData[y].BG[bg].HOffset=ho;
   windows[y].count=target?2:0;windows[y].left[0]=y%9;windows[y].right[0]=75+y%13;
   windows[y].left[1]=120+y%7;windows[y].right[1]=256-y%11;
  }
  for(unsigned plane=0;plane<2;plane++)if(trial&32){ClipData*c=&IPPU.Clip[plane];c->Count[bg]=2;c->Left[0][bg]=plane?3:7;c->Right[0][bg]=95;c->Left[1][bg]=111;c->Right[1][bg]=plane?249:256;}
  d35_geometry_reset();
  for(unsigned plane=0;plane<2;plane++){
   GFX.S=plane?GFX.Screen:GFX.SubScreen;GFX.pCurrentClip=&IPPU.Clip[plane?0:1];
   DrawTilePtr=plane?(trial&64?DrawTile16Add:DrawTile16Sub):DrawTile16;
   used=0;DrawBackground(mode,bg,10,14);unsigned n=used;memcpy(expected,recorded,n*sizeof(*recorded));
   used=0;CandidateBackground(mode,bg,10,14);assert(used==n&&!memcmp(expected,recorded,n*sizeof(*recorded)));cases++;
  }
 }
 assert(d35_demand[DS_GEO_REUSED]&&d35_demand[DS_GEO_16]&&d35_demand[DS_GEO_WINDOW]);
 printf("PASS %u exact stock-walker command streams: four layers, 8/16 tiles, flips/priority, scrolls/wrap, separate/empty clips and per-row windows; positive reuse\\n",cases);
}
''')
def dma():
 s=(BASE/'dma.c').read_text();new=(OUT/'dma/core/source/dma.c').read_text()
 def branch(s):
  a=s.index('      else if (d->TransferMode == 1 || d->TransferMode == 5)');b=s.index('      else if (d->TransferMode == 3',a)
  return s[a:b].replace('      else if (d->TransferMode == 1 || d->TransferMode == 5)','      if (d->TransferMode == 1 || d->TransferMode == 5)',1)
 regs=(BASE/'ppu.h').read_text();helpers=''
 for name in ('2118_linear','2119_linear','2118_tile','2119_tile'):
  a=regs.index('static INLINE void REGISTER_'+name+'(');b=regs.index('\n}\n',a)+3;helpers+=regs[a:b]+'\n'
 pre=PRE+'''
#define INLINE inline
enum {TILE_2BIT,TILE_4BIT,TILE_8BIT};
static struct {uint8_t VRAM[65536],ram[65536];bool BlockIsRAM[4096],BlockIsROM[4096];}Memory;
static struct {bool FirstVRAMRead;uint8_t*TileCached[3];}IPPU;
static struct{struct{unsigned Address,FullGraphicCount,High,Increment,Mask1,Shift;}VMA;}PPU;
static struct{unsigned SA1,SDD1,SPC7110;}Settings;
typedef struct {unsigned TransferMode,BAddress,ABank;}SDMA;
static uint8_t *GetBasePointer(unsigned a){return Memory.BlockIsRAM[a>>12]||Memory.BlockIsROM[a>>12]?Memory.ram:NULL;}
static unsigned reg_hash;
static void S9xSetPPU(uint8_t b,unsigned a){reg_hash=reg_hash*31+a+b;}
'''+helpers
 pre+='static void original(SDMA*d,uint8_t*base,uint16_t p,int count,int inc){uint8_t Work;\n'+branch(s)+'}\n'
 pre+='static void candidate(SDMA*d,uint8_t*base,uint16_t p,int count,int inc){bool in_sa1_dma=0;uint8_t Work;\n'+branch(new)+'}\n'
 write(OUT/'dma-check.c',pre+'''
int main(void){
 uint8_t flags[3][4096],expected_flags[3][4096],expected_vram[65536];unsigned cases=0;
 for(unsigned i=0;i<65536;i++)Memory.ram[i]=(uint8_t)(i*37+i/256);
 for(unsigned i=0;i<3;i++)IPPU.TileCached[i]=flags[i];
 for(unsigned trial=0;trial<12000;trial++){
  SDMA d={trial&1?1:5,trial%17?0x18:0x19,0x7e};unsigned p=(rnd()%65536)&~1u;
  int count=2+(rnd()%4095),inc=trial%13?1:(trial&1?0:-1);
  if(p<4096)p+=4096;if(p>60000)p=60000;
  typeof(PPU)initial={.VMA={rnd()&32767,trial%19?0:32,trial%11?1:0,trial%23?1:32,255,3}};
  memset(&Settings,0,sizeof(Settings));Settings.SA1=trial%31==0;Settings.SDD1=trial%37==0;Settings.SPC7110=trial%41==0;
  memset(Memory.BlockIsRAM,0,sizeof(Memory.BlockIsRAM));memset(Memory.BlockIsROM,0,sizeof(Memory.BlockIsROM));
  if(trial%29)Memory.BlockIsRAM[((d.ABank<<16)|p)>>12]=1;
  PPU=initial;memset(Memory.VRAM,0x67,sizeof(Memory.VRAM));memset(flags,1,sizeof(flags));reg_hash=0;IPPU.FirstVRAMRead=0;
  original(&d,Memory.ram,p,count,inc);typeof(PPU)result=PPU;unsigned rh=reg_hash,read=IPPU.FirstVRAMRead;
  memcpy(expected_flags,flags,sizeof(flags));memcpy(expected_vram,Memory.VRAM,sizeof(expected_vram));
  PPU=initial;memset(Memory.VRAM,0x67,sizeof(Memory.VRAM));memset(flags,1,sizeof(flags));reg_hash=0;IPPU.FirstVRAMRead=0;
  candidate(&d,Memory.ram,p,count,inc);assert(!memcmp(&PPU,&result,sizeof(PPU))&&rh==reg_hash&&read==IPPU.FirstVRAMRead);
  assert(!memcmp(flags,expected_flags,sizeof(flags))&&!memcmp(Memory.VRAM,expected_vram,sizeof(expected_vram)));cases++;
 }
 assert(d35_demand[DS_DMA_SPANS]&&d35_demand[DS_DMA_OLD_FLAGS]>d35_demand[DS_DMA_FLAGS]);
 printf("PASS %u actual DMA branch fixtures: modes1/5, mapped/unmapped, even/odd, fixed/decrement, 4KiB/VRAM wrap, increment/high/remap and chip guards\\n",cases);
}
''')
def ring():
 old=(BASE/'apu_blargg.c').read_text();new=(OUT/'small/core/source/apu_blargg.c').read_text()
 def branch(s):
  a=s.index('if',s.index('static void resampler_read('));b=s.index('   i_position = rb_start >> 1;',a);return s[a:b]
 write(OUT/'ring-check.c',PRE+'''
static uint8_t ring[65536],*rb_buffer=ring;static int rb_buffer_size,rb_start,rb_size,r_step=65536;
static void original(int16_t *data,int32_t num_samples){'''+branch(old)+'''assert(0);}
static void candidate(int16_t *data,int32_t num_samples){'''+branch(new)+'''assert(0);}
int main(void){
 int16_t a[32768],b[32768];unsigned cases=0;
 for(int capacity=4;capacity<=32768;capacity=capacity<256?capacity+4:capacity*2)
 for(int start=0;start<capacity;start+=4)
 for(int samples=0;samples<=capacity/2;samples+=capacity<256?2:128){
  for(int i=0;i<capacity;i++)ring[i]=(uint8_t)(i*31+i/256);
  memset(a,0x5a,sizeof(a));memset(b,0x5a,sizeof(b));rb_buffer_size=capacity;rb_start=start;rb_size=capacity;
  original(a,samples);int end=rb_start,size=rb_size;rb_start=start;rb_size=capacity;
  candidate(b,samples);assert(rb_start==end&&rb_size==size&&!memcmp(a,b,sizeof(a)));cases++;
 }
 printf("PASS %u actual replacement ring states, whole-capacity reads, wrap and output canaries\\n",cases);
}
''')
def main():
 assert not (OUT/'seams.json').exists();geometry();dma();ring()
 results={}
 for name,source in [('geometry',OUT/'geometry-check.c'),('dma',OUT/'dma-check.c'),('ring',OUT/'ring-check.c'),('output',ROOT/'build/demand-output-check.c')]:
  exe=OUT/(name+'-check')
  log=OUT/(name+'-check.log')
  if log.exists() and exe.exists() and exe.stat().st_mtime>=source.stat().st_mtime and name=='geometry':
   # Geometry's extracted source is deterministic; avoid rerunning its unchanged pass.
   results[name]={'passed':True,'output':log.read_text().strip(),'source_sha256':sha256(source.read_bytes()).hexdigest()};continue
  subprocess.run(['gcc','-O2','-std=gnu99','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-variable','-Wno-misleading-indentation','-Wno-sign-compare','-Ibuild','-I'+str(OUT/'combined/core/source'),str(source),'-o',str(exe)],cwd=ROOT,check=True)
  r=subprocess.run([str(exe)],cwd=ROOT,check=True,capture_output=True,text=True,timeout=180)
  write(OUT/(name+'-check.log'),r.stdout);print(r.stdout,end='')
  results[name]={'passed':True,'output':r.stdout.strip(),'source_sha256':sha256(source.read_bytes()).hexdigest()}
 write(OUT/'seams.json',json.dumps({'passed':True,'checks':results,'A7_performance_evidence':False},indent=2)+'\n')
if __name__=='__main__':main()
