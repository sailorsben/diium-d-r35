"""Add offline 4bpp visibility-before-materialization probe, no render changes."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/partial-preflight-private-v1'
def main():
 assert not OUT.exists();OUT.mkdir();core=OUT/'profile-core'
 shutil.copytree(ROOT/'build/partial-merge-private-v1/profile-core',core,ignore=shutil.ignore_patterns('*.o','*.so'))
 shutil.copy2(ROOT/'build/partial-preflight-census.h',core/'source/a7_partial_merge.h')
 p=core/'source/a7_common_batch.h';s=p.read_text();assert s.count(' CB(0);')==1;s=s.replace(' CB(0);',' CB(0);\n d35_partial_preflight(mode,offset,lines);');p.write_text(s,newline='\n')
 shutil.copy2(ROOT/'build/partial-merge-private-v1/compare.c',OUT/'compare.c')
 (ROOT/'build/build-partial-preflight.sh').write_text((ROOT/'build/build-partial-merge.sh').read_text().replace('partial-merge-private-v1','partial-preflight-private-v1'),newline='\n')
 print('Prepared isolated visibility preflight census; no card access')
if __name__=='__main__':main()
