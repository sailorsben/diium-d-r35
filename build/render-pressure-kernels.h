/* ROM-free command stream driving actual shipped project row kernels.
 * Scalar arithmetic comes independently from pinned Snes9x gfx.h. */
#ifndef D35_RENDER_PRESSURE_H
#define D35_RENDER_PRESSURE_H
#include "snes9x2005/source/gfx.h"
#include "plus-a7-render.h"
#include <stdint.h>
#include <string.h>
#define RP_MAX (640u*480u)
struct rp_scene { const char *name; unsigned w,h,layers,math,occluded,window,churn,working_rows; };
static const struct rp_scene rp_scenes[]={
 {"static",256,224,2,0,0,0,0,16}, {"dense_math",256,224,8,1,0,0,0,32},
 {"occluded",256,224,8,1,1,0,0,64}, {"window_churn",256,224,4,1,0,1,1,256},
 {"highres",512,448,4,1,0,1,0,256}, {"native",640,480,2,0,0,0,0,16}};
struct rp_image { uint16_t pixels[RP_MAX],sub[RP_MAX];uint8_t depth[RP_MAX],sd[RP_MAX]; };
struct rp_cached { uint32_t key,epoch;uint16_t colors[8]; };
static struct rp_cached rp_cache[64];
static uint8_t rp_tiles[256][8];static uint16_t rp_palette[16];
static uint16_t rp_scalar_math(unsigned mode,uint16_t a,uint16_t b) {
 switch(mode){case 1:return COLOR_ADD(a,b);case 2:return COLOR_ADD1_2(a,b);
 case 3:return COLOR_SUB(a,b);default:return COLOR_SUB1_2(a,b);}
}
static void rp_prepare(const struct rp_scene *s,unsigned frame) {
 unsigned t,x;uint32_t epoch=s->churn?frame:0;
 for(t=0;t<256;t++)for(x=0;x<8;x++)rp_tiles[t][x]=(uint8_t)((t*3+x*5+(s->churn?frame:0))&15);
 for(x=0;x<16;x++)rp_palette[x]=(uint16_t)(x*4051u+epoch*157u);
 /* Key all palette/tile changes together; reset between scenes and epochs. */
 for(t=0;t<64;t++)if(rp_cache[t].epoch!=epoch+1 || rp_cache[t].key==UINT32_MAX) {
  rp_cache[t].key=UINT32_MAX;rp_cache[t].epoch=epoch+1;
 }
}
static void rp_invalidate(void){unsigned i;for(i=0;i<64;i++)rp_cache[i].key=UINT32_MAX;}
static __attribute__((noinline,optimize("no-tree-vectorize,no-tree-slp-vectorize"))) void rp_render(struct rp_image *im,uint16_t *dst,
 const struct rp_scene *s,unsigned frame,unsigned variant) {
 unsigned n=s->w*s->h,x,y,l;rp_prepare(s,frame);
 for(x=0;x<n;x++){dst[x]=0x0821;im->depth[x]=0;im->sub[x]=(uint16_t)(x*31u);im->sd[x]=(uint8_t)((x/8)%4);}
 if(s->window)for(y=0;y<s->h;y++) {
  unsigned a=(y*3+frame)%s->w,b=(y*7+frame+13)%s->w;if(a>b){unsigned t=a;a=b;b=t;}
  for(x=0;x<s->w;x++)if(x<a || x>b)im->depth[y*s->w+x]=255;
 }
 for(l=0;l<s->layers;l++)for(y=0;y<s->h;y++)for(x=0;x<s->w;x+=8) {
  unsigned pos=y*s->w+x,t=(x/8+y*17+l*29)&(s->working_rows-1),flip=(y+l+frame)&1;
  unsigned mode=s->math?(l%6)+1:0,z=s->occluded?(l?32:200):16+l*16,j;
  uint16_t fixed=0x632d;
  if(!variant)for(j=0;j<8;j++) {
   unsigned idx=rp_tiles[t][flip?7-j:j],p=pos+j;
   if(idx && z>im->depth[p]) {
    uint16_t c=rp_palette[idx];unsigned sd=im->sd[p];
    if(mode>=5){if(sd==1)c=rp_scalar_math(mode==5?2:4,c,fixed);}
    else if(mode && sd)c=rp_scalar_math(sd==1&&(mode==2||mode==4)?mode-1:mode,c,sd==1?fixed:im->sub[p]);
    dst[p]=c;im->depth[p]=(uint8_t)(z-1);
   }
  } else if(variant==1) d35_row(rp_tiles[t],d35_palette(rp_palette,4),flip,dst+pos,im->depth+pos,im->sd+pos,im->sub+pos,z,z-1,fixed,mode);
  else {
   struct rp_cached *c=&rp_cache[t&63];
   if(c->key!=t){for(j=0;j<8;j++)c->colors[j]=rp_palette[rp_tiles[t][j]];c->key=t;}
   d35_row_colored(rp_tiles[t],c->colors,flip,dst+pos,im->depth+pos,im->sd+pos,im->sub+pos,z,z-1,fixed,mode);
  }
 }
}
static uint32_t rp_hash(const void *p,size_t n){const uint8_t *b=p;uint32_t h=2166136261u;while(n--)h=(h^*b++)*16777619u;return h;}
static void rp_zero_table(void){unsigned i;for(i=0;i<65536;i++){unsigned r=i>>11,g=(i>>5)&63,b=i&31;GFX.ZERO[i]=BUILD_PIXEL2((r&16)?r&15:0,(g&32)?g&31:0,(b&16)?b&15:0);}}
#endif
