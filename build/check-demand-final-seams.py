"""Recheck changed v2 geometry selection and ring code, using frozen C oracles."""
from pathlib import Path
import json,runpy,subprocess
from hashlib import sha256
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/demand-final-private-v2'
def main():
 assert not (OUT/'seams.json').exists()
 m=runpy.run_path(str(ROOT/'build/check-demand-seams.py'))
 # The extraction helper's global OUT is explicitly redirected to a fresh tree.
 g=m['ring'].__globals__;g['OUT']=OUT
 original_read=g['ring']
 code=(ROOT/'build/check-demand-seams.py').read_text().replace("OUT/'small/core/source/apu_blargg.c'","OUT/'core/source/apu_blargg.c'")
 ns={'__file__':str(ROOT/'build/check-demand-seams.py'),'__name__':'demand_final_seams'};exec(compile(code,'check-demand-seams.py','exec'),ns)
 ns['OUT']=OUT;ns['ring']();ns['geometry']()
 p=OUT/'geometry-check.c';s=p.read_text().replace('#include "demand-geometry.h"','#include "geometry-under-test.h"')
 s=s.replace(' assert(d35_demand[DS_GEO_REUSED]', ''' /* BG0 is enabled on both planes but its 8bpp/direct-color family is
    unsupported; the producer must select the next eligible BG1. */
 GFX.r212c=GFX.r212d=3;GFX.r2130=1;GFX.S=GFX.SubScreen;GFX.pCurrentClip=&IPPU.Clip[1];DrawTilePtr=DrawTile16;
 d35_geometry_reset();used=0;CandidateBackground(3,0,5,13);assert(d35_geometry_layer==4);
 used=0;DrawBackground(3,1,2,9);unsigned n=used;memcpy(expected,recorded,n*sizeof(*recorded));
 used=0;CandidateBackground(3,1,2,9);assert(d35_geometry_layer==1&&used==n&&!memcmp(expected,recorded,n*sizeof(*recorded)));cases++;
 assert(d35_demand[DS_GEO_REUSED]''')
 p.write_text(s,newline='\n');(OUT/'geometry-under-test.h').write_bytes((OUT/'core/source/a7_demand_geometry.h').read_bytes())
 result={}
 for name in ('geometry','ring'):
  source=OUT/(name+'-check.c');exe=OUT/(name+'-check')
  subprocess.run(['gcc','-O2','-std=gnu99','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-variable','-Wno-sign-compare','-Wno-misleading-indentation','-Ibuild','-I'+str(OUT/'core/source'),str(source),'-o',str(exe)],cwd=ROOT,check=True)
  r=subprocess.run([str(exe)],cwd=ROOT,check=True,capture_output=True,text=True,timeout=180)
  (OUT/(name+'-check.log')).write_text(r.stdout);print(r.stdout,end='');result[name]={'passed':True,'output':r.stdout.strip(),'source_sha256':sha256(source.read_bytes()).hexdigest()}
 (OUT/'seams.json').write_text(json.dumps({'passed':True,'checks':result,'A7_performance_evidence':False},indent=2)+'\n')
if __name__=='__main__':main()
