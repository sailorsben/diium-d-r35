/* Derived fixed-operand palettes. Never cache output, depth or subscreen data.
 * Only active lanes whose subdepth is exactly1 are eligible. Other lanes use
 * the original compositor. RGB565 arithmetic is the pinned Plus NEON kernel. */
#ifndef D35_MATH_PALETTE_H
#define D35_MATH_PALETTE_H
struct d35_math_entry {
    const uint16_t *palette;
    unsigned epoch,bits,mode;
    uint16_t fixed;
    d35_palette_t table;
};
static struct d35_math_entry d35_math_entries[80];
#ifdef D35_MATH_COUNTS
static unsigned long long d35_math_counts[8];
__attribute__((visibility("default"))) void d35_math_read(unsigned long long *out) {
    memcpy(out,d35_math_counts,sizeof(d35_math_counts));
    memset(d35_math_counts,0,sizeof(d35_math_counts));
}
#define D35_MATH_COUNT(n) (++d35_math_counts[n])
#else
#define D35_MATH_COUNT(n) ((void)0)
#endif
static inline uint16x8_t d35_math_color(uint16x8_t color,uint16_t fixed,unsigned mode)
{
    uint16x8_t other=vdupq_n_u16(fixed);
    if(mode==1)return d35_add(color,other);
    if(mode==3)return d35_sub(color,other);
    if(mode==5)return d35_add_half(color,other);
    return d35_sub_half(color,other);
}
static inline d35_palette_t d35_cached_math_palette(const uint16_t *palette,unsigned bits,
                                                  uint16_t fixed,unsigned mode)
{
    uintptr_t address=(uintptr_t)palette,base=(uintptr_t)IPPU.ScreenColors;
    unsigned offset=(unsigned)((address-base)/sizeof(uint16_t));
    struct d35_math_entry *entry=NULL;
    if(address>=base && offset+(1u<<bits)<=256 && (bits==2 || bits==4)) {
        unsigned slot=bits==4?64+(offset>>4):offset>>2;
        entry=&d35_math_entries[slot];
        if(entry->palette==palette && entry->epoch==d35_palette_epoch &&
           entry->bits==bits && entry->fixed==fixed && entry->mode==mode) {
            D35_MATH_COUNT(2);return entry->table;
        }
    }
    D35_MATH_COUNT(3);
    uint16_t colors[16];
    if(bits==2) {
        /* Four input colors, no over-read at the last 2bpp palette. */
        memset(colors,0,sizeof(colors));memcpy(colors,palette,8);
        vst1q_u16(colors,d35_math_color(vld1q_u16(colors),fixed,mode));
    } else {
        vst1q_u16(colors,d35_math_color(vld1q_u16(palette),fixed,mode));
        vst1q_u16(colors+8,d35_math_color(vld1q_u16(palette+8),fixed,mode));
    }
    d35_palette_t table=d35_palette(colors,bits);
    if(entry) {
        entry->table=table;entry->palette=palette;entry->epoch=d35_palette_epoch;
        entry->bits=bits;entry->fixed=fixed;entry->mode=mode;
    }
    return table;
}
static inline void d35_math_palette_reset(void) {
    memset(d35_math_entries,0,sizeof(d35_math_entries));
}
#endif
