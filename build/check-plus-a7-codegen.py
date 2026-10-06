"""Check the emitted A7 code, not just the source's inline intentions."""
from pathlib import Path
import re
import subprocess
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
decode=re.search(r'^\w+ <ConvertTile(?:\.lto_priv\.\d+)?>:\n(.*?)(?=^\w+ <)',assembly,re.M|re.S)
assert decode and 'vshl.u8' in decode[1] and 'vst1.8' in decode[1], 'Planar NEON decode missing'
symbols=subprocess.check_output(['arm-linux-gnueabihf-readelf','--dyn-syms','--wide',str(out/'plus-a7.so')],text=True)
exports=set(re.findall(r'GLOBAL DEFAULT\s+(?!UND)\d+\s+(\w+)',symbols))
assert {'retro_run','retro_load_game','retro_unserialize','d35_profile_begin','d35_profile_end'}<=exports
assert all(n.startswith('retro_') or n in ('d35_profile_begin','d35_profile_end') for n in exports), exports
build=(out/'build.log').read_text()
assert '-O3 -DNDEBUG -flto=4 -fno-semantic-interposition -fvisibility=hidden' in build
assert '-fno-builtin' not in build and '-shared -nostdlib -flto=4 -O3' in build
result=('PASS: seven A7 tile modes specialized; deinterleaved palette NEON lookup and vector backdrop/window stores emitted\n'
        'PASS: planar decoder NEON emitted; O3/LTO and internal visibility applied; only libretro and two owned phase exports\n')
(out/'codegen-check.log').write_text(result)
print(result,end='')
