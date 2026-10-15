"""Observe current demand-v3, with raw graphics/PCM/state comparisons."""
from pathlib import Path
from hashlib import sha256
import json,re,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/current-work-private-v1'
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def once(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
def main():
 assert not OUT.exists();OUT.mkdir();src=ROOT/'build/demand-visible-private-v3/core'
 frozen={p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in src.rglob('*') if p.is_file() and p.suffix in ('.c','.h','.so')}
 write(OUT/'frozen.json',json.dumps(frozen,indent=2)+'\n')
 shutil.copytree(src,OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'));core=OUT/'core'
 shutil.copy2(ROOT/'build/current-work-census.h',core/'source/a7_current_work.h')
 p=core/'source/gfx.c';s=p.read_text();s=once(s,'extern bool reduce_sprite_flicker;','extern bool reduce_sprite_flicker;\n#define D35_CURRENT_WORK_IMPLEMENTATION\n#include "a7_current_work.h"\n#undef D35_CURRENT_WORK_IMPLEMENTATION')
 s=once(s,'   endy   = GFX.EndY;','   endy   = GFX.EndY;\n   work_begin();d35_work[13]++;')
 s=once(s,'   d35_fixed_end();','   work_end();\n   d35_fixed_end();')
 s=once(s,'static void DrawOBJS(bool OnMain, uint8_t D)\n{','static void DrawOBJS(bool OnMain, uint8_t D)\n{\n work_layer=1;d35_work[12]++;')
 s=once(s,'static void DrawBackground(uint32_t BGMode, uint32_t bg, uint8_t Z1, uint8_t Z2)\n{','static void DrawBackground(uint32_t BGMode, uint32_t bg, uint8_t Z1, uint8_t Z2)\n{\n work_layer=bg+2;d35_work[11]++;')
 write(p,s)
 p=core/'source/a7_tile.h';s=p.read_text();s=once(s,'#include <arm_neon.h>','#include <arm_neon.h>\n#include "a7_current_work.h"\nstatic unsigned char work_pending_math[8];\nstatic inline void work_vwrite(uint16_t *out,uint8x8_t mask){unsigned char m[8];vst1_u8(m,mask);work_vector(out,m,work_pending_math);memset(work_pending_math,0,8);}')
 a=s.index('static inline d35_palette_t d35_palette(');b=s.index('{',a);s=s[:b+1]+'\n d35_work[10]++;'+s[b+1:]
 a=s.index('static inline uint16x8_t d35_blend(');b=s.index('{',a);s=s[:b+1]+'''\n {unsigned char m[8],z[8];vst1_u8(m,active);vst1_u8(z,sd);for(unsigned i=0;i<8;i++)work_pending_math[i]=m[i]&&(mode>=5?z[i]==1:z[i]>0);}
'''+s[b+1:]
 s=once(s,'static inline void d35_store(uint16_t *screen,uint16x8_t color,uint8x8_t mask)\n{','static inline void d35_store(uint16_t *screen,uint16x8_t color,uint8x8_t mask)\n{\n work_vwrite(screen,mask);')
 a=s.index('static inline unsigned d35_backdrop(');b=s.index('static inline unsigned d35_window(',a);part=s[a:b]
 part=once(part,'    unsigned used=count&~7u,i;','    work_final=1;work_layer=0;\n    unsigned used=count&~7u,i;');part=once(part,'    return used;','    work_final=0;return used;');s=s[:a]+part+s[b:];write(p,s)
 p=core/'source/a7_common_batch.h';s=p.read_text();s=s.replace('    if(active==UINT64_MAX){FT(20);','    work_vwrite(out,mask);\n    if(active==UINT64_MAX){FT(20);').replace('  if(active==UINT64_MAX){FT(22);','  work_vwrite(out,mask);\n  if(active==UINT64_MAX){FT(22);').replace('  if(active==UINT64_MAX){CB(6);','  work_vwrite(out,mask);\n  if(active==UINT64_MAX){CB(6);')
 assert s.count('work_vwrite(out,mask)')==3
 s=s.replace('  uint8x8_t idx=vld1_u8(p);','  d35_work[24]++;uint8x8_t idx=vld1_u8(p);').replace('uint8x8_t idx=vld1_u8(p);FT(10);','uint8x8_t idx=vld1_u8(p);d35_work[24]++;FT(10);')
 s=once(s,'  CB(4);','  d35_work[mode?25:24]++;CB(4);');s=s.replace('uint8x8x2_t zip=vzip_u8','d35_work[27]++;uint8x8x2_t zip=vzip_u8');write(p,s)
 p=core/'source/a7_partial_kernels.h';s=p.read_text();s=once(s,'#define D35_PARTIAL_KERNELS_H','#define D35_PARTIAL_KERNELS_H\n#include "a7_current_work.h"')
 s=once(s,'  out[lane]=colors[indices[flip?7-lane:lane]];depth[lane]=z2;','  work_pixel(out+lane,0);d35_work[28]++;out[lane]=colors[indices[flip?7-lane:lane]];depth[lane]=z2;');write(p,s)
 p=core/'source/tile.c';s=p.read_text();s=once(s,'    while(count--) {','    while(count--) {\n        d35_work[26]++;');s=once(s,'static uint8_t ConvertTile(uint8_t* pCache, uint32_t TileAddr)\n{','static uint8_t ConvertTile(uint8_t* pCache, uint32_t TileAddr)\n{\n d35_work[9]++;')
 pattern=re.compile(r'(static (?:INLINE )?void (WRITE_4PIXELS16\w*)\([^\n]+\)\n\{)(.*?)(?=\n(?:static |void |#define)|\Z)',re.S)
 def scalar(m):
  name,body=m[2],m[3]
  if 'HALFWIDTH' in name or 'x2' in name:return m[0]
  math='SubDepth[N]==1' if 'ADDF1_2' in name or 'SUBF1_2' in name else 'SubDepth[N]>0' if '_ADD' in name or '_SUB' in name else '0'
  return m[1]+body.replace('         Depth [N] = GFX.Z2;','         work_pixel(Screen+N,'+math+');\n         Depth [N] = GFX.Z2;')
 s=pattern.sub(scalar,s);write(p,s)
 p=core/'source/a7_pearl_sub2.h';s=p.read_text();s=once(s,'   vst1q_u16(out,color);','   work_vwrite(out,vmvn_u8(transparent));vst1q_u16(out,color);');write(p,s)
 p=core/'source/cpuexec.c';s='#include "a7_current_work.h"\n'+p.read_text();s=s.replace('         CPU.PCAtOpcodeStart = CPU.PC;','         d35_work[0]++;CPU.PCAtOpcodeStart = CPU.PC;');assert s.count('d35_work[0]++')==4;write(p,s)
 p=core/'source/apu_blargg.c';s='#include "a7_current_work.h"\n'+p.read_text()
 for anchor,field in [('static uint8_t* spc_run_until_( int32_t end_time )',1),('static void spc_end_frame( int32_t end_time )',5),('static void dsp_run( int32_t clocks_remain )',6),('static INLINE int32_t dsp_interpolate( dsp_voice_t *v )',7)]:
  needle=anchor+'\n{';s=once(s,needle,needle+'\n d35_work['+str(field)+']'+('+=clocks_remain;' if field==6 else '++;'))
 s=once(s,'      opcode = *pc;','      d35_work[2]++;opcode = *pc;')
 s=once(s,'uint8_t S9xAPUReadPort (int32_t port)\t{','uint8_t S9xAPUReadPort (int32_t port)\t{ d35_work[3]++;')
 s=once(s,'void S9xAPUWritePort (int32_t port, uint8_t byte)\n{','void S9xAPUWritePort (int32_t port, uint8_t byte)\n{\n d35_work[4]++;');write(p,s)
 p=core/'libretro.c';s=p.read_text()+'\n#include "source/a7_current_work.h"\n__attribute__((visibility("default"))) void d35_work_read(unsigned long long *p){memcpy(p,d35_work,sizeof(d35_work));memset(d35_work,0,sizeof(d35_work));}\n';write(p,s)
 p=core/'link.T';write(p,p.read_text().replace('global:','global: d35_work_read;'))
 s=(ROOT/'build/ppu-refinements-private-v4/compare.c').read_text();s=once(s,'    unsigned long long dc[40];counts(dc);','    unsigned long long dc[40];counts(dc);\n    void (*work)(unsigned long long *);*(void **)(&work)=dlsym(candidate.handle,"d35_work_read");assert(work);unsigned long long wc[64];work(wc);')
 s=once(s,'        counts(dc);printf("DEMAND','        work(wc);printf("CURRENT %u",frame);for(unsigned j=0;j<64;j++)printf(",%llu",wc[j]);puts("");\n        counts(dc);printf("DEMAND');write(OUT/'compare.c',s)
 shutil.copy2(ROOT/'build/ppu-refinements-private-v4/demand-equivalence.c',OUT/'demand-equivalence.c')
 print('Prepared current-v3 observer: engine work, actual stores/overdraw, palette/materialization; no timing claims')
if __name__=='__main__':main()
