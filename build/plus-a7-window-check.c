/* Oracle uses the original ComputeClipWindows, not a duplicate window formula. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "snes9x2005/source/clip.c"
SPPU PPU;
InternalPPU IPPU;
CMemory Memory;
#define D35_WINDOW_IMPLEMENTATION
#include "plus-a7-window.h"
static unsigned char registers[65536];
static void eligible(void)
{
    memset(&PPU,0,sizeof(PPU)); memset(&IPPU,0,sizeof(IPPU));
    memset(registers,0,sizeof(registers)); Memory.FillRAM=registers;
    PPU.BGMode=1; PPU.ClipWindow2Enable[0]=1; IPPU.RenderThisFrame=true;
    IPPU.CurrentLine=1; registers[0x212c]=registers[0x212d]=1;
    d35_window_reset();
}
static unsigned visible(unsigned x,unsigned sub)
{
    unsigned i; ClipData *clip=&IPPU.Clip[sub];
    if(!clip->Count[0]) return 1;
    for(i=0;i<clip->Count[0];i++)
        if(x>=clip->Left[i][0] && x<clip->Right[i][0]) return 1;
    return 0;
}
static unsigned captured_visible(unsigned x,const struct d35_window_clip *clip)
{
    unsigned i;
    for(i=0;i<clip->count;i++)
        if(x>=clip->left[i] && x<clip->right[i]) return 1;
    return 0;
}
int main(void)
{
    unsigned left,right,inside,masks,sub,x,cases=0,i;
    struct d35_window_clip clip,saved;
    eligible();
    for(left=0;left<256;left++) for(right=0;right<256;right++)
    for(inside=0;inside<2;inside++) for(masks=0;masks<4;masks++) {
        PPU.Window2Left=left; PPU.Window2Right=right; PPU.ClipWindow2Inside[0]=inside;
        registers[0x212e]=masks&1; registers[0x212f]=(masks>>1)&1;
        ComputeClipWindows(); d35_window_capture(0); assert(d35_window_defer());
        for(sub=0;sub<2;sub++) {
            assert(d35_window_fetch(0,sub,&clip));
            for(x=0;x<256;x++) assert(visible(x,sub)==captured_visible(x,&clip));
        }
        ++cases;
    }
    printf("PASS: %u window states, both screens and every pixel match original ComputeClipWindows\n",cases);
    eligible(); registers[0x212e]=1; PPU.Window2Left=20; PPU.Window2Right=100;
    d35_window_capture(0); assert(d35_window_fetch(0,0,&saved));
    PPU.Window2Left=30; PPU.Window2Right=90;
    assert(d35_window_fetch(0,0,&clip) && !memcmp(&saved,&clip,sizeof(clip)));
    d35_window_capture(1); assert(!d35_window_same(0,1));
    IPPU.CurrentLine=2; assert(d35_window_defer());
    IPPU.CurrentLine=3; assert(!d35_window_defer()); /* Missing row forbids deferral. */
    d35_window_reset(); assert(!d35_window_fetch(0,0,&clip) && !d35_window_defer());
    for(i=0;i<12;i++) {
        eligible();
        switch(i) {
        case 0:PPU.BGMode=7;break;
        case 1:PPU.ForcedBlanking=true;break;
        case 2:registers[0x2133]=1;break;
        case 3:PPU.BGMosaic[0]=true;PPU.Mosaic=2;break;
        case 4:registers[0x2130]=0x10;break;
        case 5:PPU.ClipWindow1Enable[0]=1;break;
        case 6:PPU.ClipWindow2Enable[0]=0;break;
        default:PPU.ClipWindow2Enable[i-6]=1;break;
        }
        d35_window_capture(0); assert(!d35_window_fetch(0,0,&clip) && !d35_window_defer());
    }
    eligible(); d35_window_capture(0); IPPU.RenderThisFrame=false; assert(!d35_window_defer());
    assert(!d35_window_same(0,256) && !d35_window_fetch(256,0,&clip));
    puts("PASS: retained row ownership, frame reset, missing rows and fallback guards");
    return 0;
}
