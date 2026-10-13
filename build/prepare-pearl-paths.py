"""Separate and combined exact work-removal experiments atop fullpaths1.
Never touches staged payloads, ROM, hardware or production core.
"""
from pathlib import Path
import re,shutil,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/pearl-paths-private-v1'
ZHELP='''
static inline unsigned d35_depth_covered(int32_t offset,unsigned lines)
{
    uint8x8_t z=vdup_n_u8(GFX.Z1);
    while(lines--){
        if(vget_lane_u64(vreinterpret_u64_u8(vcgt_u8(z,vld1_u8(GFX.DB+offset))),0))return 0;
        offset+=GFX.PPL;
    }
    return 1;
}
'''
def patch(core,kind,counted):
 source=core/'source'
 if kind in ('earlyz','both'):
  p=source/'tile.c';s=p.read_text();anchor='/* Replaces only the eligible full-tile helper in isolated offline copies. */';assert anchor in s
  s=s.replace(anchor,ZHELP+'\n'+anchor)
  anchor='void DrawTile16(uint32_t Tile, int32_t Offset, uint32_t StartLine, uint32_t LineCount)\n{';assert s.count(anchor)==1
  count='PW(20);d35_pearl[(d35_pearl_plane*6+d35_pearl_layer)*24+21]+=LineCount;' if counted else ''
  s=s.replace(anchor,anchor+'''\n   if(BG.BitShift==2 && GFX.S==GFX.Screen && d35_depth_covered(Offset,LineCount)){'''+count+'return;}')
  p.write_text(s,newline='\n')
 if kind in ('flat','both'):
  shutil.copy2(ROOT/'build/pearl-flat.h',source/'a7_pearl_flat.h')
  p=source/'gfx.c';s=p.read_text();anchor='static void DrawBackground(uint32_t BGMode, uint32_t bg, uint8_t Z1, uint8_t Z2)';assert s.count(anchor)==1
  s=s.replace(anchor,'#include "a7_pearl_flat.h"\n'+anchor)
  anchor='      clipcount = (window_custom?window_clip.count:GFX.pCurrentClip->Count [bg]);';assert s.count(anchor)==1
  count='d35_pearl[(d35_pearl_plane*6+d35_pearl_layer)*24+17]+=Lines;d35_pearl[(d35_pearl_plane*6+d35_pearl_layer)*24+18]+=((HOffset&7)+256+7)/8;' if counted else ''
  s=s.replace(anchor,'''      if(BGMode==1 && bg==2 && BG.TileSize==8 && BG.BitShift==2 &&
         GFX.S==GFX.SubScreen && (GFX.r212d&31)==4 && !GFX.Pseudo && PPU.Mosaic<=1 &&
         !IPPU.DoubleWidthPixels && !IPPU.DoubleHeightPixels && !IPPU.HalfWidthPixels &&
         GFX.PixSize==1 && GFX.ZPitch==GFX.PPL &&
         !(window_custom?window_clip.count:GFX.pCurrentClip->Count[bg]) &&
         d35_flat_band(Y,Lines,HOffset,VOffset,b1,b2,depths[0],depths[1])){'''+count+'''continue;}
'''+anchor)
  p.write_text(s,newline='\n')
def prepare():
 assert not OUT.exists();OUT.mkdir()
 for kind in ('earlyz','flat','both'):
  d=OUT/kind;d.mkdir()
  for label,base in (('core',ROOT/'build/fullpaths-private-v2/combined-core'),('counted-core',ROOT/'build/pearl-work-private-v1/core')):
   shutil.copytree(base,d/label,ignore=shutil.ignore_patterns('*.o','*.so'));patch(d/label,kind,label=='counted-core')
  shutil.copy2(ROOT/'build/pearl-work-private-v1/compare.c',d/'compare.c')
  script=(ROOT/'build/build-fixed-rows.sh').read_text().replace('build/fixed-rows-private-v3',str(d.relative_to(ROOT)).replace('\\','/')).replace('-L../../sysroot/lib','-L../../../sysroot/lib')
  script=script.replace("echo 'Built offline fixed-color batching hypothesis'",f"echo 'Built offline Pearl {kind}'")
  # Use the ordinary checker for counter-free and the extended one for census.
  shutil.copy2(ROOT/'build/fullpaths-private-v2/compare.c',d/'ordinary-compare.c')
  script=script.replace('"$out/compare.c"','"$out/ordinary-compare.c"')
  script+='''arm-linux-gnueabihf-gcc $flags -DUSE_BLARGG_APU -O2 -std=gnu99 -Wall -Wextra -Werror -no-pie -nostdlib \\
 -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o "$out/compare.c" $libs -o "$out/census-compare"\n'''
  (ROOT/f'build/build-pearl-{kind}.sh').write_text(script,newline='\n')
 print('Prepared three owned full-frame hypotheses; no timing claims')
if __name__=='__main__':prepare()
