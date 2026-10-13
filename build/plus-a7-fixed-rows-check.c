/* Independent row-snapshot/control tests: no performance claims. */
#include "fixed-rows-private-v3/core/source/snes9x.h"
#include "fixed-rows-private-v3/core/source/memmap.h"
#include "fixed-rows-private-v3/core/source/ppu.h"
#include "fixed-rows-private-v3/core/source/gfx.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
SPPU PPU;InternalPPU IPPU;CMemory Memory;SGFX GFX;
#define D35_FIXED_ROWS_IMPLEMENTATION
#define D35_FIXED_ROWS_USE
#include "plus-a7-fixed-rows.h"
static unsigned char registers[65536];
static unsigned char brightness[32];
static unsigned rng=0x73594752;
static unsigned next(void){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
static void setup(unsigned pitch)
{
    memset(&PPU,0,sizeof(PPU));memset(&IPPU,0,sizeof(IPPU));
    memset(&GFX,0,sizeof(GFX));memset(registers,0,sizeof(registers));
    Memory.FillRAM=registers;GFX.PPL=pitch;PPU.BGMode=1;IPPU.RenderThisFrame=true;
    IPPU.XB=brightness;
    for(unsigned i=0;i<32;i++)brightness[i]=i;
    d35_fixed_reset();
}
int main(void)
{
    unsigned checks=0;
    for(unsigned pitch=256;pitch<=512;pitch+=256)for(unsigned run=0;run<1024;run++) {
        unsigned expected[256];setup(pitch);
        for(unsigned row=0;row<240;row++) {
            unsigned r=next()&31,g=next()&31,b=next()&31;
            PPU.FixedColourRed=r;PPU.FixedColourGreen=g;PPU.FixedColourBlue=b;
            expected[row]=(r<<11)|(g<<6)|b; /* pinned BUILD_PIXEL leaves bit5 clear */
            d35_fixed_capture(row);IPPU.CurrentLine=row+1;
            assert(d35_fixed_defer());++checks;
        }
        GFX.FixedColour=0x1234;d35_fixed_begin();assert(d35_fixed_active);
        for(unsigned row=0;row<240;row++)for(unsigned x=0;x<256;x+=7) {
            assert(d35_fixed_at_offset(row*pitch+x)==expected[row]);
            d35_fixed_select_offset(row*pitch+x);assert(GFX.FixedColour==expected[row]);++checks;
        }
        /* Clipped bases -1..-7 require StartPixel to identify the visible row.
         * This includes row0, whose negative base cannot index any row array. */
        for(unsigned row=0;row<240;row++)for(unsigned clip=1;clip<8;clip++) {
            int offset=(int)(row*pitch)-(int)clip;
            d35_fixed_select_offset((unsigned)(offset+clip));
            assert(GFX.FixedColour==expected[row]);++checks;
        }
        d35_fixed_end();assert(!d35_fixed_active && GFX.FixedColour==0x1234);
        /* Clearing a no-color-math update must discard pending, preserve global. */
        d35_fixed_capture(239);assert(d35_fixed_defer());
        GFX.FixedColour=0x4321;d35_fixed_end();assert(GFX.FixedColour==0x4321);
        d35_fixed_begin();assert(!d35_fixed_active);d35_fixed_end();
    }
    for(unsigned guard=0;guard<7;guard++) {
        setup(512);
        switch(guard) {
            case 0:PPU.BGMode=7;break;case 1:PPU.ForcedBlanking=true;break;
            case 2:registers[0x2133]=1;break;case 3:PPU.Mosaic=2;break;
            case 4:GFX.PPL=1024;break;case 5:IPPU.RenderThisFrame=false;break;
            case 6:registers[0x2133]=8;break;
        }
        d35_fixed_capture(0);IPPU.CurrentLine=1;assert(!d35_fixed_defer());
    }
    setup(512);d35_fixed_capture(0);IPPU.CurrentLine=2;assert(!d35_fixed_defer());
    setup(512);d35_fixed_capture(1);IPPU.CurrentLine=2;assert(!d35_fixed_defer());
    setup(512);d35_fixed_capture(0);PPU.BGMode=7;d35_fixed_capture(1);
    PPU.BGMode=1;IPPU.CurrentLine=2;assert(!d35_fixed_defer());
    IPPU.PreviousLine=2;d35_fixed_capture(2);IPPU.CurrentLine=3;assert(d35_fixed_defer());
    d35_fixed_reset();assert(!d35_fixed_defer());
    setup(512);d35_fixed_capture(256);IPPU.CurrentLine=257;assert(!d35_fixed_defer());
    printf("PASS: %u independent RGB packing/retained row/offset checks; unsupported modes, gaps, repeats, invalid prefix, reset and non-math clearing\n",checks);
}
