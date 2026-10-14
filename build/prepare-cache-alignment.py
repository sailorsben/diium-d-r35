"""Owned 64-byte tile allocation and compact nonstraddling palette experiment."""
from pathlib import Path
from hashlib import sha256
import shutil,json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/cache-alignment-private-v1'
BASE=ROOT/'build/common-band-private-v3'
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def main():
 assert not OUT.exists();assert sha256((BASE/'plus-a7.so').read_bytes()).hexdigest()=='e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129'
 OUT.mkdir();shutil.copytree(BASE/'core',OUT/'core',ignore=shutil.ignore_patterns('*.o','*.so'));core=OUT/'core'
 p=core/'source/memmap.c';s=p.read_text(encoding='utf-8');needle='bool S9xInitMemory(void)';assert s.count(needle)==1
 s=s.replace(needle,'''/* Explicit A7 L1D boundary. Keep the original allocation size/zeroing.
 * Retain the malloc owner separately from the aligned public address. */
static void *d35_tile_calloc(size_t bytes)
{
 void *owner=malloc(bytes+63+sizeof(void *));
 if(!owner)return NULL;
 uintptr_t aligned=((uintptr_t)owner+sizeof(void *)+63)&~(uintptr_t)63;
 ((void **)aligned)[-1]=owner;memset((void *)aligned,0,bytes);return (void *)aligned;
}
static void d35_tile_free(void *ptr){if(ptr)free(((void **)ptr)[-1]);}
'''+needle)
 for bits in (2,4,8):
  old=f'(uint8_t*) calloc(MAX_{bits}BIT_TILES, 128)';assert s.count(old)==1;s=s.replace(old,f'(uint8_t*) d35_tile_calloc(MAX_{bits}BIT_TILES * 128)')
 assert s.count('free(IPPU.TileCache[t]);')==1;s=s.replace('free(IPPU.TileCache[t]);','d35_tile_free(IPPU.TileCache[t]);');write(p,s)
 p=core/'source/a7_color_cache.h';s=p.read_text(encoding='utf-8')
 s=s.replace('unsigned epoch,bits; d35_palette_t table;','unsigned epoch,bits;')
 s=s.replace('static struct d35_palette_entry d35_palette_entries[80];','static struct d35_palette_entry d35_palette_entries[80];\nstatic d35_palette_t d35_palette_tables[80] __attribute__((aligned(64)));')
 s=s.replace('entry->table=d35_palette(palette,bits);','d35_palette_tables[slot]=d35_palette(palette,bits);').replace('return entry->table;','return d35_palette_tables[slot];');write(p,s)
 p=core/'source/tile.c';s=p.read_text(encoding='utf-8');s+='''
__attribute__((visibility("default"))) void d35_layout_read(unsigned *p){
 p[0]=(unsigned)(uintptr_t)IPPU.TileCache[0];p[1]=(unsigned)(uintptr_t)IPPU.TileCache[1];p[2]=(unsigned)(uintptr_t)IPPU.TileCache[2];
 p[3]=sizeof(d35_palette_t);p[4]=__alignof__(d35_palette_t);p[5]=sizeof(struct d35_palette_entry);
 p[6]=sizeof(d35_palette_tables[0]);p[7]=(unsigned)(uintptr_t)d35_palette_tables;
}
''';write(p,s)
 p=core/'link.T';s=p.read_text(encoding='utf-8').replace('global:','global: d35_layout_read;');write(p,s)
 s=(BASE/'ordinary-compare.c').read_text(encoding='utf-8')
 s=s.replace('    unsigned char *a=malloc(size),*b=malloc(size);','''    void (*layout)(unsigned *);*(void **)(&layout)=dlsym(candidate.handle,"d35_layout_read");assert(layout);
    unsigned lp[8];layout(lp);assert(!(lp[0]%64)&&!(lp[1]%64)&&!(lp[2]%64)&&!(lp[7]%64)&&lp[3]==32&&lp[6]==32);
    for(unsigned i=0;i<80;i++){assert(((lp[7]+i*lp[6])%64)+lp[3]<=64);}
    printf("ALIGNED");for(unsigned j=0;j<8;j++){printf(" %u",lp[j]);}puts("");
    unsigned char *a=malloc(size),*b=malloc(size);''');write(OUT/'compare.c',s)
 shutil.copy2(ROOT/'build/shared-geometry-private-v1/inputs.json',OUT/'inputs.json')
 print('Prepared explicit64B tile alignment and separate32B palette tables; no renderer decisions or device changes')
if __name__=='__main__':main()
