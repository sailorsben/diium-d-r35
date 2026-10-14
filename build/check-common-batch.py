"""Actual original scalar tile oracle for all seven common full-tile modes."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/('build/common-band-private-v3' if sys.argv[1:] in (['band3'],['palette']) else 'build/common-band-private-v2' if sys.argv[1:]==['band'] else 'build/common-batch-private-v1')
def main():
 s=(ROOT/'build/plus-a7-fixed-clipping-check.c').read_text().replace('fixed-rows-private-v3/core/source/',OUT.name+'/core/source/')
 wrappers='#ifdef D35_CLIPPING_CANDIDATE\n#include "'+OUT.name+'/core/source/a7_common_batch.h"\n'
 names=['','Add','Add1_2','Sub','Sub1_2','FixedAdd1_2','FixedSub1_2']
 for mode,n in enumerate(names):
  wrappers+=f'''static void batch_{mode}(uint32_t t,int32_t o,uint32_t s,uint32_t w,uint32_t l,uint32_t n){{
 if(s==0&&w==8){{struct d35_batch_context c={{0}};c.mode={mode};assert(d35_batch_tile(&c,t,o,l,n));}}
 else DrawClippedTile16{n}(t,o,s,w,l,n);
}}
'''
 wrappers+='#endif\n';s=s.replace('int main(void)',wrappers+'int main(void)')
 start=s.index('    clipped_fn draw[]=');end=s.index(';',start)+1;old=s[start:end]
 s=s[:start]+'#ifdef D35_CLIPPING_CANDIDATE\n    clipped_fn draw[]={'+','.join('batch_'+str(i) for i in range(7))+'};\n#else\n'+old+'\n#endif'+s[end:]
 s=s.replace('for(unsigned bits=2;','for(unsigned cover=0;cover<4;cover++)for(unsigned blank=0;blank<2;blank++)for(unsigned bits=2;')
 s=s.replace('i<SPAN?i%33:i%4','i<SPAN?(cover==0?i%33:cover==1?30:cover==2?31:0):i%4').replace('cached[0]=1','cached[0]=blank?BLANK_TILE:1')
 s=s.replace('PASS: %u original/candidate clipped tile cases;', 'PASS: %u original/candidate common tile cases; blank states, covered/equal/visible depth;')
 palette=sys.argv[1:]==['palette']
 if palette:
  s=s.replace('#include "'+OUT.name+'/core/source/a7_common_batch.h"','#include "'+OUT.name+'/core/source/a7_common_batch.h"\nstatic struct d35_batch_context palette_context;')
  for mode in range(7):s=s.replace(f'struct d35_batch_context c={{0}};c.mode={mode};assert(d35_batch_tile(&c,t,o,l,n));',f'palette_context.mode={mode};assert(d35_batch_tile(&palette_context,t,o,l,n));')
  s=s.replace('for(unsigned cover=0;','for(unsigned palbase=0;palbase<=128;palbase+=128)for(unsigned cover=0;')
  s=s.replace('left<2','left<1').replace('start<8','start<1').replace('width=1;width<=8-start','width=8;width<=8-start')
  s=s.replace('        BG.BitShift=bits;', '        BG.StartPalette=palbase;\n        BG.BitShift=bits;')
  s=s.replace('        d35_fixed_reset();','        memset(&palette_context,0,sizeof(palette_context));\n        d35_fixed_reset();')
  s=s.replace('draw[mode](tile,offset,start,width,0,8);','for(unsigned p=0;p<16;p++)draw[mode](tile|((p%8)<<10),offset+(p%8)*8,start,width,0,8);')
  s=s.replace('draw[mode](tile,offset+row*pitch,start,width,row*8,1);','for(unsigned p=0;p<16;p++)draw[mode](tile|((p%8)<<10),offset+row*pitch+(p%8)*8,start,width,row*8,1);')
 if not palette:(OUT/'tile-check.c').write_text(s,newline='\n')
 sh=(ROOT/'build/check-fixed-clipping.sh').read_text().replace('"$(dirname "$0")/.."','"$(dirname "$0")/../.."').replace('out=build/fixed-rows-private-v3','out=build/'+OUT.name).replace('build/plus-a7-fixed-clipping-check.c','"$out/tile-check.c"')
 if palette:
  sh=sh.replace('tile-check.c','palette-check.c').replace('clipping-','palette-')
  (OUT/'palette-check.c').write_text(s,newline='\n')
  (OUT/'palette-check.sh').write_text(sh,newline='\n');subprocess.run(['sh',str(OUT/'palette-check.sh')],cwd=ROOT,check=True)
  print((OUT/'palette-exact.log').read_text().strip());print((OUT/'palette-candidate.log').read_text().strip());return
 (OUT/'check.sh').write_text(sh,newline='\n');subprocess.run(['sh',str(OUT/'check.sh')],cwd=ROOT,check=True)
 print((OUT/'clipping-exact.log').read_text().strip());print((OUT/'clipping-candidate.log').read_text().strip())
if __name__=='__main__':
 assert sys.argv[1:] in ([],['band'],['band3'],['palette']);main()
