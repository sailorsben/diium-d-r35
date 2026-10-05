"""Apply guarded D-R35 kernels to the pinned core; keep upstream sources local."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parent
CORE=ROOT/'snes9x2005'
PIN='a79dfe9047e7fec58808aefe48ad2bf499c7af11'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CORE).decode().strip()==PIN

def change(name,transform):
    path=CORE/name
    base=subprocess.check_output(['git','show',PIN+':'+name],cwd=CORE).decode()
    modified=transform(base)
    current=path.read_text()
    assert current in (base,modified), 'Unrelated core change: '+name
    path.write_text(modified,newline='\n')

helper='''
#ifdef D35_PLUS_A7
#include "a7_tile.h"
static INLINE bool d35_render_tile(uint32_t tile,int32_t offset,uint32_t line,
    uint32_t count,uint8_t *cache,uint16_t *colors,unsigned mode)
{
    uint8x8x4_t table;
    uint8_t *bp;
    int step;
    if(BG.DirectColourMode || (BG.BitShift!=2 && BG.BitShift!=4)) return false;
    table=d35_palette(colors,BG.BitShift);
    bp=cache+((tile&V_FLIP)?56-line:line); step=(tile&V_FLIP)?-8:8;
    while(count--) {
        uint16_t *screen=(uint16_t *)GFX.S+offset;
        uint8_t *depth=(mode?GFX.ZBuffer:GFX.DB)+offset;
        d35_row(bp,table,!!(tile&H_FLIP),screen,depth,
                GFX.SubZBuffer+offset,screen+GFX.Delta,GFX.Z1,GFX.Z2,GFX.FixedColour,mode);
        bp+=step; offset+=GFX.PPL;
    }
    return true;
}
#endif
'''
names=['DrawTile16','DrawTile16Add','DrawTile16Add1_2','DrawTile16Sub',
       'DrawTile16Sub1_2','DrawTile16FixedAdd1_2','DrawTile16FixedSub1_2']
def tiles(text):
    assert text.count('#include "tile.h"')==1
    text=text.replace('#include "tile.h"','#include "tile.h"\n'+helper)
    for mode,name in enumerate(names):
        start=text.index('void '+name+'(')
        end=text.index('   TILE_PREAMBLE_CODE();',start)+len('   TILE_PREAMBLE_CODE();')
        text=text[:end]+f'''
#ifdef D35_PLUS_A7
   if(d35_render_tile(Tile,Offset,StartLine,LineCount,pCache,ScreenColors,{mode})) return;
#endif'''+text[end:]
    return text

def libretro(text):
    anchor='   if (IPPU.RenderThisFrame)\n   {\n#ifdef PSP'
    assert text.count(anchor)==1
    text=text.replace(anchor,'#ifdef D35_PLUS_A7\n   audio_upload_samples();\n#endif\n\n'+anchor)
    anchor='   audio_upload_samples();\n}\n\nbool S9xReadMousePosition'
    assert text.count(anchor)==1
    return text.replace(anchor,'#ifndef D35_PLUS_A7\n   audio_upload_samples();\n#endif\n}\n\nbool S9xReadMousePosition')

change('source/tile.c',tiles)
change('libretro.c',libretro)
(CORE/'source/a7_tile.h').write_bytes((ROOT/'plus-a7-render.h').read_bytes())
print('Applied pinned A7 tile/color kernels and audio-first delivery')
