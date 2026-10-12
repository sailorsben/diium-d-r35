/* Original clipping is the oracle; candidate formulas are not duplicated. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "snes9x2005/source/clip.c"
SPPU PPU;
InternalPPU IPPU;
CMemory Memory;
unsigned long long d35_conf[128],d35_hyp[128];
#define D35_WINDOW_IMPLEMENTATION
#include "confuser-private-v1/bg3-window/core/source/a7_window.h"
static unsigned char registers[65536];
static void eligible(unsigned bg)
{
    memset(&PPU,0,sizeof(PPU));memset(&IPPU,0,sizeof(IPPU));
    memset(registers,0,sizeof(registers));Memory.FillRAM=registers;
    PPU.BGMode=1;PPU.ClipWindow2Enable[bg]=1;IPPU.RenderThisFrame=true;
    IPPU.CurrentLine=1;registers[0x212c]=registers[0x212d]=1u<<bg;
    d35_window_reset();
}
static unsigned visible(unsigned bg,unsigned x,unsigned sub)
{
    ClipData *clip=&IPPU.Clip[sub];
    if(!clip->Count[bg])return 1;
    for(unsigned i=0;i<clip->Count[bg];i++)
        if(x>=clip->Left[i][bg] && x<clip->Right[i][bg])return 1;
    return 0;
}
static unsigned captured(unsigned x,const struct d35_window_clip *clip)
{
    for(unsigned i=0;i<clip->count;i++)
        if(x>=clip->left[i] && x<clip->right[i])return 1;
    return 0;
}
int main(void)
{
    unsigned cases=0;
    struct d35_window_clip clip,saved;
    for(unsigned bg=0;bg<=2;bg+=2) {
        eligible(bg);
        /* Confuser enables BG4 too. It is absent from the Mode1 renderer. */
        PPU.ClipWindow2Enable[3]=1;
        for(unsigned left=0;left<256;left++)for(unsigned right=0;right<256;right++)
        for(unsigned inside=0;inside<2;inside++)for(unsigned masks=0;masks<4;masks++) {
            PPU.Window2Left=left;PPU.Window2Right=right;PPU.ClipWindow2Inside[bg]=inside;
            registers[0x212e]=(masks&1)<<bg;registers[0x212f]=((masks>>1)&1)<<bg;
            ComputeClipWindows();d35_window_capture(0);assert(d35_window_defer());
            for(unsigned sub=0;sub<2;sub++) {
                assert(d35_window_fetch(bg,0,sub,&clip));
                for(unsigned x=0;x<256;x++)assert(visible(bg,x,sub)==captured(x,&clip));
            }
            assert(!d35_window_fetch(bg==0?2:0,0,0,&clip));
            ++cases;
        }
        eligible(bg);registers[0x212e]=1u<<bg;PPU.Window2Left=20;PPU.Window2Right=100;
        d35_window_capture(0);assert(d35_window_fetch(bg,0,0,&saved));
        PPU.Window2Left=30;PPU.Window2Right=90;
        assert(d35_window_fetch(bg,0,0,&clip) && !memcmp(&saved,&clip,sizeof(clip)));
        d35_window_capture(1);assert(!d35_window_same(0,1));IPPU.CurrentLine=2;
        assert(d35_window_defer());IPPU.CurrentLine=3;assert(!d35_window_defer());
        d35_window_reset();assert(!d35_window_fetch(bg,0,0,&clip));assert(!d35_window_defer());
        for(unsigned i=0;i<10;i++) {
            eligible(bg);
            switch(i) {
            case 0:PPU.BGMode=7;break;
            case 1:PPU.ForcedBlanking=true;break;
            case 2:registers[0x2133]=1;break;
            case 3:PPU.BGMosaic[bg]=true;PPU.Mosaic=2;break;
            case 4:registers[0x2130]=0x10;break;
            case 5:PPU.ClipWindow1Enable[bg]=1;break;
            case 6:PPU.ClipWindow2Enable[bg]=0;break;
            case 7:PPU.ClipWindow2Enable[1]=1;break;
            case 8:PPU.ClipWindow2Enable[4]=1;break;
            case 9:PPU.ClipWindow2Enable[5]=1;break;
            }
            d35_window_capture(0);assert(!d35_window_fetch(bg,0,0,&clip));assert(!d35_window_defer());
        }
        eligible(bg);d35_window_capture(0);IPPU.RenderThisFrame=false;assert(!d35_window_defer());
        assert(!d35_window_same(0,256) && !d35_window_fetch(bg,256,0,&clip));
    }
    printf("PASS: %u BG1/BG3 window states match original ComputeClipWindows on both screens, all pixels\n",cases);
    puts("PASS: BG4 Mode1 guard, retained rows, wrong layer, reset, missing rows and unsupported fallbacks");
    return 0;
}
