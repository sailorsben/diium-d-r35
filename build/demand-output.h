/* Caller reserves a slot and FIFO credit before retro_run. Acquisition is at
 * the visible-frame boundary; migration precedes every resolution expansion.
 * A callback may transfer ownership. Never retain its main pointer afterward. */
#ifndef D35_DEMAND_OUTPUT_H
#define D35_DEMAND_OUTPUT_H
void d35_output_frame_begin(void);
void d35_output_promote(void);
void d35_output_finish(void);
void d35_output_cancel(void);
#ifdef D35_OUTPUT_IMPLEMENTATION
#include "a7_demand_stats.h"
#include <limits.h>
static uint8_t *d35_pending,*d35_owned;
static size_t d35_pending_bytes;
static unsigned d35_direct,d35_compact_aux;
/* Preserve the baseline's 32-byte prefix and a full extra row on each end. */
static uint8_t d35_sub_store[512*240+1024] __attribute__((aligned(64)));
static uint8_t d35_z_store[256*240+512] __attribute__((aligned(64)));
static uint8_t d35_sz_store[256*240+512] __attribute__((aligned(64)));
static uint8_t *d35_output_sub=d35_sub_store+512,*d35_z=d35_z_store+256,*d35_sz=d35_sz_store+256;
static void d35_full_layout(void) {
 GFX.Screen=GFX.Screen_buffer+32;GFX.SubScreen=GFX.SubScreen_buffer+32;
 GFX.ZBuffer=GFX.ZBuffer_buffer+32;GFX.SubZBuffer=GFX.SubZBuffer_buffer+32;
 GFX.RealPitch=GFX.Pitch=GFX.Pitch2=1024;GFX.PPL=512;GFX.PPLx2=1024;GFX.ZPitch=512;
 GFX.Delta=(int32_t)(((intptr_t)GFX.SubScreen-(intptr_t)GFX.Screen)/2);
 GFX.DepthDelta=(intptr_t)GFX.SubZBuffer-(intptr_t)GFX.ZBuffer;
 GFX.S=GFX.Screen;GFX.DB=GFX.ZBuffer;
}
static void d35_aux_migrate(unsigned to_full) {
 for(unsigned y=0;y<240;y++) {
  uint8_t *ps=GFX.SubScreen_buffer+32+y*1024,*pz=GFX.ZBuffer_buffer+32+y*512,*pd=GFX.SubZBuffer_buffer+32+y*512;
  if(to_full){memcpy(ps,d35_output_sub+y*512,512);memcpy(pz,d35_z+y*256,256);memcpy(pd,d35_sz+y*256,256);}
  else{memcpy(d35_output_sub+y*512,ps,512);memcpy(d35_z+y*256,pz,256);memcpy(d35_sz+y*256,pd,256);}
 }
 DS_ADD(DS_OUTPUT_MIGRATE_BYTES,240*1024);d35_compact_aux=!to_full;
}
__attribute__((visibility("default"))) unsigned d35_output_acquire(void *p,size_t bytes) {
 if(d35_direct)return 0;
 d35_pending=NULL;d35_pending_bytes=0;
 /* p has a caller-owned accessible 32-byte prefix, plus bytes after p. */
 if(!p||((uintptr_t)p&15)||bytes<512*240+32)return 0;
 intptr_t delta=((intptr_t)d35_output_sub-(intptr_t)p)/2;
 if(delta<INT32_MIN||delta>INT32_MAX)return 0;
 d35_pending=p;d35_pending_bytes=bytes;return 1;
}
void d35_output_frame_begin(void) {
 unsigned admit=d35_pending&&d35_pending_bytes>=512*240+32&&PPU.ScreenHeight<=239&&
  PPU.BGMode!=5&&PPU.BGMode!=6&&!IPPU.Interlace&&!IPPU.DoubleWidthPixels&&
  !IPPU.DoubleHeightPixels&&!IPPU.HalfWidthPixels&&!(Memory.FillRAM[0x2133]&9);
 if(!admit){DS_ADD(DS_OUTPUT_FALLBACK,1);if(d35_compact_aux)d35_aux_migrate(1);d35_pending=NULL;return;}
 if(!d35_compact_aux)d35_aux_migrate(0);
 d35_owned=d35_pending;d35_pending=NULL;d35_direct=1;
 memcpy(d35_owned-32,GFX.Screen_buffer,32);
 GFX.Screen=d35_owned;GFX.SubScreen=d35_output_sub;GFX.ZBuffer=d35_z;GFX.SubZBuffer=d35_sz;
 GFX.RealPitch=GFX.Pitch=GFX.Pitch2=512;GFX.PPL=256;GFX.PPLx2=512;GFX.ZPitch=256;
 GFX.Delta=(int32_t)(((intptr_t)d35_output_sub-(intptr_t)d35_owned)/2);
 GFX.DepthDelta=(intptr_t)d35_sz-(intptr_t)d35_z;GFX.S=GFX.Screen;GFX.DB=GFX.ZBuffer;
 DS_ADD(DS_OUTPUT_FRAMES,1);
}
void d35_output_promote(void) {
 if(!d35_direct)return;
 if(PPU.BGMode!=5&&PPU.BGMode!=6&&!IPPU.Interlace&&!IPPU.DoubleHeightPixels&&
    !IPPU.DoubleWidthPixels&&!IPPU.HalfWidthPixels&&PPU.ScreenHeight<=239&&!(Memory.FillRAM[0x2133]&9))return;
 /* IPPU.PreviousLine is the completed prefix, before the pending redraw. */
 for(unsigned y=0;y<IPPU.PreviousLine;y++)memcpy(GFX.Screen_buffer+32+y*1024,d35_owned+y*512,512);
 DS_ADD(DS_OUTPUT_MIGRATE_BYTES,IPPU.PreviousLine*512);
 d35_aux_migrate(1);d35_full_layout();d35_direct=0;d35_owned=NULL;DS_ADD(DS_OUTPUT_PROMOTIONS,1);
}
void d35_output_finish(void) {
 if(d35_direct){d35_full_layout();d35_direct=0;d35_owned=NULL;}
 d35_pending=NULL;
}
void d35_output_cancel(void) {
 if(d35_direct){d35_aux_migrate(1);d35_full_layout();d35_direct=0;d35_owned=NULL;}
 else if(d35_compact_aux){d35_aux_migrate(1);d35_full_layout();}
 d35_pending=NULL;
}
#endif
#endif
