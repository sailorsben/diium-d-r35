"""Extract pinned and actual patched $2132 blocks for an independent ARM test."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parent
CORE=ROOT/'snes9x2005'
PIN=(ROOT/'core-source-commit.txt').read_text().strip()
base=subprocess.check_output(['git','show',PIN+':source/ppu.c'],cwd=CORE).decode()
candidate=(CORE/'source/ppu.c').read_text()
def block(text):
    start=text.index('      case 0x2132:\n');end=text.index('      case 0x2133:',start)
    return text[start:end]
source=r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "plus-a7-raster.h"
struct color { unsigned FixedColourRed,FixedColourGreen,FixedColourBlue; } PPU,observed;
static struct { uint8_t FillRAM[0x2140]; } Memory;
static unsigned flushed;
static void flush(void) { ++flushed; observed=PPU; }
#define FLUSH_REDRAW() flush()
static void stock(uint8_t Byte) { switch(0x2132) {
'''+block(base)+r'''} Memory.FillRAM[0x2132]=Byte; }
static void patched(uint8_t Byte) { switch(0x2132) {
'''+block(candidate)+r'''} Memory.FillRAM[0x2132]=Byte; }
int main(void) {
    unsigned r,g,b,byte,last,trial,count=0,redundant=0,changed=0;
    for(r=0;r<32;r++) for(g=0;g<32;g++) for(b=0;b<32;b++) for(byte=0;byte<256;byte++) {
        struct color before={r,g,b},expected; unsigned old_flush;
        for(trial=0;trial<2;trial++) {
            last=trial?byte:byte^64u;
            PPU=before;Memory.FillRAM[0x2132]=(uint8_t)last;flushed=0;stock((uint8_t)byte);
            expected=PPU;old_flush=flushed;
            PPU=before;Memory.FillRAM[0x2132]=(uint8_t)last;flushed=0;patched((uint8_t)byte);
            /* Expected effect comes from executed stock code, not our predicate. */
            unsigned effect=memcmp(&before,&expected,sizeof(before))!=0;
            if(memcmp(&PPU,&expected,sizeof(PPU)) || Memory.FillRAM[0x2132]!=byte ||
               flushed!=(old_flush&&effect) || (flushed && memcmp(&observed,&before,sizeof(before)))) {
                printf("FAIL r=%u g=%u b=%u byte=%u last=%u\n",r,g,b,byte,last);return 1;
            }
            ++count;redundant+=old_flush&&!effect;changed+=effect;
        }
    }
    printf("PASS: %u extracted stock/patched register cases preserve color, byte latch and flush-before-change; %u redundant invalidations suppressed; %u real changes retained\n",count,redundant,changed);
    return 0;
}
'''
out=ROOT/'plus-a7-out';out.mkdir(exist_ok=True)
(out/'raster-contract.c').write_text(source,encoding='utf-8',newline='\n')
flags=['-DD35_PLUS_A7','-mcpu=cortex-a7','-mfpu=neon-vfpv4','-mfloat-abi=hard','-marm','-fno-stack-protector',
       '-O2','-std=gnu99','-Wall','-Wextra','-Werror','-no-pie','-nostdlib','-I.',
       '/usr/arm-linux-gnueabihf/lib/crt1.o','plus-a7-out/raster-contract.c','-L./sysroot/lib',
       '-Wl,--no-as-needed','-l:libc-2.30.so','-l:libgcc_s.so.1','-o','plus-a7-out/raster-contract']
subprocess.run(['arm-linux-gnueabihf-gcc',*flags],cwd=ROOT,check=True)
result=subprocess.check_output(['qemu-arm','-cpu','cortex-a7','-L','./sysroot','-E','LD_LIBRARY_PATH=./sysroot/lib',
                               'plus-a7-out/raster-contract'],cwd=ROOT)
(out/'raster-contract.log').write_bytes(result)
print(result.decode(),end='')
