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
static inline uint8x8x4_t d35_palette(const uint16_t *colors,unsigned bits)
{
    uint8x8x4_t table;
    const uint8_t *p=(const uint8_t *)colors;
    table.val[0]=vld1_u8(p);
    table.val[1]=bits==4?vld1_u8(p+8):vdup_n_u8(0);
    table.val[2]=bits==4?vld1_u8(p+16):vdup_n_u8(0);
    table.val[3]=bits==4?vld1_u8(p+24):vdup_n_u8(0);
    return table;
}
/* Modes: 0 plain, 1 add, 2 add-half, 3 sub, 4 sub-half,
 * 5 fixed-add-half, 6 fixed-sub-half. Caller guarantees eight valid pixels. */
static inline void d35_row(const uint8_t *pixels,uint8x8x4_t table,int flip,
                          uint16_t *screen,uint8_t *depth,const uint8_t *subdepth,
                          const uint16_t *sub,uint8_t z1,uint8_t z2,
                          uint16_t fixed,unsigned mode)
{
    uint8x8_t idx=vld1_u8(pixels),old_depth=vld1_u8(depth),mask;
    uint16x8_t color,old,mask16;
    uint8x8x2_t zip;
    if(flip) idx=vrev64_u8(idx);
    mask=vand_u8(vcgt_u8(vdup_n_u8(z1),old_depth),vmvn_u8(vceq_u8(idx,vdup_n_u8(0))));
    if(!vget_lane_u64(vreinterpret_u64_u8(mask),0)) return;
    idx=vshl_n_u8(idx,1);
    zip=vzip_u8(vtbl4_u8(table,idx),vtbl4_u8(table,vadd_u8(idx,vdup_n_u8(1))));
    color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));
    if(mode) {
        uint8x8_t sd=vld1_u8(subdepth);
        uint16x8_t is_fixed=d35_mask16(vceq_u8(sd,vdup_n_u8(1)));
        uint16x8_t fixed_color=vdupq_n_u16(fixed),result;
        if(mode>=5) {
            result=mode==5?d35_add_half(color,fixed_color):d35_sub_half(color,fixed_color);
            color=vbslq_u16(is_fixed,result,color);
        } else {
            uint16x8_t other=vbslq_u16(is_fixed,fixed_color,vld1q_u16(sub));
            if(mode==1) result=d35_add(color,other);
            else if(mode==3) result=d35_sub(color,other);
            else if(mode==2) result=vbslq_u16(is_fixed,d35_add(color,other),d35_add_half(color,other));
            else result=vbslq_u16(is_fixed,d35_sub(color,other),d35_sub_half(color,other));
            color=vbslq_u16(d35_mask16(vceq_u8(sd,vdup_n_u8(0))),color,result);
        }
    }
    old=vld1q_u16(screen); mask16=d35_mask16(mask);
    vst1q_u16(screen,vbslq_u16(mask16,color,old));
    vst1_u8(depth,vbsl_u8(mask,vdup_n_u8(z2),old_depth));
}
#endif
