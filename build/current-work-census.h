/* Offline observer only: no output, timing or emulated-state decisions. */
#ifndef D35_CURRENT_WORK_H
#define D35_CURRENT_WORK_H
#include <stdint.h>
extern unsigned long long d35_work[64];
extern unsigned work_layer,work_final;
void work_begin(void);void work_end(void);void work_pixel(uint16_t *,unsigned);
void work_vector(uint16_t *,const unsigned char *,const unsigned char *);
#endif
#ifdef D35_CURRENT_WORK_IMPLEMENTATION
unsigned long long d35_work[64];unsigned work_layer,work_final;
static unsigned work_active;
static unsigned char work_written[512*512],work_math[512*512],work_owner[512*512];
void work_begin(void){
 work_active=GFX.PPL<=512&&!IPPU.DoubleWidthPixels&&!IPPU.DoubleHeightPixels&&!IPPU.HalfWidthPixels;
 work_final=0;work_layer=0;if(!work_active){d35_work[23]++;return;}
 for(unsigned y=GFX.StartY;y<=GFX.EndY&&y<512;y++){
  memset(work_written+y*GFX.PPL,0,IPPU.RenderedScreenWidth);
  memset(work_math+y*GFX.PPL,0,IPPU.RenderedScreenWidth);
  memset(work_owner+y*GFX.PPL,0,IPPU.RenderedScreenWidth);
 }
}
void work_pixel(uint16_t *out,unsigned math){
 if(!work_active)return;
 if(GFX.S==GFX.SubScreen){d35_work[22]++;return;}
 if(GFX.S!=GFX.Screen)return;
 intptr_t o=out-(uint16_t *)GFX.Screen;if(o<0||o>=512*512){d35_work[23]++;return;}
 d35_work[16]++;
 if(work_written[o]){d35_work[17]++;d35_work[32+work_owner[o]]++;d35_work[40+work_layer]++;}
 if(work_math[o])d35_work[19]++;
 if(math){d35_work[18]++;if(work_final)d35_work[56]++;}
 work_written[o]=1;work_math[o]=!!math;work_owner[o]=work_layer;
}
void work_vector(uint16_t *out,const unsigned char *mask,const unsigned char *math){
 for(unsigned i=0;i<8;i++)if(mask[i])work_pixel(out+i,math?math[i]:0);
}
void work_end(void){
 if(!work_active)return;
 for(unsigned y=GFX.StartY;y<=GFX.EndY&&y<512;y++)for(unsigned x=0;x<IPPU.RenderedScreenWidth;x++){
  unsigned o=y*GFX.PPL+x;if(work_math[o])d35_work[20]++;
  if(GFX.ZBuffer[o]&&!work_written[o])d35_work[21]++;
 }
 work_active=0;
}
#endif
