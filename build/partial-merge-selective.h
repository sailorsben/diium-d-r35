/* Exact indexed full-tile production inside the owning background batch.
 * Cold caches and unsupported modes retain the original renderer. Palette
 * context cannot outlive DrawBackground: no cross-call palette invalidation. */
#ifndef D35_COMMON_TILE_BATCH_H
#define D35_COMMON_TILE_BATCH_H
#include "a7_partial_kernels.h"
#ifdef D35_COMMON_COUNT
#define CB(n) (++d35_pearl[336+(n)])
#else
#define CB(n) ((void)0)
#endif
struct d35_batch_context {unsigned mode,valid;d35_palette_t tables[8];};
static inline unsigned d35_batch_covered(int32_t offset,unsigned lines)
{
 uint8x8_t z=vdup_n_u8(GFX.Z1);
 while(lines--){
  if(vget_lane_u64(vreinterpret_u64_u8(vcgt_u8(z,vld1_u8(GFX.DB+offset))),0))return 0;
  offset+=GFX.PPL;
 }
 return 1;
}
static inline __attribute__((always_inline)) unsigned d35_batch_tile_mode_base(
 struct d35_batch_context *ctx,unsigned tile,int32_t offset,unsigned line,unsigned lines,unsigned mode)
{
 CB(0);
 /* Retain the qualified early-visibility path, now before indirect dispatch. */
 if(!mode&&BG.BitShift==2&&GFX.S==GFX.Screen&&d35_batch_covered(offset,lines)){
  CB(14);
#ifdef D35_COMMON_COUNT
  PW(20);d35_pearl[(d35_pearl_plane*6+d35_pearl_layer)*24+21]+=lines;
#endif
  return 1;
 }
 unsigned addr=(BG.TileAddress+((tile&1023)<<BG.TileShift)+
    (((tile&511)>=256)?BG.NameSelect:0))&65535;
 unsigned number=addr>>BG.TileShift,state=BG.Buffered[number];
 if(!state){CB(1);return 0;}
 if(state==BLANK_TILE){CB(2);return 1;}
 CB(3);
 uint8_t *p=BG.Buffer+(number<<6)+((tile&V_FLIP)?56-line:line);
 const uint16_t *colors=IPPU.ScreenColors+(((tile>>10)&BG.PaletteMask)<<BG.PaletteShift)+BG.StartPalette;
 int step=(tile&V_FLIP)?-8:8;
 unsigned slot=(tile>>10)&BG.PaletteMask;
 d35_palette_t table;bool ready=false;
 for(unsigned row=0;row<lines;row++,p+=step,offset+=GFX.PPL){
  CB(4);
  uint16_t *out=(uint16_t *)GFX.S+offset;
  uint8_t *depth=(mode?GFX.ZBuffer:GFX.DB)+offset;
  uint8x8_t old=vld1_u8(depth),idx=vld1_u8(p);
  if(tile&H_FLIP)idx=vrev64_u8(idx);
  uint8x8_t dm=vcgt_u8(vdup_n_u8(GFX.Z1),old);
  uint8x8_t mask=vand_u8(dm,vmvn_u8(vceq_u8(idx,vdup_n_u8(0))));
  uint64_t active=vget_lane_u64(vreinterpret_u64_u8(mask),0);
#ifdef D35_COMMON_COUNT
  d35_pearl_row(mode,mask,old,dm);
#endif
  if(!active){CB(13);continue;}
  CB(5);
  if(!ready){
   if(!(ctx->valid&(1u<<slot))){table=d35_palette(colors,BG.BitShift);ctx->tables[slot]=table;ctx->valid|=1u<<slot;CB(8);}
   else{table=ctx->tables[slot];CB(9);}
   ready=true;
  }else{CB(9);}
  uint8x8x2_t zip=vzip_u8(vtbl2_u8(table.low,idx),vtbl2_u8(table.high,idx));
  uint16x8_t color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));
  if(mode){CB(10);CB(12);color=d35_blend(color,vld1_u8(GFX.SubZBuffer+offset),out+GFX.Delta,d35_fixed_at_offset((unsigned)offset),mode,mask);}else{CB(11);}
  if(active==UINT64_MAX){CB(6);vst1q_u16(out,color);vst1_u8(depth,vdup_n_u8(GFX.Z2));}
  else{CB(7);vst1q_u16(out,vbslq_u16(d35_boolean_mask16(mask),color,vld1q_u16(out)));vst1_u8(depth,vbsl_u8(mask,vdup_n_u8(GFX.Z2),old));}
 }
 return 1;
}
static inline __attribute__((always_inline)) unsigned d35_batch_tile_mode_plain(
 struct d35_batch_context *ctx,unsigned tile,int32_t offset,unsigned line,unsigned lines,unsigned mode)
{
 CB(0);
 /* Retain the qualified early-visibility path, now before indirect dispatch. */
 if(!mode&&BG.BitShift==2&&GFX.S==GFX.Screen&&d35_batch_covered(offset,lines)){
  CB(14);
#ifdef D35_COMMON_COUNT
  PW(20);d35_pearl[(d35_pearl_plane*6+d35_pearl_layer)*24+21]+=lines;
#endif
  return 1;
 }
 unsigned addr=(BG.TileAddress+((tile&1023)<<BG.TileShift)+
    (((tile&511)>=256)?BG.NameSelect:0))&65535;
 unsigned number=addr>>BG.TileShift,state=BG.Buffered[number];
 if(!state){CB(1);return 0;}
 if(state==BLANK_TILE){CB(2);return 1;}
 CB(3);
 /* Snapshot immutable row state before stores can confuse alias analysis. */
 const unsigned pitch=GFX.PPL,z1=GFX.Z1,z2=GFX.Z2,bits=BG.BitShift;
 uint16_t *const screen=(uint16_t *)GFX.S;
 uint8_t *const zbuffer=mode?GFX.ZBuffer:GFX.DB;
 const uint8_t *const subdepth=GFX.SubZBuffer;
 const int delta=GFX.Delta;
 const unsigned fixed_active=d35_fixed_active,fixed_shift=d35_fixed_shift,fixed=GFX.FixedColour;
 const uint8x8_t z1v=vdup_n_u8(z1),z2v=vdup_n_u8(z2);
 uint8_t *p=BG.Buffer+(number<<6)+((tile&V_FLIP)?56-line:line);
 const uint16_t *colors=IPPU.ScreenColors+(((tile>>10)&BG.PaletteMask)<<BG.PaletteShift)+BG.StartPalette;
 int step=(tile&V_FLIP)?-8:8;
 unsigned slot=(tile>>10)&BG.PaletteMask;
 d35_palette_t table;bool ready=false;
 for(unsigned row=0;row<lines;row++,p+=step,offset+=pitch){
  CB(4);
  uint16_t *out=screen+offset;
  uint8_t *depth=zbuffer+offset;
  uint8x8_t old=vld1_u8(depth),idx=vld1_u8(p);
  if(tile&H_FLIP)idx=vrev64_u8(idx);
  uint8x8_t dm=vcgt_u8(z1v,old);
  uint8x8_t mask=vand_u8(dm,vmvn_u8(vceq_u8(idx,vdup_n_u8(0))));
  uint64_t active=vget_lane_u64(vreinterpret_u64_u8(mask),0);
#ifdef D35_COMMON_COUNT
  d35_pearl_row(mode,mask,old,dm);
#endif
  if(!active){CB(13);continue;}
  CB(5);
  if(!mode&&active!=UINT64_MAX&&d35_sparse_plain(out,depth,p,colors,active,!!(tile&H_FLIP),(uint8_t)z2))continue;
  if(!ready){
   if(!(ctx->valid&(1u<<slot))){table=d35_palette(colors,bits);ctx->tables[slot]=table;ctx->valid|=1u<<slot;CB(8);}
   else{table=ctx->tables[slot];CB(9);}
   ready=true;
  }else{CB(9);}
  uint8x8x2_t zip=vzip_u8(vtbl2_u8(table.low,idx),vtbl2_u8(table.high,idx));
  uint16x8_t color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));
  if(mode){CB(10);CB(12);color=d35_blend(color,vld1_u8(subdepth+offset),out+delta,fixed_active?d35_fixed_rows[(unsigned)offset>>fixed_shift]:fixed,mode,mask);}else{CB(11);}
  if(active==UINT64_MAX){CB(6);vst1q_u16(out,color);vst1_u8(depth,z2v);}
  else{CB(7);vst1q_u16(out,vbslq_u16(d35_boolean_mask16(mask),color,vld1q_u16(out)));vst1_u8(depth,vbsl_u8(mask,z2v,old));}
 }
 return 1;
}
static inline __attribute__((always_inline)) unsigned d35_batch_tile_mode(
 struct d35_batch_context *ctx,unsigned tile,int32_t offset,unsigned line,unsigned lines,unsigned mode)
{
 if(!mode)return d35_batch_tile_mode_plain(ctx,tile,offset,line,lines,0);
 return d35_batch_tile_mode_base(ctx,tile,offset,line,lines,mode);
}

static inline __attribute__((always_inline)) unsigned d35_batch_tile(
 struct d35_batch_context *ctx,unsigned tile,int32_t offset,unsigned line,unsigned lines)
{return d35_batch_tile_mode(ctx,tile,offset,line,lines,ctx->mode);}
#undef CB
#endif
