"""Count pasted traversal hypotheses in a new offline observer copy."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/architecture-followup-private-v1'
OLD=ROOT/'build/architecture-audit-private-v1'
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def main():
 assert not OUT.exists();OUT.mkdir();shutil.copytree(OLD/'core',OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'));core=OUT/'core'
 p=core/'source/a7_arch_audit.h';write(p,p.read_text().replace('d35_arch[32]','d35_arch[64]'))
 p=core/'libretro.c';write(p,p.read_text().replace('d35_arch[32]','d35_arch[64]'))
 p=core/'source/gfx.c';s=p.read_text()
 anchor='static void DrawOBJS(bool OnMain, uint8_t D)';i=s.index(anchor)
 helpers='''
static unsigned arch_clip_has_pixels(unsigned layer){
 unsigned n=GFX.pCurrentClip->Count[layer];if(!n)return 1;
 for(unsigned j=0;j<n;j++)if(GFX.pCurrentClip->Right[j][layer]>GFX.pCurrentClip->Left[j][layer])return 1;
 return 0;
}
static unsigned arch_BG_has_pixels(unsigned bg){
 for(unsigned y=GFX.StartY;y<=GFX.EndY;y++){
  struct d35_window_clip clip;
  if(d35_window_fetch(bg,y,GFX.pCurrentClip==&IPPU.Clip[1],&clip)){
   for(unsigned j=0;j<clip.count;j++)if(clip.right[j]>clip.left[j])return 1;
  }else if(arch_clip_has_pixels(bg))return 1;
 }
 return 0;
}
'''
 s=s[:i]+helpers+s[i:]
 s=s.replace('   unsigned arch_last_normal=2;d35_arch[5]++;','   unsigned arch_last_normal=2;d35_arch[5]++;\n   if(!arch_clip_has_pixels(4)){d35_arch[36]++;d35_arch[37]+=GFX.EndY-GFX.StartY+1;}')
 anchor='static void DrawBackground(uint32_t BGMode, uint32_t bg, uint8_t Z1, uint8_t Z2)\n{';assert anchor in s
 s=s.replace(anchor,anchor+'\n   d35_arch[32]++;if(!arch_BG_has_pixels(bg)){d35_arch[33]++;d35_arch[34]+=GFX.EndY-GFX.StartY+1;}')
 s=s.replace('         int32_t TileInc = 1;','         d35_arch[48]++;\n         int32_t TileInc = 1;')
 s=s.replace('for (; WinIdx < 7 && Windows[WinIdx].Pos <= X; WinIdx++);','for (d35_arch[45]++; WinIdx < 7 && Windows[WinIdx].Pos <= X; WinIdx++){d35_arch[46]++;}')
 s=s.replace('for (; WinIdx < 7 && Windows[WinIdx].Pos <= x; WinIdx++);','for (d35_arch[45]++; WinIdx < 7 && Windows[WinIdx].Pos <= x; WinIdx++){d35_arch[46]++;}')
 needle='         {\n            if (X < -7 || --t < 0 || X == 256)';assert needle in s;s=s.replace(needle,'         {\n            d35_arch[49]++;\n            if (X < -7 || --t < 0 || X == 256)')
 needle='               while (x < X + 8)\n               {';assert needle in s;s=s.replace(needle,needle+'\n                  d35_arch[50]++;')
 needle='      ClipData* pClip;';assert s.count(needle)==1
 s=s.replace(needle,needle+'\n      d35_arch[40]++;\n      if(!GFX.Pseudo&&!(GFX.r2130&0xf0)&&!(GFX.r2131&((GFX.r212c&31)|32))){d35_arch[41]++;d35_arch[42]+=endy-starty+1;}')
 write(p,s)
 p=core/'source/ppu.c';s=p.read_text();needle='void S9xFixColourBrightness()\n{';assert needle in s;s=s.replace(needle,needle+'\n   d35_arch[52]++;d35_arch[54]+=256;');write(p,s)
 p=core/'source/dma.c';s=p.read_text();needle='   inc = d->AAddressFixed ? 0 : (!d->AAddressDecrement ? 1 : -1);';assert needle in s
 s=s.replace(needle,needle+'''
   d35_arch[56]++;
   { unsigned a=(d->ABank<<16)|d->AAddress,v=(PPU.VMA.Address<<1)&65535u;
     if(!d->TransferDirection&&(d->TransferMode==1||d->TransferMode==5)&&d->BAddress==0x18&&
        !PPU.VMA.FullGraphicCount&&PPU.VMA.High&&PPU.VMA.Increment==1&&inc==1&&
        !Settings.SA1&&!Settings.SDD1&&!Settings.SPC7110&&!(count&1)&&
        (unsigned)count<=4096u-(a&4095u)&&(unsigned)count<=65536u-v&&
        (Memory.BlockIsRAM[a>>12]||Memory.BlockIsROM[a>>12])&&GetBasePointer(a)){
       d35_arch[57]+=(unsigned)count;d35_arch[58]++;
       d35_arch[59]+=((v+count-1)>>4)-(v>>4)+1;
       d35_arch[59]+=((v+count-1)>>5)-(v>>5)+1;
       d35_arch[59]+=((v+count-1)>>6)-(v>>6)+1;
     }
   }
''');write(p,s)
 s=(OLD/'compare.c').read_text().replace('ac[32]','ac[64]').replace('j<32','j<64');write(OUT/'compare.c',s)
 s=(ROOT/'build/build-architecture-audit.sh').read_text().replace('build/architecture-audit-private-v1','build/architecture-followup-private-v1');write(ROOT/'build/build-architecture-followup.sh',s)
 shutil.copy2(OLD/'inputs.json',OUT/'inputs.json')
 print('Prepared fully clipped layers, math recipients, sprite windows, brightness and strict DMA population census')
if __name__=='__main__':main()
