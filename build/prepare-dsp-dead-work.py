"""Skip pure interpolation whose result is provably unused; keep DSP clocks.

Comparable zero-envelope mechanism: Snes9x-Z c3c6710f9efcfec4c2c513baeb602cf17dd7d909.
This adapts the idea to our pinned C DSP and also removes interpolation that
is immediately replaced by noise. No timer, envelope, BRR or register update
is skipped. Separate hypothesis, never a replacement ROM or installed core.
"""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/dsp-dead-work-private-v1'

def patch(core,counted=False):
    p=core/'source/apu_blargg.c';s=p.read_text()
    start=s.index('   output = dsp_interpolate( v );')
    end=s.index('   /* Immediate silence',start)
    s=s[:start]+'''   COUNT_CALL
   if(!v->env) {
      COUNT_SILENT
      output=0;
   } else if(dsp_m.t_non & v->vbit) {
      COUNT_NOISE
      output=(int16_t)(dsp_m.noise*2);
   } else {
      COUNT_INTERPOLATE
      output=dsp_interpolate(v);
   }
   /* Preserve the original envelope scaling and visible DSP intermediates. */
   dsp_m.t_output=(output*v->env)>>11 & ~1;
   v->t_envx_out=(uint8_t)(v->env>>4);

'''+s[end:]
    for key,index in (('CALL',120),('SILENT',121),('NOISE',122),('INTERPOLATE',123)):
        s=s.replace('COUNT_'+key,'++d35_conf[%d];'%index if counted else '')
    if counted:s='extern unsigned long long d35_conf[128];\n'+s
    p.write_text(s,newline='\n')

if __name__=='__main__':
    assert not OUT.exists();OUT.mkdir()
    base=ROOT/'build/ability-regression-private-v1'
    shutil.copytree(base/'core',OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'));patch(OUT/'core')
    shutil.copytree(ROOT/'build/ff6-effect-screen-private-v1/natural/core',OUT/'counted-core',
                    ignore=shutil.ignore_patterns('*.o','*.so'));patch(OUT/'counted-core',True)
    s=(base/'compare.c').read_text().replace('census(ce);hyp(hy);conf(co);flush(fl);',
        'census(ce);hyp(hy);conf(co);flush(fl);\n            printf("DSP %u,%llu,%llu,%llu,%llu\\n",frame,co[120],co[121],co[122],co[123]);')
    (OUT/'compare.c').write_text(s,newline='\n')
    import re
    s=re.sub(r'fixed-rows-private-v[0-9]+',OUT.name,(ROOT/'build/build-fixed-rows.sh').read_text())
    (ROOT/'build/build-dsp-dead-work.sh').write_text(s,newline='\n')
