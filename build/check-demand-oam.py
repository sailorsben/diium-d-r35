"""Original sprite scheduler is the independent oracle for reduced dirtiness."""
from pathlib import Path
import subprocess,json
from hashlib import sha256
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-private-v1'
BASE=ROOT/'build/common-band-private-v3/core/source'
def function(s,anchor):
 a=s.index(anchor);b=s.index('\n}\n',a)+3;return s[a:b]
def main():
 assert not (OUT/'oam-proof.json').exists()
 regs=(BASE/'ppu.h').read_text();new=(OUT/'small/core/source/ppu.h').read_text()
 setup=function((BASE/'gfx.c').read_text(),'void S9xSetupOBJ(void)')
 pre='''#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef unsigned char bool;
#define D35_DEMAND_COUNT
#include "demand-stats.h"
unsigned long long d35_demand[DS_FIELDS];
#define INLINE inline
#define true 1
#define false 0
#define SNES_HEIGHT_EXTENDED 239
typedef struct {int32_t HPos,VPos;unsigned Name,Palette,Priority,HFlip,VFlip,Size;}SOBJ;
static struct {unsigned OAMAddr,OAMFlip,OAMWriteRegister,OAMPriorityRotation,FirstSprite,OBJSizeSelect;
 unsigned OBJNameBase,OBJNameSelect;uint8_t OAMData[544];SOBJ OBJ[128];}PPU;
static struct {unsigned OBJChanged;}IPPU;
static struct {uint8_t FillRAM[65536];}Memory;
static struct {uint8_t OBJWidths[128],OBJVisibleTiles[128];
 struct {uint8_t RTOFlags;int16_t Tiles;struct {int8_t Sprite;uint8_t Line;}OBJ[32];}OBJLines[239];}GFX;
static unsigned reduce_sprite_flicker,flushes;
static int16_t SignExtend[2]={0,-256};
static void FLUSH_REDRAW(void){flushes++;}
static unsigned seed=8;static unsigned rnd(void){seed=seed*1664525u+1013904223u;return seed;}
'''
 s=pre+function(regs,'static INLINE void REGISTER_2104(').replace('REGISTER_2104','original2104')+'\n'
 s+=function(new,'static INLINE void REGISTER_2104(').replace('REGISTER_2104','candidate2104')+'\n'+setup
 for name,path in [('original2101',BASE/'ppu.c'),('candidate2101',OUT/'small/core/source/ppu.c')]:
  t=path.read_text();a=t.index('      case 0x2101:');b=t.index('      case 0x2102:',a)
  part=t[a:b];part=part[part.index('         if'):];part=part[:part.rindex('         break;')]
  s+='\nstatic void '+name+'(uint8_t Byte){'+part+'Memory.FillRAM[0x2101]=Byte;}\n'
 s+='''
int main(void){
 unsigned cases=0;
 for(unsigned trial=0;trial<2048;trial++){
  memset(&PPU,0,sizeof(PPU));memset(&GFX,0,sizeof(GFX));memset(&Memory,0,sizeof(Memory));
  for(unsigned i=0;i<544;i++)PPU.OAMData[i]=(uint8_t)(rnd()>>16);
  for(unsigned i=0;i<128;i++){
   unsigned high=PPU.OAMData[4*i+3],size=PPU.OAMData[512+i/4]>>((i%4)*2);
   PPU.OBJ[i]=(SOBJ){PPU.OAMData[4*i]|SignExtend[size&1],PPU.OAMData[4*i+1],
    PPU.OAMData[4*i+2]|((high&1)<<8),(high>>1)&7,(high>>4)&3,(high>>6)&1,(high>>7)&1,size&2};
  }
  PPU.OBJSizeSelect=trial%8;PPU.FirstSprite=trial%128;PPU.OAMPriorityRotation=trial%7==0;
  PPU.OAMFlip=trial%3?1:2;PPU.OAMAddr=(trial*7)&511;PPU.OAMWriteRegister=rnd()&65535;
  reduce_sprite_flicker=trial&1;S9xSetupOBJ();typeof(PPU)initial=PPU;typeof(GFX)before=GFX;
  uint8_t byte=(uint8_t)(rnd()>>16);unsigned action=trial%5;
  IPPU.OBJChanged=0;flushes=0;if(action)original2104(byte);else original2101(byte);
  if(IPPU.OBJChanged)S9xSetupOBJ();typeof(PPU)expected=PPU;typeof(GFX)after=GFX;
  unsigned expected_flushes=flushes;uint8_t reg=Memory.FillRAM[action?0x2104:0x2101];
  PPU=initial;GFX=before;IPPU.OBJChanged=0;flushes=0;memset(&Memory,0,sizeof(Memory));
  if(action)candidate2104(byte);else candidate2101(byte);if(IPPU.OBJChanged)S9xSetupOBJ();
  assert(flushes==expected_flushes&&reg==Memory.FillRAM[action?0x2104:0x2101]);
  assert(!memcmp(&PPU,&expected,sizeof(PPU))&&!memcmp(&GFX,&after,sizeof(GFX)));cases++;
 }
 assert(d35_demand[DS_OBJ_AVOIDED]);
 printf("PASS %u original OAM/OBJ scheduler fixtures: appearance, position, VFlip, sizes, high table, latch, first-sprite and rotation; identical flushes and complete schedule\\n",cases);
}
'''
 p=OUT/'oam-check.c';p.write_text(s,newline='\n')
 subprocess.run(['gcc','-O2','-std=gnu99','-Wall','-Wextra','-Werror','-Wno-sign-compare','-Wno-misleading-indentation','-Ibuild',str(p),'-o',str(OUT/'oam-check')],cwd=ROOT,check=True)
 r=subprocess.run([str(OUT/'oam-check')],check=True,capture_output=True,text=True,timeout=120)
 (OUT/'oam-check.log').write_text(r.stdout)
 (OUT/'oam-proof.json').write_text(json.dumps({'passed':True,'source_sha256':sha256(p.read_bytes()).hexdigest(),'output':r.stdout.strip(),'A7_performance_evidence':False},indent=2)+'\n');print(r.stdout,end='')
if __name__=='__main__':main()
