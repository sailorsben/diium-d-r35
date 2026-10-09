/* Independent oracle: actual pinned gfx.h scalar functions/table semantics. */
#include "snes9x2005/source/gfx.h"
#include "plus-a7-render.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include "plus-a7-color-cache.h"
SGFX GFX;
static uint32_t seed=0x31415926;
static uint32_t random_word(void) { seed^=seed<<13; seed^=seed>>17; seed^=seed<<5; return seed; }
static uint16_t scalar(unsigned mode,uint16_t a,uint16_t b)
{
    switch(mode) {
    case 1:return COLOR_ADD(a,b);
    case 2:return COLOR_ADD1_2(a,b);
    case 3:return COLOR_SUB(a,b);
    default:return COLOR_SUB1_2(a,b);
    }
}
int main(void)
{
    unsigned i,j,mode,bits,flip;
    uint16_t a[8],b[8],result[8];
    GFX.ZERO=calloc(65536,2); assert(GFX.ZERO);
    for(i=0;i<65536;i++) {
        unsigned r=i>>11,g=(i>>5)&63,bl=i&31;
        GFX.ZERO[i]=BUILD_PIXEL2((r&16)?r&15:0,(g&32)?g&31:0,(bl&16)?bl&15:0);
    }
    for(i=0;i<262144;i++) {
        for(j=0;j<8;j++) { a[j]=(uint16_t)random_word(); b[j]=(uint16_t)random_word(); }
        /* Also cover every input word against edge values. */
        a[0]=(uint16_t)i; b[0]=i<65536?0:i<131072?65535:i<196608?0x821:0xf7de;
        for(mode=1;mode<=4;mode++) {
            uint16x8_t x=vld1q_u16(a),y=vld1q_u16(b),z;
            z=mode==1?d35_add(x,y):mode==2?d35_add_half(x,y):mode==3?d35_sub(x,y):d35_sub_half(x,y);
            vst1q_u16(result,z);
            for(j=0;j<8;j++) if(result[j]!=scalar(mode,a[j],b[j])) {
                printf("FAIL color mode%u %04x %04x got%04x expected%04x\n",mode,a[j],b[j],result[j],scalar(mode,a[j],b[j]));
                return 1;
            }
        }
    }
    /* Independent SNES bitplane definition, not the SIMD implementation. */
    for(bits=2;bits<=8;bits*=2) for(i=0;i<20000;i++) {
        uint8_t planes[64],cache[66],expect[64]; unsigned row,x,plane,any=0;
        for(j=0;j<bits*8;j++) planes[j]=i?random_word():0;
        memset(cache,0xa5,sizeof(cache));
        for(row=0;row<8;row++) for(x=0;x<8;x++) {
            unsigned pixel=0;
            for(plane=0;plane<bits;plane++)
                pixel|=((planes[(plane/2)*16+row*2+plane%2]>>(7-x))&1u)<<plane;
            expect[row*8+x]=(uint8_t)pixel; any|=pixel;
        }
        assert(d35_decode_tile(cache+1,planes,bits)==(any!=0));
        assert(cache[0]==0xa5 && cache[65]==0xa5 && !memcmp(cache+1,expect,64));
    }
    for(bits=2;bits<=4;bits+=2) for(mode=0;mode<=6;mode++) for(flip=0;flip<=1;flip++)
    for(i=0;i<10000;i++) {
        uint16_t palette[16],screen[8],expect[8],sub[8],original_screen[8],fixed=(uint16_t)random_word();
        uint8_t original_depth[8];
        uint8_t pixels[8],depth[8],expected_depth[8],sd[8],z1=random_word(),z2=random_word();
        for(j=0;j<(1u<<bits);j++) palette[j]=(uint16_t)random_word();
        for(j=0;j<8;j++) {
            pixels[j]=random_word()&((1u<<bits)-1); screen[j]=(uint16_t)random_word();
            sub[j]=(uint16_t)random_word(); depth[j]=random_word(); sd[j]=random_word()%4;
        }
        memcpy(expect,screen,sizeof(screen)); memcpy(expected_depth,depth,sizeof(depth));
        memcpy(original_screen,screen,sizeof(screen));memcpy(original_depth,depth,sizeof(depth));
        for(j=0;j<8;j++) if(pixels[flip?7-j:j] && z1>depth[j]) {
            uint16_t c=palette[pixels[flip?7-j:j]];
            if(mode>=5) { if(sd[j]==1) c=scalar(mode==5?2:4,c,fixed); }
            else if(mode && sd[j]) c=scalar((sd[j]==1 && (mode==2 || mode==4))?mode-1:mode,c,sd[j]==1?fixed:sub[j]);
            expect[j]=c; expected_depth[j]=z2;
        }
        d35_row(pixels,d35_palette(palette,bits),flip,screen,depth,sd,sub,z1,z2,fixed,mode);
        assert(!memcmp(screen,expect,sizeof(screen)) && !memcmp(depth,expected_depth,sizeof(depth)));
        uint16_t colored[8];
        for(j=0;j<8;j++)colored[j]=palette[pixels[j]];
        memcpy(screen,original_screen,sizeof(screen));memcpy(depth,original_depth,sizeof(depth));
        d35_row_colored(pixels,colored,flip,screen,depth,sd,sub,z1,z2,fixed,mode);
        assert(!memcmp(screen,expect,sizeof(screen)) && !memcmp(depth,expected_depth,sizeof(depth)));
    }
    /* Span lengths/offsets expose clipping tails; canaries cover both sides. */
    for(mode=0;mode<=7;mode++) if(mode!=5 && mode!=6)
    for(i=0;i<10000;i++) {
        uint16_t screen[48],expect[48],sub[48],back=random_word(),fixed=random_word();
        uint8_t depth[48],sd[48]; unsigned start=random_word()%8,count=random_word()%34,used;
        for(j=0;j<48;j++) { screen[j]=expect[j]=random_word(); sub[j]=random_word(); depth[j]=random_word()%3; sd[j]=random_word()%4; }
        used=count&~7u;
        for(j=start;j<start+used;j++) if(!depth[j]) {
            uint16_t c=back;
            if(mode==0 && sd[j]) c=sd[j]==1?fixed:sub[j];
            else if(mode!=7 && sd[j]) c=scalar(sd[j]==1&&(mode==2||mode==4)?mode-1:mode,c,sd[j]==1?fixed:sub[j]);
            expect[j]=c;
        }
        assert(d35_backdrop(screen+start,depth+start,sd+start,sub+start,count,back,fixed,mode)==used);
        assert(!memcmp(screen,expect,sizeof(screen)));
        for(j=start;j<start+used;j++) expect[j]=sd[j]>1?sub[j]:back;
        assert(d35_window(screen+start,sd+start,sub+start,count,back)==used);
        assert(!memcmp(screen,expect,sizeof(screen)));
    }
    /* Real inaccessible page, not a padded array: the final 2bpp palette is 8 bytes. */
    {
        size_t page=(size_t)sysconf(_SC_PAGESIZE);
        uint8_t *memory=mmap(NULL,page*2,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
        uint16_t *last; uint8_t pixels[8]={1,2,3,1,2,3,1,2},depth[8]={0};
        assert(memory!=MAP_FAILED && !mprotect(memory+page,page,PROT_NONE));
        last=(uint16_t *)(memory+page-8);
        for(j=0;j<4;j++) last[j]=j*123;
        d35_row(pixels,d35_palette(last,2),0,result,depth,NULL,NULL,1,1,0,0);
        for(j=0;j<8;j++) assert(result[j]==last[pixels[j]]);
        assert(!munmap(memory,page*2));
    }
    {
        size_t page=(size_t)sysconf(_SC_PAGESIZE);
        uint8_t *memory=mmap(NULL,page*2,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0),cache[64];
        assert(memory!=MAP_FAILED && !mprotect(memory+page,page,PROT_NONE));
        for(bits=2;bits<=8;bits*=2) {
            memset(memory+page-bits*8,0xff,bits*8);
            assert(d35_decode_tile(cache,memory+page-bits*8,bits));
            for(j=0;j<64;j++) assert(cache[j]==(1u<<bits)-1);
        }
        assert(!munmap(memory,page*2));
    }
    /* Cache keys, colliding VRAM tiles, color writes and epoch wrap. The
     * expected RGB data uses ordinary independent palette indexing. */
    {
        uint8_t tiles[(D35_COLOR_CACHE_ENTRIES+1)*64];uint16_t palettes[2][16];
        for(bits=2;bits<=4;bits+=2)for(i=0;i<20000;i++) {
            uint8_t *tile=tiles+(i%2?D35_COLOR_CACHE_ENTRIES:0)*64;
            for(j=0;j<64;j++)tile[j]=random_word()&((1u<<bits)-1);
            for(j=0;j<16;j++){palettes[0][j]=random_word();palettes[1][j]=random_word();}
            d35_color_tile_changed(tile);d35_color_palette_changed();
            for(unsigned bank=0;bank<2;bank++) {
                const uint16_t *rgb=d35_color_tile(tile,palettes[bank],bits);
                for(j=0;j<64;j++)assert(rgb[j]==palettes[bank][tile[j]]);
                assert(d35_color_tile(tile,palettes[bank],bits)==rgb);
                palettes[bank][tile[0]]^=0xffff;d35_color_palette_changed();
                rgb=d35_color_tile(tile,palettes[bank],bits);
                for(j=0;j<64;j++)assert(rgb[j]==palettes[bank][tile[j]]);
            }
        }
        d35_color_epoch=UINT32_MAX;d35_color_palette_changed();assert(d35_color_epoch==1);
        for(i=0;i<D35_COLOR_CACHE_ENTRIES;i++)assert(!d35_color_entries[i].tile);
    }
    free(GFX.ZERO);
    puts("PASS: 8388608 scalar/vector color comparisons; 280000 tile rows, 2/4bpp, all math modes, flips/transparency/depth");
    puts("PASS: 60000 backdrop/window spans match scalar arithmetic; clipped tails/canaries and palette guard page intact");
    puts("PASS: 60000 planar tiles match independent 2/4/8bpp oracle; blank classification, destination canaries and exact source guard pages");
    puts("PASS: 280000 cached-color rows preserve independent pixel/depth/math/flip oracle; 40000 color-cache cases cover palette changes, tile changes, hash collisions and epoch wrap");
    return 0;
}
