"""Fresh general PPU variants from frozen v3; counters never enter ordinary cores."""
from pathlib import Path
from hashlib import sha256
import json,shutil
ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT/'build/demand-visible-private-v3'
OUT=ROOT/'build/ppu-refinements-private-v4'
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def once(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
def main():
 assert not OUT.exists();frozen=json.loads((OLD/'frozen.json').read_text())
 for p in OLD.rglob('*'):
  if p.is_file() and p.suffix in ('.c','.h','.so','.json','.log'):frozen[p.relative_to(ROOT).as_posix()]=sha256(p.read_bytes()).hexdigest()
 for n,h in frozen.items():assert sha256((ROOT/n).read_bytes()).hexdigest()==h,n
 OUT.mkdir();write(OUT/'frozen.json',json.dumps(frozen,indent=2)+'\n')
 for name,defines in [('obj','D35_PPU_OBJ'),('shapes','D35_PPU_SHAPES'),('bulk','D35_PPU_BULK'),('combined','D35_PPU_OBJ D35_PPU_SHAPES D35_PPU_BULK')]:
  for observer in (False,True):
   label=name+('-counted' if observer else '');core=OUT/label
   shutil.copytree(OLD/'core',core,ignore=shutil.ignore_patterns('*.o','*.so'))
   pre='\n'.join('#define '+x for x in defines.split())+'\n'
   if observer:pre+='#define D35_PPU_COUNT\n'
   header=pre+'''#ifndef D35_PPU_STATS_H
#define D35_PPU_STATS_H
#ifdef D35_PPU_COUNT
extern unsigned long long d35_ppu[32];
#define PP_ADD(n,v) (d35_ppu[n]+=(v))
#else
#define PP_ADD(n,v) ((void)0)
#endif
#endif
'''
   write(core/'source/a7_ppu_stats.h',header)
   shutil.copy2(ROOT/'build/ppu-window-start.h',core/'source/a7_ppu_window.h')
   shutil.copy2(ROOT/'build/ppu-sparse-math.h',core/'source/a7_ppu_math.h')
   p=core/'source/gfx.c';s=p.read_text();s='#include "a7_ppu_stats.h"\n'+s
   s=once(s,'static void DrawOBJS(bool OnMain, uint8_t D)','''#include "a7_ppu_window.h"
static void DrawOBJS(bool OnMain, uint8_t D)''')
   s=once(s,'   GFX.Z1 = D + 2;','''#ifdef D35_PPU_OBJ
   struct d35_obj_lookup obj_lookup;D35_OBJ_PREPARE(obj_lookup,Windows);
#endif
   GFX.Z1 = D + 2;''')
   a='''               for (; WinIdx < 7 && Windows[WinIdx].Pos <= X; WinIdx++);
               if (WinIdx == 0)
                  WinStat = false;
               else
                  WinStat = Windows[WinIdx - 1].Value;
               NextPos = (WinIdx < 7) ? Windows[WinIdx].Pos : 1000;'''
   s=once(s,a,'''#ifdef D35_PPU_OBJ
               if(WinIdx==0&&NextPos==-1000){D35_OBJ_START(obj_lookup,Windows,X,WinIdx,WinStat,NextPos);}
               else
#endif
               {
'''+a+'''
               }''')
   anchor='''      /* Clear the z-buffer */
      if (pClip->Count [5])'''
   s=once(s,anchor,'''#ifdef D35_PPU_BULK
      unsigned bulk_depth=GFX.ZPitch==IPPU.RenderedScreenWidth&&endy>=starty;
      if(bulk_depth){
         size_t bytes=(size_t)(endy-starty+1)*GFX.ZPitch;
         memset(GFX.ZBuffer+starty*GFX.ZPitch,0,bytes);
         memset(GFX.SubZBuffer+starty*GFX.ZPitch,pClip->Count[5]?0:1,bytes);
         PP_ADD(14,(endy-starty+1)*2);PP_ADD(16,bytes*2);
      }
#endif
'''+anchor)
   a='''            memset(GFX.SubZBuffer + y * GFX.ZPitch, 0, IPPU.RenderedScreenWidth);
            memset(GFX.ZBuffer + y * GFX.ZPitch, 0, IPPU.RenderedScreenWidth);'''
   s=once(s,a,'''#ifdef D35_PPU_BULK
            if(!bulk_depth)
#endif
            {
'''+a+'''
            }''')
   a='''            memset(GFX.ZBuffer + y * GFX.ZPitch, 0, IPPU.RenderedScreenWidth);
            memset(GFX.SubZBuffer + y * GFX.ZPitch, 1, IPPU.RenderedScreenWidth);'''
   s=once(s,a,'''#ifdef D35_PPU_BULK
            if(!bulk_depth)
#endif
            {
'''+a+'''
            }''')
   if observer:s+='\nunsigned long long d35_ppu[32];\n__attribute__((visibility("default"))) void d35_ppu_read(unsigned long long *p){memcpy(p,d35_ppu,sizeof(d35_ppu));memset(d35_ppu,0,sizeof(d35_ppu));}\n'
   write(p,s)
   p=core/'link.T';s=p.read_text()
   if observer:s=s.replace('global:','global: d35_ppu_read;')
   write(p,s)
   p=core/'source/tile.c';s=p.read_text();s=once(s,'#include "a7_color_cache.h"','#include "a7_color_cache.h"\n#include "a7_partial_kernels.h"\n#include "a7_ppu_stats.h"\n#include "a7_ppu_math.h"')
   s=once(s,'            if(!ready) { table=d35_cached_palette(colors,BG.BitShift);ready=true; }','''#ifdef D35_PPU_SHAPES
            if(!mode&&active!=UINT64_MAX&&d35_sparse_plain(screen,depth,bp,colors,active,!!(tile&H_FLIP),GFX.Z2)){bp+=step;offset+=GFX.PPL;continue;}
            if(mode&&active!=UINT64_MAX&&d35_sparse_math(screen,depth,bp,colors,active,!!(tile&H_FLIP),GFX.Z2,GFX.SubZBuffer+offset,screen+GFX.Delta,d35_fixed_at_offset((unsigned)offset),mode)){bp+=step;offset+=GFX.PPL;continue;}
#endif
            if(!ready) { table=d35_cached_palette(colors,BG.BitShift);ready=true; }''')
   s=once(s,'''            d35_store(screen,color,mask);
            vst1_u8(depth,vbsl_u8(mask,vdup_n_u8(GFX.Z2),old_depth));''','''#ifdef D35_PPU_OBJ
            if(active==UINT64_MAX){PP_ADD(0,1);vst1q_u16(screen,color);vst1_u8(depth,vdup_n_u8(GFX.Z2));}
            else
#endif
            {d35_store(screen,color,mask);vst1_u8(depth,vbsl_u8(mask,vdup_n_u8(GFX.Z2),old_depth));}''')
   functions=['DrawClippedTile16','DrawClippedTile16Add','DrawClippedTile16Add1_2','DrawClippedTile16Sub','DrawClippedTile16Sub1_2','DrawClippedTile16FixedAdd1_2','DrawClippedTile16FixedSub1_2']
   for mode,fn in enumerate(functions):
    start=s.index('void '+fn+'(');end=s.index('\n}',start)+2;block=s[start:end]
    anchor='   TILE_PREAMBLE_CODE();'
    block=once(block,anchor,anchor+f'''
#ifdef D35_PPU_OBJ
   if(StartPixel==0&&Width==8&&Offset>=0&&(GFX.PPL==256||GFX.PPL==512)&&
      ((unsigned)Offset&(GFX.PPL-1))<=248&&StartLine<=56&&!(StartLine&7)&&LineCount<=8-StartLine/8&&
      d35_render_tile(Tile,Offset,StartLine,LineCount,pCache,ScreenColors,{mode})){{
      PP_ADD({1+mode},1);if(LineCount)d35_fixed_select_offset((unsigned)(Offset+(LineCount-1)*GFX.PPL));return;
   }}
#endif''')
    s=s[:start]+block+s[end:]
   write(p,s)
   p=core/'source/a7_common_batch.h';s=p.read_text();s=once(s,'#include "a7_partial_kernels.h"','#include "a7_partial_kernels.h"\n#include "a7_ppu_math.h"')
   s=once(s,'  CB(5);','''#ifdef D35_PPU_SHAPES
  if(mode&&active!=UINT64_MAX&&d35_sparse_math(out,depth,p,colors,active,!!(tile&H_FLIP),GFX.Z2,GFX.SubZBuffer+offset,out+GFX.Delta,d35_fixed_at_offset((unsigned)offset),mode))continue;
#endif
  CB(5);''')
   write(p,s)
   p=core/'source/a7_partial_kernels.h';s=p.read_text();s='#include "a7_ppu_stats.h"\n'+s
   s=once(s,' if(!count||count>2)return 0;','''#ifdef D35_PPU_SHAPES
 PP_ADD(15,1);
 if(count==4&&(lo==UINT32_MAX||hi==UINT32_MAX)){
  unsigned base=lo==UINT32_MAX?0:4;
  for(unsigned j=0;j<4;j++)out[base+j]=colors[indices[flip?7-base-j:base+j]];
  memset(depth+base,z2,4);PP_ADD(13,1);return 1;
 }
 if(count==3)PP_ADD(12,1);
 if(!count||count>3)return 0;
#else
 if(!count||count>2)return 0;
#endif''')
   write(p,s)
 shutil.copy2(OLD/'demand-equivalence.c',OUT/'demand-equivalence.c')
 s=(OLD/'compare.c').read_text()
 s=once(s,'    unsigned long long dc[40];counts(dc);','''    unsigned long long dc[40];counts(dc);
    void (*pp)(unsigned long long *);*(void **)(&pp)=dlsym(candidate.handle,"d35_ppu_read");unsigned long long pc[32];if(pp)pp(pc);''')
 s=once(s,'        counts(dc);printf(','''        if(pp){pp(pc);printf("PPU %u",frame);for(unsigned j=0;j<32;j++)printf(",%llu",pc[j]);puts("");}
        counts(dc);printf(''')
 write(OUT/'compare.c',s)
 print('Prepared isolated OBJ/shape/combined PPU cores plus observer twins; v3 untouched')
if __name__=='__main__':main()
