/* Experimental 4bpp color cache. No emulator state or frame skipping. */
#ifndef D35_PLATFORM_LAB_KERNELS_H
#define D35_PLATFORM_LAB_KERNELS_H
#include <stdint.h>
#include <string.h>
#include "plus-a7-render.h"
#define LAB_TILES 1024u
#define LAB_CACHE 128u
struct lab_tile { uint8_t index[64]; uint32_t generation; };
struct lab_palette { uint16_t color[16]; uint32_t generation; };
struct lab_color {
    uint32_t tile, palette, tile_generation, palette_generation;
    uint16_t color[64];
    uint8_t opaque[64];
    int valid;
};
struct lab_cache {
    struct lab_color entry[LAB_CACHE];
    uint64_t hits, misses;
};
/* Keep compositing dynamic: current depth, transparency and flip are applied
 * on every draw. Only immutable derived colors/masks are reused. Production
 * integration additionally needs all VRAM/CGRAM/brightness/state-load hooks. */
static struct lab_color *lab_lookup(struct lab_cache *cache,
    struct lab_tile *tile, unsigned id, struct lab_palette *palette, unsigned pal)
{
    struct lab_color *c=&cache->entry[(id*13u+pal*17u)&(LAB_CACHE-1u)];
    unsigned i;
    if(c->valid && c->tile==id && c->palette==pal &&
       c->tile_generation==tile->generation &&
       c->palette_generation==palette->generation) { ++cache->hits; return c; }
    ++cache->misses;
    c->valid=1; c->tile=id; c->palette=pal;
    c->tile_generation=tile->generation;
    c->palette_generation=palette->generation;
    for(i=0;i<64;++i) {
        c->color[i]=palette->color[tile->index[i]];
        c->opaque[i]=tile->index[i]?255:0;
    }
    return c;
}
static __attribute__((noinline)) void lab_scalar(const struct lab_tile *t,
    const struct lab_palette *p, int flip, uint16_t *screen, uint8_t *depth)
{
    unsigned y,x;
    for(y=0;y<8;++y) for(x=0;x<8;++x) {
        unsigned idx=t->index[y*8+(flip?7-x:x)], pos=y*8+x;
        if(idx && depth[pos]<6) { screen[pos]=p->color[idx]; depth[pos]=5; }
    }
}
static __attribute__((noinline)) void lab_neon(const struct lab_tile *t,
    const struct lab_palette *p, int flip, uint16_t *screen, uint8_t *depth)
{
    d35_palette_t table=d35_palette(p->color,4);
    unsigned y;
    for(y=0;y<8;++y)
        d35_row(t->index+y*8,table,flip,screen+y*8,depth+y*8,NULL,NULL,6,5,0,0);
}
static __attribute__((noinline)) void lab_cached(struct lab_cache *cache,
    struct lab_tile *t,unsigned id,struct lab_palette *p,unsigned pal,
    int flip,uint16_t *screen,uint8_t *depth)
{
    struct lab_color *c=lab_lookup(cache,t,id,p,pal);
    unsigned y;
    for(y=0;y<8;++y) {
        uint8x8_t old=vld1_u8(depth+y*8), opaque=vld1_u8(c->opaque+y*8),mask;
        uint16x8_t color=vld1q_u16(c->color+y*8);
        if(flip) { opaque=vrev64_u8(opaque); color=vrev64q_u16(color);
            color=vcombine_u16(vget_high_u16(color),vget_low_u16(color)); }
        mask=vand_u8(opaque,vcgt_u8(vdup_n_u8(6),old));
        if(!vget_lane_u64(vreinterpret_u64_u8(mask),0)) continue;
        d35_store(screen+y*8,color,mask);
        vst1_u8(depth+y*8,vbsl_u8(mask,vdup_n_u8(5),old));
    }
}
#endif
