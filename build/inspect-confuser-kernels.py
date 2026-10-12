"""Counter-free compiler sanity check; static instructions are not A7 timing."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/confuser-private-v1/kernel-inspection'
if len(sys.argv)==1:
    assert not OUT.exists();OUT.mkdir()
else:assert sys.argv[1]=='submask' and OUT.is_dir()
base=(ROOT/'build/a7-pair-private-v1/core/source/a7_tile.h').read_text()
anchor='    if(!enabled_bits) return color;'
assert base.count(anchor)==1
fast=base.replace(anchor,anchor+'''
    if(mode==2 && !fixed_bits && enabled_bits==active_bits)
        return d35_add_half(color,vld1q_u16(sub));''')
submask=base.replace('    uint8x8_t fixed_mask=vceq_u8(sd,vdup_n_u8(1));','''    if(mode==2 && !vget_lane_u64(vreinterpret_u64_u8(
        vbic_u8(active,vcgt_u8(sd,vdup_n_u8(1)))),0))
        return d35_add_half(color,vld1q_u16(sub));
    uint8x8_t fixed_mask=vceq_u8(sd,vdup_n_u8(1));''')
variants=[('original',base),('fast',fast)] if len(sys.argv)==1 else [('submask',submask)]
for name,text in variants:
    assert not (OUT/(name+'.s')).exists()
    (OUT/(name+'.h')).write_text(text)
    (OUT/(name+'.c')).write_text('''#include <stdint.h>
#include "'''+name+'''.h"
void kernel(const uint8_t *pixels,d35_palette_t table,int flip,
            uint16_t *screen,uint8_t *depth,const uint8_t *sd,const uint16_t *sub,
            uint8_t z1,uint8_t z2,uint16_t fixed)
{ d35_row(pixels,table,flip,screen,depth,sd,sub,z1,z2,fixed,2); }
''')
    subprocess.run(['arm-linux-gnueabihf-gcc','-S','-O3','-mcpu=cortex-a7','-mfpu=neon-vfpv4',
                    '-mfloat-abi=hard','-marm',str(OUT/(name+'.c')),'-o',str(OUT/(name+'.s'))],check=True)
print('Counter-free original and fast row assembly retained; no time/cycle conversion')
