"""Counterfactual priority scheduling on the qualified observer, not a release."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/priority-research-private-v1'
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def once(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
def main():
 src=ROOT/'build/current-work-private-v1';assert json.loads((src/'qualification.json').read_text())['passed']
 assert not OUT.exists();OUT.mkdir();shutil.copytree(src/'core',OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'))
 shutil.copy2(src/'frozen.json',OUT/'frozen.json')
 for name in ('compare.c','demand-equivalence.c'):shutil.copy2(src/name,OUT/name)
 core=OUT/'core';p=core/'source/a7_current_work.h';s=p.read_text();s=once(s,'extern unsigned work_layer,work_final;','extern unsigned work_layer,work_final;\nextern unsigned work_priority_filter;\n#define WORK_PRIORITY_ACCEPT (!work_priority_filter||GFX.Z2==work_priority_filter)')
 s=once(s,'unsigned long long d35_work[64];unsigned work_layer,work_final;','unsigned long long d35_work[64];unsigned work_layer,work_final;unsigned work_priority_filter;');write(p,s)
 p=core/'source/gfx.c';s=p.read_text()
 # Guard by rendering state only. Unique highest BG3 priority in mode1;
 # transparent pixels, windows, sprite evaluation and low BG3 retain stock rules.
 anchor='''      case 0:
      case 1:
         if (OB)'''
 replacement='''      case 0:
      case 1:
      {
         unsigned work_top=PPU.BGMode==1&&PPU.BG3Priority&&BG2&&
          (PPU.Mosaic<=1||!PPU.BGMosaic[2])&&!GFX.Pseudo&&GFX.PPL==256&&
          !IPPU.DoubleWidthPixels&&!IPPU.DoubleHeightPixels&&!IPPU.HalfWidthPixels;
         if(work_top){
            d35_work[57]++;SelectTileRenderer(normal_all || !SUB_OR_ADD(2));
            work_priority_filter=D+17;DrawBackground(PPU.BGMode,2,D+3,D+17);work_priority_filter=0;
         }
         if (OB)'''
 s=once(s,anchor,replacement)
 anchor='''            DrawBackground(PPU.BGMode, 2, D + 3, PPU.BG3Priority ? D + 17 : D + 6);'''
 s=once(s,anchor,'''            if(work_top)work_priority_filter=D+3;
'''+anchor+'''
            work_priority_filter=0;''')
 # End the extra lexical scope only at this mode's break.
 a=s.index(replacement);b=s.index('      case 2:',a);part=s[a:b];assert part.count('         break;')==1
 part=part.replace('         break;','         break;\n      }');s=s[:a]+part+s[b:];write(p,s)
 p=core/'source/tile.c';s=p.read_text();import re
 s,n=re.subn(r'(void Draw\w+\([^\n]+\)\n\{)',r'\1\n   if(!WORK_PRIORITY_ACCEPT){d35_work[58]++;return;}',s);assert n>=14;write(p,s)
 p=core/'source/a7_common_batch.h';s=p.read_text()
 for name in ('d35_fused_plain','d35_fused_sole','d35_batch_tile_mode_base'):
  a=s.index(name+'(');b=s.index('{',a);s=s[:b+1]+'\n if(!WORK_PRIORITY_ACCEPT){d35_work[58]++;return 1;}'+s[b+1:]
 write(p,s)
 p=core/'source/a7_pearl_sub2.h';s=p.read_text();a=s.index('d35_sub2(');b=s.index('{',a);s=s[:b+1]+'\n if(!WORK_PRIORITY_ACCEPT){d35_work[58]++;return 1;}'+s[b+1:];write(p,s)
 script=(ROOT/'build/build-current-work-census.sh').read_text().replace('build/current-work-private-v1','build/priority-research-private-v1')
 script=script.replace('"$(dirname "$0")/.."','"$(dirname "$0")/../.."');write(OUT/'build.sh',script)
 print('Prepared priority-scheduling research clone; extra traversal/guards retained and unpriced')
if __name__=='__main__':main()
