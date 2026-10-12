/* Replaces only the eligible full-tile helper in isolated offline copies. */
static INLINE __attribute__((always_inline)) bool d35_render_tile(uint32_t tile,int32_t offset,uint32_t line,
    uint32_t count,uint8_t *cache,uint16_t *colors,unsigned mode)
{
    if(BG.DirectColourMode || (BG.BitShift!=2 && BG.BitShift!=4)) return false;
    uint8_t *bp=cache+((tile&V_FLIP)?56-line:line);
    int step=(tile&V_FLIP)?-8:8;
    d35_palette_t table;bool ready=false;
    while(count--) {
        ++d35_census[40];
        uint16_t *screen=(uint16_t *)GFX.S+offset;
        uint8_t *depth=(mode?GFX.ZBuffer:GFX.DB)+offset;
        uint8x8_t old_depth=vld1_u8(depth),idx=vld1_u8(bp);
        if(tile&H_FLIP)idx=vrev64_u8(idx);
        uint8x8_t depth_mask=vcgt_u8(vdup_n_u8(GFX.Z1),old_depth);
        uint8x8_t mask=vand_u8(depth_mask,vmvn_u8(vceq_u8(idx,vdup_n_u8(0))));
        uint64_t active=vget_lane_u64(vreinterpret_u64_u8(mask),0);
        if(!vget_lane_u64(vreinterpret_u64_u8(depth_mask),0))++d35_census[43];
        if(!active)++d35_census[41];
        if(active==UINT64_MAX)++d35_census[42];
        if(active) {
            ++d35_hyp[8];++d35_hyp[9];
            if(!ready) { table=d35_cached_palette(colors,BG.BitShift);ready=true; }
            uint8x8x2_t zip=vzip_u8(vtbl2_u8(table.low,idx),vtbl2_u8(table.high,idx));
            uint16x8_t color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));
            if(mode)color=d35_blend(color,vld1_u8(GFX.SubZBuffer+offset),screen+GFX.Delta,GFX.FixedColour,mode,mask);
            d35_store(screen,color,mask);
            vst1_u8(depth,vbsl_u8(mask,vdup_n_u8(GFX.Z2),old_depth));
        }
        bp+=step;offset+=GFX.PPL;
    }
    return true;
}
