/* Actual original scalar tile functions versus the captured-row integration.
 * The original draws one row per flush; candidate draws eight captured rows.
 * No ROM, owned fixtures only. Compare pixels/depth/canaries via CRC receipts.
 */
#include "ability-regression-private-v1/core/source/snes9x.h"
#include "ability-regression-private-v1/core/source/memmap.h"
#include "ability-regression-private-v1/core/source/ppu.h"
#include "ability-regression-private-v1/core/source/gfx.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>
SPPU PPU;InternalPPU IPPU;CMemory Memory;SGFX GFX;SBG BG;
uint16_t DirectColourMaps[8][256];
uint32_t HeadMask[4]={0xffffffff,0xffffff00,0xffff0000,0xff000000};
uint32_t TailMask[5]={0,0x000000ff,0x0000ffff,0x00ffffff,0xffffffff};
uint32_t odd_high[4][16],odd_low[4][16],even_high[4][16],even_low[4][16];
void S9xBuildDirectColourMaps(void){abort();} /* Outside the indexed fixture. */
#ifdef D35_CLIPPING_CANDIDATE
#define D35_PLUS_A7
#define D35_FIXED_ROWS_USE
#define D35_FIXED_ROWS_IMPLEMENTATION
#ifdef D35_CLIPPING_OLD_CANDIDATE
#include "fixed-rows-private-v2/core/source/a7_fixed.h"
#include "fixed-rows-private-v2/core/source/tile.c"
#else
#include "fixed-rows-private-v3/core/source/a7_fixed.h"
#include "fixed-rows-private-v3/core/source/tile.c"
#endif
#else
#include "ability-regression-private-v1/core/source/tile.c"
#endif
#define SPAN (512*16+32)
static uint16_t screen[2*SPAN],zero[65536];
static uint8_t depth[2*SPAN],cache[64],cached[1],registers[65536],brightness[32];
static uint16_t fixed[240];
typedef void (*clipped_fn)(uint32_t,int32_t,uint32_t,uint32_t,uint32_t,uint32_t);
int main(void)
{
    clipped_fn draw[]={DrawClippedTile16,DrawClippedTile16Add,DrawClippedTile16Add1_2,
        DrawClippedTile16Sub,DrawClippedTile16Sub1_2,DrawClippedTile16FixedAdd1_2,DrawClippedTile16FixedSub1_2};
    for(unsigned i=0;i<65536;i++) {
        unsigned r=i>>11,g=(i>>5)&63,b=i&31;
        zero[i]=BUILD_PIXEL2((r&16)?r&15:0,(g&32)?g&31:0,(b&16)?b&15:0);
    }
    unsigned tests=0;
    for(unsigned bits=2;bits<=4;bits+=2)for(unsigned pitch=256;pitch<=512;pitch+=256)
    for(unsigned mode=0;mode<7;mode++)for(unsigned flip=0;flip<4;flip++)
    for(unsigned first=0;first<2;first++)for(unsigned left=0;left<2;left++)
    for(unsigned start=0;start<8;start++)for(unsigned width=1;width<=8-start;width++) {
        memset(&GFX,0,sizeof(GFX));memset(&BG,0,sizeof(BG));
        memset(&PPU,0,sizeof(PPU));memset(&IPPU,0,sizeof(IPPU));
        Memory.FillRAM=registers;PPU.BGMode=1;IPPU.RenderThisFrame=true;IPPU.XB=brightness;
        GFX.PPL=pitch;GFX.PPLx2=pitch*2;GFX.Pitch2=GFX.Pitch=pitch*2;GFX.ZPitch=pitch;
        GFX.Screen=(uint8_t *)(screen+16);GFX.SubScreen=(uint8_t *)(screen+SPAN+16);
        GFX.S=GFX.Screen;GFX.Delta=SPAN;GFX.ZBuffer=depth+16;GFX.SubZBuffer=depth+SPAN+16;
        GFX.DB=GFX.ZBuffer;GFX.ZERO=zero;GFX.Z1=30;GFX.Z2=29;
        for(unsigned i=0;i<2*SPAN;i++){screen[i]=(i*2719+mode*137)&65535;depth[i]=i<SPAN?i%33:i%4;}
        for(unsigned i=0;i<256;i++)IPPU.ScreenColors[i]=(i*521+7)&65535;
        for(unsigned i=0;i<64;i++)cache[i]=(i*13+i/8+mode)&((1u<<bits)-1);
        BG.BitShift=bits;BG.TileShift=bits==2?4:5;BG.PaletteMask=7;BG.PaletteShift=bits;
        BG.Buffer=cache;BG.Buffered=cached;cached[0]=1;
        for(unsigned i=0;i<32;i++)brightness[i]=i;
#ifdef D35_CLIPPING_CANDIDATE
        d35_fixed_reset();
#endif
        for(unsigned row=0;row<240;row++) {
            unsigned r=(row*7+1)&31,g=(row*11+2)&31,b=(row*13+3)&31;
            fixed[row]=(r<<11)|(g<<6)|b;
            PPU.FixedColourRed=r;PPU.FixedColourGreen=g;PPU.FixedColourBlue=b;
#ifdef D35_CLIPPING_CANDIDATE
            d35_fixed_capture(row);
#endif
        }
        unsigned tile=(flip&1?H_FLIP:0)|(flip&2?V_FLIP:0);
        int offset=(int)(first*pitch)+(left?248:-(int)start);
#ifdef D35_CLIPPING_CANDIDATE
        IPPU.CurrentLine=240;assert(d35_fixed_defer());GFX.FixedColour=fixed[239];
        d35_fixed_begin();draw[mode](tile,offset,start,width,0,8);d35_fixed_end();
#else
        for(unsigned row=0;row<8;row++) {
            GFX.FixedColour=fixed[first+row];
            draw[mode](tile,offset+row*pitch,start,width,row*8,1);
        }
#endif
        unsigned long crc=crc32(0,(const unsigned char *)screen,sizeof(screen));
        crc=crc32(crc,depth,sizeof(depth));printf("%u %08lx\n",tests++,crc);
    }
    fprintf(stderr,"PASS: %u original/candidate clipped tile cases; negative X, first row, right edge, eight distinct colors, all flips/math modes/2-4bpp/256-512 stride\n",tests);
}
