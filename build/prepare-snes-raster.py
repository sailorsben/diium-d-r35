"""Apply guarded raster experiments to the frozen private core source."""
from pathlib import Path
import sys

from importlib import import_module

replace_once = import_module('prepare-snes-throughput').replace_once
HERE = Path(__file__).resolve().parent


def prepare(core, variant):
    toggle = variant.endswith('-toggle')
    variant = variant.removesuffix('-toggle')
    assert variant in ('raster-offset', 'raster-offset-neon', 'raster-offset-full',
                       'raster-offset-neon-isolated', 'raster-objects',
                       'raster-objects-wide', 'raster-count', 'raster-count-wide')
    gfx = core / 'source/gfx.c'
    text = gfx.read_text()
    counts = variant in ('raster-count', 'raster-count-wide')
    wide = variant in ('raster-objects-wide', 'raster-count-wide')
    if counts:
        counters = '''static uint64_t d35_raster_counts[11];
#define D35_RASTER_ADD(i, n) (d35_raster_counts[i] += (n))
__attribute__((visibility("default"))) void d35_raster_census(uint64_t *out)
{
   memcpy(out, d35_raster_counts, sizeof(d35_raster_counts));
   memset(d35_raster_counts, 0, sizeof(d35_raster_counts));
}
'''
        link = core / 'link.T'
        link.write_text(replace_once(link.read_text(), 'retro_*;', 'retro_*; d35_raster_census;'))
    else:
        counters = '#define D35_RASTER_ADD(i, n) ((void)0)\n'
    if toggle:
        assert not counts
        counters += '''static bool d35_raster_enabled;
__attribute__((visibility("default"))) void d35_raster_set_enabled(bool enabled)
{
   d35_raster_enabled = enabled;
}
'''
        link = core / 'link.T'
        link.write_text(replace_once(link.read_text(), 'retro_*;', 'retro_*; d35_raster_set_enabled;'))
    obj = 'static void DrawOBJS(bool OnMain, uint8_t D)'
    text = replace_once(text, obj, counters + '\n' + obj)
    if counts or variant in ('raster-objects', 'raster-objects-wide'):
        text = replace_once(text, obj, (HERE / 'snes-raster-objects.h').read_text() + '\n' + obj)
        start = text.index(obj)
        end = text.index('static void DrawBackgroundMosaic(', start)
        body = text[start:end]
        body = replace_once(body, '''   GFX.Z1 = D + 2;

   for (Y = GFX.StartY, Offset = Y * GFX.PPL; Y <= GFX.EndY; Y++, Offset += GFX.PPL)
   {''', '''   GFX.Z1 = D + 2;
   bool batch = !clipcount && (!OnMain || !SUB_OR_ADD(4)) &&
                PPU.BGMode != 5 && PPU.BGMode != 6 && !GFX.Pseudo &&
                !IPPU.HalfWidthPixels && !IPPU.DoubleWidthPixels &&
                !IPPU.DoubleHeightPixels && !IPPU.Interlace &&
                GFX.PPL >= 256 && GFX.ZPitch == GFX.PPL && GFX.EndY < SNES_HEIGHT_EXTENDED;
   unsigned rows;
   D35_RASTER_ADD(7, GFX.EndY - GFX.StartY + 1);

   for (Y = GFX.StartY, Offset = Y * GFX.PPL; Y <= GFX.EndY; Y += rows, Offset += rows * GFX.PPL)
   {
      rows = batch ? d35_obj_rows(Y) : 1;
      D35_RASTER_ADD(8, 1);
      D35_RASTER_ADD(9, rows > 1 ? rows : 0);''')
        body = replace_once(body, '         if (PPU.OBJ[S].HFlip)', '''         if (rows > 1 && PPU.OBJ[S].VFlip)
         {
            BaseTile |= V_FLIP;
            TileLine = 56 - TileLine;
         }

         if (PPU.OBJ[S].HFlip)''')
        body = replace_once(body, '                  (*DrawTilePtr)(BaseTile | TileX, O, TileLine, 1);',
                            '                  (*DrawTilePtr)(BaseTile | TileX, O, TileLine, rows);')
        body = replace_once(body, '                     (*DrawClippedTilePtr)(BaseTile | TileX, O, x - X, NextPos - x, TileLine, 1);',
                            '                     (*DrawClippedTilePtr)(BaseTile | TileX, O, x - X, NextPos - x, TileLine, rows);')
        body = replace_once(body, '         tiles += GFX.OBJVisibleTiles[S];', '''         D35_RASTER_ADD(10, rows - 1);
         tiles += GFX.OBJVisibleTiles[S];''')
        if wide:
            # OBJ window changes still force a flush. During the flush each
            # sprite's renderer depends on static layer and palette state.
            body = replace_once(body, '!clipcount && (!OnMain || !SUB_OR_ADD(4))',
                                '!d35_fixed_active')
        if toggle:
            body = replace_once(body, 'bool batch = ', 'bool batch = d35_raster_enabled && ')
        text = text[:start] + body + text[end:]
    if counts or variant.startswith('raster-offset'):
        anchor = '#include "a7_demand_geometry.h"\n'
        payload = {'raster-offset-neon': '#define D35_RASTER_NEON\n',
                   'raster-offset-neon-isolated': '#define D35_RASTER_NEON\n#define D35_RASTER_ISOLATED\n',
                   'raster-offset-full': '#define D35_RASTER_FULL\n'}.get(variant, '')
        text = replace_once(text, anchor, anchor + payload + (HERE / 'snes-raster-offset.h').read_text() + '\n')
        gate = 'd35_raster_enabled && ' if toggle else ''
        text = replace_once(text, '''      case 2:
      case 4: /* Used by Puzzle Bobble */''', f'''      case 2:
         if ({gate}d35_offset_strip(bg, Z1, Z2)) return;
         /* Fall through to the scanline walker for unsupported layouts. */
      case 4: /* Used by Puzzle Bobble */''')
    gfx.write_text(text, newline='\n')


if __name__ == '__main__':
    prepare(Path(sys.argv[1]), sys.argv[2])
