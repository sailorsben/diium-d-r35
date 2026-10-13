"""Isolate non-half-add true-subscreen shortcuts; never stack unpriced hypotheses."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/subscreen-rows-private-v1'

def patch(core,counted=False):
    p=core/'source/a7_tile.h';s=p.read_text()
    anchor='    uint8x8_t fixed_mask=vceq_u8(sd,vdup_n_u8(1));'
    assert s.count(anchor)==1
    block='''    if(mode==1 || mode==3 || mode==4) {
        uint8x8_t unsupported=vbic_u8(active,vcgt_u8(sd,vdup_n_u8(1)));
        if(!vget_lane_u64(vreinterpret_u64_u8(unsupported),0)) {
            COUNT_FAST
            uint16x8_t other=vld1q_u16(sub);
            return mode==1?d35_add(color,other):mode==3?d35_sub(color,other):d35_sub_half(color,other);
        }
    }
'''.replace('COUNT_FAST','++d35_conf[112+mode];' if counted else '')
    s=s.replace(anchor,block+anchor)
    p.write_text(s,newline='\n')

if __name__=='__main__':
    assert not OUT.exists();OUT.mkdir()
    base=ROOT/'build/ability-regression-private-v1'
    shutil.copytree(base/'core',OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'));patch(OUT/'core')
    shutil.copytree(ROOT/'build/ff6-effect-screen-private-v1/natural/core',OUT/'counted-core',
                    ignore=shutil.ignore_patterns('*.o','*.so'));patch(OUT/'counted-core',True)
    s=(base/'compare.c').read_text().replace('census(ce);hyp(hy);conf(co);flush(fl);',
        'census(ce);hyp(hy);conf(co);flush(fl);\n            printf("SUBSCREEN %u,%llu,%llu,%llu\\n",frame,co[113],co[115],co[116]);')
    (OUT/'compare.c').write_text(s,newline='\n')
    import re
    s=re.sub(r'fixed-rows-private-v[0-9]+',OUT.name,(ROOT/'build/build-fixed-rows.sh').read_text())
    (ROOT/'build/build-subscreen-rows.sh').write_text(s,newline='\n')
    s=(ROOT/'build/plus-a7-check.c').read_text().replace('"plus-a7-render.h"','"subscreen-rows-private-v1/core/source/a7_tile.h"')
    (OUT/'check.c').write_text(s,newline='\n')
