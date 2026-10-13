"""Owned seam fixtures; original renderer is the early-depth oracle."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/pearl-paths-private-v1'
def main():
 s=(ROOT/'build/plus-a7-fixed-clipping-check.c').read_text()
 s=s.replace('fixed-rows-private-v3/core/source/','pearl-paths-private-v1/both/core/source/')
 anchor='int main(void)'
 wrappers='''
#ifdef D35_CLIPPING_CANDIDATE
#define FULL_WRAPPER(name) static void full_##name(uint32_t t,int32_t o,uint32_t s,uint32_t w,uint32_t l,uint32_t n){if(s==0&&w==8)name(t,o,l,n);else clipped_##name(t,o,s,w,l,n);}
'''
 names=['DrawTile16','DrawTile16Add','DrawTile16Add1_2','DrawTile16Sub','DrawTile16Sub1_2','DrawTile16FixedAdd1_2','DrawTile16FixedSub1_2']
 for n in names:
  clipped=n.replace('DrawTile','DrawClippedTile')
  wrappers+=f'#define clipped_{n} {clipped}\nFULL_WRAPPER({n})\n'
 wrappers+='#endif\n'
 s=s.replace(anchor,wrappers+anchor)
 start=s.index('    clipped_fn draw[]=');end=s.index(';',start)+1
 old=s[start:end]
 s=s[:start]+'#ifdef D35_CLIPPING_CANDIDATE\n    clipped_fn draw[]={'+','.join('full_'+n for n in names)+'};\n#else\n'+old+'\n#endif'+s[end:]
 s=s.replace('for(unsigned bits=2;', 'for(unsigned cover=0;cover<4;cover++)for(unsigned bits=2;')
 s=s.replace('i<SPAN?i%33:i%4','i<SPAN?(cover==0?i%33:cover==1?30:cover==2?31:0):i%4')
 (OUT/'tile-check.c').write_text(s,newline='\n')
 sh=(ROOT/'build/check-fixed-clipping.sh').read_text().replace('"$(dirname "$0")/.."','"$(dirname "$0")/../.."').replace('out=build/fixed-rows-private-v3','out=build/pearl-paths-private-v1').replace('build/plus-a7-fixed-clipping-check.c','"$out/tile-check.c"')
 sh+='''arm-linux-gnueabihf-gcc $flags -std=gnu99 -O3 -Wall -Wextra -Werror -Wno-misleading-indentation -no-pie -nostdlib -Ibuild /usr/arm-linux-gnueabihf/lib/crt1.o build/pearl-flat-check.c $libs -o "$out/flat-check"
LD_LIBRARY_PATH=build/sysroot/lib qemu-arm -cpu cortex-a7 -L build/sysroot "$out/flat-check" > "$out/flat-check.log" 2>&1
'''
 (OUT/'check.sh').write_text(sh,newline='\n')
 subprocess.run(['sh',str(OUT/'check.sh')],cwd=ROOT,check=True)
 print((OUT/'clipping-exact.log').read_text().strip())
 print((OUT/'clipping-candidate.log').read_text().strip())
 print((OUT/'flat-check.log').read_text().strip())
def subcheck():
 out=ROOT/'build/pearl-sub-private-v2'
 s=(ROOT/'build/plus-a7-fixed-clipping-check.c').read_text().replace('fixed-rows-private-v3/core/source/','pearl-sub-private-v2/sub/core/source/')
 wrappers='''
#ifdef D35_CLIPPING_CANDIDATE
#include "pearl-sub2.h"
static void sole(uint32_t t,int32_t o,uint32_t s,uint32_t w,uint32_t l,uint32_t n){
 if(s==0&&w==8){struct d35_sub2_context c={0};assert(d35_sub2(&c,t,o,l,n));}
 else DrawClippedTile16(t,o,s,w,l,n);
}
#endif
'''
 s=s.replace('int main(void)',wrappers+'int main(void)')
 start=s.index('    clipped_fn draw[]=');end=s.index(';',start)+1
 s=s[:start]+'#ifdef D35_CLIPPING_CANDIDATE\n    clipped_fn draw[]={sole};\n#else\n    clipped_fn draw[]={DrawClippedTile16};\n#endif'+s[end:]
 s=s.replace('for(unsigned bits=2;bits<=4;bits+=2)','for(unsigned blank=0;blank<2;blank++)for(unsigned bits=2;bits<=2;bits+=2)')
 s=s.replace('mode<7','mode<1').replace('cached[0]=1','cached[0]=blank?BLANK_TILE:1')
 s=s.replace('GFX.S=GFX.Screen;','GFX.S=GFX.SubScreen;').replace('GFX.DB=GFX.ZBuffer;','GFX.DB=GFX.SubZBuffer;')
 (out/'sub-check.c').write_text(s,newline='\n')
 sh=(ROOT/'build/check-fixed-clipping.sh').read_text().replace('"$(dirname "$0")/.."','"$(dirname "$0")/../.."').replace('out=build/fixed-rows-private-v3','out=build/pearl-sub-private-v2').replace('build/plus-a7-fixed-clipping-check.c','"$out/sub-check.c"')
 (out/'check.sh').write_text(sh,newline='\n')
 subprocess.run(['sh',str(out/'check.sh')],cwd=ROOT,check=True)
 print((out/'clipping-exact.log').read_text().strip());print((out/'clipping-candidate.log').read_text().strip())
if __name__=='__main__':
 assert len(sys.argv)==1 or sys.argv[1:]==['sub']
 if len(sys.argv)>1:subcheck()
 else:main()
