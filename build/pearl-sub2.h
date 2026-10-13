/* A sole 2bpp subscreen layer has no competing depth. Cached indexed pixels
 * remain authoritative; cold tiles use the original converter/fallback. */
#ifndef D35_PEARL_SUB2_H
#define D35_PEARL_SUB2_H
struct d35_sub2_context {const uint16_t *last;d35_palette_t table;};
static inline unsigned d35_sub2(struct d35_sub2_context *ctx,unsigned tile,
 int32_t offset,unsigned line,unsigned lines)
{
 unsigned addr=(BG.TileAddress+((tile&1023)<<BG.TileShift)+
    (((tile&511)>=256)?BG.NameSelect:0))&65535;
 unsigned number=addr>>BG.TileShift,state=BG.Buffered[number];
 if(!state)return 0;
 if(state==BLANK_TILE)return 1;
 uint8_t *p=BG.Buffer+(number<<6)+((tile&V_FLIP)?56-line:line);
 const uint16_t *colors=IPPU.ScreenColors+(((tile>>10)&BG.PaletteMask)<<BG.PaletteShift)+BG.StartPalette;
 if(ctx->last!=colors){ctx->table=d35_palette(colors,2);ctx->last=colors;}
 int step=(tile&V_FLIP)?-8:8;
 for(unsigned row=0;row<lines;row++,p+=step,offset+=GFX.PPL){
  uint8x8_t idx=vld1_u8(p);if(tile&H_FLIP)idx=vrev64_u8(idx);
  uint8x8x2_t zip=vzip_u8(vtbl2_u8(ctx->table.low,idx),vtbl2_u8(ctx->table.high,idx));
  uint16x8_t color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));
  uint8x8_t transparent=vceq_u8(idx,vdup_n_u8(0));
  uint16_t *out=(uint16_t *)GFX.S+offset;uint8_t *depth=GFX.DB+offset;
  if(!vget_lane_u64(vreinterpret_u64_u8(transparent),0)){
   vst1q_u16(out,color);vst1_u8(depth,vdup_n_u8(GFX.Z2));
#ifdef D35_PEARL_SUB_COUNT
   ++d35_pearl[330];
#endif
  }else{
   d35_store(out,color,vmvn_u8(transparent));
   vst1_u8(depth,vbsl_u8(transparent,vld1_u8(depth),vdup_n_u8(GFX.Z2)));
#ifdef D35_PEARL_SUB_COUNT
   ++d35_pearl[331];
#endif
  }
 }
#ifdef D35_PEARL_SUB_COUNT
 ++d35_pearl[332];
#endif
 return 1;
}
#endif
