"""Isolated sole-subsurface production, alone and with early depth rejection."""
from pathlib import Path
import shutil,re
from importlib.util import spec_from_file_location,module_from_spec
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/pearl-sub-private-v2'
def main():
 assert not OUT.exists();OUT.mkdir()
 spec=spec_from_file_location('paths',ROOT/'build/prepare-pearl-paths.py');m=module_from_spec(spec);spec.loader.exec_module(m)
 for kind in ('sub','both'):
  d=OUT/kind;d.mkdir()
  for label,base in (('core',ROOT/'build/fullpaths-private-v2/combined-core'),('counted-core',ROOT/'build/pearl-work-private-v1/core')):
   core=d/label;counted=label=='counted-core'
   shutil.copytree(base,core,ignore=shutil.ignore_patterns('*.o','*.so'))
   if kind=='both':m.patch(core,'earlyz',counted)
   shutil.copy2(ROOT/'build/pearl-sub2.h',core/'source/a7_pearl_sub2.h')
   p=core/'source/gfx.c';s=p.read_text();start=s.index('static void DrawBackground(uint32_t BGMode, uint32_t bg, uint8_t Z1, uint8_t Z2)');end=s.index('#define RENDER_BACKGROUND_MODE7',start)
   part=s[start:end]
   part=part.replace('   depths [0] = Z1;', '''   unsigned sub_fast=BGMode==1 && bg==2 && BG.BitShift==2 && !BG.DirectColourMode &&
      GFX.S==GFX.SubScreen && GFX.DB==GFX.SubZBuffer && (GFX.r212d&31)==4 &&
      !GFX.Pseudo && !IPPU.DoubleWidthPixels && !IPPU.DoubleHeightPixels && !IPPU.HalfWidthPixels &&
      GFX.PixSize==1 && GFX.ZPitch==GFX.PPL;
   struct d35_sub2_context sub_context={0};
   depths [0] = Z1;''')
   pat=r'\(\*DrawTilePtr\)\(([^;]+), s, VirtAlign, Lines\);'
   part,n=re.subn(pat,lambda a:'{if(!sub_fast || !d35_sub2(&sub_context,'+a[1]+',s,VirtAlign,Lines)) '+a[0]+'}',part);assert n==5,n
   header=('#define D35_PEARL_SUB_COUNT\n' if counted else '')+'#include "a7_pearl_sub2.h"\n'
   s=s[:start]+header+part+s[end:];p.write_text(s,newline='\n')
  shutil.copy2(ROOT/'build/fullpaths-private-v2/compare.c',d/'ordinary-compare.c');shutil.copy2(ROOT/'build/pearl-work-private-v1/compare.c',d/'compare.c')
  script=(ROOT/'build/build-pearl-both.sh').read_text().replace('pearl-paths-private-v1/both',OUT.name+'/'+kind)
  (OUT/f'build-{kind}.sh').write_text(script.replace('"$(dirname "$0")/.."','"$(dirname "$0")/../.."'),newline='\n')
 print('Prepared two isolated subscreen hypotheses; no card access')
if __name__=='__main__':main()
