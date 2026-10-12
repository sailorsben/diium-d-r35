"""Price population, not QEMU time: separate half-add fast-path experiment."""
from pathlib import Path
import shutil, json, sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/confuser-private-v1'
name=sys.argv[1] if len(sys.argv)>1 else 'bg3-blend'
assert name in ('bg3-blend','bg3-submask')
dest=OUT/name
assert not dest.exists()
shutil.copytree(OUT/'bg3-window/core',dest/'core',ignore=shutil.ignore_patterns('*.o','*.so'))
p=dest/'core/source/a7_tile.h';s='#include "confuser.h"\n'+p.read_text()
anchor='    if(!enabled_bits) return color;'
assert s.count(anchor)==1
if name=='bg3-submask':
    begin='    uint8x8_t fixed_mask=vceq_u8(sd,vdup_n_u8(1));'
    assert s.count(begin)==1
    s=s.replace(begin,'''    if(mode==2) {
        ++d35_conf[96];
        /* Every active lane must use a real subscreen pixel. One zero test
         * replaces separate enabled/fixed 64-bit comparisons on this path. */
        uint8x8_t unsupported=vbic_u8(active,vcgt_u8(sd,vdup_n_u8(1)));
        if(!vget_lane_u64(vreinterpret_u64_u8(unsupported),0)) {
            ++d35_conf[102];return d35_add_half(color,vld1q_u16(sub));
        }
    }
'''+begin)
else:
    s=s.replace(anchor,'''    if(mode==2) {
        ++d35_conf[96];
        if(!enabled_bits)++d35_conf[97];
        if(enabled_bits==active_bits)++d35_conf[98];
        if(fixed_bits==active_bits)++d35_conf[99];
        if(!fixed_bits && enabled_bits==active_bits)++d35_conf[100];
        if(active_bits==UINT64_MAX)++d35_conf[101];
    }
'''+anchor+'''
    /* Only active lanes are stored. When all active lanes use the true
     * subscreen, fixed-color selects and a final enabled select are redundant. */
    if(mode==2 && !fixed_bits && enabled_bits==active_bits) {
        ++d35_conf[102];
        return d35_add_half(color,vld1q_u16(sub));
    }''')
p.write_text(s,newline='\n')
shutil.copy2(OUT/'bg3-window/replay.c',dest/'replay.c')
fields=json.loads((OUT/'fields.json').read_text())
fields.update({str(k):v for k,v in {96:'half_add_rows',97:'half_add_disabled',
 98:'half_add_all_active_enabled',99:'half_add_fixed_only',100:'half_add_true_subscreen',
 101:'half_add_all_pixels_active',102:'half_add_fast_rows'}.items()})
(OUT/'fields.json').write_text(json.dumps(fields,indent=2)+'\n')
print('Prepared independent BG3 plus half-add simplification')
