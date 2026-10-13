"""Create an owned offline fixed-color batching hypothesis from ability2.

No installer or card writes. Original qualified artifacts remain immutable.
"""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fixed-rows-private-v3'

def replace(s,old,new,count=1):
    assert s.count(old)==count,(old,s.count(old),count)
    return s.replace(old,new)

def patch(core):
    source=core/'source'
    shutil.copy2(ROOT/'build/plus-a7-fixed-rows.h',source/'a7_fixed.h')
    p=source/'ppu.c';s=p.read_text()
    s=replace(s,'#include "a7_window.h"','#include "a7_window.h"\n#include "a7_fixed.h"')
    s=replace(s,'PPU.FixedColourGreen,PPU.FixedColourBlue))',
                'PPU.FixedColourGreen,PPU.FixedColourBlue) && !d35_fixed_defer())')
    p.write_text(s,newline='\n')
    p=source/'gfx.c';s=p.read_text()
    s=replace(s,'#include "a7_window.h"','#include "a7_window.h"\n#define D35_FIXED_ROWS_USE\n#define D35_FIXED_ROWS_IMPLEMENTATION\n#include "a7_fixed.h"')
    s=replace(s,'d35_window_reset();','d35_window_reset();d35_fixed_reset();')
    s=replace(s,'d35_window_capture(C);','d35_window_capture(C);d35_fixed_capture(C);')
    # Begin only after original code computes the current effective fixed color;
    # save and restore that original value so renderer traversal has no residue.
    mark='GFX.FixedColour = BUILD_PIXEL(IPPU.XB [PPU.FixedColourRed], IPPU.XB [PPU.FixedColourGreen], IPPU.XB [PPU.FixedColourBlue]);'
    s=replace(s,mark,mark+'\n      d35_fixed_begin();')
    start=s.index(mark);end=s.index('   } /* force blanking */',start)
    region=s[start:end]
    # Every row loop in the color-math branch selects its own captured operand.
    import re
    region,n=re.subn(r'(for \(y = starty; y <= endy; y\+\+\)\n\s*\{)',r'\1\n            d35_fixed_select(y);',region)
    assert n==6,n
    s=s[:start]+region+s[end:]
    # Clear pending deferral even when the update did not consume color math.
    # Restoration is conditional on begin/active, avoiding an old saved value.
    s=replace(s,'   IPPU.PreviousLine = IPPU.CurrentLine;',
                '   d35_fixed_end();\n   IPPU.PreviousLine = IPPU.CurrentLine;')
    p.write_text(s,newline='\n')
    p=source/'tile.c';s=p.read_text()
    s=replace(s,'#include "tile.h"','#define D35_FIXED_ROWS_USE\n#include "a7_fixed.h"\n#include "tile.h"')
    s=replace(s,'screen+GFX.Delta,GFX.FixedColour,mode,mask)',
                'screen+GFX.Delta,d35_fixed_at_offset((unsigned)offset),mode,mask)')
    p.write_text(s,newline='\n')
    p=source/'tile.h';s=p.read_text()
    # Full and clipped scalar fallback loops, including flips. Large-pixel
    # mosaic and hires paths are outside the guarded deferral envelope.
    start=s.index('#define RENDER_TILE(');end=s.index('#define RENDER_TILE_LARGE(',start)
    region=s[start:end]
    needle='Offset += GFX.PPL) \\\n       { \\\n'
    region=replace(region,needle,needle+'          d35_fixed_select_offset((unsigned)Offset); \\\n',8)
    # A clipped tile's base can precede pixel0 or the current row. Choose
    # the line using its first visible destination pixel, not its base.
    split=region.index('#define RENDER_CLIPPED_TILE_CODE(')
    clipped=replace(region[split:],'d35_fixed_select_offset((unsigned)Offset);',
                    'd35_fixed_select_offset((unsigned)(Offset + StartPixel));',4)
    region=region[:split]+clipped
    s=s[:start]+region+s[end:]
    p.write_text(s,newline='\n')

def prepare():
    assert not OUT.exists();OUT.mkdir()
    baseline=ROOT/'build/ability-regression-private-v1'
    shutil.copytree(baseline/'core',OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'))
    patch(OUT/'core')
    shutil.copytree(ROOT/'build/ff6-effect-screen-private-v1/natural/core',OUT/'counted-core',
                    ignore=shutil.ignore_patterns('*.o','*.so'))
    patch(OUT/'counted-core')
    shutil.copy2(baseline/'compare.c',OUT/'compare.c')
    p=OUT/'compare.c';s=p.read_text()
    s=replace(s,'census(ce);hyp(hy);conf(co);flush(fl);',
                'census(ce);hyp(hy);conf(co);flush(fl);\n            printf("FIXED %u,%llu,%llu\\n",frame,co[110],co[111]);')
    p.write_text(s,newline='\n')
    s=(ROOT/'build/build-ability-regression.sh').read_text()
    start=s.index('libs=');end=s.index('arm-linux-gnueabihf-gcc $flags -DUSE_BLARGG_APU',start)
    # Offline checker only: no new physical runner or dispatch payload.
    libs=s[start:s.index('if [ ! -e',start)]
    s=s[:start]+libs+s[end:]
    s=s[:s.index('arm-linux-gnueabihf-readelf')]+"echo 'Built offline fixed-color batching hypothesis'\n"
    s=s.replace('ability-regression-private-v1',OUT.name)
    start=s.index('(cd "$out/core"');end=s.index(' > "$out/core-build.log"',start)
    counted=s[start:end].replace('"$out/core"','"$out/counted-core"')
    s+=counted+' > "$out/counted-build.log" 2>&1\n'
    (ROOT/'build/build-fixed-rows.sh').write_text(s,newline='\n')

if __name__=='__main__':prepare()
