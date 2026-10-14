"""Create isolated offline Meteor/Quasar row-shape census; never access card."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/partial-merge-private-v1'
def main():
 assert not OUT.exists();OUT.mkdir()
 shutil.copytree(ROOT/'build/common-band-private-v3/counted-core',OUT/'profile-core',ignore=shutil.ignore_patterns('*.o','*.so'))
 core=OUT/'profile-core';shutil.copy2(ROOT/'build/partial-merge-census.h',core/'source/a7_partial_merge.h')
 p=core/'source/gfx.c';s=p.read_text();anchor='#include "a7_pearl_work.h"';assert s.count(anchor)==1;s=s.replace(anchor,anchor+'\n#define D35_PARTIAL_IMPLEMENTATION\n#include "a7_partial_merge.h"');p.write_text(s,newline='\n')
 p=core/'source/a7_common_batch.h';s=p.read_text();s=s.replace('#include "a7_partial_merge.h"','');s=s.replace('  d35_pearl_row(mode,mask,old,dm);','  d35_pearl_row(mode,mask,old,dm);\n  d35_partial_observe(mode,idx,old,mask,dm);');s=s.replace('  if(active==UINT64_MAX)', '  d35_partial_colors(mode,mask,color,out,(unsigned)offset);\n  if(active==UINT64_MAX)');p.write_text(s,newline='\n')
 p=core/'link.T';s=p.read_text().replace('global:','global: d35_partial_read;');p.write_text(s,newline='\n')
 p=OUT/'compare.c';s=(ROOT/'build/common-band-private-v3/compare.c').read_text();s=s.replace('    unsigned char *a=malloc(size)', '    void (*partial)(unsigned long long *);*(void **)(&partial)=dlsym(candidate.handle,"d35_partial_read");assert(partial);\n    unsigned long long pm[3808];partial(pm);\n    unsigned first=lab_number(getenv("D35_MERGE_FIRST"),10),last=lab_number(getenv("D35_MERGE_LAST"),10);\n    unsigned char *a=malloc(size)');s=s.replace('        pearl(pc);printf(', '        partial(pm);if(frame>=first&&frame<=last){printf("MERGE %u",frame);for(unsigned j=0;j<3808;j++)printf(",%llu",pm[j]);puts("");}\n        pearl(pc);printf(');p.write_text(s,newline='\n')
 script=(ROOT/'build/build-common-band.sh').read_text();a=script.index('if [ ! -e');b=script.index("libs=",a);script=script[:a]+script[b:];a=script.index('arm-linux-gnueabihf-gcc $flags');b=script.index('(cd "$out/counted-core"',a);script=script[:a]+script[b:];script=script.replace('common-band-private-v3','partial-merge-private-v1').replace('counted-core','profile-core').replace('census-compare','profile-compare');(ROOT/'build/build-partial-merge.sh').write_text(script,newline='\n')
 print('Prepared isolated partial-row census, no card access')
if __name__=='__main__':main()
