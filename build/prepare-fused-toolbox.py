"""Fuse exact rendering tools offline, preserve the staged measurement untouched."""
from pathlib import Path
import shutil,sys
ROOT=Path(__file__).resolve().parent.parent
V2=sys.argv[1:]==['--v2']
assert sys.argv[1:] in ([],['--v2'])
OUT=ROOT/('build/fused-toolbox-private-v2' if V2 else 'build/fused-toolbox-private-v1')
def main():
 assert not OUT.exists();OUT.mkdir()
 src=(ROOT/'build/partial-merge-selective.h').read_text();a=src.index('static inline __attribute__((always_inline)) unsigned d35_batch_tile_mode_base(');b=src.index('static inline __attribute__((always_inline)) unsigned d35_batch_tile_mode_plain(',a);base=src[a:b]
 for label in ('core','counted-core'):
  core=OUT/label;shutil.copytree(ROOT/f'build/common-band-private-v3/{label}',core,ignore=shutil.ignore_patterns('*.o','*.so'))
  (core/'source/a7_common_batch.h').write_text((ROOT/('build/fused-toolbox-v2.h' if V2 else 'build/fused-toolbox.h')).read_text().replace('/* FUSED_BASE */',base),newline='\n');shutil.copy2(ROOT/('build/fused-toolbox-band-v2.h' if V2 else 'build/fused-toolbox-band.h'),core/'source/a7_common_band.h');shutil.copy2(ROOT/'build/partial-merge-kernels.h',core/'source/a7_partial_kernels.h')
  p=core/'source/gfx.c';s=p.read_text();anchor='batch.mode=7;batch.valid=0;';assert s.count(anchor)==1;s=s.replace(anchor,anchor+'batch.depth_policy=0;')
  if label=='counted-core':
   s='#define D35_FUSED_COUNT\n'+s
   anchor='#include "gfx.h"';assert s.count(anchor)==1;s=s.replace(anchor,anchor+'\nunsigned long long d35_fused[32];\n__attribute__((visibility("default"))) void d35_fused_read(unsigned long long *out){memcpy(out,d35_fused,sizeof(d35_fused));memset(d35_fused,0,sizeof(d35_fused));}');p.write_text(s,newline='\n')
   p=core/'link.T';p.write_text(p.read_text().replace('global:','global: d35_fused_read;'),newline='\n')
  else:p.write_text(s,newline='\n')
 shutil.copy2(ROOT/'build/common-band-private-v3/ordinary-compare.c',OUT/'ordinary-compare.c')
 s=(ROOT/'build/common-band-private-v3/compare.c').read_text();anchor='    unsigned char *a=malloc(size)';s=s.replace(anchor,'    void (*fused)(unsigned long long *);*(void **)(&fused)=dlsym(candidate.handle,"d35_fused_read");assert(fused);unsigned long long fu[32];fused(fu);\n'+anchor)
 s=s.replace('        pearl(pc);printf(', '        fused(fu);printf("FUSED %u",frame);for(unsigned j=0;j<32;j++)printf(",%llu",fu[j]);puts("");\n        pearl(pc);printf(');(OUT/'compare.c').write_text(s,newline='\n')
 (ROOT/('build/build-fused-toolbox-v2.sh' if V2 else 'build/build-fused-toolbox.sh')).write_text((ROOT/'build/build-common-band.sh').read_text().replace('common-band-private-v3',OUT.name),newline='\n');print('Prepared fused visibility/palette/store pipeline, ordinary+counted; no card access')
if __name__=='__main__':main()
