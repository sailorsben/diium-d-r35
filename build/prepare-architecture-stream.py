"""Observe overwritten color math; keep the original render sequence unchanged."""
from pathlib import Path
import re,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/architecture-stream-private-v1'
OLD=ROOT/'build/architecture-followup-private-v1'
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def main():
 assert not OUT.exists();OUT.mkdir();shutil.copytree(OLD/'core',OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'));core=OUT/'core'
 p=core/'source/a7_arch_audit.h';write(p,p.read_text().replace('d35_arch[64]','d35_arch[96]')+'\n#include "a7_arch_stream.h"\n')
 shutil.copy2(ROOT/'build/architecture-stream-census.h',core/'source/a7_arch_stream.h')
 p=core/'libretro.c';write(p,p.read_text().replace('d35_arch[64]','d35_arch[96]'))
 p=core/'source/gfx.c';s=p.read_text();s=s.replace('extern bool reduce_sprite_flicker;','extern bool reduce_sprite_flicker;\n#define ARCH_STREAM_IMPLEMENTATION\n#include "a7_arch_stream.h"\n#undef ARCH_STREAM_IMPLEMENTATION')
 s=s.replace('   unsigned arch_last_normal=2;','   arch_bg=4;\n   unsigned arch_last_normal=2;')
 s=s.replace('   d35_arch[32]++;','   arch_bg=bg;d35_arch[32]++;')
 s=s.replace('   endy   = GFX.EndY;','   endy   = GFX.EndY;\n   arch_region_begin();')
 s=s.replace('   d35_fixed_end();','   arch_region_end();\n   d35_fixed_end();')
 # Count explicit depth initialization requests; retain the actual memset.
 s=re.sub(r'(memset\(GFX\.(?:Sub)?ZBuffer[^;]+);',lambda m:'(d35_arch[80]+=IPPU.RenderedScreenWidth,'+m[1]+');',s)
 # Count scalar RGB initialization stores by their actual destination size.
 s=re.sub(r'while \(p < q\)\s*\n\s*(\*p\+\+ = (?:black|b|back|\(uint16_t\) (?:GFX.FixedColour|back));)',lambda m:'while (p < q) {d35_arch[81]+=sizeof(*p);'+m[1]+'}',s)
 write(p,s)
 p=core/'source/a7_tile.h';s=p.read_text();s=s.replace('#include <arm_neon.h>','#include <arm_neon.h>\n#include "a7_arch_audit.h"\nstatic unsigned char arch_pending_math[8];\nstatic inline void arch_vwrite(uint16_t *out,uint8x8_t mask){unsigned char m[8];vst1_u8(m,mask);arch_vector(out,m,arch_pending_math);memset(arch_pending_math,0,8);}')
 needle='static inline d35_palette_t d35_palette(';a=s.index(needle);b=s.index('{',a);s=s[:b+1]+'\n    d35_arch[74]++;'+s[b+1:]
 a=s.index('static inline uint16x8_t d35_blend(');b=s.index('{',a)
 s=s[:b+1]+'''\n    {unsigned char active_bytes[8],sub_bytes[8];vst1_u8(active_bytes,active);vst1_u8(sub_bytes,sd);
     for(unsigned ai=0;ai<8;ai++)arch_pending_math[ai]=active_bytes[ai]&&(mode>=5?sub_bytes[ai]==1:sub_bytes[ai]>0);}
'''+s[b+1:]
 s=s.replace('static inline void d35_store(uint16_t *screen,uint16x8_t color,uint8x8_t mask)\n{','static inline void d35_store(uint16_t *screen,uint16x8_t color,uint8x8_t mask)\n{\n    arch_vwrite(screen,mask);')
 a=s.index('static inline unsigned d35_backdrop(');b=s.index('static inline unsigned d35_window(',a);part=s[a:b]
 part=part.replace('    unsigned used=count&~7u,i;','    arch_final=1;d35_arch[69]+=count%8;\n    unsigned used=count&~7u,i;')
 part=part.replace('        uint8x8_t mask=','        d35_arch[82]+=8;\n        uint8x8_t mask=')
 part=part.replace('    return used;','    arch_final=0;return used;');s=s[:a]+part+s[b:];write(p,s)
 p=core/'source/a7_common_batch.h';s=p.read_text();needle='  CB(4);';assert needle in s;s=s.replace(needle,needle+'arch_source(p,colors,!!(tile&H_FLIP),offset);')
 s=s.replace('  if(active==UINT64_MAX){','  arch_vwrite(out,mask);\n  if(active==UINT64_MAX){');write(p,s)
 p=core/'source/tile.c';s=p.read_text();s=s.replace('        uint16_t *screen=(uint16_t *)GFX.S+offset;','        arch_source(bp,colors,!!(tile&H_FLIP),offset);\n        uint16_t *screen=(uint16_t *)GFX.S+offset;')
 # Add one-pixel observation only after a successful ordinary scalar write.
 pattern=re.compile(r'(static (?:INLINE )?void (WRITE_4PIXELS16\w*)\([^\n]+\)\n\{)(.*?)(?=\n(?:static |void |#define)|\Z)',re.S)
 def scalar(m):
  name=m[2];body=m[3]
  if 'HALFWIDTH' in name or 'x2' in name:return m[0]
  math='0'
  if 'ADDF1_2' in name or 'SUBF1_2' in name:math='SubDepth[N]==1'
  elif '_ADD' in name or '_SUB' in name:math='SubDepth[N]>0'
  body=body.replace('         Depth [N] = GFX.Z2;','         arch_pixel(Screen+N,'+math+');\n         Depth [N] = GFX.Z2;')
  return m[1]+body
 s=pattern.sub(scalar,s);write(p,s)
 p=core/'source/a7_pearl_sub2.h';s=p.read_text();s=s.replace('  uint8x8_t idx=vld1_u8(p);','  arch_source(p,colors,!!(tile&H_FLIP),offset);\n  uint8x8_t idx=vld1_u8(p);');write(p,s)
 p=core/'source/a7_color_cache.h';s=p.read_text();s=s.replace('    uintptr_t address=','    d35_arch[70]++;\n    uintptr_t address=');s=s.replace('        entry->table=d35_palette','        d35_arch[71]++;entry->table=d35_palette');s=s.replace('    if(!++d35_palette_epoch)','    d35_arch[73]++;\n    if(!++d35_palette_epoch)');write(p,s)
 p=core/'source/ppu.c';s=p.read_text().replace('   d35_arch[52]++;','   d35_arch[PPU.Brightness==0?90:91]++;\n   d35_arch[52]++;');write(p,s)
 s=(OLD/'compare.c').read_text().replace('ac[64]','ac[96]').replace('j<64','j<96');write(OUT/'compare.c',s)
 s=(ROOT/'build/build-architecture-audit.sh').read_text().replace('build/architecture-audit-private-v1','build/architecture-stream-private-v1');write(ROOT/'build/build-architecture-stream.sh',s)
 shutil.copy2(OLD/'inputs.json',OUT/'inputs.json');print('Prepared observer-only pixel ownership, shared source rows, palette and explicit initialization census')
if __name__=='__main__':main()
