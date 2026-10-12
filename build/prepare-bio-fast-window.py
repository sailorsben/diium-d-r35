"""Isolated prefix-validity variant; preserve all four prior experiments."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/bio-hypotheses-private/palette-fast-window'
assert not OUT.exists()
shutil.copytree(OUT.parent/'palette-window',OUT,
                ignore=shutil.ignore_patterns('*.o','*.so','*.log','capture','replay'))
p=OUT/'core/source/a7_window.h';s=p.read_text()
anchor='static struct d35_window_row d35_window_rows[256];'
s=s.replace(anchor,anchor+'''
static unsigned d35_invalid_prefix[257],d35_captured_until,d35_capture_ordered;
static void d35_window_record_validity(unsigned row,unsigned valid)
{
    if(row==d35_captured_until || row+1==d35_captured_until) {
        d35_invalid_prefix[row+1]=d35_invalid_prefix[row]+!valid;
        if(row==d35_captured_until) ++d35_captured_until;
    } else d35_capture_ordered=0;
}
''')
s=s.replace('void d35_window_reset(void) { memset(d35_window_rows,0,sizeof(d35_window_rows)); }',
'''void d35_window_reset(void) {
    memset(d35_window_rows,0,sizeof(d35_window_rows));
    d35_captured_until=0;d35_capture_ordered=1;d35_invalid_prefix[0]=0;
}''')
s=s.replace('    if(!d35_window_eligible()) return;',
'''    if(!d35_window_eligible()) { d35_window_record_validity(row&255u,0);return; }''')
anchor='    r->sub_mask=(Memory.FillRAM[0x212d]&Memory.FillRAM[0x212f]&1u)!=0;'
s=s.replace(anchor,anchor+'\n    d35_window_record_validity(row&255u,1);')
anchor='    for(row=IPPU.PreviousLine;row<(unsigned)IPPU.CurrentLine;row++)'
assert s.count(anchor)==1
s=s.replace(anchor,'''    if(d35_capture_ordered && (unsigned)IPPU.PreviousLine<=(unsigned)IPPU.CurrentLine &&
       (unsigned)IPPU.CurrentLine<=d35_captured_until)
        return d35_invalid_prefix[IPPU.PreviousLine]==d35_invalid_prefix[IPPU.CurrentLine];
'''+anchor)
p.write_text(s,newline='\n')
# Independently compare the fast query to the original scan under varied
# eligible/ineligible, missing, repeated and out-of-order row captures.
oracle=(ROOT/'build/plus-a7-window-check.c').read_text().replace('"plus-a7-window.h"','"bio-fast-window.h"')
anchor='    puts("PASS: retained row ownership, frame reset, missing rows and fallback guards");'
extra='''
    for(unsigned trial=0;trial<128;trial++) {
        eligible();unsigned seed=trial+1;
        for(unsigned step=0;step<300;step++) {
            seed=seed*1664525u+1013904223u;
            unsigned row=trial<64 ? step%256 : (seed>>24);
            PPU.ForcedBlanking=(seed&7u)==0;
            d35_window_capture(row);PPU.ForcedBlanking=false;
            unsigned end=(seed>>16)%257,start=(seed>>8)%(end+1);
            IPPU.PreviousLine=start;IPPU.CurrentLine=end;
            unsigned expected=1;
            for(unsigned q=start;q<end;q++) if(!d35_window_rows[q].valid) {expected=0;break;}
            assert(d35_window_defer()==expected);
        }
    }
    puts("PASS: 38400 prefix queries match independent original validity scan");
'''
assert oracle.count(anchor)==1
oracle=oracle.replace(anchor,anchor+extra)
(OUT.parent/'fast-window-check.c').write_text(oracle,newline='\n')
(OUT.parent/'bio-fast-window.h').write_text(s,newline='\n')
print('Prepared constant-time ordered-capture query; unordered captures retain original scan')
