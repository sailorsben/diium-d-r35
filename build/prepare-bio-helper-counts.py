"""Separate offline helper-count copy; preserve correctness candidates."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
base=ROOT/'build/bio-hypotheses-private'
dest=base/'palette-fast-window-counts'
assert not dest.exists()
shutil.copytree(base/'palette-fast-window',dest,
    ignore=shutil.ignore_patterns('*.o','*.so','*.log','capture','replay'))
p=dest/'core/source/a7_color_cache.h';s=p.read_text()
s=s.replace('    uintptr_t address=','    ++d35_hyp[10];\n    uintptr_t address=')
p.write_text(s,newline='\n')
p=dest/'core/source/a7_window.h';s=p.read_text()
s=s.replace('static unsigned d35_invalid_prefix','extern unsigned long long d35_hyp[128];\nstatic unsigned d35_invalid_prefix')
s=s.replace('    if(!IPPU.RenderThisFrame || !d35_window_eligible()) return 0;',
            '    ++d35_hyp[80];\n    if(!IPPU.RenderThisFrame || !d35_window_eligible()) return 0;')
s=s.replace('IPPU.PreviousLine<=(unsigned)IPPU.CurrentLine',
            '(unsigned)IPPU.PreviousLine<=(unsigned)IPPU.CurrentLine')
s=s.replace('        return d35_invalid_prefix[IPPU.PreviousLine]==d35_invalid_prefix[IPPU.CurrentLine];',
'''    {
        ++d35_hyp[81];d35_hyp[82]+=(unsigned)IPPU.CurrentLine-(unsigned)IPPU.PreviousLine;
        return d35_invalid_prefix[IPPU.PreviousLine]==d35_invalid_prefix[IPPU.CurrentLine];
    }
    ++d35_hyp[83];''')
s=s.replace('        if(row>=256 || !d35_window_rows[row].valid) return 0;',
            '        { ++d35_hyp[84];if(row>=256 || !d35_window_rows[row].valid) return 0; }')
p.write_text(s,newline='\n')
print('Prepared separate helper-count replay')
