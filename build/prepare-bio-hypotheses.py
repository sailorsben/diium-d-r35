"""Owned offline experiments; source trees and private replay evidence stay separate."""
from pathlib import Path
import json, shutil, re, subprocess, sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/bio-hypotheses-private'
assert not OUT.exists(), 'Preserve prior experiments'
OUT.mkdir()
names={0:'tile_calls',1:'clipped_calls',2:'cache_tile_conflict',3:'cache_palette_conflict',
       4:'cache_epoch_conflict',5:'cache_bits_conflict',6:'cache_new_rows',
       7:'palette_tables_built',8:'direct_gathers',9:'visible_neon_rows',
       **{16+i:f'tile_calls_lines_{i}' for i in range(9)},
       **{32+i:f'clipped_calls_lines_{i}' for i in range(9)},
       **{48+i:f'full_mode_{i}_calls' for i in range(7)},
       **{64+i:f'clipped_mode_{i}_calls' for i in range(7)}}
(OUT/'fields.json').write_text(json.dumps(names,indent=2)+'\n')
for variant in ['baseline','window','palette','palette-window']:
    dest=OUT/variant
    origin=ROOT/'build'/('render-census-window-batch-private' if 'window' in variant else 'render-census-bio-lazy')/'core'
    shutil.copytree(origin,dest/'core',ignore=shutil.ignore_patterns('.git','*.o','*.so'))
    core=dest/'core'
    (core/'source/hyp.h').write_text('extern unsigned long long d35_hyp[128];\n')
    p=core/'libretro.c';s=p.read_text()
    s='unsigned long long d35_hyp[128];\n__attribute__((visibility("default"))) void d35_hyp_read(unsigned long long *out) { for(unsigned i=0;i<128;i++){out[i]=d35_hyp[i];d35_hyp[i]=0;} }\n'+s
    p.write_text(s,newline='\n')
    p=core/'link.T';s=p.read_text();s=s.replace('d35_census_read;','d35_census_read; d35_hyp_read;');p.write_text(s,newline='\n')
    p=core/'source/tile.c';s='#include "hyp.h"\n'+p.read_text()
    for mode,suffix in enumerate(['','Add','Add1_2','Sub','Sub1_2','FixedAdd1_2','FixedSub1_2']):
        for clipped in (False,True):
            name=('DrawClippedTile16' if clipped else 'DrawTile16')+suffix
            match=re.search(r'void '+name+r'\([^\n]*\)\n\{',s);assert match,name
            hist=32 if clipped else 16;modebase=64 if clipped else 48
            code=f'\n   ++d35_hyp[{1 if clipped else 0}]; ++d35_hyp[{modebase+mode}]; if(LineCount<=8) ++d35_hyp[{hist}+LineCount];'
            s=s[:match.end()]+code+s[match.end():]
    if 'palette' in variant:
        a=s.index('static INLINE __attribute__((always_inline)) bool d35_render_tile(')
        b=s.index('\n}\n',a)+3
        s=s[:a]+(ROOT/'build/bio-palette-direct.h').read_text()+s[b:]
    p.write_text(s,newline='\n')
    p=core/'source/a7_color_cache.h';s=p.read_text()
    if 'palette' in variant:
        s=(ROOT/'build/bio-palette-cache.h').read_text()
    else:
        anchor='        entry->tile=tile;entry->palette=palette;entry->epoch=d35_color_epoch;entry->bits=bits;'
        assert s.count(anchor)==1
        s=s.replace(anchor,'''        if(entry->tile!=tile) ++d35_hyp[2];
        else if(entry->palette!=palette) ++d35_hyp[3];
        else if(entry->epoch!=d35_color_epoch) ++d35_hyp[4];
        else ++d35_hyp[5];
'''+anchor)
        s=s.replace('        ++d35_census[46];','        ++d35_census[46]; ++d35_hyp[6];')
        s=s.replace('        d35_palette_t table=d35_palette(palette,bits);','        ++d35_hyp[7];\n        d35_palette_t table=d35_palette(palette,bits);')
    p.write_text(s,newline='\n')
    runner=(ROOT/'build/replay-snes-scene.c').read_text()
    anchor='    char path[1024],line[256];'
    runner=runner.replace(anchor,'''    void (*hyp_read)(unsigned long long *);
    *(void **)(&hyp_read)=dlsym(c.handle,"d35_hyp_read");assert(hyp_read);
    unsigned long long unused[128];hyp_read(unused);
'''+anchor)
    runner=runner.replace('frame=(unsigned)total_frames;c.run();total_frames++;','''frame=(unsigned)total_frames;c.run();total_frames++;
                unsigned long long hyp[128];hyp_read(hyp);
                printf("HYP frame=%llu",(unsigned long long)total_frames);
                for(unsigned i=0;i<128;i++) { printf(" %llu",hyp[i]); }
                puts("");''')
    (dest/'replay.c').write_text(runner,newline='\n')
print('Prepared four isolated offline hypotheses; production source unchanged')
