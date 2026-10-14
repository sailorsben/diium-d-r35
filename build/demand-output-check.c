/* Independent row-pattern oracle for the actual output implementation. */
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define D35_DEMAND_COUNT
#include "demand-stats.h"
unsigned long long d35_demand[DS_FIELDS];
static struct {
 uint8_t *Screen_buffer,*SubScreen_buffer,*ZBuffer_buffer,*SubZBuffer_buffer;
 uint8_t *Screen,*SubScreen,*ZBuffer,*SubZBuffer,*S,*DB;
 unsigned RealPitch,Pitch,Pitch2,PPL,PPLx2,ZPitch;int32_t Delta;ptrdiff_t DepthDelta;
} GFX;
static struct {unsigned ScreenHeight,BGMode;} PPU;
static struct {unsigned Interlace,DoubleWidthPixels,DoubleHeightPixels,HalfWidthPixels,PreviousLine;} IPPU;
static struct {uint8_t FillRAM[65536];} Memory;
#define D35_OUTPUT_IMPLEMENTATION
#include "demand-output.h"
static uint8_t *owned;
static void patterns(void) {
 for(unsigned y=0;y<240;y++)for(unsigned x=0;x<256;x++) {
  unsigned p=y*512+x*2;d35_output_sub[p]=(uint8_t)(y+x);d35_output_sub[p+1]=(uint8_t)(y^x);
  d35_z[y*256+x]=(uint8_t)(y*17+x);d35_sz[y*256+x]=(uint8_t)(y+x*19);
  owned[p]=(uint8_t)(y*13+x);owned[p+1]=(uint8_t)(y+x*7);
 }
}
static void expect_aux(void) {
 for(unsigned y=0;y<240;y++) {
  assert(!memcmp(GFX.SubScreen+y*1024,d35_output_sub+y*512,512));
  assert(!memcmp(GFX.ZBuffer+y*512,d35_z+y*256,256));
  assert(!memcmp(GFX.SubZBuffer+y*512,d35_sz+y*256,256));
 }
}
int main(void) {
 GFX.Screen_buffer=calloc(1,1024*512+64);GFX.SubScreen_buffer=calloc(1,1024*512+64);
 GFX.ZBuffer_buffer=calloc(1,512*512+64);GFX.SubZBuffer_buffer=calloc(1,512*512+64);
 uint8_t *allocation;assert(!posix_memalign((void **)&allocation,64,512*240+128));owned=allocation+64;
 memset(allocation,0xc7,512*240+128);PPU.ScreenHeight=224;d35_full_layout();
 assert(!d35_output_acquire(NULL,512*240+64));assert(!d35_output_acquire(owned+1,512*240+64));
 assert(!d35_output_acquire(owned,512*240));
 unsigned cases=0;
 for(unsigned kind=0;kind<7;kind++)for(unsigned rows=0;rows<240;rows++) {
  memset(&IPPU,0,sizeof(IPPU));memset(&Memory,0,sizeof(Memory));PPU.BGMode=1;PPU.ScreenHeight=224;
  assert(d35_output_acquire(owned,512*240+64));d35_output_frame_begin();
  assert(d35_direct&&GFX.Screen==owned&&GFX.PPL==256&&GFX.ZPitch==256&&GFX.Pitch==512);
  patterns();IPPU.PreviousLine=rows;
  switch(kind){case 0:PPU.BGMode=5;break;case 1:PPU.BGMode=6;break;case 2:IPPU.Interlace=1;break;
   case 3:IPPU.DoubleWidthPixels=1;break;case 4:IPPU.DoubleHeightPixels=1;break;
   case 5:PPU.ScreenHeight=240;break;case 6:Memory.FillRAM[0x2133]=8;break;}
  d35_output_promote();assert(!d35_direct&&!d35_compact_aux&&GFX.PPL==512&&GFX.Pitch==1024);
  for(unsigned y=0;y<rows;y++)assert(!memcmp(GFX.Screen+y*1024,owned+y*512,512));
  expect_aux();assert(allocation[0]==0xc7&&owned[512*240+32]==0xc7);cases++;
 }
 for(unsigned kind=0;kind<7;kind++) {
  memset(&IPPU,0,sizeof(IPPU));memset(&Memory,0,sizeof(Memory));PPU.BGMode=1;PPU.ScreenHeight=224;
  assert(d35_output_acquire(owned,512*240+64));d35_output_frame_begin();patterns();
  d35_output_finish();assert(!d35_direct&&d35_compact_aux&&GFX.Screen==GFX.Screen_buffer+32);
  /* Simulate immediate scaler reuse: no retained main pointer may read it. */
  memset(owned,0x89,512*240);
  switch(kind){case 0:PPU.BGMode=5;break;case 1:PPU.BGMode=6;break;case 2:IPPU.Interlace=1;break;
   case 3:IPPU.DoubleWidthPixels=1;break;case 4:IPPU.DoubleHeightPixels=1;break;
   case 5:PPU.ScreenHeight=240;break;case 6:Memory.FillRAM[0x2133]=8;break;}
  assert(d35_output_acquire(owned,512*240+64));d35_output_frame_begin();assert(!d35_direct&&!d35_compact_aux);expect_aux();cases++;
 }
 memset(&IPPU,0,sizeof(IPPU));memset(&Memory,0,sizeof(Memory));PPU.BGMode=1;PPU.ScreenHeight=239;
 for(unsigned i=0;i<4;i++){assert(d35_output_acquire(owned,512*240+64));d35_output_frame_begin();assert(d35_direct);patterns();d35_output_finish();cases++;}
 d35_output_cancel();assert(!d35_compact_aux);expect_aux();
 printf("PASS %u output layout/migration cases: compact 224/239, seven promotion/fallback reasons, state-load cancellation, prefix/tail canaries, released main ownership\n",cases);
 free(allocation);free(GFX.Screen_buffer);free(GFX.SubScreen_buffer);free(GFX.ZBuffer_buffer);free(GFX.SubZBuffer_buffer);
}
