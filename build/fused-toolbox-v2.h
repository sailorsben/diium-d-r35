/* Exact indexed toolkit: reuse visibility, defer materialization, shared palettes. */
#ifndef D35_FUSED_TOOLBOX_H
#define D35_FUSED_TOOLBOX_H
#include "a7_partial_kernels.h"
#ifdef D35_COMMON_COUNT
#define CB(n) (++d35_pearl[336+(n)])
#else
#define CB(n) ((void)0)
#endif
#ifdef D35_FUSED_COUNT
extern unsigned long long d35_fused[32];
#define FT(n) (++d35_fused[n])
#define FA(n,v) (d35_fused[n]+=(v))
#else
#define FT(n) ((void)0)
#define FA(n,v) ((void)0)
#endif
struct d35_batch_context {unsigned mode,valid;d35_palette_t tables[8];unsigned depth_policy;};
/* Original math path is appended by the isolated preparer. */
static inline unsigned d35_batch_covered(int32_t offset,unsigned lines){
 uint8x8_t z=vdup_n_u8(GFX.Z1);
 while(lines--){if(vget_lane_u64(vreinterpret_u64_u8(vcgt_u8(z,vld1_u8(GFX.DB+offset))),0))return 0;offset+=GFX.PPL;}return 1;
}
static inline __attribute__((always_inline)) unsigned d35_fused_plain(
 struct d35_batch_context *ctx,unsigned tile,int32_t offset,unsigned line,unsigned lines)
{
 if(!lines)return 1;
 const unsigned pitch=GFX.PPL,z1=GFX.Z1,z2=GFX.Z2,bits=BG.BitShift;
 uint16_t *const screen=(uint16_t *)GFX.S;uint8_t *const zbuffer=GFX.DB;
 const uint8x8_t zv=vdup_n_u8(z1),z2v=vdup_n_u8(z2);
 const unsigned main=GFX.S==GFX.Screen;
 unsigned skipped=0,have_depth=0,force=main&&(bits==2||(bits==4&&ctx->depth_policy==2));
 uint8x8_t old,dm;
 if(force){
  if(bits==2)FT(4);else FT(3);
  for(;skipped<lines;skipped++,offset+=pitch){
   old=vld1_u8(zbuffer+offset);dm=vcgt_u8(zv,old);FT(5);if(bits==2)FT(29);else FT(30);
   if(vget_lane_u64(vreinterpret_u64_u8(dm),0)){have_depth=1;if(bits==4){ctx->depth_policy=1;FT(11);}break;}
  }
  FA(7,skipped);
  if(skipped==lines){FT(6);return 1;}
 }
 unsigned addr=(BG.TileAddress+((tile&1023)<<BG.TileShift)+(((tile&511)>=256)?BG.NameSelect:0))&65535;
 unsigned number=addr>>BG.TileShift,state=BG.Buffered[number];
 if(!state){FT(15);return 0;} /* Caller draws original full requested tile. */
 if(state==BLANK_TILE){FT(14);return 1;}
 /* Sample one warm 4bpp main tile per DrawBackground. Prediction affects cost only. */
 if(main&&bits==4&&!ctx->depth_policy){
  FT(2);
  for(;skipped<lines;skipped++,offset+=pitch){
   old=vld1_u8(zbuffer+offset);dm=vcgt_u8(zv,old);FT(5);if(bits==2)FT(29);else FT(30);
   if(vget_lane_u64(vreinterpret_u64_u8(dm),0)){have_depth=1;break;}
  }
  FA(7,skipped);ctx->depth_policy=skipped==lines?2:1;
  if(skipped==lines){FT(31);FT(6);return 1;}
 }
 unsigned first=(tile&V_FLIP)?56-line:line;int step=(tile&V_FLIP)?-8:8;
 uint8_t *p=BG.Buffer+(number<<6)+first+(int)skipped*step;
 const uint16_t *colors=IPPU.ScreenColors+(((tile>>10)&BG.PaletteMask)<<BG.PaletteShift)+BG.StartPalette;
 unsigned slot=(tile>>10)&BG.PaletteMask;d35_palette_t table;unsigned ready=0;
 unsigned remaining=lines-skipped;
 if(have_depth){FA(27,skipped);FT(8);}else{old=vld1_u8(zbuffer+offset);dm=vcgt_u8(zv,old);FT(9);}
 for(;;){
  uint16_t *out=screen+offset;uint8_t *depth=zbuffer+offset;
  uint8x8_t idx=vld1_u8(p);FT(10);if(tile&H_FLIP)idx=vrev64_u8(idx);
  uint8x8_t mask=vand_u8(dm,vmvn_u8(vceq_u8(idx,vdup_n_u8(0))));
  uint64_t active=vget_lane_u64(vreinterpret_u64_u8(mask),0);
  if(active){
   FT(18);
   if(active!=UINT64_MAX&&d35_sparse_plain(out,depth,p,colors,active,!!(tile&H_FLIP),(uint8_t)z2)){
#ifdef D35_FUSED_COUNT
    unsigned n=((((uint32_t)active&0x01010101u)+((uint32_t)(active>>32)&0x01010101u))*0x01010101u)>>24;
    FT(n==1?16:17);
#endif
   }else{
    if(!ready){if(!(ctx->valid&(1u<<slot))){table=d35_palette(colors,bits);ctx->tables[slot]=table;ctx->valid|=1u<<slot;FT(26);}else table=ctx->tables[slot];ready=1;}
    uint8x8x2_t zip=vzip_u8(vtbl2_u8(table.low,idx),vtbl2_u8(table.high,idx));
    uint16x8_t color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));
    if(active==UINT64_MAX){FT(20);vst1q_u16(out,color);vst1_u8(depth,z2v);}
    else{FT(19);vst1q_u16(out,vbslq_u16(d35_boolean_mask16(mask),color,vld1q_u16(out)));vst1_u8(depth,vbsl_u8(mask,z2v,old));}
   }
  }
  if(!--remaining)break;
  offset+=pitch;p+=step;old=vld1_u8(zbuffer+offset);dm=vcgt_u8(zv,old);FT(9);
 }
 return 1;
}
/* Eligible sole 2bpp sub layer: no competing depth; share the same palette owner. */
static inline __attribute__((always_inline)) unsigned d35_fused_sole(
 struct d35_batch_context *ctx,unsigned tile,int32_t offset,unsigned line,unsigned lines)
{
 unsigned addr=(BG.TileAddress+((tile&1023)<<BG.TileShift)+(((tile&511)>=256)?BG.NameSelect:0))&65535;
 unsigned number=addr>>BG.TileShift,state=BG.Buffered[number];
 if(!state){FT(15);return 0;}if(state==BLANK_TILE){FT(14);return 1;}
 uint8_t *p=BG.Buffer+(number<<6)+((tile&V_FLIP)?56-line:line);int step=(tile&V_FLIP)?-8:8;
 const uint16_t *colors=IPPU.ScreenColors+(((tile>>10)&BG.PaletteMask)<<BG.PaletteShift)+BG.StartPalette;
 unsigned slot=(tile>>10)&BG.PaletteMask;d35_palette_t table;unsigned ready=0;
 uint8x8_t z2=vdup_n_u8(GFX.Z2);
 for(unsigned row=0;row<lines;row++,p+=step,offset+=GFX.PPL){
  FT(21);uint8x8_t idx=vld1_u8(p);if(tile&H_FLIP)idx=vrev64_u8(idx);
  uint8x8_t mask=vmvn_u8(vceq_u8(idx,vdup_n_u8(0)));uint64_t active=vget_lane_u64(vreinterpret_u64_u8(mask),0);
  if(!active)continue;
  uint16_t *out=(uint16_t *)GFX.S+offset;uint8_t *depth=GFX.DB+offset;
  if(active!=UINT64_MAX&&d35_sparse_plain(out,depth,p,colors,active,!!(tile&H_FLIP),GFX.Z2)){FT(24);continue;}
  if(!ready){if(!(ctx->valid&(1u<<slot))){table=d35_palette(colors,2);ctx->tables[slot]=table;ctx->valid|=1u<<slot;FT(25);}else table=ctx->tables[slot];ready=1;}
  uint8x8x2_t zip=vzip_u8(vtbl2_u8(table.low,idx),vtbl2_u8(table.high,idx));uint16x8_t color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));
  if(active==UINT64_MAX){FT(22);vst1q_u16(out,color);vst1_u8(depth,z2);}
  else{FT(23);vst1q_u16(out,vbslq_u16(d35_boolean_mask16(mask),color,vld1q_u16(out)));vst1_u8(depth,vbsl_u8(mask,z2,vld1_u8(depth)));}
 }
 return 1;
}
/* FUSED_BASE */
static inline __attribute__((always_inline)) unsigned d35_batch_tile_mode(
 struct d35_batch_context *ctx,unsigned tile,int32_t offset,unsigned line,unsigned lines,unsigned mode)
{return mode?d35_batch_tile_mode_base(ctx,tile,offset,line,lines,mode):d35_fused_plain(ctx,tile,offset,line,lines);}
static inline __attribute__((always_inline)) unsigned d35_batch_tile(
 struct d35_batch_context *ctx,unsigned tile,int32_t offset,unsigned line,unsigned lines)
{return d35_batch_tile_mode(ctx,tile,offset,line,lines,ctx->mode);}
#undef CB
#undef FT
#undef FA
#endif
