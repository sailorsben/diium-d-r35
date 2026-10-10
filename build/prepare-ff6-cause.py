"""Make an isolated behavior trace core; never alter the shipping core or card."""
from pathlib import Path
from hashlib import sha256
import json
import shutil

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/ff6-cause-private'
CORE = OUT / 'core'
assert not CORE.exists(), 'Keep prior traces immutable'
release = json.loads((ROOT / 'releases/snes-mvp-1.19/manifest.json').read_text())
assert sha256((ROOT / 'build/plus-a7-out/plus-a7.so').read_bytes()).hexdigest() == release['core_sha256']
shutil.copytree(ROOT / 'build/snes9x2005', CORE,
                ignore=shutil.ignore_patterns('.git', '*.o', '*.so'))
shutil.copy2(ROOT / 'build/ff6-bio-blast-model.h', CORE / 'source/bio-blast-model.h')
header = 'void d35_cause_pc(unsigned);\nvoid d35_cause_ppu(unsigned,unsigned);\nvoid d35_cause_flush(unsigned);\n'
for name in ('cpuexec.c', 'ppu.c'):
    path = CORE / 'source' / name
    text = path.read_text(encoding='utf-8')
    if name == 'cpuexec.c':
        text = header + text
        anchor = 'CPU.PCAtOpcodeStart = CPU.PC;'
        assert text.count(anchor) == 4
        text = text.replace(anchor, anchor + '\n         d35_cause_pc(ICPU.ShiftedPB+(unsigned)(CPU.PC-CPU.PCBase));')
    else:
        text = header + text
        anchor = 'void S9xSetPPU(uint8_t Byte, uint16_t Address)\n{'
        assert text.count(anchor) == 1
        text = text.replace(anchor, anchor + '\n   d35_cause_ppu(Address,Byte);')
        start, end = text.index('void S9xSetPPU('), text.index('uint8_t S9xGetPPU(')
        text = text[:start] + text[start:end].replace('FLUSH_REDRAW();', '{ d35_cause_flush(Address); FLUSH_REDRAW(); }') + text[end:]
    path.write_text(text, encoding='utf-8', newline='\n')
path = CORE / 'libretro.c'
text = path.read_text(encoding='utf-8')
text = 'void d35_cause_begin(void);\nvoid d35_cause_end(void);\n' + text
assert text.count('   S9xMainLoop();') == 1
text = text.replace('   S9xMainLoop();', '   d35_cause_begin();\n   S9xMainLoop();\n   d35_cause_end();')
text += '\n' + (ROOT / 'build/ff6-cause-trace.c').read_text(encoding='utf-8')
path.write_text(text, encoding='utf-8', newline='\n')
print('Prepared separate ROM behavior trace; shipping core unchanged')
