"""Refine observer counters only; preserve qualified ordinary fusion binary."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fused-count-private-v2'
def main():
 assert not OUT.exists();OUT.mkdir();core=OUT/'core';shutil.copytree(ROOT/'build/fused-toolbox-private-v1/counted-core',core,ignore=shutil.ignore_patterns('*.o','*.so'))
 p=core/'source/a7_common_batch.h';s=p.read_text();assert s.count('old=vld1_u8(zbuffer+offset);dm=vcgt_u8(zv,old);FT(5);')==2
 needle='old=vld1_u8(zbuffer+offset);dm=vcgt_u8(zv,old);FT(5);';s=s.replace(needle,needle+'if(bits==2)FT(29);else FT(30);');s=s.replace(' if(have_depth)FT(8);else{',' if(have_depth){FA(27,skipped);FT(8);}else{');p.write_text(s,newline='\n')
 p=core/'source/a7_common_band.h';s=p.read_text();s=s.replace('#define FBAND(n) (++d35_fused[n])','#define FBAND(n) (++d35_fused[n])\n#define FCELL (++d35_fused[28])').replace('#define FBAND(n) ((void)0)','#define FBAND(n) ((void)0)\n#define FCELL ((void)0)');s=s.replace(' for(unsigned cell=0;cell<cells;cell++){ \\',' for(unsigned cell=0;cell<cells;cell++){ FCELL; \\');s=s.replace('#undef FBAND','#undef FBAND\n#undef FCELL');p.write_text(s,newline='\n')
 script=(ROOT/'build/build-fused-toolbox.sh').read_text();a=script.index('if [ ! -e');b=script.index("libs=",a);head=script[:a].replace('fused-toolbox-private-v1','fused-count-private-v2');start=script.index('(cd "$out/counted-core"');end=script.index('\narm-linux-gnueabihf-gcc $flags',start);block=script[start:end].replace('counted-core','core').replace('counted-build.log','core-build.log');(ROOT/'build/build-fused-count.sh').write_text(head+block+'\n',newline='\n');print('Prepared extra observer counters only; ordinary fusion unchanged')
if __name__=='__main__':main()
