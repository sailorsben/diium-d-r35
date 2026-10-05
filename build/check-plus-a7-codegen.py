"""Check the emitted A7 code, not just the source's inline intentions."""
from pathlib import Path
import re
out=Path(__file__).resolve().parent/'plus-a7-out'
assembly=(out/'disassembly.txt').read_text()
assert '<d35_render_tile>' not in assembly, 'Compiler retained a generic per-row mode dispatcher'
names=['DrawTile16','DrawTile16Add','DrawTile16Add1_2','DrawTile16Sub',
       'DrawTile16Sub1_2','DrawTile16FixedAdd1_2','DrawTile16FixedSub1_2']
for name in names:
    match=re.search(r'^\w+ <'+name+r'>:\n(.*?)(?=^\w+ <)',assembly,re.M|re.S)
    assert match and 'vtbl.8' in match[1] and 'vld2.8' in match[1], name
gfx=re.search(r'^\w+ <S9xUpdateScreen>:\n(.*?)(?=^\w+ <)',assembly,re.M|re.S)
assert gfx and 'vst1.16' in gfx[1] and 'vceq.i8' in gfx[1]
result='PASS: seven A7 tile modes specialized; deinterleaved palette NEON lookup and vector backdrop/window stores emitted\n'
(out/'codegen-check.log').write_text(result)
print(result,end='')
