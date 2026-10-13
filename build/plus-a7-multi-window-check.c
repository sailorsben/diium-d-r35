/* Independent upstream ComputeClipWindows oracle, including per-layer masks. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "snes9x2005/source/clip.c"
SPPU PPU;
InternalPPU IPPU;
CMemory Memory;
#define D35_WINDOW_IMPLEMENTATION
#include "plus-a7-multi-window.h"
static unsigned char registers[65536];
static unsigned rng=0x87359a2d;
static unsigned random_word(void) { rng=rng*1664525u+1013904223u;return rng; }
static void setup(unsigned mask)
{
    memset(&PPU,0,sizeof(PPU));memset(&IPPU,0,sizeof(IPPU));
    memset(registers,0,sizeof(registers));Memory.FillRAM=registers;
    PPU.BGMode=1;IPPU.RenderThisFrame=true;IPPU.CurrentLine=1;
    for(unsigned i=0;i<3;i++)PPU.ClipWindow2Enable[i]=(mask>>i)&1;
    PPU.ClipWindow2Enable[3]=1;
    registers[0x212c]=registers[0x212d]=7;
    d35_window_reset();
}
static void compare(unsigned mask)
{
    ComputeClipWindows();d35_window_capture(0);assert(d35_window_defer());
    for(unsigned bg=0;bg<3;bg++) for(unsigned sub=0;sub<2;sub++) {
        struct d35_window_clip clip;
        if(!(mask&(1u<<bg))) { assert(!d35_window_fetch(bg,0,sub,&clip));continue; }
        assert(d35_window_fetch(bg,0,sub,&clip));
        for(unsigned x=0;x<256;x++) {
            unsigned original=!IPPU.Clip[sub].Count[bg],captured=0;
            for(unsigned i=0;i<IPPU.Clip[sub].Count[bg];i++)
                original|=x>=IPPU.Clip[sub].Left[i][bg] && x<IPPU.Clip[sub].Right[i][bg];
            for(unsigned i=0;i<clip.count;i++)captured|=x>=clip.left[i] && x<clip.right[i];
            assert(original==captured);
        }
    }
}
int main(void)
{
    unsigned exhaustive=0,multi=0;
    for(unsigned bg=0;bg<3;bg++) {
        unsigned mask=1u<<bg;setup(mask);
        for(unsigned left=0;left<256;left++)for(unsigned right=0;right<256;right++)
        for(unsigned inside=0;inside<2;inside++)for(unsigned screens=0;screens<4;screens++) {
            PPU.Window2Left=left;PPU.Window2Right=right;PPU.ClipWindow2Inside[bg]=inside;
            registers[0x212e]=(screens&1)?mask:0;registers[0x212f]=(screens&2)?mask:0;
            compare(mask);++exhaustive;
        }
    }
    for(unsigned i=0;i<524288;i++) {
        unsigned mask=1+random_word()%7;setup(mask);
        PPU.Window2Left=random_word()>>24;PPU.Window2Right=random_word()>>24;
        for(unsigned bg=0;bg<3;bg++)PPU.ClipWindow2Inside[bg]=(random_word()>>24)&1;
        registers[0x212c]=(random_word()>>24)&7;registers[0x212d]=(random_word()>>24)&7;
        registers[0x212e]=(random_word()>>24)&7;registers[0x212f]=(random_word()>>24)&7;
        compare(mask);++multi;
    }
    /* Window2-disabled rows remain safe even with unrelated Window1 clipping. */
    setup(0);PPU.ClipWindow1Enable[1]=1;registers[0x2130]=0x30;
    PPU.BGMosaic[0]=true;PPU.Mosaic=8;compare(0);
    for(unsigned mask=1;mask<8;mask++) {
        for(unsigned guard=0;guard<7;guard++) {
            setup(mask);unsigned bg=0;while(!(mask&(1u<<bg)))++bg;
            switch(guard) {
                case 0:PPU.BGMode=7;break;
                case 1:PPU.ForcedBlanking=true;break;
                case 2:registers[0x2133]=1;break;
                case 3:PPU.BGMosaic[bg]=true;PPU.Mosaic=2;break;
                case 4:registers[0x2130]=0x10;break;
                case 5:PPU.ClipWindow1Enable[bg]=1;break;
                case 6:PPU.ClipWindow2Enable[4]=1;break;
            }
            d35_window_capture(0);assert(!d35_window_defer());
        }
        setup(mask);PPU.Window2Left=30;PPU.Window2Right=90;d35_window_capture(0);
        struct d35_window_clip old,new;
        unsigned bg=0;while(!(mask&(1u<<bg)))++bg;
        assert(d35_window_fetch(bg,0,0,&old));
        PPU.Window2Left=31;PPU.Window2Right=89;d35_window_capture(1);
        assert(d35_window_fetch(bg,0,0,&new) && !memcmp(&old,&new,sizeof(old)));
        assert(!d35_window_same(0,1));IPPU.CurrentLine=2;assert(d35_window_defer());
        IPPU.CurrentLine=3;assert(!d35_window_defer());d35_window_reset();assert(!d35_window_defer());
        assert(!d35_window_fetch(bg,256,0,&new) && !d35_window_fetch(4,0,0,&new));
    }
    puts("PASS: guarded mode/hires/mosaic/Window1/OBJ/color fallbacks, retained rows, prefix/reset and disabled Window2");
    printf("PASS: %u exhaustive single-layer and %u randomized multi-layer states match original ComputeClipWindows, both screens/all pixels\n",exhaustive,multi);
    return 0;
}
