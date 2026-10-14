"""Refine generic batching: retain constant arithmetic, one call per band."""
from pathlib import Path
import shutil,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/('build/common-band-private-v2' if sys.argv[1:]==['--v2'] else 'build/common-band-private-v3')
def main():
 assert not OUT.exists();OUT.mkdir()
 for label in ('core','counted-core'):
  counted=label=='counted-core';core=OUT/label
  shutil.copytree(ROOT/'build/pearl-sub-private-v2/both'/label,core,ignore=shutil.ignore_patterns('*.o','*.so'))
  for src,dest in [('common-tile-batch-v2.h' if OUT.name.endswith('v2') else 'common-tile-batch.h','a7_common_batch.h'),('common-band.h','a7_common_band.h')]:shutil.copy2(ROOT/'build'/src,core/'source'/dest)
  p=core/'source/gfx.c';s=p.read_text();start=s.index('static void DrawBackground(uint32_t BGMode, uint32_t bg, uint8_t Z1, uint8_t Z2)');end=s.index('#define RENDER_BACKGROUND_MODE7',start)
  part=s[start:end];anchor='   struct d35_sub2_context sub_context={0};';assert part.count(anchor)==1
  part=part.replace(anchor,anchor+'''
   struct d35_batch_context batch;batch.mode=7;batch.valid=0;
   if(DrawTilePtr==DrawTile16)batch.mode=0;
   if(DrawTilePtr==DrawTile16Add)batch.mode=1;
   if(DrawTilePtr==DrawTile16Sub)batch.mode=3;
   unsigned batch_ok=batch.mode<7&&!BG.DirectColourMode&&(BG.BitShift==2||BG.BitShift==4)&&BG.PaletteMask<8&&
      !IPPU.DoubleWidthPixels&&!IPPU.DoubleHeightPixels&&!IPPU.HalfWidthPixels&&
      GFX.PixSize==1&&GFX.ZPitch==GFX.PPL;
''')
  a=part.index('         for (C = Middle; C > 0;');b=part.index('         /* Right-hand edge clipped tiles */',a)
  old=part[a:b]
  # Original right/left clipped paths and unsupported modes stay verbatim.
  block='''         if(batch_ok&&Middle){
            struct d35_band_walk walk={t,b1,b2,Quot,s,t1,t2,(unsigned)VirtAlign,Lines,depths[0],depths[1],sub_fast?&sub_context:NULL};
            if(batch.mode==0)d35_band_0(&batch,&walk,Middle);
            else if(batch.mode==1)d35_band_1(&batch,&walk,Middle);
            else d35_band_3(&batch,&walk,Middle);
            t=walk.t;Quot=walk.quot;s=walk.offset;
         }else{
'''+old+'         }\n'
  part=part[:a]+block+part[b:]
  if OUT.name.endswith('v2'):part=part.replace('struct d35_batch_context batch;batch.mode=7;batch.valid=0;','struct d35_batch_context batch={0};batch.mode=7;')
  header=('#define D35_COMMON_COUNT\n' if counted else '')+'#include "a7_common_band.h"\n'
  p.write_text(s[:start]+header+part+s[end:],newline='\n')
 shutil.copy2(ROOT/'build/fullpaths-private-v2/compare.c',OUT/'ordinary-compare.c');shutil.copy2(ROOT/'build/pearl-work-private-v1/compare.c',OUT/'compare.c')
 script=(ROOT/'build/build-common-batch.sh').read_text().replace('common-batch-private-v1',OUT.name)
 (ROOT/'build/build-common-band.sh').write_text(script,newline='\n')
 print('Prepared constant-mode band dispatch; no card access')
if __name__=='__main__':
 assert sys.argv[1:] in ([],['--v2']);main()
