"""Work backwards from real C execution. No card access or timing inference."""
from pathlib import Path
import re,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/pearl-work-private-v1'
def prepare():
 assert not OUT.exists();OUT.mkdir()
 shutil.copytree(ROOT/'build/fullpaths-private-v2/combined-core',OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'))
 source=OUT/'core/source';shutil.copy2(ROOT/'build/pearl-work.h',source/'a7_pearl_work.h')
 p=source/'gfx.c';s=p.read_text();anchor='static void RenderScreen(uint8_t* Screen, bool sub, bool force_no_add, uint8_t D)\n{'
 assert anchor in s
 # a7_tile already included above; globals are wholly outside emulated state.
 s=s.replace('#include "a7_tile.h"','#include "a7_tile.h"\n#define D35_PEARL_IMPLEMENTATION\n#include "a7_pearl_work.h"')
 s=s.replace(anchor,anchor+'''
   d35_pearl_plane=sub?1:0;
   if(!sub && D==MAIN_SCREEN_DEPTH && PPU.BGMode==1){
      unsigned rows=GFX.EndY-GFX.StartY+1;
      d35_pearl[288]+=rows;++d35_pearl[290];
      unsigned pair=(GFX.r212d&3);
      int same=(GFX.r212c&3)==pair && pair;
      int subpair=!(GFX.r212d&0x1c) && (GFX.r2130&2) && (GFX.r2130&0x30)!=0x30;
      int color=!IPPU.Clip[0].Count[5]&&!IPPU.Clip[1].Count[5];
      int clip=!IPPU.Clip[0].Count[0]&&!IPPU.Clip[0].Count[1]&&!IPPU.Clip[1].Count[0]&&!IPPU.Clip[1].Count[1];
      int other=PPU.Mosaic<=1 && !GFX.Pseudo && !IPPU.DoubleWidthPixels && !IPPU.DoubleHeightPixels && !IPPU.HalfWidthPixels;
      if(same)d35_pearl[291]+=rows;if(subpair)d35_pearl[292]+=rows;
      if(color)d35_pearl[293]+=rows;if(clip)d35_pearl[294]+=rows;if(other)d35_pearl[295]+=rows;
      if(same&&subpair&&color&&clip&&other)d35_pearl[289]+=rows;
      d35_pearl[300]=GFX.r212c;d35_pearl[301]=GFX.r212d;d35_pearl[302]=GFX.r2130;d35_pearl[303]=GFX.r2131;
   }
''')
 s=s.replace('static void DrawOBJS(bool OnMain, uint8_t D)\n{','static void DrawOBJS(bool OnMain, uint8_t D)\n{\n   d35_pearl_layer=4;')
 s=s.replace('static void DrawBackground(uint32_t BGMode, uint32_t bg, uint8_t Z1, uint8_t Z2)\n{','static void DrawBackground(uint32_t BGMode, uint32_t bg, uint8_t Z1, uint8_t Z2)\n{\n   d35_pearl_layer=bg;')
 p.write_text(s,newline='\n')
 p=source/'tile.c';s=p.read_text().replace('#include "a7_tile.h"','#include "a7_tile.h"\n#include "a7_pearl_work.h"')
 s=s.replace('        if(active) {','        d35_pearl_row(mode,mask,old_depth,depth_mask);\n        if(active) {',1)
 names=('','Add','Add1_2','Sub','Sub1_2','FixedAdd1_2','FixedSub1_2')
 for name in names:
  for kind,metric in (('Tile',0),('ClippedTile',1)):
   pat=r'(void Draw'+kind+'16'+name+r'\([^\n]+\)\n\{)'
   s,n=re.subn(pat,r'\1\n   PW('+str(metric)+');',s);assert n==1,(name,kind,n)
 p.write_text(s,newline='\n')
 p=OUT/'core/link.T';p.write_text(p.read_text().replace('global:','global: d35_pearl_read;'),newline='\n')
 s=(ROOT/'build/fullpaths-private-v2/compare.c').read_text()
 anchor='    unsigned char *a=malloc(size),*b=malloc(size);assert(a && b);'
 s=s.replace(anchor,'''    void (*pearl)(unsigned long long *);*(void **)(&pearl)=dlsym(candidate.handle,"d35_pearl_read");
    assert(pearl);unsigned long long pc[352];pearl(pc);
'''+anchor)
 s=s.replace('        unsigned long long sc[8]={0};','        pearl(pc);printf("PEARL %u",frame);for(unsigned pi=0;pi<352;pi++)printf(",%llu",pc[pi]);puts("");\n        unsigned long long sc[8]={0};')
 (OUT/'compare.c').write_text(s,newline='\n')
 s=(ROOT/'build/build-fixed-rows.sh').read_text().replace('fixed-rows-private-v3',OUT.name)
 s=s[:s.index('(cd "$out/counted-core"')]
 (ROOT/'build/build-pearl-work.sh').write_text(s,newline='\n')
 print('Prepared isolated C work census; no A7 timing or card change')
if __name__=='__main__':prepare()
