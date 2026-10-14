"""Retain qualified v1; remove a generic ring division and count intersections."""
from pathlib import Path
import json,shutil
from hashlib import sha256
ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT/'build/demand-private-v1'
OUT=ROOT/'build/demand-final-private-v2'
def write(p,s):p.write_text(s,encoding='utf-8',newline='\n')
def main():
 assert not OUT.exists();assert json.loads((OLD/'qualification.json').read_text())['passed']
 OUT.mkdir()
 frozen=json.loads((OLD/'frozen.json').read_text())
 for p in OLD.rglob('*'):
  if p.is_file() and p.suffix in ('.c','.h','.so','.json','.log'):frozen[p.relative_to(ROOT).as_posix()]=sha256(p.read_bytes()).hexdigest()
 write(OUT/'frozen.json',json.dumps(frozen,indent=2)+'\n')
 for label in ('core','counted-core'):
  core=OUT/label;shutil.copytree(OLD/'combined'/label,core,ignore=shutil.ignore_patterns('*.o','*.so'))
  p=core/'source/apu_blargg.c';s=p.read_text();a='rb_start=(rb_start+bytes)%rb_buffer_size;rb_size-=bytes;';assert s.count(a)==1
  s=s.replace(a,'rb_start+=bytes;if(rb_start>=rb_buffer_size)rb_start-=rb_buffer_size;rb_size-=bytes;');write(p,s)
  p=core/'source/a7_demand_geometry.h';s=p.read_text();a='if(d35_geometry_layer==4){for(unsigned i=0;i<4;i++)if(both&(1u<<i)){d35_geometry_layer=i;break;}}';assert s.count(a)==1
  s=s.replace(a,'if(d35_geometry_layer==4)d35_geometry_layer=bg; /* first eligible dual layer */')
  marker='#define D35_GEOMETRY_DRAW(MODE)';assert s.count(marker)==1
  s=s.replace(marker,'''#if defined(D35_FUSED_COUNT) && defined(D35_DEMAND_COUNT)
#define GEO_BEFORE unsigned long long hidden_before=d35_fused[6],rows_before=d35_fused[7];
#define GEO_AFTER if(GFX.S==GFX.Screen){DS_ADD(30,d35_fused[6]-hidden_before);DS_ADD(31,d35_fused[7]-rows_before);}
#else
#define GEO_BEFORE
#define GEO_AFTER
#endif
'''+marker)
  s=s.replace('    else {DS_ADD(DS_GEO_FULL,1); '+chr(92)+'\n','    else {DS_ADD(DS_GEO_FULL,1);GEO_BEFORE '+chr(92)+'\n')
  s=s.replace('(*DrawTilePtr)(tile,offset,g->line,g->lines); '+chr(92)+'\n','(*DrawTilePtr)(tile,offset,g->line,g->lines);GEO_AFTER '+chr(92)+'\n');write(p,s)
  # Observe pointer guarantees for eventual A7 use, without any clocks.
  p=core/'source/tile.c';s=p.read_text();s+='''
__attribute__((visibility("default"))) void d35_final_layout(unsigned *p){
 p[0]=(unsigned)(uintptr_t)IPPU.TileCache[0];p[1]=(unsigned)(uintptr_t)IPPU.TileCache[1];p[2]=(unsigned)(uintptr_t)IPPU.TileCache[2];p[3]=(unsigned)(uintptr_t)d35_palette_tables;
}
''';write(p,s)
  p=core/'link.T';write(p,p.read_text().replace('global:','global: d35_final_layout;'))
 shutil.copy2(OLD/'demand-equivalence.c',OUT/'demand-equivalence.c')
 s=(OLD/'compare.c').read_text()
 s=s.replace('    unsigned long long dc[32];counts(dc);','''    unsigned long long dc[32];counts(dc);
    void (*fused)(unsigned long long *);*(void **)(&fused)=dlsym(candidate.handle,"d35_fused_read");unsigned long long fu[32];if(fused)fused(fu);
    void (*layout)(unsigned *);*(void **)(&layout)=dlsym(candidate.handle,"d35_final_layout");assert(layout);unsigned lp[4];layout(lp);for(unsigned j=0;j<4;j++)assert(!(lp[j]%64));
    printf("ALIGNED %u %u %u %u\\n",lp[0],lp[1],lp[2],lp[3]);''')
 s=s.replace('        counts(dc);printf(','''        if(fused){fused(fu);printf("FUSED %u",frame);for(unsigned j=0;j<32;j++)printf(",%llu",fu[j]);puts("");}
        counts(dc);printf(''')
 write(OUT/'compare.c',s)
 print('Prepared v2 from exact qualified combined v1; no ring division; first eligible dual layer; fused intersections and alignment assertions')
if __name__=='__main__':main()
