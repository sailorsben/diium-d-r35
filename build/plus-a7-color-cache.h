/* Bounded RGB565 materialization of already decoded SNES tiles.
 * One direct-mapped entry per indexed-tile bucket; palette identity and an
 * actual color-write epoch are part of its key. Never cache depth or math.
 * Include in the tile translation unit only. 32 KiB pixel storage. */
#ifndef D35_PLUS_A7_COLOR_CACHE_H
#define D35_PLUS_A7_COLOR_CACHE_H
#define D35_COLOR_CACHE_ENTRIES 256u
struct d35_color_entry {
    const uint8_t *tile;
    const uint16_t *palette;
    uint32_t epoch;
    unsigned bits;
    uint16_t pixels[64];
};
static struct d35_color_entry d35_color_entries[D35_COLOR_CACHE_ENTRIES];
static uint32_t d35_color_epoch=1;
static inline unsigned d35_color_bucket(const uint8_t *tile)
{ return ((uintptr_t)tile>>6)&(D35_COLOR_CACHE_ENTRIES-1); }
void d35_color_tile_changed(const uint8_t *tile)
{ d35_color_entries[d35_color_bucket(tile)].tile=NULL; }
void d35_color_palette_changed(void)
{
    if(!++d35_color_epoch) {
        /* A wrapped epoch must never make a very old entry valid again. */
        for(unsigned i=0;i<D35_COLOR_CACHE_ENTRIES;i++)d35_color_entries[i].tile=NULL;
        d35_color_epoch=1;
    }
}
static inline const uint16_t *d35_color_tile(const uint8_t *tile,
                                            const uint16_t *palette,unsigned bits)
{
    struct d35_color_entry *entry=&d35_color_entries[d35_color_bucket(tile)];
    if(entry->tile!=tile || entry->palette!=palette || entry->epoch!=d35_color_epoch || entry->bits!=bits) {
        d35_palette_t table=d35_palette(palette,bits);
        for(unsigned row=0;row<8;row++) {
            uint8x8_t idx=vld1_u8(tile+row*8);
            uint8x8x2_t zip=vzip_u8(vtbl2_u8(table.low,idx),vtbl2_u8(table.high,idx));
            vst1q_u16(entry->pixels+row*8,vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1])));
        }
        entry->tile=tile;entry->palette=palette;entry->epoch=d35_color_epoch;entry->bits=bits;
    }
    return entry->pixels;
}
#endif
