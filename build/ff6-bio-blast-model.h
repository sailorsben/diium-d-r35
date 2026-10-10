/* Private semantic reconstruction of owner ROM C1/EF34, not a playable port.
 * Original instruction widths, 16-bit stores, 32-entry wrap and stride remain
 * explicit so the model can be compared with execution of the original ROM. */
#ifndef FF6_BIO_BLAST_MODEL_H
#define FF6_BIO_BLAST_MODEL_H
#include <stdint.h>
static uint16_t ff6_ram_word(const uint8_t *ram,unsigned offset)
{ return ram[offset&65535u]|(uint16_t)(ram[(offset+1)&65535u]<<8); }
static void ff6_copy_scroll_wave(const uint8_t *ram,unsigned sine_base,
                                 unsigned phase,uint16_t out[32])
{
    unsigned cursor=(phase*2u)&63u;
    for(unsigned row=0;row<32;row++) {
        out[row]=ff6_ram_word(ram,sine_base+cursor);
        cursor=(cursor+2u)&63u;
    }
}
/* C1/ED86, BG1 portion: vertical first, horizontal second. The apparent
 * frequency parameter passed through DP14 is unused by C1/EF34. It instead
 * advances each axis's phase after copying the 32 samples. */
static void ff6_update_bg1_wave(uint8_t command,uint8_t *ram,
                                const uint16_t sine_bases[8])
{
    if(!(command&4))return;
    for(unsigned axis=0;axis<2;axis++) {
        unsigned vertical=axis==0;
        if(!(command&(vertical?128:64)))continue;
        unsigned amplitude=ram[vertical?0x6096:0x6095];
        unsigned phase_address=vertical?0x6098:0x6097;
        unsigned frequency_address=vertical?0x609a:0x6099;
        unsigned destination=0x63b0+(vertical?2:0);
        uint16_t values[32];
        ff6_copy_scroll_wave(ram,sine_bases[(amplitude&14u)/2],ram[phase_address],values);
        for(unsigned row=0;row<32;row++) {
            unsigned at=destination+row*4;
            ram[at]=(uint8_t)values[row];ram[at+1]=(uint8_t)(values[row]>>8);
        }
        ram[phase_address]=(uint8_t)(ram[phase_address]+ram[frequency_address]);
    }
}
#endif
