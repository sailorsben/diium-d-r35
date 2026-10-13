/* Independent pinned scalar arithmetic, cache invalidations and guard pages. */
#include "ability3-private-v1/core/source/gfx.h"
#include "ability3-private-v1/core/source/ppu.h"
#include "ability3-private-v1/core/source/a7_tile.h"
#include "ability3-private-v1/core/source/a7_color_cache.h"
#include "ability3-private-v1/core/source/a7_math_palette.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>
SGFX GFX;
InternalPPU IPPU;
static uint32_t seed=0x73594752;
static uint32_t next(void) { seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed; }
static uint16_t scalar(uint16_t a,uint16_t b,unsigned mode) {
    if(mode==1)return COLOR_ADD(a,b);
    if(mode==3)return COLOR_SUB(a,b);
    if(mode==5)return COLOR_ADD1_2(a,b);
    return COLOR_SUB1_2(a,b);
}
static void check(const uint16_t *palette,unsigned bits,uint16_t fixed,unsigned mode) {
    d35_palette_t table=d35_cached_math_palette(palette,bits,fixed,mode);
    for(unsigned bank=0;bank<(bits==4?2:1);bank++) {
        uint8_t indices[8];uint16_t result[8];
        for(unsigned j=0;j<8;j++)indices[j]=(bank*8+j)&((1u<<bits)-1);
        uint8x8_t ix=vld1_u8(indices);
        uint8x8x2_t zip=vzip_u8(vtbl2_u8(table.low,ix),vtbl2_u8(table.high,ix));
        vst1q_u16(result,vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1])));
        for(unsigned j=0;j<8;j++)assert(result[j]==scalar(palette[indices[j]],fixed,mode));
    }
}
int main(void) {
    GFX.ZERO=calloc(65536,2);assert(GFX.ZERO);
    for(unsigned i=0;i<65536;i++) {
        unsigned r=i>>11,g=(i>>5)&63,b=i&31;
        GFX.ZERO[i]=BUILD_PIXEL2((r&16)?r&15:0,(g&32)?g&31:0,(b&16)?b&15:0);
    }
    unsigned operations[]={1,3,5,6};
    for(unsigned i=0;i<65536;i++)for(unsigned bits=2;bits<=4;bits+=2) {
        unsigned offset=bits==2?(i%64)*4:(i%16)*16;
        uint16_t *p=IPPU.ScreenColors+offset;
        for(unsigned j=0;j<(1u<<bits);j++)p[j]=j?next():i;
        d35_color_palette_changed();
        for(unsigned m=0;m<4;m++) {
            uint16_t fixed=i<16384?0:i<32768?65535:i<49152?0x821:next();
            check(p,bits,fixed,operations[m]);check(p,bits,fixed,operations[m]);
            check(p,bits,fixed^0xffff,operations[m]);
            p[0]^=0xffff;d35_color_palette_changed();check(p,bits,fixed,operations[m]);
        }
    }
    /* Force epoch1 tags to survive until UINT_MAX wraps, then require reset. */
    d35_math_palette_reset();d35_palette_epoch=1;
    check(IPPU.ScreenColors,2,123,1);
    IPPU.ScreenColors[0]^=0xffff;d35_palette_epoch=UINT32_MAX;
    d35_color_palette_changed();assert(d35_palette_epoch==1);
    check(IPPU.ScreenColors,2,123,1);
    size_t page=sysconf(_SC_PAGESIZE);
    uint8_t *memory=mmap(NULL,page*2,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    assert(memory!=MAP_FAILED && !mprotect(memory+page,page,PROT_NONE));
    for(unsigned bits=2;bits<=4;bits+=2) {
        uint16_t *p=(uint16_t *)(memory+page-(1u<<bits)*2);
        for(unsigned j=0;j<(1u<<bits);j++)p[j]=next();
        for(unsigned m=0;m<4;m++)check(p,bits,0xffff,operations[m]);
    }
    assert(!munmap(memory,page*2));free(GFX.ZERO);
    puts("PASS: 2097152 palette checks against pinned scalar math; mode/fixed/palette/epoch keys, wrap and 2/4bpp guard pages");
}
