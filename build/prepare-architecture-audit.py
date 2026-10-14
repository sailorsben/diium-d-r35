"""Instrument a fresh owned copy of the exact running core; counts, not timings."""
from pathlib import Path
from hashlib import sha256
import json,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/architecture-audit-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def main():
 assert not OUT.exists();OUT.mkdir();src=ROOT/'build/common-band-private-v3/core'
 assert digest(ROOT/'build/common-band-private-v3/plus-a7.so')=='e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129'
 shutil.copytree(src,OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'));core=OUT/'core'
 for name in ('libretro.c','source/gfx.c','source/apu_blargg.c','source/ppu.h'):
  p=core/name;write(p,'#include "'+('source/' if name=='libretro.c' else '')+'a7_arch_audit.h"\n'+p.read_text())
 shutil.copy2(ROOT/'build/architecture-audit.h',core/'source/a7_arch_audit.h')
 p=core/'libretro.c';s=p.read_text();s+='\nunsigned long long d35_arch[32];\n__attribute__((visibility("default"))) void d35_arch_read(unsigned long long *out){memcpy(out,d35_arch,sizeof(d35_arch));memset(d35_arch,0,sizeof(d35_arch));}\n';write(p,s)
 p=core/'link.T';write(p,p.read_text().replace('global:','global: d35_arch_read;'))
 p=core/'source/gfx.c';s=p.read_text();needle='void S9xSetupOBJ(void)\n{';assert needle in s
 observer='''
struct arch_obj_key {int size,first,rotation,evil,flicker;int sprite[128][4];};
static struct arch_obj_key arch_old_key;
static unsigned arch_key_valid,arch_same;
static unsigned char arch_old_lines[sizeof(GFX.OBJLines)];
static unsigned char arch_old_widths[sizeof(GFX.OBJWidths)];
static unsigned char arch_old_visible[sizeof(GFX.OBJVisibleTiles)];
static void arch_obj_before(void){
 struct arch_obj_key k;memset(&k,0,sizeof(k));
 k.size=PPU.OBJSizeSelect;k.first=PPU.FirstSprite;k.rotation=PPU.OAMPriorityRotation;
 k.evil=!!(PPU.OAMFlip&PPU.OAMAddr&1);k.flicker=reduce_sprite_flicker;
 for(unsigned i=0;i<128;i++){k.sprite[i][0]=PPU.OBJ[i].HPos;k.sprite[i][1]=PPU.OBJ[i].VPos;k.sprite[i][2]=PPU.OBJ[i].Size;k.sprite[i][3]=PPU.OBJ[i].VFlip;}
 d35_arch[0]++;arch_same=arch_key_valid&&!memcmp(&k,&arch_old_key,sizeof(k));
 if(arch_same)d35_arch[1]++;if(k.rotation&&k.evil)d35_arch[2]++;
 arch_old_key=k;arch_key_valid=1;
}
static void arch_obj_after(void){
 if(arch_same&&(memcmp(arch_old_lines,GFX.OBJLines,sizeof(GFX.OBJLines))||memcmp(arch_old_widths,GFX.OBJWidths,sizeof(GFX.OBJWidths))||memcmp(arch_old_visible,GFX.OBJVisibleTiles,sizeof(GFX.OBJVisibleTiles))))d35_arch[28]++;
 memcpy(arch_old_lines,GFX.OBJLines,sizeof(GFX.OBJLines));memcpy(arch_old_widths,GFX.OBJWidths,sizeof(GFX.OBJWidths));memcpy(arch_old_visible,GFX.OBJVisibleTiles,sizeof(GFX.OBJVisibleTiles));
}
'''
 s=s.replace(needle,observer+needle+'\n   arch_obj_before();');s=s.replace('   IPPU.OBJChanged = false;','   arch_obj_after();\n   IPPU.OBJChanged = false;')
 needle='static void DrawOBJS(bool OnMain, uint8_t D)\n{';assert needle in s;s=s.replace(needle,needle+'\n   unsigned arch_last_normal=2;d35_arch[5]++;')
 needle='         if (OnMain && SUB_OR_ADD(4))\n            SelectTileRenderer(!GFX.Pseudo && PPU.OBJ [S].Palette < 4);';assert needle in s
 s=s.replace(needle,'''         if (OnMain && SUB_OR_ADD(4)){
            unsigned normal=!GFX.Pseudo&&PPU.OBJ[S].Palette<4;d35_arch[3]++;
            if(normal==arch_last_normal)d35_arch[4]++;arch_last_normal=normal;
            SelectTileRenderer(normal);
         }''')
 s=s.replace('                     (*DrawClippedTilePtr)(BaseTile | TileX, O, x - X, NextPos - x, TileLine, 1);','''                     {d35_arch[7]++;
                      if(x==X&&NextPos-x==8){d35_arch[8]++;if(DrawClippedTilePtr==DrawClippedTile16)d35_arch[9]++;else if(DrawClippedTilePtr==DrawClippedTile16Add)d35_arch[10]++;else d35_arch[11]++;}
                      (*DrawClippedTilePtr)(BaseTile | TileX, O, x - X, NextPos - x, TileLine, 1);}''')
 write(p,s)
 p=core/'source/apu_blargg.c';s=p.read_text();s=s.replace('static void resampler_read(int16_t *data, int32_t num_samples)\n{','static void resampler_read(int16_t *data, int32_t num_samples)\n{\n   unsigned arch_copies=0;')
 s=s.replace('int bytesUntilBufferEnd = rb_buffer_size - rb_start;','int bytesUntilBufferEnd = rb_buffer_size - rb_start;\n        d35_arch[16]++;d35_arch[21]+=(unsigned)num_samples*2;\n        d35_arch[18]+=(num_samples*2>bytesUntilBufferEnd)?2:!!num_samples;')
 s=s.replace('memcpy(data, &rb_buffer[rb_start], bytesToConsume);','++arch_copies;++d35_arch[17];memcpy(data, &rb_buffer[rb_start], bytesToConsume);')
 s=s.replace('\t\treturn;\n\t}\n\n   i_position = rb_start >> 1;','\t\tif(arch_copies>2)d35_arch[19]++;if(arch_copies>d35_arch[20])d35_arch[20]=arch_copies;\n\t\treturn;\n\t}\n\n   d35_arch[22]++;\n   i_position = rb_start >> 1;');write(p,s)
 p=core/'source/ppu.h';s=p.read_text();needle='   IPPU.TileCached [TILE_2BIT][address >> 4] = false;';assert s.count(needle)==6
 s=s.replace(needle,'   d35_arch[24]++;if(!IPPU.TileCached[TILE_2BIT][address>>4]&&!IPPU.TileCached[TILE_4BIT][address>>5]&&!IPPU.TileCached[TILE_8BIT][address>>6])d35_arch[25]++;\n'+needle);write(p,s)
 # Reuse the existing original-input/state/output oracle; replace only census I/O.
 s=(ROOT/'build/common-band-private-v3/compare.c').read_text()
 a=s.index('    void (*pearl)');b=s.index('    unsigned char *a=malloc',a)
 s=s[:a]+'''    void (*arch)(unsigned long long *);*(void **)(&arch)=dlsym(candidate.handle,"d35_arch_read");assert(arch);unsigned long long ac[32];arch(ac);
'''+s[b:]
 needle='        pearl(pc);printf("PEARL %u",frame);for(unsigned pi=0;pi<352;pi++)printf(",%llu",pc[pi]);puts("");';assert needle in s
 s=s.replace(needle,'        arch(ac);printf("ARCH %u",frame);for(unsigned j=0;j<32;j++)printf(",%llu",ac[j]);puts("");')
 write(OUT/'compare.c',s)
 inputs=[src/n for n in ('libretro.c','source/gfx.c','source/apu_blargg.c','source/ppu.h','source/a7_window.h','source/a7_common_batch.h')]
 write(OUT/'inputs.json',json.dumps({'input_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in inputs},'baseline_core_sha256':digest(ROOT/'build/common-band-private-v3/plus-a7.so'),'observer_only':True,'card_access':False},indent=2)+'\n')
 print('Prepared owned observer-only architecture census; frozen cores untouched')
if __name__=='__main__':main()
