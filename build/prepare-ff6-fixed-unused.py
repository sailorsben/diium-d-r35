"""Test the source-derived unused-fixed-color predicate, separately from windows."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ff6-effect-screen-private-v1'
dest=OUT/'fixed-unused';assert not dest.exists()
core=dest/'core'
shutil.copytree(OUT/'general/core',core,ignore=shutil.ignore_patterns('*.o','*.so','.git'))
shutil.copy2(ROOT/'build/plus-a7-fixed-unused.h',core/'source/fixed-unused.h')
p=core/'source/ppu.c';s='#include "fixed-unused.h"\n'+p.read_text()
old='if(d35_fixed_color_changes(Byte,PPU.FixedColourRed,';assert s.count(old)==1
s=s.replace(old,'if(d35_fixed_color_used(Memory.FillRAM[0x2130],Memory.FillRAM[0x2131],Memory.FillRAM[0x2133]) &&\n               d35_fixed_color_changes(Byte,PPU.FixedColourRed,')
p.write_text(s,newline='\n')
print('Prepared isolated fixed-unused hypothesis; effective register updates stay intact')
