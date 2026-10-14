"""Common renderer hypothesis atop the qualified Pearl combination. Offline."""
from pathlib import Path
import shutil,re
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/common-batch-private-v1'
def main():
 assert not OUT.exists();OUT.mkdir()
 for label in ('core','counted-core'):
  counted=label=='counted-core';core=OUT/label
  shutil.copytree(ROOT/'build/pearl-sub-private-v2/both'/label,core,ignore=shutil.ignore_patterns('*.o','*.so'))
  shutil.copy2(ROOT/'build/common-tile-batch-v2.h',core/'source/a7_common_batch.h')
  p=core/'source/gfx.c';s=p.read_text();start=s.index('static void DrawBackground(uint32_t BGMode, uint32_t bg, uint8_t Z1, uint8_t Z2)');end=s.index('#define RENDER_BACKGROUND_MODE7',start)
  part=s[start:end];anchor='   struct d35_sub2_context sub_context={0};'
  assert part.count(anchor)==1
  names=('','Add','Add1_2','Sub','Sub1_2','FixedAdd1_2','FixedSub1_2')
  select='   struct d35_batch_context batch={0};batch.mode=7;\n'
  select+='\n'.join(f'   if(DrawTilePtr==DrawTile16{name})batch.mode={i};' for i,name in enumerate(names))
  select+='''
   unsigned batch_ok=batch.mode<7 && !BG.DirectColourMode && (BG.BitShift==2||BG.BitShift==4) &&
      !IPPU.DoubleWidthPixels&&!IPPU.DoubleHeightPixels&&!IPPU.HalfWidthPixels&&
      GFX.PixSize==1&&GFX.ZPitch==GFX.PPL;
'''
  part=part.replace(anchor,anchor+'\n'+select)
  pat=r'\(\*DrawTilePtr\)\(([^;]+), s, VirtAlign, Lines\);'
  part,n=re.subn(pat,lambda a:'{if(!batch_ok || !d35_batch_tile(&batch,'+a[1]+',s,VirtAlign,Lines)) '+a[0]+'}',part);assert n==5,n
  header=('#define D35_COMMON_COUNT\n' if counted else '')+'#include "a7_common_batch.h"\n'
  p.write_text(s[:start]+header+part+s[end:],newline='\n')
 shutil.copy2(ROOT/'build/fullpaths-private-v2/compare.c',OUT/'ordinary-compare.c')
 shutil.copy2(ROOT/'build/pearl-work-private-v1/compare.c',OUT/'compare.c')
 script=(ROOT/'build/build-pearl-both.sh').read_text().replace('pearl-paths-private-v1/both',OUT.name).replace('-L../../../sysroot/lib','-L../../sysroot/lib')
 script=script.replace('Built offline Pearl both','Built isolated common background batching hypothesis')
 (ROOT/'build/build-common-batch.sh').write_text(script,newline='\n')
 print('Prepared common full-tile batch hypothesis; no card access')
if __name__=='__main__':main()
