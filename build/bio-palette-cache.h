/* Offline candidate: store small NEON palette tables rather than tile RGB rows.
 * Epoch invalidation preserves exact colors. No depth/math/output is cached. */
#ifndef D35_BIO_PALETTE_CACHE_H
#define D35_BIO_PALETTE_CACHE_H
struct d35_palette_entry { const uint16_t *palette; unsigned epoch,bits; d35_palette_t table; };
static struct d35_palette_entry d35_palette_entries[80];
static unsigned d35_palette_epoch=1;
void d35_color_tile_changed(const uint8_t *tile) { (void)tile; }
void d35_color_palette_changed(void)
{
    if(!++d35_palette_epoch) {
        memset(d35_palette_entries,0,sizeof(d35_palette_entries));d35_palette_epoch=1;
    }
}
static inline d35_palette_t d35_cached_palette(const uint16_t *palette,unsigned bits)
{
    uintptr_t address=(uintptr_t)palette,base=(uintptr_t)IPPU.ScreenColors;
    unsigned offset=(unsigned)((address-base)/sizeof(uint16_t));
    if(address<base || offset>=256 || (bits!=2 && bits!=4)) {
        ++d35_hyp[7];return d35_palette(palette,bits);
    }
    unsigned slot=bits==4 ? 64+(offset>>4) : offset>>2;
    struct d35_palette_entry *entry=&d35_palette_entries[slot];
    if(entry->palette!=palette || entry->epoch!=d35_palette_epoch || entry->bits!=bits) {
        ++d35_hyp[7];entry->table=d35_palette(palette,bits);
        entry->palette=palette;entry->epoch=d35_palette_epoch;entry->bits=bits;
    }
    return entry->table;
}
#endif
