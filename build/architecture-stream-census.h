/* Offline only: observe successful stores and matching full-tile source rows.
 * No output/timing decisions depend on these counters. */
#ifndef ARCH_STREAM_CENSUS_H
#define ARCH_STREAM_CENSUS_H
#include <stdint.h>
extern unsigned long long d35_arch[96];
void arch_region_begin(void);
void arch_region_end(void);
void arch_pixel(uint16_t *,unsigned);
void arch_vector(uint16_t *,const unsigned char *,const unsigned char *);
void arch_source(const unsigned char *,const uint16_t *,unsigned,int);
extern unsigned arch_bg,arch_final;
#endif
#ifdef ARCH_STREAM_IMPLEMENTATION
unsigned arch_bg,arch_final;
static unsigned arch_region,arch_epoch;
static unsigned char arch_written[512*512],arch_math[512*512];
struct arch_source_slot{unsigned epoch,bg,offset,flip;const unsigned char *source;const uint16_t *palette;};
static struct arch_source_slot arch_sources[131072];
void arch_region_begin(void){
 arch_region=GFX.PPL<=512&&!IPPU.DoubleWidthPixels&&!IPPU.DoubleHeightPixels&&!IPPU.HalfWidthPixels;
 arch_final=0;arch_bg=4;
 if(!++arch_epoch){memset(arch_sources,0,sizeof(arch_sources));arch_epoch=1;}
 if(!arch_region){d35_arch[93]++;return;}
 for(unsigned y=GFX.StartY;y<=GFX.EndY&&y<512;y++){
  memset(arch_written+y*GFX.PPL,0,IPPU.RenderedScreenWidth);
  memset(arch_math+y*GFX.PPL,0,IPPU.RenderedScreenWidth);
 }
}
void arch_pixel(uint16_t *out,unsigned math){
 if(!arch_region||GFX.S!=GFX.Screen)return;
 intptr_t offset=out-(uint16_t *)GFX.Screen;
 if(offset<0||offset>=512*512)return;
 d35_arch[64]++;if(arch_written[offset])d35_arch[65]++;
 if(arch_math[offset])d35_arch[67]++;
 if(math)d35_arch[arch_final?86:66]++;
 arch_written[offset]=1;arch_math[offset]=!!math;
}
void arch_vector(uint16_t *out,const unsigned char *mask,const unsigned char *math){
 for(unsigned i=0;i<8;i++)if(mask[i])arch_pixel(out+i,math?math[i]:0);
}
void arch_region_end(void){
 if(!arch_region)return;
 for(unsigned y=GFX.StartY;y<=GFX.EndY&&y<512;y++)for(unsigned x=0;x<IPPU.RenderedScreenWidth;x++){
  unsigned o=y*GFX.PPL+x;if(arch_math[o])d35_arch[68]++;
  if(GFX.ZBuffer[o]&&!arch_written[o])d35_arch[94]++;
 }
 arch_region=0;
}
void arch_source(const unsigned char *source,const uint16_t *palette,unsigned flip,int offset){
 if(!arch_region||arch_bg>=4||offset<0||offset>=512*512)return;
 unsigned sub=GFX.S==GFX.SubScreen,main=GFX.S==GFX.Screen;
 if(!sub&&!main)return;
 d35_arch[sub?75:76]++;
 unsigned h=((unsigned)offset*2654435761u+arch_bg*40503u)&131071u;
 for(unsigned n=0;n<131072;n++,h=(h+1)&131071u){
  struct arch_source_slot *s=&arch_sources[h];
  if(s->epoch!=arch_epoch){
   if(sub){*s=(struct arch_source_slot){arch_epoch,arch_bg,(unsigned)offset,flip,source,palette};d35_arch[78]++;}
   return;
  }
  if(s->bg==arch_bg&&s->offset==(unsigned)offset){
   if(sub){s->source=source;s->palette=palette;s->flip=flip;}
   else if(s->source==source&&s->palette==palette&&s->flip==flip)d35_arch[77]++;
   return;
  }
 }
 d35_arch[92]++;
}
#endif
