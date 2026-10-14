"""Build an owned, bounded geometry-sharing experiment; no device installer."""
from pathlib import Path
from hashlib import sha256
import json,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/shared-geometry-private-v1'
BASE=ROOT/'build/common-band-private-v3'
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def edit(p,old,new):
 s=p.read_text(encoding='utf-8');assert s.count(old)==1,(p,old,s.count(old));write(p,s.replace(old,new))
def main():
 assert not OUT.exists();assert sha256((BASE/'plus-a7.so').read_bytes()).hexdigest()=='e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129'
 OUT.mkdir();shutil.copytree(BASE/'core',OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'))
 core=OUT/'core';p=core/'source/gfx.c'
 edit(p,'#include "a7_common_band.h"','#include "a7_common_batch.h"\n#include "a7_shared_geometry.h"\n#include "a7_common_band.h"')
 edit(p,'   SC0 = (uint16_t*) &Memory.VRAM[PPU.BG[bg].SCBase << 1];\n\n   if (PPU.BG[bg].SCSize & 1)\n      SC1 = SC0 + 1024;\n   else\n      SC1 = SC0;\n\n   if (SC1 >= (uint16_t*)(Memory.VRAM + 0x10000))',
        '   if(d35_shared_begin(BGMode,bg,batch_ok,&batch,Z1,Z2))return;\n\n   SC0 = (uint16_t*) &Memory.VRAM[PPU.BG[bg].SCBase << 1];\n\n   if (PPU.BG[bg].SCSize & 1)\n      SC1 = SC0 + 1024;\n   else\n      SC1 = SC0;\n\n   if (SC1 >= (uint16_t*)(Memory.VRAM + 0x10000))')
 # Restrict edits to the ordinary background walker, after its special modes.
 s=p.read_text(encoding='utf-8');a=s.index('static void DrawBackground(uint32_t');b=s.index('#define RENDER_BACKGROUND_MODE7',a);part=s[a:b]
 assert part.count('         if (HPos & 7)\n         {')==1
 part=part.replace('         if (HPos & 7)\n         {','         if (HPos & 7)\n         {\n            d35_shared_edge();')
 part=part.replace('         if (Count)\n         {','         if (Count)\n         {\n            d35_shared_edge();')
 assert part.endswith('}\n\n');part=part[:-3]+'   d35_shared_capture=0;\n}\n\n';write(p,s[:a]+part+s[b:])
 edit(p,'   int32_t x2 = 1;','   d35_shared_region();\n   int32_t x2 = 1;')
 p=core/'source/a7_common_band.h'
 edit(p,'if(w->sole&&d35_sub2(w->sole,actual,w->offset,w->line,w->lines)){}',
      'd35_shared_record(actual,w->offset,w->line,w->lines); '+chr(92)+'\n  if(w->sole&&d35_sub2(w->sole,actual,w->offset,w->line,w->lines)){}')
 shutil.copy2(ROOT/'build/shared-bg-geometry.h',core/'source/a7_shared_geometry.h')
 # Layout export reports this ARM/QEMU process, not archived A7 heap addresses.
 p=core/'source/tile.c';s=p.read_text(encoding='utf-8');s+='''\n#ifdef D35_PLUS_A7
__attribute__((visibility("default"))) void d35_layout_read(unsigned *p){
 p[0]=(unsigned)(uintptr_t)IPPU.TileCache[0];p[1]=(unsigned)(uintptr_t)IPPU.TileCache[1];p[2]=(unsigned)(uintptr_t)IPPU.TileCache[2];
 p[3]=sizeof(d35_palette_t);p[4]=__alignof__(d35_palette_t);p[5]=sizeof(struct d35_palette_entry);
 p[6]=(unsigned)((char *)&d35_palette_entries[0].table-(char *)&d35_palette_entries[0]);
 p[7]=(unsigned)(uintptr_t)d35_palette_entries;
}
#endif
''';write(p,s)
 edit(core/'link.T','d35_profile_end;','d35_profile_end; d35_shared_read; d35_layout_read;')
 s=(BASE/'ordinary-compare.c').read_text(encoding='utf-8')
 s=s.replace('    unsigned char *a=malloc(size),*b=malloc(size);', '''    void (*shared)(unsigned long long *);void (*layout)(unsigned *);
    *(void **)(&shared)=dlsym(candidate.handle,"d35_shared_read");assert(shared);
    *(void **)(&layout)=dlsym(candidate.handle,"d35_layout_read");assert(layout);
    unsigned lp[8];layout(lp);printf("LAYOUT");for(unsigned j=0;j<8;j++)printf(" %u",lp[j]);puts("");
    unsigned long long discard[16];shared(discard);
    unsigned char *a=malloc(size),*b=malloc(size);''')
 s=s.replace('        unsigned long long sc[8]={0};', '''        unsigned long long sh[16];shared(sh);printf("SHARED %u",frame);
        for(unsigned j=0;j<16;j++){printf(",%llu",sh[j]);}puts("");
        unsigned long long sc[8]={0};''')
 write(OUT/'compare.c',s)
 write(OUT/'inputs.json',json.dumps({'baseline_core_sha256':sha256((BASE/'plus-a7.so').read_bytes()).hexdigest(),'baseline_sources':{p.relative_to(BASE).as_posix():sha256(p.read_bytes()).hexdigest() for p in (BASE/'core').rglob('*') if p.is_file() and p.suffix in ('.c','.h')}},indent=2)+'\n')
 print('Prepared isolated BG0 command reuse; no timing, framebuffer or card changes')
if __name__=='__main__':main()
