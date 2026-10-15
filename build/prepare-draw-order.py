"""Fresh ordinary draw-order/control cores; no edits to qualified ancestors."""
from pathlib import Path
from hashlib import sha256
import json, re, shutil

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/draw-order-private-v1'
OLD = ROOT / 'build/demand-visible-private-v3'

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def write(p, s):
    p.write_text(s, encoding='utf-8', newline='\n')

def once(s, a, b):
    assert s.count(a) == 1, a
    return s.replace(a, b)

def main():
    assert not OUT.exists()
    assert json.loads((OLD / 'qualification.json').read_text())['passed']
    frozen = json.loads((OLD / 'frozen.json').read_text())
    for tree in (OLD, ROOT / 'build/priority-research-private-v1', ROOT / 'build/compiler-research-private-v1'):
        for p in tree.rglob('*'):
            if p.is_file() and p.suffix in ('.c', '.h', '.so', '.json'):
                frozen[p.relative_to(ROOT).as_posix()] = digest(p)
    OUT.mkdir()
    write(OUT / 'frozen.json', json.dumps(frozen, indent=2) + '\n')
    for label in ('boundary', 'priority'):
        core = OUT / label
        shutil.copytree(OLD / 'core', core, ignore=shutil.ignore_patterns('*.o', '*.so'))
        p = core / 'Makefile'
        write(p, p.read_text() + '\n# Freeze the entire SPC/DSP translation unit outside LTO.\nsource/apu_blargg.o: CFLAGS += -fno-lto\n')
        if label == 'boundary':
            continue
        shutil.copy2(ROOT / 'build/draw-order.h', core / 'source/a7_draw_order.h')
        p = core / 'source/gfx.c'
        s = p.read_text()
        s = '#define D35_DRAW_ORDER\n#include "a7_draw_order.h"\n' + s
        s = once(s, 'static void RenderScreen(uint8_t* Screen, bool sub, bool force_no_add, uint8_t D)',
                 'unsigned d35_bg_priority_filter;\nstatic void RenderScreen(uint8_t* Screen, bool sub, bool force_no_add, uint8_t D)')
        anchor = '''      case 0:
      case 1:
         if (OB)'''
        replacement = '''      case 0:
      case 1:
      {
         unsigned order_top = PPU.BGMode == 1 && PPU.BG3Priority && BG2 &&
            (PPU.Mosaic <= 1 || !PPU.BGMosaic[2]) && !GFX.Pseudo && GFX.PPL == 256 &&
            !IPPU.DoubleWidthPixels && !IPPU.DoubleHeightPixels && !IPPU.HalfWidthPixels;
         if (order_top)
         {
            SelectTileRenderer(normal_all || !SUB_OR_ADD(2));
            d35_bg_priority_filter = D + 17;
            DrawBackground(PPU.BGMode, 2, D + 3, D + 17);
            d35_bg_priority_filter = 0;
         }
         if (OB)'''
        s = once(s, anchor, replacement)
        anchor = '            DrawBackground(PPU.BGMode, 2, D + 3, PPU.BG3Priority ? D + 17 : D + 6);'
        s = once(s, anchor, '            if (order_top) d35_bg_priority_filter = D + 3;\n' + anchor + '\n            d35_bg_priority_filter = 0;')
        a, b = s.index(replacement), s.index('      case 2:', s.index(replacement))
        block = s[a:b]
        block = once(block, '         break;', '         break;\n      }')
        write(p, s[:a] + block + s[b:])
        p = core / 'source/tile.c'
        s = '#define D35_DRAW_ORDER\n#include "a7_draw_order.h"\n' + p.read_text()
        s, n = re.subn(r'(void Draw\w+\([^\n]+\)\n\{)', r'\1\n   if (!D35_PRIORITY_ACCEPT) return;', s)
        assert n >= 14
        write(p, s)
        p = core / 'source/a7_common_batch.h'
        s = p.read_text()
        for name in ('d35_fused_plain', 'd35_fused_sole', 'd35_batch_tile_mode_base'):
            start = s.index(name + '(')
            brace = s.index('{', start)
            s = s[:brace + 1] + '\n if (!D35_PRIORITY_ACCEPT) return 1;' + s[brace + 1:]
        write(p, s)
        p = core / 'source/a7_pearl_sub2.h'
        s = p.read_text()
        brace = s.index('{', s.index('d35_sub2('))
        write(p, s[:brace + 1] + '\n if (!D35_PRIORITY_ACCEPT) return 1;' + s[brace + 1:])
    for n in ('compare.c', 'demand-equivalence.c'):
        shutil.copy2(ROOT / 'build/ppu-refinements-private-v4' / n, OUT / n)
    for n, h in frozen.items():
        assert digest(ROOT / n) == h, n
    print('Prepared ordinary priority and fixed-APU control; all qualified ancestors exact')

if __name__ == '__main__':
    main()
