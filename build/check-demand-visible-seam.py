"""Original tile commands independently bound the whole-clip rejection guard."""
from pathlib import Path
import runpy,json,subprocess
from hashlib import sha256
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-visible-private-v3'
MOCK='''
typedef struct {uint8_t lane[8];}uint8x8_t;
static uint8x8_t vdup_n_u8(uint8_t b){uint8x8_t r;memset(&r,b,8);return r;}
static uint8x8_t vld1_u8(const uint8_t*p){uint8x8_t r;memcpy(&r,p,8);return r;}
static uint8x8_t vcgt_u8(uint8x8_t a,uint8x8_t b){uint8x8_t r;for(unsigned i=0;i<8;i++)r.lane[i]=a.lane[i]>b.lane[i]?255:0;return r;}
static uint64_t vreinterpret_u64_u8(uint8x8_t a){uint64_t r;memcpy(&r,&a,8);return r;}
static uint64_t vget_lane_u64(uint64_t a,unsigned i){assert(!i);return a;}
'''
def main():
 assert not (OUT/'visibility-seam.json').exists()
 m=runpy.run_path(str(ROOT/'build/check-demand-seams.py'));m['geometry'].__globals__['OUT']=OUT;m['geometry']()
 p=OUT/'geometry-check.c';s=p.read_text().replace('#include "demand-stats.h"','#include "a7_demand_stats.h"')
 s=s.replace('#include "demand-geometry.h"',MOCK+'\n#include "geometry-under-test.h"')
 s=s.replace('uint8_t screen,sub,depth;', 'uint8_t screen,sub;static uint8_t depth[512*240+64];')
 s=s.replace('GFX.SubZBuffer=&depth;GFX.DB=&depth;', 'GFX.SubZBuffer=depth;GFX.DB=depth;')
 s=s.replace(' assert(d35_demand[DS_GEO_REUSED]', '''
 /* Every original full/clipped tile command must fail its depth test before
    a wholly covered clip may bypass geometry/color preparation. */
 GFX.r212c=GFX.r212d=2;GFX.r2130=0;GFX.S=GFX.Screen;GFX.pCurrentClip=&IPPU.Clip[0];DrawTilePtr=DrawTile16;
 memset(depth,255,sizeof(depth));d35_geometry_reset();used=0;DrawBackground(1,1,10,14);
 unsigned n=used;assert(n);for(unsigned i=0;i<n;i++)assert(recorded[i].z1<=255);
 used=0;CandidateBackground(1,1,10,14);assert(!used&&d35_demand[33]&&d35_demand[34]);
 unsigned guards=0;
 for(unsigned left=0;left<16;left++)for(unsigned width=1;width<257-left;width++){
  unsigned right=left+width;memset(depth,255,sizeof(depth));
  assert(d35_geometry_covered(2,3,left,right,49));
  /* A pixel outside the clip cannot veto it. The first/last pixel of each
     clipped row must veto it, including vector starts and scalar tails. */
  if(left)depth[2*512+left-1]=0;if(right<512)depth[2*512+right]=0;
  assert(d35_geometry_covered(2,3,left,right,49));
  for(unsigned row=2;row<5;row++){
   depth[row*512+left]=48;assert(!d35_geometry_covered(2,3,left,right,49));depth[row*512+left]=255;
   depth[row*512+right-1]=48;assert(!d35_geometry_covered(2,3,left,right,49));depth[row*512+right-1]=255;
  }
  guards++;
 }
 printf("PASS %u clip coverage bounds, vector/tail endpoints and independent all-hidden original commands\\n",guards);
 assert(d35_demand[DS_GEO_REUSED]''')
 p.write_text(s,newline='\n');(OUT/'geometry-under-test.h').write_bytes((OUT/'core/source/a7_demand_geometry.h').read_bytes())
 exe=OUT/'geometry-check'
 subprocess.run(['gcc','-O2','-std=gnu99','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-variable','-Wno-sign-compare','-Wno-misleading-indentation','-Ibuild','-I'+str(OUT/'core/source'),str(p),'-o',str(exe)],cwd=ROOT,check=True)
 r=subprocess.run([str(exe)],check=True,capture_output=True,text=True,timeout=120);(OUT/'geometry-check.log').write_text(r.stdout)
 (OUT/'visibility-seam.json').write_text(json.dumps({'passed':True,'output':r.stdout.strip(),'source_sha256':sha256(p.read_bytes()).hexdigest(),'NEON_lanes_emulated_for_native_fixture':True,'actual_ARM_NEON_qualified_in_original_replays':True,'A7_performance_evidence':False},indent=2)+'\n');print(r.stdout,end='')
if __name__=='__main__':main()
