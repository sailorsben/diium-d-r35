"""Patch an isolated copy of the PGO-era Plus source for stack experiments."""
from importlib import import_module
from pathlib import Path
import re
import shutil
import sys


replace_once = import_module('prepare-snes-throughput').replace_once
HERE = Path(__file__).resolve().parent


def tile_transpose(core):
    tile = core / 'source/tile.c'
    shutil.copyfile(HERE / 'snes-tile-transpose.h', core / 'source/snes-tile-transpose.h')
    text = replace_once(tile.read_text(), '#include "a7_color_cache.h"', '''#include "a7_color_cache.h"
#include "snes-tile-transpose.h"

static bool d35_transpose_enabled;
__attribute__((visibility("default"))) void d35_raster_set_enabled(bool enabled)
{
    d35_transpose_enabled = enabled;
}''')
    text = replace_once(text, '   if ((BG.BitShift==2 || BG.BitShift==4 || BG.BitShift==8) &&',
                        '''   if (d35_transpose_enabled && (BG.BitShift == 2 || BG.BitShift == 4) &&
       TileAddr <= 65536u - BG.BitShift * 8u)
      return d35_transpose_tile(pCache, Memory.VRAM + TileAddr, BG.BitShift) ? 1 : BLANK_TILE;
   if ((BG.BitShift==2 || BG.BitShift==4 || BG.BitShift==8) &&''')
    tile.write_text(text, newline='\n')


def mode2_dependencies(core, memo=False, ranges=False, small=False, bounded=False):
    source = core / 'source'
    gfx = source / 'gfx.c'
    tile = source / 'tile.h'
    header = 'snes-mode2-dependencies.h'
    shutil.copyfile(HERE / header, source / header)
    define = '#define D35_MODE2_MEMO\n' if memo else ''
    if ranges:
        define += '#define D35_MODE2_RANGES\n'
    if small:
        define += '#define D35_MODE2_SMALL\n'
    if bounded:
        define += '#define D35_MODE2_BOUNDED\n'
    text = replace_once(gfx.read_text(), 'extern bool reduce_sprite_flicker;',
                        f'extern bool reduce_sprite_flicker;\n{define}#include "{header}"')
    text = replace_once(text, '   d35_window_reset();d35_fixed_reset();',
                        '   d35_window_reset();d35_fixed_reset();\n   d35_dependency_frame();')
    text = replace_once(text, 'void S9xSetupOBJ(void)\n{',
                        'void S9xSetupOBJ(void)\n{\n   d35_mode2_object_setup();')
    text = replace_once(text, '   endy   = GFX.EndY;', '''   endy   = GFX.EndY;
   if (d35_capture_span(starty, endy)) {
      d35_fixed_end();
      IPPU.PreviousLine = IPPU.CurrentLine;
#ifdef D35_PLUS_A7
      if(d35_profile_active) d35_profile_leave(0,d35_began);
#endif
      return;
   }''')
    text = replace_once(text, '\n   d35_fixed_end();', '\n   d35_finish_span();\n   d35_fixed_end();')
    text = replace_once(text, '         DrawBackgroundOffset(BGMode, bg, Z1, Z2);',
                        '         if (d35_record) d35_record->valid = false;\n'
                        '         DrawBackgroundOffset(BGMode, bg, Z1, Z2);')
    text = replace_once(text, '      DrawBackgroundMosaic(BGMode, bg, Z1, Z2);',
                        '      if (d35_record) d35_record->valid = false;\n'
                        '      DrawBackgroundMosaic(BGMode, bg, Z1, Z2);')
    for addr, name in [('addr_h', 'cell_h'), ('addr_v', 'cell_v'), ('addr', 'tile')]:
        old = f'unsigned {name} = READ_2BYTES(Memory.VRAM + {addr});'
        text = replace_once(text, old, f'd35_mode2_vram({addr}, 2);\n            {old}')
    gfx.write_text(text, newline='\n')
    text = replace_once(tile.read_text(), '#define _TILE_H_',
                        '#define _TILE_H_\n\nvoid d35_mode2_vram(unsigned addr, unsigned bytes);')
    anchor = '    TileAddr &= 0xffff; ' + chr(92)
    text = replace_once(text, anchor, anchor + '\n    d35_mode2_vram(TileAddr, BG.BitShift * 8); ' + chr(92))
    tile.write_text(text, newline='\n')
    if memo:
        libretro = core / 'libretro.c'
        text = replace_once(libretro.read_text(), 'void retro_reset(void)\n{',
                            'void d35_mode2_clear(void);\n\nvoid retro_reset(void)\n{\n   d35_mode2_clear();')
        for signature in ('bool retro_unserialize(const void* data, size_t size)',
                          'bool retro_load_game(const struct retro_game_info* game)',
                          'void retro_unload_game(void)'):
            text = replace_once(text, signature + '\n{', signature + '\n{\n   d35_mode2_clear();')
        libretro.write_text(text, newline='\n')


def fx_register_pairs(core):
    path = core / 'source/fxinst.c'
    header = 'snes-superfx-register-pairs.h'
    text = path.read_text()
    table = text.split('void (*fx_apfOpcodeTable[])(void) =', 1)[1]
    functions = re.findall(r'&(fx_\w+)', table)
    assert len(functions) == 1024
    for base, name in ((0x10, 'to'), (0x20, 'with'), (0xb0, 'from')):
        for alt in range(4):
            assert functions[alt * 256 + base:alt * 256 + base + 14] == [
                f'fx_{name}_r{i}' for i in range(14)]
    shutil.copyfile(HERE / header, path.with_name(header))
    anchor = 'uint32_t fx_run(uint32_t nInstructions)\n{'
    text = replace_once(text, anchor, f'#include "{header}"\n\n{anchor}\n'
                        '   if (d35_register_pairs_enabled) return d35_fx_run_register_pairs(nInstructions);')
    path.write_text(text, newline='\n')


if __name__ == '__main__':
    root, mode = Path(sys.argv[1]), sys.argv[2]
    {'tile-transpose': tile_transpose, 'mode2-dependencies': mode2_dependencies,
     'mode2-memo': lambda core: mode2_dependencies(core, memo=True),
     'mode2-memo-ranges': lambda core: mode2_dependencies(core, memo=True, ranges=True),
     'mode2-memo-small': lambda core: mode2_dependencies(core, memo=True, ranges=True, small=True),
     'mode2-memo-bounded': lambda core: mode2_dependencies(core, memo=True, ranges=True, bounded=True),
     'fx-register-pairs': fx_register_pairs}[mode](root)
    link = root / 'link.T'
    exports = 'retro_*; d35_raster_set_enabled;'
    if mode.startswith('mode2-'):
        exports += ' d35_mode2_read;'
    link.write_text(replace_once(link.read_text(), 'retro_*;', exports), newline='\n')
