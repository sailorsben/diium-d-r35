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
    prior={'source/tile.c':{'b75fd5e0e454838f0b7a466e0ac55c066abe984f20cb706ac210c8e368bf6f68',
                           '77ebe2b06c18148973997ae973f6a0016d18230ed77e19043de9f41ab7355317',
                           '3b435476c9c70e00bc0f4ff5d07282702b6e60b437e51af447bc77eaf50b5bb5'},
           'source/gfx.c':{'6c5e6390ac5c4ce3c60f5fb72ba7350db335ff206348655e5eb5bbdbd37136d1',
                           'e95ac252f717e6a185165adf980467082d45dd499cf0496eb6ffdf3290401feb'},
           'libretro.c':{'3cc3a0ffeebc27e2195ba38a3fdf873beab4dc9747f65b11c780a1b396e0ec2a',
                         '9cff29a5de7a805f1d5dc4f5989074b7feb39799b7a22e98d50d0db5d95a3324'}}
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
    anchor='static uint8_t ConvertTile(uint8_t* pCache, uint32_t TileAddr)\n{'
    assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'''
#ifdef D35_PLUS_A7
   if ((BG.BitShift==2 || BG.BitShift==4 || BG.BitShift==8) &&
       TileAddr <= 65536u-BG.BitShift*8u)
      return d35_decode_tile(pCache,Memory.VRAM+TileAddr,BG.BitShift)?1:BLANK_TILE;
#endif''')
    for mode,name in enumerate(names):
        start=text.index('void '+name+'(')
        end=text.index('   TILE_PREAMBLE_CODE();',start)+len('   TILE_PREAMBLE_CODE();')
        text=text[:end]+f'''
#ifdef D35_PLUS_A7
   if(d35_render_tile(Tile,Offset,StartLine,LineCount,pCache,ScreenColors,{mode})) return;
#endif'''+text[end:]
    return text

def libretro(text):
    text='#ifdef D35_PLUS_A7\n#include "source/a7_profile_core.h"\nunsigned d35_profile_active;\n#define D35_PROFILE_CORE\n#include "source/a7_profile.h"\n#endif\n'+text
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
    text=text.replace(anchor,anchor+'\n#ifdef D35_PLUS_A7\n#include "a7_tile.h"\n#include "a7_profile_core.h"\n#endif')
    anchor='void S9xUpdateScreen(void)\n{'
    text=text.replace(anchor,anchor+'\n#ifdef D35_PLUS_A7\n   uint64_t d35_began=d35_profile_active?d35_profile_enter():0;\n#endif')
    anchor='   IPPU.PreviousLine = IPPU.CurrentLine;\n}'
    assert text.count(anchor)==1
    text=text.replace(anchor,'   IPPU.PreviousLine = IPPU.CurrentLine;\n#ifdef D35_PLUS_A7\n   if(d35_profile_active) d35_profile_leave(0,d35_began);\n#endif\n}')
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
def apu(text):
    text='#ifdef D35_PLUS_A7\n#include "a7_profile_core.h"\n#endif\n'+text
    anchor='void S9xAPUExecute()\n{'
    assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'\n#ifdef D35_PLUS_A7\n   uint64_t d35_began=d35_profile_active?d35_profile_enter():0;\n#endif')
    anchor='   if (SPC_SAMPLE_COUNT() >= APU_MINIMUM_SAMPLE_BLOCK || !sound_in_sync)\n      sa_callback();\n}'
    assert text.count(anchor)==1
    return text.replace(anchor,anchor[:-1]+'#ifdef D35_PLUS_A7\n   if(d35_profile_active) d35_profile_leave(1,d35_began);\n#endif\n}')

def makefile(text):
    assert text.count('FLAGS += -O2 -DNDEBUG')==1
    return text.replace('FLAGS += -O2 -DNDEBUG',
        'FLAGS += -O3 -DNDEBUG -flto=4 -fno-semantic-interposition -fvisibility=hidden').replace('-fno-builtin','')

change('source/apu_blargg.c',apu)
change('Makefile',makefile)
change('link.T',lambda text:text.replace('global: retro_*;','global: retro_*; d35_profile_begin; d35_profile_end;'))
(CORE/'source/a7_tile.h').write_bytes((ROOT/'plus-a7-render.h').read_bytes())
(CORE/'source/a7_profile.h').write_bytes((ROOT/'plus-a7-profile.h').read_bytes())
(CORE/'source/a7_profile_core.h').write_bytes((ROOT/'plus-a7-profile-core.h').read_bytes())
print('Applied guarded A7 whole-program build, planar decode, rendering and sampled phase ABI')
