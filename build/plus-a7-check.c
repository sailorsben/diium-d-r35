/* Independent oracle: actual pinned gfx.h scalar functions/table semantics. */
#include "snes9x2005/source/gfx.h"
#include "plus-a7-render.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
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
    for(bits=2;bits<=4;bits+=2) for(mode=0;mode<=6;mode++) for(flip=0;flip<=1;flip++)
    for(i=0;i<10000;i++) {
        uint16_t palette[16],screen[8],expect[8],sub[8],fixed=(uint16_t)random_word();
        uint8_t pixels[8],depth[8],expected_depth[8],sd[8],z1=random_word(),z2=random_word();
        for(j=0;j<(1u<<bits);j++) palette[j]=(uint16_t)random_word();
        for(j=0;j<8;j++) {
            pixels[j]=random_word()&((1u<<bits)-1); screen[j]=(uint16_t)random_word();
            sub[j]=(uint16_t)random_word(); depth[j]=random_word(); sd[j]=random_word()%4;
        }
        memcpy(expect,screen,sizeof(screen)); memcpy(expected_depth,depth,sizeof(depth));
        for(j=0;j<8;j++) if(pixels[flip?7-j:j] && z1>depth[j]) {
            uint16_t c=palette[pixels[flip?7-j:j]];
            if(mode>=5) { if(sd[j]==1) c=scalar(mode==5?2:4,c,fixed); }
            else if(mode && sd[j]) c=scalar((sd[j]==1 && (mode==2 || mode==4))?mode-1:mode,c,sd[j]==1?fixed:sub[j]);
            expect[j]=c; expected_depth[j]=z2;
        }
        d35_row(pixels,d35_palette(palette,bits),flip,screen,depth,sd,sub,z1,z2,fixed,mode);
        assert(!memcmp(screen,expect,sizeof(screen)) && !memcmp(depth,expected_depth,sizeof(depth)));
    }
    free(GFX.ZERO);
    puts("PASS: 8388608 scalar/vector color comparisons; 280000 tile rows, 2/4bpp, all math modes, flips/transparency/depth");
    return 0;
}
