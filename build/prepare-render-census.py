"""Create a local-only instrumented copy of the pinned A7 core.

Counts work in the actual snapshot replay, never uses QEMU timing as hardware
performance evidence. Does not modify the shipping source or candidate binary.
"""
from pathlib import Path
import re,shutil,json,sys
ROOT=Path(__file__).resolve().parent
OUT=ROOT/(sys.argv[1] if len(sys.argv)>1 else 'render-census')
assert OUT.parent==ROOT and OUT.name.startswith('render-census')
assert not OUT.exists(), 'Keep each census immutable; choose a fresh output directory'
shutil.copytree(ROOT/'snes9x2005',OUT/'core',ignore=shutil.ignore_patterns('.git','*.o','*.so'))
CORE=OUT/'core'
header='extern unsigned long long d35_census[128];\n'
(CORE/'source/census.h').write_text(header,encoding='utf-8',newline='\n')
p=CORE/'source/gfx.c';s=p.read_text();s='#include "census.h"\n'+s
s=s.replace('void S9xUpdateScreen(void)\n{','void S9xUpdateScreen(void)\n{\n   ++d35_census[0];')
s=s.replace('   GFX.S = Screen;','   d35_census[1+PPU.BGMode] += GFX.EndY-GFX.StartY+1;\n   GFX.S = Screen;')
s=s.replace('static void DrawBackground(uint32_t BGMode, uint32_t bg, uint8_t Z1, uint8_t Z2)\n{',
    'static void DrawBackground(uint32_t BGMode, uint32_t bg, uint8_t Z1, uint8_t Z2)\n{\n   d35_census[9+bg] += GFX.EndY-GFX.StartY+1;')
for i,name in enumerate(['DrawBackgroundMosaic','DrawBackgroundOffset','DrawBackgroundMode5']):
    match=re.search(r'static void '+name+r'\([^\n]*\)\n\{',s);assert match
    s=s[:match.end()]+f'\n   ++d35_census[{13+i}];'+s[match.end():]
for i,suffix in enumerate(['','Add','Add1_2','Sub','Sub1_2']):
    match=re.search(r'static void DrawBGMode7Background16'+suffix+r'\([^\n]*\)\n\{',s);assert match
    s=s[:match.end()]+f'\n   d35_census[{16+i}] += GFX.EndY-GFX.StartY+1;'+s[match.end():]
p.write_text(s,encoding='utf-8',newline='\n')
p=CORE/'source/tile.c';s='#include "census.h"\n'+p.read_text()
s=s.replace('static uint8_t ConvertTile(uint8_t* pCache, uint32_t TileAddr)\n{',
    'static uint8_t ConvertTile(uint8_t* pCache, uint32_t TileAddr)\n{\n   ++d35_census[21];')
for i,suffix in enumerate(['','Add','Add1_2','Sub','Sub1_2','FixedAdd1_2','FixedSub1_2']):
    for clipped,base in [(False,24),(True,32)]:
        name=('DrawClippedTile16' if clipped else 'DrawTile16')+suffix
        match=re.search(r'void '+name+r'\([^\n]*\)\n\{',s);assert match,name
        s=s[:match.end()]+f'\n   d35_census[{base+i}] += LineCount;'+s[match.end():]
p.write_text(s,encoding='utf-8',newline='\n')
p=CORE/'source/a7_tile.h';s=p.read_text()
anchor='    if(!vget_lane_u64(vreinterpret_u64_u8(mask),0)) return;'
assert s.count(anchor)==1
s=s.replace(anchor,'''    ++d35_census[40];
    if(!vget_lane_u64(vreinterpret_u64_u8(vcgt_u8(vdup_n_u8(z1),old_depth)),0)) ++d35_census[43];
    if(!vget_lane_u64(vreinterpret_u64_u8(mask),0)) { ++d35_census[41]; return; }
    if(vget_lane_u64(vreinterpret_u64_u8(mask),0)==UINT64_MAX) ++d35_census[42];''')
p.write_text(s,newline='\n')
p=CORE/'source/ppu.c';s='#include "census.h"\n'+p.read_text()
start=s.index('void S9xSetPPU(');end=s.index('uint8_t S9xGetPPU(',start)
region=s[start:end].replace('FLUSH_REDRAW();','{ if(IPPU.PreviousLine!=IPPU.CurrentLine && Address>=0x2100 && Address<0x2140) ++d35_census[64+Address-0x2100];\n            FLUSH_REDRAW(); }')
anchor='      case 0x2132:\n'
assert region.count(anchor)==1
region=region.replace(anchor,anchor+'''         if(IPPU.PreviousLine!=IPPU.CurrentLine && Byte!=Memory.FillRAM[0x2132]) {
            unsigned value=Byte&31;
            if(((Byte&128) && PPU.FixedColourBlue!=value) ||
               ((Byte&64) && PPU.FixedColourGreen!=value) ||
               ((Byte&32) && PPU.FixedColourRed!=value)) ++d35_census[44];
            else ++d35_census[45];
         }
''')
s=s[:start]+region+s[end:];p.write_text(s,newline='\n')
p=CORE/'source/ppu.h';s='#include "census.h"\n'+p.read_text()
start=s.index('static INLINE void REGISTER_2122(');region=s[start:]
region=region.replace('FLUSH_REDRAW();','if(IPPU.PreviousLine!=IPPU.CurrentLine) ++d35_census[64+0x22];\n         FLUSH_REDRAW();')
s=s[:start]+region;p.write_text(s,newline='\n')
p=CORE/'libretro.c';s=p.read_text()
s='unsigned long long d35_census[128];\n__attribute__((visibility("default"))) void d35_census_read(unsigned long long *out) { unsigned i; for(i=0;i<128;i++) { out[i]=d35_census[i]; d35_census[i]=0; } }\n'+s
p.write_text(s,encoding='utf-8',newline='\n')
p=CORE/'link.T';s=p.read_text().replace('d35_profile_end;','d35_profile_end; d35_census_read;');p.write_text(s,newline='\n')
s=(ROOT/'plus-a7-equivalence.c').read_text()
s=s.replace('assert(argc==5 || argc==6);','assert(argc==5); iterations=20;')
s=s.replace('    unsigned samples=0;', '    unsigned samples=0;\n    void (*census_read)(unsigned long long *);\n    *(void **)(&census_read)=dlsym(candidate.handle,"d35_census_read"); assert(census_read);')
s=s.replace('            if(candidate.batches>old.batches)',
    '            { unsigned long long counts[128]; census_read(counts); printf("CENSUS phase=%u frame=%u",phase,f); for(unsigned i=0;i<128;i++) printf(" %llu",counts[i]); puts(""); }\n            if(candidate.batches>old.batches)')
(OUT/'replay.c').write_text(s,encoding='utf-8',newline='\n')
names={0:'ppu_updates',**{1+i:f'mode_{i}_screen_lines' for i in range(8)},
    **{9+i:f'bg_{i}_lines' for i in range(4)},13:'mosaic_calls',14:'offset_calls',15:'hires_calls',
    **{16+i:f'mode7_{n}_lines' for i,n in enumerate(['plain','add','add_half','sub','sub_half'])},21:'tile_decodes',
    **{24+i:f'full_{n}_rows' for i,n in enumerate(['plain','add','add_half','sub','sub_half','fixed_add_half','fixed_sub_half'])},
    **{32+i:f'clipped_{n}_rows' for i,n in enumerate(['plain','add','add_half','sub','sub_half','fixed_add_half','fixed_sub_half'])},
    40:'neon_row_calls',41:'neon_row_empty',42:'neon_row_all_active',43:'neon_row_depth_rejected',
    44:'fixed_color_effective_change_flushes',45:'fixed_color_redundant_flushes',
    **{64+i:f'flush_before_{0x2100+i:04x}' for i in range(64)}}
(OUT/'fields.json').write_text(json.dumps(names,indent=2)+'\n',encoding='utf-8')
print('Prepared local-only renderer work census; source and production payload unchanged')
