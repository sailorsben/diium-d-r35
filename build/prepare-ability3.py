"""Create separately owned fixed-operand palette hypothesis and short suite."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT/'build/ability-regression-private-v1'
OUT=ROOT/'build/ability3-private-v1'
def prepare():
    assert not OUT.exists();OUT.mkdir()
    shutil.copytree(OLD/'core',OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'))
    source=OUT/'core/source'
    shutil.copy2(ROOT/'build/plus-a7-math-palette.h',source/'a7_math_palette.h')
    p=source/'tile.c';s=p.read_text().replace('#include "a7_color_cache.h"','#include "a7_color_cache.h"\n#include "a7_math_palette.h"')
    s=s.replace('d35_palette_t table;bool ready=false;', 'd35_palette_t table,math_table;bool ready=false,math_ready=false;')
    start=s.index('            if(!ready) { table=d35_cached_palette')
    end=s.index('            d35_store(screen,color,mask);',start)
    s=s[:start]+'''            D35_MATH_COUNT(0);
            uint8x8_t sd=mode?vld1_u8(GFX.SubZBuffer+offset):vdup_n_u8(0);
            bool fixed_only=mode && !vget_lane_u64(vreinterpret_u64_u8(
                vbic_u8(mask,vceq_u8(sd,vdup_n_u8(1)))),0);
            d35_palette_t used;
            if(fixed_only) {
                D35_MATH_COUNT(1);
                if(!math_ready) {
                    unsigned operation=mode<=2?1:mode<=4?3:mode;
                    math_table=d35_cached_math_palette(colors,BG.BitShift,GFX.FixedColour,operation);
                    math_ready=true;
                }
                used=math_table;
            } else {
                if(!ready) { table=d35_cached_palette(colors,BG.BitShift);ready=true; }
                used=table;
            }
            uint8x8x2_t zip=vzip_u8(vtbl2_u8(used.low,idx),vtbl2_u8(used.high,idx));
            uint16x8_t color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));
            if(mode && !fixed_only)color=d35_blend(color,sd,screen+GFX.Delta,GFX.FixedColour,mode,mask);
''' +s[end:]
    p.write_text(s,newline='\n')
    # Epoch wrap must clear both caches, including a long-unvisited math entry.
    p=source/'a7_color_cache.h';s=p.read_text().replace('void d35_color_tile_changed','static inline void d35_math_palette_reset(void);\nvoid d35_color_tile_changed')
    s=s.replace('memset(d35_palette_entries,0,sizeof(d35_palette_entries));','memset(d35_palette_entries,0,sizeof(d35_palette_entries));d35_math_palette_reset();')
    p.write_text(s,newline='\n')
    for n in ('runner','cases'):shutil.copytree(OLD/n,OUT/n)
    for p in OLD.glob('*.h'):shutil.copy2(p,OUT/p.name)
    for n in ('main.c','compare.c','launch.sh','dispatch.sh','ROM-PATH.txt'):
        (OUT/n).write_text((OLD/n).read_text().replace('1.19-ability2','1.19-ability3').replace('snes-ability2','snes-ability3'),newline='\n')
    for p in (OUT/'runner').glob('*.[ch]'):
        p.write_text(p.read_text().replace('1.19-ability2','1.19-ability3'),newline='\n')
    plan=json.loads((OLD/'plan.json').read_text());plan['version']='1.19-ability3'
    plan['returned_archive']='a7-pair-before-20261013T162915Z'
    plan['authorization']='Evaluate returned I: test, fix supported bugs, and rearm a new test.'
    plan['hypothesis']='Reuse exact fixed-operand math palettes for active subdepth1 rows.'
    (OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    shutil.copytree(OUT/'core',OUT/'counted-core')
    p=OUT/'counted-core/source/tile.c';p.write_text('#define D35_MATH_COUNTS\n'+p.read_text(),newline='\n')
    p=OUT/'counted-core/link.T';s=p.read_text().replace('global:', 'global:\n        d35_math_read;');p.write_text(s,newline='\n')
    p=OUT/'compare.c';s=p.read_text().replace('unsigned long long clear[128];', 'void (*math_read)(unsigned long long *);\n    *(void **)(&math_read)=dlsym(candidate.handle,"d35_math_read");\n    unsigned long long clear[128];if(math_read)math_read(clear);')
    s=s.replace('unsigned long long sc[8]={0};', 'if(math_read){unsigned long long mc[8];math_read(mc);printf("MATH %u,%llu,%llu,%llu,%llu\\n",frame,mc[0],mc[1],mc[2],mc[3]);}\n        unsigned long long sc[8]={0};')
    p.write_text(s,newline='\n')
    s=(ROOT/'build/build-ability-regression.sh').read_text().replace('ability-regression-private-v1','ability3-private-v1').replace('ability2','ability3')
    s=s.replace('cp "$out/core/snes9x2005_plus_libretro.so"', '''(cd "$out/counted-core";make -B -j4 platform=unix USE_BLARGG_APU=1 LOAD_FROM_MEMORY=1 \\
 CC="arm-linux-gnueabihf-gcc $flags" \\
 SHARED='-shared -nostdlib -flto=4 -O3 -Wl,-Bsymbolic-functions -Wl,--no-undefined -Wl,--version-script=link.T' \\
 LDFLAGS='-L../../sysroot/lib -Wl,--no-as-needed -l:libm-2.30.so -l:libc-2.30.so -l:libgcc_s.so.1') > "$out/counted-build.log" 2>&1
cp "$out/core/snes9x2005_plus_libretro.so"''')
    (ROOT/'build/build-ability3.sh').write_text(s,newline='\n')
if __name__=='__main__':prepare()
