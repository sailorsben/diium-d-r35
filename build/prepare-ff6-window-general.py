"""Fresh offline generalized-window candidate and inward flush census."""
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ff6-effect-screen-private-v1'
for name in ('general', 'trace-current'):
    dest=OUT/name
    assert not dest.exists()
    core=dest/'core'
    shutil.copytree(OUT/'core',core,ignore=shutil.ignore_patterns('*.o','*.so','.git'))
    if name=='general':
        s='#define D35_EFFECT_COUNTS\n'+(ROOT/'build/plus-a7-multi-window.h').read_text()
        (core/'source/a7_window.h').write_text(s,newline='\n')
    p=core/'libretro.c'
    p.write_text(p.read_text()+'''
unsigned long long d35_flushes[64];
void d35_flush_ppu(unsigned reg) {
 if(reg>=0x2100 && reg<0x2140 && IPPU.RenderThisFrame && IPPU.PreviousLine!=IPPU.CurrentLine)
  ++d35_flushes[reg-0x2100];
}
__attribute__((visibility("default"))) void d35_flush_read(unsigned long long *out) {
 for(unsigned i=0;i<64;i++){out[i]=d35_flushes[i];d35_flushes[i]=0;}}
''',newline='\n')
    p=core/'source/ppu.c';s=p.read_text()
    s='void d35_flush_ppu(unsigned);\n'+s
    start,end=s.index('void S9xSetPPU('),s.index('uint8_t S9xGetPPU(')
    s=s[:start]+s[start:end].replace('FLUSH_REDRAW();','{ d35_flush_ppu(Address);FLUSH_REDRAW(); }')+s[end:]
    p.write_text(s,newline='\n')
    p=core/'link.T'
    p.write_text(p.read_text().replace('d35_screen_read;', 'd35_screen_read; d35_flush_read;'),newline='\n')
s=(OUT/'screen.c').read_text()
s=s.replace('    puts("ROW columns=', '    void (*read_flush)(unsigned long long *);*(void **)(&read_flush)=dlsym(candidate.handle,"d35_flush_read");assert(read_flush);read_flush(clear);\n    puts("ROW columns=')
s=s.replace('            seen_init+=sc[0];seen_table+=sc[1];', '''            seen_init+=sc[0];seen_table+=sc[1];
            unsigned long long fl[64];read_flush(fl);
            printf("FLUSH frame=%u",f);for(unsigned z=0;z<64;z++)if(fl[z])printf(" %04x=%llu",0x2100+z,fl[z]);puts("");''')
(OUT/'trace-screen.c').write_text(s,newline='\n')
print('Prepared fresh current/general window variants and per-register rendered-flush census')
