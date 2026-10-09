"""Execute actual CGRAM/brightness invalidation seams against independent colors."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parent
CORE=ROOT/'snes9x2005/source'

def function(text,name,next_name):
    start=text.index(name);end=text.index(next_name,start)
    return text[start:end]
register=function((CORE/'ppu.h').read_text(encoding='utf-8'),
    'static INLINE void REGISTER_2122(', 'static INLINE void REGISTER_2180(')
brightness=function((CORE/'ppu.c').read_text(encoding='utf-8'),
    'void S9xFixColourBrightness()', 'static void S9xSetSuperFX(')
unserialize=(ROOT/'snes9x2005/libretro.c').read_text(encoding='utf-8')
assert 'S9xFixColourBrightness();' in unserialize[unserialize.index('bool retro_unserialize('):]
source=r'''
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include "plus-a7-render.h"
#include "plus-a7-color-cache.h"
#define INLINE inline
#define BUILD_PIXEL(r,g,b) (((r)<<11)|((g)<<6)|((g)>>4<<5)|(b))
static struct { bool CGFLIP; unsigned CGADD,Brightness;uint16_t CGDATA[256]; } PPU;
static struct { bool ColorsChanged;uint8_t Red[256],Green[256],Blue[256];uint16_t ScreenColors[256];uint8_t *XB; } IPPU;
static uint8_t mul_brightness[16][32],tile[64];
static unsigned flushes;static uint16_t flushed_color;
static void flush(void) {
    ++flushes;flushed_color=d35_color_tile(tile,IPPU.ScreenColors,2)[0];
}
#define FLUSH_REDRAW() flush()
'''+register+brightness+r'''
int main(void) {
    unsigned cases=0;
    for(unsigned b=0;b<16;b++)for(unsigned v=0;v<32;v++)mul_brightness[b][v]=v*b/15;
    memset(tile,1,sizeof(tile));PPU.CGADD=1;PPU.Brightness=15;S9xFixColourBrightness();
    for(unsigned i=0;i<65536;i++) {
        uint16_t before=IPPU.ScreenColors[1];PPU.CGADD=1;PPU.CGFLIP=false;flushes=0;
        const uint16_t *rgb=d35_color_tile(tile,IPPU.ScreenColors,2);assert(rgb[0]==before);
        unsigned old=PPU.CGDATA[1];REGISTER_2122(i&255);
        assert(flushes==((old&255)!=(i&255)));
        if(flushes)assert(flushed_color==before);
        unsigned value=PPU.CGDATA[1],r=IPPU.XB[value&31],g=IPPU.XB[(value>>5)&31],b=IPPU.XB[(value>>10)&31];
        uint16_t expected=BUILD_PIXEL(r,g,b);rgb=d35_color_tile(tile,IPPU.ScreenColors,2);assert(rgb[0]==expected);
        before=expected;flushes=0;REGISTER_2122(i>>8);
        assert(flushes==(((i>>8)&127)!=(value>>8)));
        if(flushes)assert(flushed_color==before);
        value=i&32767;r=IPPU.XB[value&31];g=IPPU.XB[(value>>5)&31];b=IPPU.XB[(value>>10)&31];
        expected=BUILD_PIXEL(r,g,b);rgb=d35_color_tile(tile,IPPU.ScreenColors,2);assert(rgb[0]==expected);cases+=2;
        if(!(i%127)) {
            PPU.Brightness=(i/127)%16;S9xFixColourBrightness();
            r=(value&31)*PPU.Brightness/15;g=((value>>5)&31)*PPU.Brightness/15;b=((value>>10)&31)*PPU.Brightness/15;
            expected=BUILD_PIXEL(r,g,b);assert(d35_color_tile(tile,IPPU.ScreenColors,2)[0]==expected);
        }
    }
    printf("PASS: %u actual CGRAM half-write cases flush old palette before mutation and invalidate cached RGB; brightness/load rebuild invalidation retained\n",cases);
    return 0;
}
'''
out=ROOT/'plus-a7-out';(out/'color-cache-contract.c').write_text(source,encoding='utf-8',newline='\n')
flags=['-DD35_PLUS_A7','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm',
 '-O2','-std=gnu99','-Wall','-Wextra','-Werror','-no-pie','-nostdlib','-I.',
 '/usr/arm-linux-gnueabihf/lib/crt1.o','plus-a7-out/color-cache-contract.c','-L./sysroot/lib',
 '-Wl,--no-as-needed','-l:libc-2.30.so','-l:libgcc_s.so.1','-o','plus-a7-out/color-cache-contract']
subprocess.run(['arm-linux-gnueabihf-gcc',*flags],cwd=ROOT,check=True)
result=subprocess.check_output(['qemu-arm','-cpu','cortex-a7','-L','./sysroot','-E','LD_LIBRARY_PATH=./sysroot/lib',
 'plus-a7-out/color-cache-contract'],cwd=ROOT)
(out/'color-cache-contract.log').write_bytes(result);print(result.decode(),end='')
