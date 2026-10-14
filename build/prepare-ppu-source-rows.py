"""Isolated small source-row experiment, not automatically combined/promoted."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ppu-refinements-private-v4'
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def once(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
def main():
 for counted in (False,True):
  name='rows-v2-counted' if counted else 'rows-v2';target=OUT/name;assert not target.exists()
  shutil.copytree(ROOT/'build/demand-visible-private-v3/core',target,ignore=shutil.ignore_patterns('*.o','*.so'))
  stats=(OUT/'obj-counted/source/a7_ppu_stats.h').read_text().replace('#define D35_PPU_OBJ\n','')
  if not counted:stats=stats.replace('#define D35_PPU_COUNT\n','')
  write(target/'source/a7_ppu_stats.h',stats)
  p=target/'source/a7_color_cache.h';s=p.read_text();s='#include "a7_ppu_stats.h"\n'+s
  s=once(s,'static unsigned d35_palette_epoch=1;','static unsigned d35_palette_epoch=1;\n#define D35_SOURCE_IMPLEMENTATION\n#include "a7_source_rows.h"\n#undef D35_SOURCE_IMPLEMENTATION')
  s=once(s,'        memset(d35_palette_entries,0,sizeof(d35_palette_entries));d35_palette_epoch=1;','        d35_source_clear();memset(d35_palette_entries,0,sizeof(d35_palette_entries));d35_palette_epoch=1;')
  s=once(s,'void d35_color_tile_changed(const uint8_t *tile) { (void)tile; }','void d35_color_tile_changed(const uint8_t *tile) {d35_source_tile_changed(tile);}')
  write(p,s);shutil.copy2(ROOT/'build/ppu-source-rows.h',target/'source/a7_source_rows.h')
  p=target/'source/tile.c';s=p.read_text()
  a='''            uint8x8x2_t zip=vzip_u8(vtbl2_u8(table.low,idx),vtbl2_u8(table.high,idx));
            uint16x8_t color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));'''
  s=once(s,a,'            uint16x8_t color=d35_source_color(bp,colors,BG.BitShift,idx,table,!!(tile&H_FLIP));')
  write(p,s)
  p=target/'source/a7_common_batch.h';s=p.read_text();s=once(s,'#include "a7_partial_kernels.h"','#include "a7_partial_kernels.h"\n#include "a7_source_rows.h"')
  a='''    uint8x8x2_t zip=vzip_u8(vtbl2_u8(table.low,idx),vtbl2_u8(table.high,idx));
    uint16x8_t color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));'''
  s=once(s,a,'    uint16x8_t color=d35_source_color(p,colors,bits,idx,table,!!(tile&H_FLIP));')
  a='  uint8x8x2_t zip=vzip_u8(vtbl2_u8(table.low,idx),vtbl2_u8(table.high,idx));uint16x8_t color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));'
  s=once(s,a,'  uint16x8_t color=d35_source_color(p,colors,2,idx,table,!!(tile&H_FLIP));')
  a='''  uint8x8x2_t zip=vzip_u8(vtbl2_u8(table.low,idx),vtbl2_u8(table.high,idx));
  uint16x8_t color=vreinterpretq_u16_u8(vcombine_u8(zip.val[0],zip.val[1]));'''
  s=once(s,a,'  uint16x8_t color=d35_source_color(p,colors,BG.BitShift,idx,table,!!(tile&H_FLIP));')
  write(p,s)
  if counted:
   p=target/'source/gfx.c';s=p.read_text();s+='\nunsigned long long d35_ppu[32];\n__attribute__((visibility("default"))) void d35_ppu_read(unsigned long long *p){memcpy(p,d35_ppu,sizeof(d35_ppu));memset(d35_ppu,0,sizeof(d35_ppu));}\n';write(p,s)
   p=target/'link.T';write(p,p.read_text().replace('global:','global: d35_ppu_read;'))
 print('Prepared isolated32-entry source RGB spans, tile/palette dependencies, no final depth/math cache')
if __name__=='__main__':main()
