/* Dispatch the color operation once per band, retaining constant arithmetic
 * inside its indexed full-tile loop. The caller owns clip/scroll row grouping. */
#ifndef D35_COMMON_BAND_H
#define D35_COMMON_BAND_H
#include "a7_common_batch.h"
struct d35_band_walk {
 uint16_t *t,*b1,*b2;
 unsigned quot,offset,t1,t2,line,lines,low,high;
 struct d35_sub2_context *sole;
};
#ifdef D35_COMMON_COUNT
#define D35_BAND_COUNT (++d35_pearl[351])
#else
#define D35_BAND_COUNT ((void)0)
#endif
#ifdef D35_FUSED_COUNT
#define FBAND(n) (++d35_fused[n])
#define FCELL (++d35_fused[28])
#else
#define FBAND(n) ((void)0)
#define FCELL ((void)0)
#endif
#define D35_BAND_FUNCTION(MODE,SOLE) \
static __attribute__((noinline)) void d35_fused_band_##MODE##_##SOLE(struct d35_batch_context *ctx,struct d35_band_walk *w,unsigned cells) \
{ \
 D35_BAND_COUNT; \
 if(SOLE){FBAND(1);}else{FBAND(0);} \
 for(unsigned cell=0;cell<cells;cell++){ FCELL; \
  unsigned tile=READ_2BYTES(w->t),actual=tile; \
  GFX.Z1=GFX.Z2=(tile&0x2000)?w->high:w->low; \
  if(BG.TileSize!=8){ \
   if(tile&H_FLIP)actual+=(tile&V_FLIP?w->t2:w->t1)+1-(w->quot&1); \
   else actual+=(tile&V_FLIP?w->t2:w->t1)+(w->quot&1); \
  } \
  if(SOLE){if(!d35_fused_sole(ctx,actual,w->offset,w->line,w->lines))(*DrawTilePtr)(actual,w->offset,w->line,w->lines);} \
  else if(!d35_batch_tile_mode(ctx,actual,w->offset,w->line,w->lines,MODE))(*DrawTilePtr)(actual,w->offset,w->line,w->lines); \
  if(BG.TileSize==8){w->t++;if(w->quot==31)w->t=w->b2;else if(w->quot==63)w->t=w->b1;} \
  else{w->t+=w->quot&1;if(w->quot==63)w->t=w->b2;else if(w->quot==127)w->t=w->b1;} \
  w->quot++;w->offset+=8; \
 } \
}
D35_BAND_FUNCTION(0,0)
D35_BAND_FUNCTION(0,1)
D35_BAND_FUNCTION(1,0)
D35_BAND_FUNCTION(3,0)
static inline void d35_band_0(struct d35_batch_context *c,struct d35_band_walk *w,unsigned n){if(w->sole)d35_fused_band_0_1(c,w,n);else d35_fused_band_0_0(c,w,n);}
static inline void d35_band_1(struct d35_batch_context *c,struct d35_band_walk *w,unsigned n){d35_fused_band_1_0(c,w,n);}
static inline void d35_band_3(struct d35_batch_context *c,struct d35_band_walk *w,unsigned n){d35_fused_band_3_0(c,w,n);}
#undef D35_BAND_FUNCTION
#undef D35_BAND_COUNT
#undef FBAND
#undef FCELL
#endif
