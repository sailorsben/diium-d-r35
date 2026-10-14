"""Fresh final refinement: reject hidden shared clips before per-tile setup."""
from pathlib import Path
from hashlib import sha256
import json,shutil
ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT/'build/demand-final-private-v2'
OUT=ROOT/'build/demand-visible-private-v3'
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def main():
 assert not OUT.exists();assert json.loads((OLD/'qualification.json').read_text())['passed'];assert json.loads((OLD/'transitions-fixed.json').read_text())['passed']
 OUT.mkdir();frozen=json.loads((OLD/'frozen.json').read_text())
 for p in OLD.rglob('*'):
  if p.is_file() and p.suffix in ('.c','.h','.so','.json','.log'):frozen[p.relative_to(ROOT).as_posix()]=sha256(p.read_bytes()).hexdigest()
 write(OUT/'frozen.json',json.dumps(frozen,indent=2)+'\n')
 for label in ('core','counted-core'):
  core=OUT/label;shutil.copytree(OLD/label,core,ignore=shutil.ignore_patterns('*.o','*.so'))
  p=core/'source/a7_demand_stats.h';s=p.read_text().replace('DS_FIELDS=32','DS_FIELDS=40');write(p,s)
  p=core/'source/a7_demand_geometry.h';s=p.read_text();anchor='#define D35_GEOMETRY_DRAW(MODE)'
  helper='''/* A maximum-priority test is conservative for every tile in this layer.
 * A failed probe vetoes further probes for this DrawBackground, so visible
 * layers do not pay a repeated hidden-span scan. Final per-pixel math/depth
 * remains in the original kernels. This path is plain main-screen only. */
static unsigned d35_geometry_covered(unsigned y,unsigned rows,unsigned left,unsigned right,unsigned high){
 uint8x8_t z=vdup_n_u8((uint8_t)high);
 for(unsigned row=0;row<rows;row++){
  const uint8_t *depth=GFX.DB+(y+row)*GFX.PPL;unsigned x=left;
  for(;x+8<=right;x+=8){DS_ADD(36,1);if(vget_lane_u64(vreinterpret_u64_u8(vcgt_u8(z,vld1_u8(depth+x))),0))return 0;}
  for(;x<right;x++){DS_ADD(37,1);if(depth[x]<high)return 0;}
 }
 return 1;
}
'''
  assert s.count(anchor)==1;s=s.replace(anchor,helper+anchor)
  s=s.replace('ctx,unsigned low,unsigned high,struct d35_sub2_context *sole) { '+chr(92)+'\n','ctx,unsigned low,unsigned high,struct d35_sub2_context *sole) { '+chr(92)+'\n unsigned veto=0,try_reject=MODE==0&&GFX.S==GFX.Screen; '+chr(92)+'\n')
  a='   if(right<=left)continue; '+chr(92)+'\n';assert s.count(a)==1
  s=s.replace(a,a+'''   if(try_reject&&!veto){DS_ADD(32,1);unsigned maximum=high>low?high:low; '''+chr(92)+'''
    if(d35_geometry_covered(y,g->lines,left,right,maximum)){unsigned cells=((right-1+g->shift)>>3)-((left+g->shift)>>3)+1;DS_ADD(33,1);DS_ADD(34,cells);DS_ADD(35,cells*g->lines);continue;} '''+chr(92)+'''
    veto=1;DS_ADD(38,1);DS_ADD(39,1); '''+chr(92)+'''
   } '''+chr(92)+'\n');write(p,s)
 for name in ('demand-equivalence.c','compare.c'):shutil.copy2(OLD/name,OUT/name)
 p=OUT/'compare.c';s=p.read_text().replace('dc[32]','dc[40]').replace('for(unsigned j=0;j<32;j++)printf(",%llu",dc[j])','for(unsigned j=0;j<40;j++)printf(",%llu",dc[j])');write(p,s)
 print('Prepared v3: plain main clip coverage scan + miss veto; complete prior candidates retained')
if __name__=='__main__':main()
