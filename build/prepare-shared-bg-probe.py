"""Preserve the completed first experiment; separately explain its guards."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
def main():
 a=ROOT/'build/shared-geometry-private-v1';b=ROOT/'build/shared-geometry-private-v2'
 assert (a/'qualification.json').exists() and not b.exists();b.mkdir()
 shutil.copytree(a/'core',b/'core',ignore=shutil.ignore_patterns('*.o','*.so'))
 p=b/'core/source/a7_shared_geometry.h';s=p.read_text(encoding='utf-8')
 needle=' if(bg!=0)return 0;';assert s.count(needle)==1
 s=s.replace(needle,needle+'''
 d35_shared_stats[7]++;
 if(mode!=1)d35_shared_stats[8]++;
 if(BG.TileSize!=8)d35_shared_stats[9]++;
 if(!batch_ok)d35_shared_stats[10]++;
 if(!(GFX.r212c&1)||!(GFX.r212d&1))d35_shared_stats[11]++;
 if(IPPU.Clip[0].Count[0]||IPPU.Clip[1].Count[0])d35_shared_stats[12]++;
 if(d35_window_is_target(0))d35_shared_stats[13]++;
 if(IPPU.Clip[0].Count[0]==1&&IPPU.Clip[0].Left[0][0]==0&&IPPU.Clip[0].Right[0][0]==256)d35_shared_stats[14]++;
 if(IPPU.Clip[1].Count[0]==1&&IPPU.Clip[1].Left[0][0]==0&&IPPU.Clip[1].Right[0][0]==256)d35_shared_stats[15]++;
''');p.write_text(s,encoding='utf-8',newline='\n')
 for n in ('compare.c','inputs.json'):shutil.copy2(a/n,b/n)
 print('Prepared independent guard observer; keep v1 qualification unchanged')
if __name__=='__main__':main()
