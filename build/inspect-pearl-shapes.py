"""Record why the flat-band hypothesis does not activate. Offline only."""
from pathlib import Path
import shutil,subprocess,os
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/pearl-shapes-private-v1'
def main():
 assert not OUT.exists();OUT.mkdir()
 shutil.copytree(ROOT/'build/pearl-paths-private-v1/flat/counted-core',OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'))
 p=OUT/'core/source/gfx.c';s=p.read_text();anchor='      if(BGMode==1 && bg==2 && BG.TileSize==8'
 assert s.count(anchor)==1
 s=s.replace(anchor,'''      if(BGMode==1 && bg==2 && GFX.S==GFX.SubScreen){
       d35_pearl[310]+=Lines;
       if(BG.TileSize==8&&BG.BitShift==2)d35_pearl[311]+=Lines;
       if((GFX.r212d&31)==4)d35_pearl[312]+=Lines;
       if(!GFX.Pseudo&&PPU.Mosaic<=1&&!IPPU.DoubleWidthPixels&&!IPPU.DoubleHeightPixels&&!IPPU.HalfWidthPixels&&GFX.PixSize==1&&GFX.ZPitch==GFX.PPL)d35_pearl[313]+=Lines;
       if(!(window_custom?window_clip.count:GFX.pCurrentClip->Count[bg]))d35_pearl[314]+=Lines;
      }
'''+anchor);p.write_text(s,newline='\n')
 p=OUT/'core/source/a7_pearl_flat.h';s=p.read_text().replace(' if(!lines',' ++d35_pearl[320];\n if(!lines')
 s=s.replace('!=tile)return 0;','!=tile){++d35_pearl[321];return 0;}')
 s=s.replace('if((a&&a!=255)||(b&&b!=255))return 0;','if((a&&a!=255)||(b&&b!=255)){++d35_pearl[322];return 0;}')
 s=s.replace(' unsigned z=',' ++d35_pearl[323];\n unsigned z=');p.write_text(s,newline='\n')
 p=OUT/'core/source/tile.c';s=p.read_text();anchor='        d35_pearl_row(mode,mask,old_depth,depth_mask);'
 s=s.replace(anchor,anchor+'''
        if(d35_pearl_plane==1&&d35_pearl_layer==2){
          uint8_t ii[8];vst1_u8(ii,idx);unsigned same=1,csame=1,opaque=1;
          for(unsigned j=0;j<8;j++){same&=ii[j]==ii[0];csame&=colors[ii[j]]==colors[ii[0]];opaque&=ii[j]!=0;}
          d35_pearl[324]+=same;d35_pearl[325]+=csame;d35_pearl[326]+=opaque;
        }
''');p.write_text(s,newline='\n')
 shutil.copy2(ROOT/'build/pearl-work-private-v1/compare.c',OUT/'compare.c')
 s=(ROOT/'build/build-pearl-work.sh').read_text().replace('pearl-work-private-v1',OUT.name)
 (OUT/'build.sh').write_text(s.replace('"$(dirname "$0")/.."','"$(dirname "$0")/../.."'),newline='\n')
 subprocess.run(['sh',str(OUT/'build.sh')],cwd=ROOT,check=True)
 with (OUT/'holy.log').open('x') as f:
  subprocess.run(['qemu-arm','-cpu','cortex-a7','-L','build/sysroot',str(OUT/'compare'),'build/plus-a7-out/plus-a7.so',str(OUT/'plus-a7.so'),'build/plus-a7-out/ff6.sfc','build/ability-regression-private-v1/cases/000/scene.state','build/ability-regression-private-v1/cases/000/input.txt','14','1200'],cwd=ROOT,env={**os.environ,'LD_LIBRARY_PATH':str(ROOT/'build/sysroot/lib')},stdout=f,stderr=subprocess.STDOUT,check=True)
 print('PASS shape probe exact output; work only')
if __name__=='__main__':main()
