"""Apply guarded D-R35 kernels to the pinned core; keep upstream sources local."""
from pathlib import Path
import subprocess
from hashlib import sha256
ROOT=Path(__file__).resolve().parent
CORE=ROOT/'snes9x2005'
PIN='a79dfe9047e7fec58808aefe48ad2bf499c7af11'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=CORE).decode().strip()==PIN

def change(name,transform):
    path=CORE/name
    base=subprocess.check_output(['git','show',PIN+':'+name],cwd=CORE).decode()
    modified=transform(base)
    current=path.read_text()
    # Permit exact shipped1.6/1.7 and authored transitional1.8 patches only.
    prior={'source/tile.c':{'77ebe2b06c18148973997ae973f6a0016d18230ed77e19043de9f41ab7355317',
                           '3b435476c9c70e00bc0f4ff5d07282702b6e60b437e51af447bc77eaf50b5bb5'},
           'source/gfx.c':{'e95ac252f717e6a185165adf980467082d45dd499cf0496eb6ffdf3290401feb'},
           'libretro.c':{'9cff29a5de7a805f1d5dc4f5989074b7feb39799b7a22e98d50d0db5d95a3324'}}
    assert current in (base,modified) or sha256(path.read_bytes()).hexdigest() in prior.get(name,set()), 'Unrelated core change: '+name
    path.write_text(modified,newline='\n')

helper='''
#ifdef D35_PLUS_A7
#include "a7_tile.h"
static INLINE __attribute__((always_inline)) bool d35_render_tile(uint32_t tile,int32_t offset,uint32_t line,
    uint32_t count,uint8_t *cache,uint16_t *colors,unsigned mode)
{
    d35_palette_t table;
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
    anchor='static void S9xAudioCallback(void)'
    assert text.count(anchor)==1
    text=text.replace(anchor,'#ifdef D35_PLUS_A7\nstatic bool d35_audio_in_run;\n#endif\n'+anchor)
    anchor='   audio_out_buffer_pos += available_samples;'
    assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'''
#ifdef D35_PLUS_A7
   /* These samples were already mixed at the existing APU sync point.
    * Publish without moving emulated CPU/APU time or finalization. */
   if (d35_audio_in_run && audio_out_buffer_pos)
   {
      size_t offered = audio_out_buffer_pos >> 1;
      size_t accepted = audio_batch_cb(audio_out_buffer, offered);
      if (accepted > offered) accepted = offered;
      audio_out_buffer_pos -= accepted << 1;
      if (audio_out_buffer_pos && accepted)
         memmove(audio_out_buffer, audio_out_buffer + (accepted << 1),
               audio_out_buffer_pos * sizeof(int16_t));
   }
#endif''')
    anchor='   S9xMainLoop();'
    assert text.count(anchor)==1
    text=text.replace(anchor,'#ifdef D35_PLUS_A7\n   d35_audio_in_run = true;\n#endif\n'+anchor+'\n#ifdef D35_PLUS_A7\n   d35_audio_in_run = false;\n#endif')
    anchor='   if (IPPU.RenderThisFrame)\n   {\n#ifdef PSP'
    assert text.count(anchor)==1
    text=text.replace(anchor,'#ifdef D35_PLUS_A7\n   audio_upload_samples();\n#endif\n\n'+anchor)
    anchor='   audio_upload_samples();\n}\n\nbool S9xReadMousePosition'
    assert text.count(anchor)==1
    return text.replace(anchor,'#ifndef D35_PLUS_A7\n   audio_upload_samples();\n#endif\n}\n\nbool S9xReadMousePosition')

def graphics(text):
    anchor='#include "gfx.h"'
    assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'\n#ifdef D35_PLUS_A7\n#include "a7_tile.h"\n#endif')
    start=text.index('      if (IPPU.Clip [0].Count [5])',text.index('void S9xUpdateScreen'))
    end=text.index('   } /* force blanking */',start)
    region=text[start:end]
    # Eight scalar loops in pinned order: color window, five math/copy backdrop
    # loops, two plain backdrop loops. Leave upstream tails and clipping intact.
    modes=['window',4,3,2,1,0,7,7]
    import re
    anchors=list(re.finditer(r'(?m)^( +)while \(d < e\)',region))
    assert len(anchors)==len(modes), 'Pinned backdrop topology changed'
    for match,mode in reversed(list(zip(anchors,modes))):
        indent=match.group(1)
        if mode=='window':
            call='d35_window(p,d,p+GFX.Delta,d<e?(unsigned)(e-d):0,BLACK)'
            advance='p+=used; d+=used;'
        else:
            call=f'd35_backdrop(p,d,{"NULL" if mode==7 else "s"},p+GFX.Delta,d<e?(unsigned)(e-d):0,(uint16_t)back,GFX.FixedColour,{mode})'
            advance='p+=used; d+=used;'+(' s+=used;' if mode!=7 else '')
        patch=f'#ifdef D35_PLUS_A7\n{indent}{{ unsigned used={call}; {advance} }}\n#endif\n'
        region=region[:match.start()]+patch+region[match.start():]
    return text[:start]+region+text[end:]

change('source/tile.c',tiles)
change('source/gfx.c',graphics)
change('libretro.c',libretro)
(CORE/'source/a7_tile.h').write_bytes((ROOT/'plus-a7-render.h').read_bytes())
print('Applied pinned A7 palette/tile/backdrop/window kernels and audio-first delivery')
