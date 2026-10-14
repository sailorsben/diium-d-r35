/* One dual-plane layer per redraw, chosen from live enables. Source geometry
 * only: each consumer still owns clipping, depth, transparency and math. */
#ifndef D35_DEMAND_GEOMETRY_H
#define D35_DEMAND_GEOMETRY_H
#include "a7_demand_stats.h"
struct d35_geometry_band {
 unsigned epoch,lines,line,shift;
 uint32_t tiles[33]; /* actual tile plus original priority in bit 17 */
};
static struct d35_geometry_band d35_geometry[240];
static unsigned d35_geometry_epoch=1,d35_geometry_layer=4;
static void d35_geometry_reset(void) {
 if(!++d35_geometry_epoch){memset(d35_geometry,0,sizeof(d35_geometry));d35_geometry_epoch=1;}
 d35_geometry_layer=4;
}
static struct d35_geometry_band *d35_geometry_produce(unsigned bg,unsigned y) {
 struct d35_geometry_band *g=&d35_geometry[y];
 if(g->epoch==d35_geometry_epoch){DS_ADD(DS_GEO_REUSED,1);return g;}
 unsigned vo=LineData[y].BG[bg].VOffset,ho=LineData[y].BG[bg].HOffset;
 unsigned va=(y+vo)&7,lines;
 for(lines=1;lines<8-va&&y+lines<=GFX.EndY;lines++)
  if(vo!=LineData[y+lines].BG[bg].VOffset||ho!=LineData[y+lines].BG[bg].HOffset||
     (d35_window_is_target(bg)&&!d35_window_same(y,y+lines)))break;
 unsigned size=BG.TileSize,mask=size==16?1023:511;
 unsigned sy=(vo+y)>>(size==16?4:3),t1=((vo+y)&15)>7?16:0,t2=16-t1;
 unsigned sc[4];sc[0]=PPU.BG[bg].SCBase<<1;
 sc[1]=(sc[0]+((PPU.BG[bg].SCSize&1)?2048:0))&65535;
 sc[2]=(PPU.BG[bg].SCSize&2)?(sc[1]+2048)&65535:sc[0];
 sc[3]=(sc[2]+((PPU.BG[bg].SCSize&1)?2048:0))&65535;
 g->lines=lines;g->line=va*8;g->shift=ho&7;
 for(unsigned cell=0;cell<33;cell++) {
  unsigned hp=(ho-g->shift+cell*8)&mask,q=hp>>3;
  unsigned sx=size==16?q>>1:q;
  unsigned addr=(sc[((sy&32)?2:0)+((sx&32)?1:0)]+((sy&31)*32+(sx&31))*2)&65535;
  unsigned tile=READ_2BYTES(Memory.VRAM+addr),actual=tile;
  if(size==16)actual+=(tile&V_FLIP?t2:t1)+(tile&H_FLIP?1-(q&1):q&1);
  g->tiles[cell]=actual|((tile&0x2000)<<4);
 }
 g->epoch=d35_geometry_epoch;
 DS_ADD(DS_GEO_BANDS,1);DS_ADD(DS_GEO_WRITES,33*4);
 DS_ADD(DS_GEO_16,size==16);DS_ADD(DS_GEO_BG0+bg,1);
 DS_ADD(DS_GEO_WINDOW,d35_window_is_target(bg)!=0);
 return g;
}
#define D35_GEOMETRY_DRAW(MODE) \
static __attribute__((noinline)) void d35_geometry_draw_##MODE(unsigned bg,struct d35_batch_context *ctx,unsigned low,unsigned high,struct d35_sub2_context *sole) { \
 for(unsigned y=GFX.StartY;y<=GFX.EndY;) { \
  struct d35_geometry_band *g=d35_geometry_produce(bg,y); \
  struct d35_window_clip wc; \
  unsigned custom=d35_window_fetch(bg,y,GFX.pCurrentClip==&IPPU.Clip[1],&wc); \
  unsigned count=custom?wc.count:GFX.pCurrentClip->Count[bg]; \
  for(unsigned clip=0;clip<(count?count:1);clip++) { \
   unsigned left=count?(custom?wc.left[clip]:GFX.pCurrentClip->Left[clip][bg]):0; \
   unsigned right=count?(custom?wc.right[clip]:GFX.pCurrentClip->Right[clip][bg]):256; \
   if(right<=left)continue; \
   while(left<right) { \
    unsigned cell=(left+g->shift)>>3,start=(left+g->shift)&7,n=8-start; \
    if(n>right-left)n=right-left; \
    unsigned packed=g->tiles[cell],tile=packed&0x1ffff; \
    int offset=(int)(y*GFX.PPL+cell*8)-(int)g->shift; \
    GFX.Z1=GFX.Z2=(packed&(1u<<17))?high:low; \
    DS_ADD(DS_GEO_READS,4);DS_ADD(GFX.S==GFX.Screen?DS_GEO_MAIN_CELLS:DS_GEO_SUB_CELLS,1); \
    if(start||n<8) {DS_ADD(DS_GEO_EDGES,1);(*DrawClippedTilePtr)(tile,offset,start,n,g->line,g->lines);} \
    else {DS_ADD(DS_GEO_FULL,1); \
     if(sole&&d35_sub2(sole,tile,offset,g->line,g->lines)){} \
     else if(!d35_batch_tile_mode(ctx,tile,offset,g->line,g->lines,MODE))(*DrawTilePtr)(tile,offset,g->line,g->lines); \
    } \
    left+=n; \
   } \
  } \
  y+=g->lines; \
 } \
}
D35_GEOMETRY_DRAW(0)
D35_GEOMETRY_DRAW(1)
D35_GEOMETRY_DRAW(3)
#undef D35_GEOMETRY_DRAW
static unsigned d35_geometry_begin(unsigned mode,unsigned bg,unsigned okay,
 struct d35_batch_context *ctx,unsigned low,unsigned high,struct d35_sub2_context *sole) {
 unsigned both=GFX.r212c&GFX.r212d&15;
 if(!okay||!(both&(1u<<bg))||GFX.Pseudo||GFX.EndY>=240||
    (mode!=0&&mode!=1&&mode!=3)){DS_ADD(DS_GEO_FALLBACK,1);return 0;}
 if(d35_geometry_layer==4){for(unsigned i=0;i<4;i++)if(both&(1u<<i)){d35_geometry_layer=i;break;}}
 if(bg!=d35_geometry_layer)return 0;
 if(ctx->mode==0)d35_geometry_draw_0(bg,ctx,low,high,sole);
 else if(ctx->mode==1)d35_geometry_draw_1(bg,ctx,low,high,sole);
 else d35_geometry_draw_3(bg,ctx,low,high,sole);
 return 1;
}
#endif
