/* Independent planar/map walker versus the owned exact flat-band producer.
 * No ROM, timing, device, emulator cache or candidate decoder used as oracle. */
#include <arm_neon.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define V_FLIP 0x8000
static uint16_t read16(const void *p){uint16_t v;memcpy(&v,p,2);return v;}
#define READ_2BYTES(p) read16(p)
static struct {unsigned TileAddress,TileShift,NameSelect,PaletteMask,PaletteShift,StartPalette;} BG;
static struct {uint8_t *VRAM;} Memory;
static struct {uint16_t ScreenColors[256];} IPPU;
static struct {uint8_t *S,*DB;unsigned PPL,Z1,Z2;} GFX;
#include "pearl-flat.h"
#define SPAN (512*20+32)
static uint8_t vram[65536],depth[SPAN],want_depth[SPAN];
static uint16_t screen[SPAN],want[SPAN],map[64];
static unsigned scalar(unsigned y,unsigned lines,unsigned h,unsigned v,unsigned low,unsigned high)
{
 for(unsigned row=0;row<lines;row++)for(unsigned x=0;x<256;x++){
  unsigned sx=(h+x)&511,t=map[sx/8],tx=sx&7,ty=(y+row+v)&7;
  if(t&0x4000)tx=7-tx;if(t&0x8000)ty=7-ty;
  unsigned a=(BG.TileAddress+(t&1023)*16+((t&511)>=256?BG.NameSelect:0)+ty*2)&65535;
  unsigned bit=7-tx,index=((vram[a]>>bit)&1)|(((vram[(a+1)&65535]>>bit)&1)<<1);
  if(index){unsigned off=16+(y+row)*GFX.PPL+x;
   want[off]=IPPU.ScreenColors[BG.StartPalette+((t>>10)&7)*4+index];
   want_depth[off]=(t&0x2000)?high:low;
  }
 }
 return 1;
}
static void reset(unsigned pitch)
{
 GFX.S=(uint8_t *)(screen+16);GFX.DB=depth+16;GFX.PPL=pitch;
 for(unsigned i=0;i<SPAN;i++){want[i]=screen[i]=(i*1777+91)&65535;want_depth[i]=depth[i]=i%2;}
}
int main(void)
{
 unsigned hvalues[]={0,1,7,248,255,504,511},lengths[]={1,3,8},tests=0,rejects=0;
 Memory.VRAM=vram;BG.TileShift=4;BG.PaletteMask=7;BG.PaletteShift=2;BG.StartPalette=32;
 for(unsigned i=0;i<256;i++)IPPU.ScreenColors[i]=(i*811+9)&65535;
 for(unsigned pitch=256;pitch<=512;pitch+=256)for(unsigned address=0;address<3;address++)
 for(unsigned idx=0;idx<4;idx++)for(unsigned h=0;h<7;h++)for(unsigned v=0;v<8;v++)
 for(unsigned flip=0;flip<4;flip++)for(unsigned pri=0;pri<2;pri++)
 for(unsigned pal=0;pal<8;pal++)for(unsigned ln=0;ln<3;ln++){
  BG.TileAddress=address==0?0:address==1?65528:12345;BG.NameSelect=address==2?4096:0;
  unsigned tile=(address==2?300:0)|(flip<<14)|(pri<<13)|(pal<<10);
  for(unsigned i=0;i<64;i++)map[i]=tile;
  unsigned a=(BG.TileAddress+(tile&1023)*16+((tile&511)>=256?BG.NameSelect:0))&65535;
  for(unsigned row=0;row<8;row++){
   unsigned index=(idx+row)%4;vram[(a+row*2)&65535]=(index&1)?255:0;
   vram[(a+row*2+1)&65535]=(index&2)?255:0;
  }
  reset(pitch);scalar(2,lengths[ln],hvalues[h],v,2,17);
  assert(d35_flat_band(2,lengths[ln],hvalues[h],v,map,map+32,2,17));
  assert(!memcmp(want,screen,sizeof(screen))&&!memcmp(want_depth,depth,sizeof(depth)));tests++;
 }
 /* All failure paths must preserve every pixel/depth, including an early valid
  * row followed by a nonuniform row: validation must finish before any writes. */
 BG.TileAddress=0;BG.NameSelect=0;
 for(unsigned kind=0;kind<4;kind++){
  reset(256);memset(vram,255,16);memset(map,0,sizeof(map));
  if(kind==0)map[10]=1;if(kind==1)vram[4]=0x55;
  assert(!d35_flat_band(0,kind==2?0:kind==3?9:8,0,0,map,map+32,2,17));
  assert(!memcmp(want,screen,sizeof(screen))&&!memcmp(want_depth,depth,sizeof(depth)));rejects++;
 }
 printf("PASS %u independent flat-band cases, %u transactional rejection cases; no timing claims\n",tests,rejects);
}
