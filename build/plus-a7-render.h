/* D-R35 ARMv7 RGB565 kernels. Preserve pinned Plus arithmetic, including its
 * six-bit green storage and intermediate packed half-subtract borrow rules.
 * Copyright 2026 D-R35 contributors; modifications for the Snes9x renderer. */
#ifndef D35_PLUS_A7_RENDER_H
#define D35_PLUS_A7_RENDER_H
#include <arm_neon.h>

static inline uint16x8_t d35_add(uint16x8_t a,uint16x8_t b)
{
    uint16x8_t max=vdupq_n_u16(31);
    uint16x8_t r=vminq_u16(vaddq_u16(vshrq_n_u16(a,11),vshrq_n_u16(b,11)),max);
    uint16x8_t g=vminq_u16(vaddq_u16(vandq_u16(vshrq_n_u16(a,6),max),
                                         vandq_u16(vshrq_n_u16(b,6),max)),max);
    uint16x8_t bl=vminq_u16(vaddq_u16(vandq_u16(a,max),vandq_u16(b,max)),max);
    return vorrq_u16(vorrq_u16(vshlq_n_u16(r,11),vshlq_n_u16(g,6)),
                     vorrq_u16(bl,vshlq_n_u16(vshrq_n_u16(g,4),5)));
}
static inline uint16x8_t d35_sub(uint16x8_t a,uint16x8_t b)
{
    uint16x8_t rb=vdupq_n_u16(31),gm=vdupq_n_u16(63);
    uint16x8_t r=vqsubq_u16(vshrq_n_u16(a,11),vshrq_n_u16(b,11));
    uint16x8_t g=vqsubq_u16(vandq_u16(vshrq_n_u16(a,5),gm),vandq_u16(vshrq_n_u16(b,5),gm));
    uint16x8_t bl=vqsubq_u16(vandq_u16(a,rb),vandq_u16(b,rb));
    g=vorrq_u16(vandq_u16(g,vdupq_n_u16(62)),vshrq_n_u16(g,5));
    return vorrq_u16(vorrq_u16(vshlq_n_u16(r,11),vshlq_n_u16(g,5)),bl);
}
static inline uint16x8_t d35_add_half(uint16x8_t a,uint16x8_t b)
{
    uint16x8_t low=vdupq_n_u16(0x0821);
    return vaddq_u16(vhaddq_u16(vbicq_u16(a,low),vbicq_u16(b,low)),
                     vandq_u16(vandq_u16(a,b),low));
}
static inline uint16x8_t d35_sub_half(uint16x8_t a,uint16x8_t b)
{
    uint16x8_t x=vorrq_u16(a,vdupq_n_u16(0x0820));
    uint16x8_t y=vbicq_u16(b,vdupq_n_u16(0x0821));
    uint16x8_t index=vorrq_u16(vshrq_n_u16(vsubq_u16(x,y),1),
                              vandq_u16(vcgeq_u16(x,y),vdupq_n_u16(0x8000)));
    uint16x8_t r=vandq_u16(index,vdupq_n_u16(0x7800));
    uint16x8_t g=vandq_u16(index,vdupq_n_u16(0x03e0));
    uint16x8_t bl=vandq_u16(index,vdupq_n_u16(0x000f));
    r=vandq_u16(r,vtstq_u16(index,vdupq_n_u16(0x8000)));
    g=vandq_u16(g,vtstq_u16(index,vdupq_n_u16(0x0400)));
    bl=vandq_u16(bl,vtstq_u16(index,vdupq_n_u16(0x0010)));
    return vorrq_u16(vorrq_u16(r,g),bl);
}
static inline uint16x8_t d35_mask16(uint8x8_t mask)
{
    uint8x8x2_t zip=vzip_u8(mask,mask);
    return vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));
}
typedef struct { uint8x8x2_t low,high; } d35_palette_t;
static inline d35_palette_t d35_palette(const uint16_t *colors,unsigned bits)
{
    d35_palette_t table;
    const uint8_t *p=(const uint8_t *)colors;
    if(bits==4) {
        uint8x8x2_t first=vld2_u8(p),second=vld2_u8(p+16);
        table.low.val[0]=first.val[0]; table.low.val[1]=second.val[0];
        table.high.val[0]=first.val[1]; table.high.val[1]=second.val[1];
    } else {
        /* Exactly four colors: never read beyond the final 2bpp palette. */
        uint8x8_t four=vld1_u8(p);
        uint8x8x2_t split=vuzp_u8(four,four);
        table.low.val[0]=split.val[0]; table.high.val[0]=split.val[1];
        table.low.val[1]=table.high.val[1]=vdup_n_u8(0);
    }
    return table;
}
static inline uint16x8_t d35_blend(uint16x8_t color,uint8x8_t sd,
    const uint16_t *sub,uint16_t fixed,unsigned mode,uint8x8_t active)
{
    uint8x8_t fixed_mask=vceq_u8(sd,vdup_n_u8(1));
    uint8x8_t enabled=vand_u8(active,mode>=5?fixed_mask:
                                                    vcgt_u8(sd,vdup_n_u8(0)));
    uint16x8_t fixed_color,result,is_fixed;
    uint64_t enabled_bits=vget_lane_u64(vreinterpret_u64_u8(enabled),0);
    uint64_t active_bits=vget_lane_u64(vreinterpret_u64_u8(active),0);
    uint64_t fixed_bits=vget_lane_u64(vreinterpret_u64_u8(vand_u8(active,fixed_mask)),0);
    if(!enabled_bits) return color;
    fixed_color=vdupq_n_u16(fixed);
    is_fixed=d35_mask16(fixed_mask);
    if(mode>=5) {
        result=mode==5?d35_add_half(color,fixed_color):d35_sub_half(color,fixed_color);
    } else if(fixed_bits==active_bits) {
        /* Fixed-only active lanes need neither a subscreen read nor half math. */
        result=(mode<=2)?d35_add(color,fixed_color):d35_sub(color,fixed_color);
    } else {
        uint16x8_t other=vbslq_u16(is_fixed,fixed_color,vld1q_u16(sub));
        if(mode==1) result=d35_add(color,other);
        else if(mode==3) result=d35_sub(color,other);
        else if(mode==2) {
            result=d35_add_half(color,other);
            if(fixed_bits) result=vbslq_u16(is_fixed,d35_add(color,other),result);
        } else {
            result=d35_sub_half(color,other);
            if(fixed_bits) result=vbslq_u16(is_fixed,d35_sub(color,other),result);
        }
    }
    return vbslq_u16(d35_mask16(enabled),result,color);
}
static inline void d35_store(uint16_t *screen,uint16x8_t color,uint8x8_t mask)
{
    if(vget_lane_u64(vreinterpret_u64_u8(mask),0)==UINT64_MAX) vst1q_u16(screen,color);
    else vst1q_u16(screen,vbslq_u16(d35_mask16(mask),color,vld1q_u16(screen)));
}
/* Modes: 0 plain, 1 add, 2 add-half, 3 sub, 4 sub-half,
 * 5 fixed-add-half, 6 fixed-sub-half. Caller guarantees eight valid pixels. */
static inline void d35_row(const uint8_t *pixels,d35_palette_t table,int flip,
                          uint16_t *screen,uint8_t *depth,const uint8_t *subdepth,
                          const uint16_t *sub,uint8_t z1,uint8_t z2,
                          uint16_t fixed,unsigned mode)
{
    uint8x8_t idx=vld1_u8(pixels),old_depth=vld1_u8(depth),mask;
    uint16x8_t color;
    uint8x8x2_t zip;
    if(flip) idx=vrev64_u8(idx);
    mask=vand_u8(vcgt_u8(vdup_n_u8(z1),old_depth),vmvn_u8(vceq_u8(idx,vdup_n_u8(0))));
    if(!vget_lane_u64(vreinterpret_u64_u8(mask),0)) return;
    zip=vzip_u8(vtbl2_u8(table.low,idx),vtbl2_u8(table.high,idx));
    color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));
    if(mode) color=d35_blend(color,vld1_u8(subdepth),sub,fixed,mode,mask);
    d35_store(screen,color,mask);
    vst1_u8(depth,vbsl_u8(mask,vdup_n_u8(z2),old_depth));
}
/* Process complete eight-pixel spans only; upstream handles the clipped tail.
 * Modes 1..4 are backdrop math, 0 copies sub/fixed, 7 is plain backdrop fill. */
static inline unsigned d35_backdrop(uint16_t *screen,const uint8_t *depth,
    const uint8_t *sd,const uint16_t *sub,unsigned count,uint16_t back,
    uint16_t fixed,unsigned mode)
{
    unsigned used=count&~7u,i;
    uint16x8_t backdrop=vdupq_n_u16(back);
    for(i=0;i<used;i+=8) {
        uint8x8_t mask=vceq_u8(vld1_u8(depth+i),vdup_n_u8(0));
        uint16x8_t color=backdrop;
        if(!vget_lane_u64(vreinterpret_u64_u8(mask),0)) continue;
        if(mode==0) {
            uint8x8_t subdepth=vld1_u8(sd+i);
            color=vbslq_u16(d35_mask16(vcgt_u8(subdepth,vdup_n_u8(1))),vld1q_u16(sub+i),color);
            color=vbslq_u16(d35_mask16(vceq_u8(subdepth,vdup_n_u8(1))),vdupq_n_u16(fixed),color);
        } else if(mode!=7) color=d35_blend(color,vld1_u8(sd+i),sub+i,fixed,mode,mask);
        d35_store(screen+i,color,mask);
    }
    return used;
}
static inline unsigned d35_window(uint16_t *screen,const uint8_t *sd,
    const uint16_t *sub,unsigned count,uint16_t black)
{
    unsigned used=count&~7u,i;
    for(i=0;i<used;i+=8) vst1q_u16(screen+i,vbslq_u16(
        d35_mask16(vcgt_u8(vld1_u8(sd+i),vdup_n_u8(1))),vld1q_u16(sub+i),vdupq_n_u16(black)));
    return used;
}
#endif
