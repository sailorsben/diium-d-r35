/* Analysis-only hooks. Calls run the real ROM; the independent C model checks
 * its resulting wave tables. Traces are work/behavior evidence, not timing. */
#include "source/bio-blast-model.h"
static unsigned cause_frame,cause_wave_checks,cause_wave_bad;
static unsigned cause_writes[64],cause_changes[64],cause_flush[64],cause_calls[6];
static unsigned cause_pending,cause_destination;
static uint16_t cause_expected[32];
void d35_cause_begin(void)
{
    ++cause_frame;
    memset(cause_writes,0,sizeof(cause_writes));memset(cause_changes,0,sizeof(cause_changes));
    memset(cause_flush,0,sizeof(cause_flush));memset(cause_calls,0,sizeof(cause_calls));
}
void d35_cause_pc(unsigned pc)
{
    static const unsigned entries[6]={0xc1ed86,0xc1ee9c,0xc1efa3,0xc1ef34,0xc1f088,0xc103fb};
    if(cause_frame<200 || cause_frame>500)return;
    for(unsigned i=0;i<6;i++)if(pc==entries[i])++cause_calls[i];
    if(pc==0xc1ef34) {
        unsigned dp=ICPU.Registers.D.W;
        unsigned amplitude=Memory.RAM[(dp+0x24)&65535u];
        unsigned phase=Memory.RAM[(dp+0x16)&65535u];
        unsigned table=Memory.ROM[0x1ef24+(amplitude&14u)]|
            (unsigned)(Memory.ROM[0x1ef25+(amplitude&14u)]<<8);
        cause_destination=ff6_ram_word(Memory.RAM,dp+0x10);
        ff6_copy_scroll_wave(Memory.RAM,table,phase,cause_expected);
        cause_pending=1;
        if(cause_frame>=260 && cause_frame<=445)
            printf("WAVE frame=%u amp=%u phase=%u frequency=%u dst=%04x sine=%04x db=%02x dp=%04x\n",
                cause_frame,amplitude,phase,Memory.RAM[(dp+0x14)&65535u],cause_destination,
                table,ICPU.Registers.DB,dp);
    }
    if(pc==0xc1ef69 && cause_pending) {
        unsigned bad=0;
        for(unsigned i=0;i<32;i++)
            if(ff6_ram_word(Memory.RAM,cause_destination+4*i)!=cause_expected[i])++bad;
        ++cause_wave_checks;cause_wave_bad+=bad;cause_pending=0;
    }
}
void d35_cause_ppu(unsigned address,unsigned byte)
{
    if(address<0x2100 || address>=0x2140)return;
    ++cause_writes[address-0x2100];
    if(Memory.FillRAM[address]!=byte)++cause_changes[address-0x2100];
}
void d35_cause_flush(unsigned address)
{
    if(address>=0x2100 && address<0x2140 && IPPU.PreviousLine!=IPPU.CurrentLine)
        ++cause_flush[address-0x2100];
}
void d35_cause_end(void)
{
    if(cause_frame<200 || cause_frame>500)return;
    printf("CAUSE frame=%u wave_checks=%u wave_bad=%u calls=",cause_frame,cause_wave_checks,cause_wave_bad);
    for(unsigned i=0;i<6;i++)printf("%s%u",i?",":"",cause_calls[i]);
    printf(" bg1_hdma=%u window=%02x,%02x,%02x main=%02x sub=%02x math=%02x\n",
        Memory.RAM[0x800c]&127u,Memory.FillRAM[0x2123],Memory.FillRAM[0x2124],Memory.FillRAM[0x2125],
        Memory.FillRAM[0x212c],Memory.FillRAM[0x212d],Memory.FillRAM[0x2131]);
    for(unsigned i=0;i<64;i++)if(cause_writes[i] || cause_flush[i])
        printf("REG frame=%u address=%04x writes=%u byte_changes=%u rendered_flushes=%u\n",
            cause_frame,0x2100+i,cause_writes[i],cause_changes[i],cause_flush[i]);
}
