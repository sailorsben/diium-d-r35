"""Apply the bounded window experiment to a fresh private census core only."""
from pathlib import Path
import shutil
import subprocess
import sys
import re

ROOT = Path(__file__).resolve().parent.parent
name = sys.argv[1] if len(sys.argv) > 1 else 'render-census-window-batch-private'
assert re.fullmatch(r'render-census-window-[a-z0-9-]+', name), 'Owned isolated output only'
OUT = ROOT / 'build' / name
assert not OUT.exists(), 'Keep prior experiments immutable'
subprocess.run([sys.executable, str(ROOT / 'build/prepare-render-census.py'), OUT.name], check=True)
CORE = OUT / 'core'
shutil.copy2(ROOT / 'build/plus-a7-window.h', CORE / 'source/a7_window.h')
path = CORE / 'source/ppu.c'
text = '#include "a7_window.h"\n' + path.read_text(encoding='utf-8')
for address in ('0x2128', '0x2129'):
    start = text.index('      case ' + address + ':')
    end = text.index('         break;', start)
    section = text[start:end]
    assert section.count('FLUSH_REDRAW();') == 1
    section = section.replace('FLUSH_REDRAW();', 'if(!d35_window_defer()) { FLUSH_REDRAW(); }')
    text = text[:start] + section + text[end:]
path.write_text(text, encoding='utf-8', newline='\n')
path = CORE / 'source/gfx.c'
text = path.read_text(encoding='utf-8')
anchor = '#include "gfx.h"'
assert text.count(anchor) == 1
text = text.replace(anchor, anchor + '\n#define D35_WINDOW_IMPLEMENTATION\n#include "a7_window.h"')
anchor = 'void S9xStartScreenRefresh(void)\n{'
assert text.count(anchor) == 1
text = text.replace(anchor, anchor + '\n   d35_window_reset();')
anchor = 'void RenderLine(uint8_t C)\n{'
assert text.count(anchor) == 1
text = text.replace(anchor, anchor + '\n   d35_window_capture(C);')
start = text.index('static void DrawBackground(uint32_t BGMode, uint32_t bg, uint8_t Z1, uint8_t Z2)\n{')
end = text.index('\n}\n', start) + 2
section = text[start:end]
anchor = '      int32_t clipcount;'
assert section.count(anchor) == 1
section = section.replace(anchor, anchor + '\n      struct d35_window_clip window_clip;\n      unsigned window_custom=bg==0 && d35_window_fetch(Y,GFX.pCurrentClip==&IPPU.Clip[1],&window_clip);')
anchor = '(VOffset != LineData [Y + Lines].BG[bg].VOffset) || (HOffset != LineData [Y + Lines].BG[bg].HOffset)'
assert section.count(anchor) == 1
section = section.replace(anchor, anchor + ' || (bg==0 && !d35_window_same(Y,Y+Lines))')
section = section.replace('GFX.pCurrentClip->Count [bg]', '(window_custom?window_clip.count:GFX.pCurrentClip->Count [bg])')
section = section.replace('GFX.pCurrentClip->Left [clip][bg]', '(window_custom?window_clip.left[clip]:GFX.pCurrentClip->Left [clip][bg])')
section = section.replace('GFX.pCurrentClip->Right [clip][bg]', '(window_custom?window_clip.right[clip]:GFX.pCurrentClip->Right [clip][bg])')
text = text[:start] + section + text[end:]
path.write_text(text, encoding='utf-8', newline='\n')
print('Prepared isolated window batch experiment, preserving shipping1.19 core')
