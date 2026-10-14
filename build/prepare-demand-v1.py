"""Fresh, isolated candidates. No installer; refuse all existing output trees."""
from pathlib import Path
from hashlib import sha256
import json, shutil
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'build/common-band-private-v3'
OUT=ROOT/'build/demand-private-v1'
REFERENCE='e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129'
def write(p,s): p.write_text(s,encoding='utf-8',newline='\n')
def edit(p,a,b):
 s=p.read_text(); assert s.count(a)==1,(p,a,s.count(a));write(p,s.replace(a,b))
def dma(core):
 p=core/'source/dma.c'
 edit(p,'#include "dma.h"','#include "dma.h"\n#include "a7_demand_stats.h"')
 a='''            if (!PPU.VMA.FullGraphicCount)
            {
               while (count > 1)'''
 b='''            unsigned source=(d->ABank<<16)|p,v=(PPU.VMA.Address<<1)&65535u;
            if(inc==1&&!PPU.VMA.FullGraphicCount&&PPU.VMA.High&&PPU.VMA.Increment==1&&
               !Settings.SA1&&!Settings.SDD1&&!Settings.SPC7110&&!in_sa1_dma&&
               !(count&1)&&(unsigned)count<=4096u-(source&4095u)&&
               (unsigned)count<=65536u-v&&
               (Memory.BlockIsRAM[source>>12]||Memory.BlockIsROM[source>>12])&&
               GetBasePointer(source)) {
               /* Existing flush, cycle charge and A-address update precede us.
                * The common HBlank and register finalization follow unchanged. */
               memcpy(Memory.VRAM+v,base+p,count);
               DS_ADD(DS_DMA_SPANS,1);DS_ADD(DS_DMA_BYTES,count);DS_ADD(DS_DMA_OLD_FLAGS,3*count);
               for(unsigned bits=0;bits<3;bits++) {
                  unsigned shift=4+bits,first=v>>shift,last=(v+count-1)>>shift;
                  memset(IPPU.TileCached[bits]+first,0,last-first+1);
                  DS_ADD(DS_DMA_FLAGS,last-first+1);
               }
               PPU.VMA.Address+=count/2;count=0;
            }
            else if (!PPU.VMA.FullGraphicCount)
            {
               while (count > 1)'''
 edit(p,a,b)
def small(core):
 p=core/'source/apu_blargg.c';s=p.read_text();a=s.index('\tif (r_step == 65536)',s.index('static void resampler_read('));b=s.index('   i_position = rb_start >> 1;',a)
 s=s[:a]+'''   if(r_step==65536) {
      int bytes=num_samples*2,tail=rb_buffer_size-rb_start;
      if(bytes) {
         int first=bytes<tail?bytes:tail;
         DS_ADD(DS_RING_OLD_COPIES,(bytes+tail-1)/tail);
         memcpy(data,rb_buffer+rb_start,first);DS_ADD(DS_RING_COPIES,1);
         if(bytes>first){memcpy((uint8_t *)data+first,rb_buffer,bytes-first);DS_ADD(DS_RING_COPIES,1);}
         rb_start=(rb_start+bytes)%rb_buffer_size;rb_size-=bytes;
      }
      return;
   }

'''+s[b:];write(p,'#include "a7_demand_stats.h"\n'+s)
 p=core/'source/ppu.c';edit(p,'#include "ppu.h"','#include "ppu.h"\n#include "a7_demand_stats.h"')
 edit(p,'   IPPU.XB = mul_brightness [PPU.Brightness];','''   IPPU.XB = mul_brightness [PPU.Brightness];
   if(!PPU.Brightness) {
      memset(IPPU.Red,0,sizeof(IPPU.Red));memset(IPPU.Green,0,sizeof(IPPU.Green));
      memset(IPPU.Blue,0,sizeof(IPPU.Blue));memset(IPPU.ScreenColors,0,sizeof(IPPU.ScreenColors));
      DS_ADD(DS_ZERO_PALETTES,1);return;
   }''')
 edit(p,'            PPU.OBJNameBase   = (Byte & 3) << 14;','''            if(PPU.OBJSizeSelect!=((Byte>>5)&7)||PPU.OAMPriorityRotation)IPPU.OBJChanged=true;
            else DS_ADD(DS_OBJ_AVOIDED,1);
            PPU.OBJNameBase   = (Byte & 3) << 14;''')
 edit(p,'            PPU.OBJSizeSelect = (Byte >> 5) & 7;\n            IPPU.OBJChanged = true;','            PPU.OBJSizeSelect = (Byte >> 5) & 7;')
 p=core/'source/ppu.h';edit(p,'static INLINE void REGISTER_2104(uint8_t byte)','''#include "a7_demand_stats.h"
static INLINE void REGISTER_2104(uint8_t byte)''')
 edit(p,'         PPU.OAMData [addr] = lowbyte;\n         PPU.OAMData [addr + 1] = highbyte;\n         IPPU.OBJChanged = true;','''         if(!(addr&2)||((PPU.OAMData[addr+1]^highbyte)&0x80)||PPU.OAMPriorityRotation)
            IPPU.OBJChanged=true;
         else DS_ADD(DS_OBJ_AVOIDED,1);
         PPU.OAMData [addr] = lowbyte;
         PPU.OAMData [addr + 1] = highbyte;''')
 p=core/'source/gfx.c';s=p.read_text();a=s.index('static void RenderScreen(');b=s.index('void S9xUpdateScreen(',a);part=s[a:b]
 part=part.replace('   sub |= force_no_add;','''   unsigned no_recipient=!GFX.Pseudo&&!(GFX.r2130&0xf0)&&!(GFX.r2131&((GFX.r212c&31)|32));
   if(!sub&&!force_no_add&&no_recipient)DS_ADD(DS_NO_RECIPIENT,GFX.EndY-GFX.StartY+1);
   unsigned normal_all=sub||force_no_add||no_recipient;
   sub |= force_no_add;''')
 part=part.replace('sub || !SUB_OR_ADD(','normal_all || !SUB_OR_ADD(')
 write(p,s[:a]+part+s[b:])
 # Last-key preparation reuse also benefits ordinary OBJ/clipped dispatch. The
 # palette epoch remains the owner, including explicit invalidation on wrap.
 p=core/'source/a7_color_cache.h';s=p.read_text();i=s.index('static unsigned d35_palette_epoch=1;')
 s=s[:i]+'''static const uint16_t *d35_last_palette;
static unsigned d35_last_bits,d35_last_epoch;
static d35_palette_t d35_last_table;
'''+s[i:];s=s.replace('    if(!++d35_palette_epoch)', '    d35_last_epoch=0;\n    if(!++d35_palette_epoch)')
 s=s.replace('    uintptr_t address=(uintptr_t)palette,base=(uintptr_t)IPPU.ScreenColors;','''    if(d35_last_palette==palette&&d35_last_bits==bits&&d35_last_epoch==d35_palette_epoch){DS_ADD(DS_PALETTE_REUSE,1);return d35_last_table;}
    DS_ADD(DS_PALETTE_LOOKUP,1);
    uintptr_t address=(uintptr_t)palette,base=(uintptr_t)IPPU.ScreenColors;''')
 ret='d35_palette_tables[slot]' if 'd35_palette_tables' in s else 'entry->table'
 s=s.replace('    return '+ret+';','''    d35_last_palette=palette;d35_last_bits=bits;d35_last_epoch=d35_palette_epoch;
    d35_last_table='''+ret+''';return d35_last_table;''')
 write(p,'#include "a7_demand_stats.h"\n'+s)
def geometry(core):
 p=core/'source/gfx.c'
 edit(p,'#include "a7_common_band.h"','#include "a7_common_band.h"\n#include "a7_demand_geometry.h"')
 s=p.read_text();a=s.index('static void DrawBackground(uint32_t');b=s.index('#define RENDER_BACKGROUND_MODE7',a);part=s[a:b]
 needle='   SC0 = (uint16_t*) &Memory.VRAM[PPU.BG[bg].SCBase << 1];'
 assert part.count(needle)==1;part=part.replace(needle,'   if(d35_geometry_begin(BGMode,bg,batch_ok,&batch,Z1,Z2,sub_fast?&sub_context:NULL))return;\n\n'+needle)
 write(p,s[:a]+part+s[b:]);edit(p,'   int32_t x2 = 1;','   d35_geometry_reset();\n   int32_t x2 = 1;')
 shutil.copy2(ROOT/'build/demand-geometry.h',core/'source/a7_demand_geometry.h')
def output(core):
 p=core/'source/gfx.c';edit(p,'#include "gfx.h"','#include "gfx.h"\n#define D35_OUTPUT_IMPLEMENTATION\n#include "a7_demand_output.h"')
 edit(p,'   if (++IPPU.FrameCount == (uint32_t)Memory.ROMFramesPerSecond)','   if(IPPU.RenderThisFrame)d35_output_frame_begin();\n\n   if (++IPPU.FrameCount == (uint32_t)Memory.ROMFramesPerSecond)')
 edit(p,'   GFX.S = GFX.Screen;\n   GFX.r2131','   d35_output_promote();\n   GFX.S = GFX.Screen;\n   GFX.r2131')
 p=core/'libretro.c';edit(p,'static retro_video_refresh_t video_cb = NULL;','#include "source/a7_demand_output.h"\nstatic retro_video_refresh_t video_cb = NULL;')
 edit(p,'void retro_deinit(void)\n{','void retro_deinit(void)\n{\n   d35_output_cancel();')
 edit(p,'bool retro_unserialize(const void* data, size_t size)\n{','bool retro_unserialize(const void* data, size_t size)\n{\n   d35_output_cancel();')
 edit(p,'   else\n      video_cb(NULL, IPPU.RenderedScreenWidth, IPPU.RenderedScreenHeight, GFX.Pitch);','   else\n      video_cb(NULL, IPPU.RenderedScreenWidth, IPPU.RenderedScreenHeight, GFX.Pitch);\n   d35_output_finish();')
 edit(core/'link.T','global:','global: d35_output_acquire;')
 shutil.copy2(ROOT/'build/demand-output.h',core/'source/a7_demand_output.h')
def runtime():
 shutil.copy2(ROOT/'build/plus-a7-profile.h',OUT/'plus-a7-profile.h')
 rt=OUT/'runtime-v1';rt.mkdir()
 for p in (ROOT/'build/snes-mvp').iterdir():
  if p.is_file() and p.suffix in ('.c','.h','.sh'):shutil.copy2(p,rt/p.name)
 p=rt/'board.h';edit(p,'int board_video_reserve(void);','int board_video_reserve(void);\nvoid *board_video_target(size_t *bytes);')
 edit(p,'    uint64_t submitted, scaled, flipped, reserve_wait_ns, copy_ns;','    uint64_t submitted, scaled, flipped, reserve_wait_ns, copy_ns;\n    uint64_t direct_submitted, copied_payload_bytes;')
 p=rt/'board.c';edit(p,'#define SLOT_BYTES (640u * 512u * 2u)','#define SLOT_BYTES (640u * 512u * 2u + 64u)')
 edit(p,'b.pixels+slot*SLOT_BYTES),(int)width','b.pixels+slot*SLOT_BYTES+32),(int)width')
 edit(p,'int board_video_submit(const void *rgb565,unsigned width,unsigned height,size_t pitch)','''/* A reserved slot includes the 32-byte renderer prefix and tail. The sole
 * producer owns both slot and FIFO credit until submission/cancel. */
void *board_video_target(size_t *bytes) {
 void *p=NULL;if(bytes)*bytes=0;
 pthread_mutex_lock(&display_lock);
 if(b.opened&&!b.null_backend&&b.reserved>=0&&b.slots[b.reserved].owner==RESERVED){
  p=b.pixels+(unsigned)b.reserved*SLOT_BYTES+32;if(bytes)*bytes=SLOT_BYTES-64;
 }
 pthread_mutex_unlock(&display_lock);return p;
}
int board_video_submit(const void *rgb565,unsigned width,unsigned height,size_t pitch)''')
 edit(p,'slot=(unsigned)b.reserved; target=b.pixels+slot*SLOT_BYTES;','slot=(unsigned)b.reserved; target=b.pixels+slot*SLOT_BYTES+32;')
 edit(p,'''    for(y=0;y<height;++y)
        memcpy(target+(size_t)y*width*2u,(const uint8_t *)rgb565+(size_t)y*pitch,(size_t)width*2u);
    pthread_mutex_lock(&display_lock);''','''    unsigned direct=rgb565==target&&pitch==(size_t)width*2u;
    if(!direct)for(y=0;y<height;++y)
        memcpy(target+(size_t)y*width*2u,(const uint8_t *)rgb565+(size_t)y*pitch,(size_t)width*2u);
    pthread_mutex_lock(&display_lock);
    if(direct)++b.metrics.direct_submitted;else b.metrics.copied_payload_bytes+=(uint64_t)width*height*2u;''')
 p=rt/'runner.c';edit(p,'static void (*p_profile_begin)(unsigned);','static unsigned (*p_output_acquire)(void *,size_t);\nstatic void (*p_profile_begin)(unsigned);')
 edit(p,'    p_profile_begin=NULL; p_profile_end=NULL;','    p_output_acquire=NULL;p_profile_begin=NULL; p_profile_end=NULL;')
 edit(p,'    *(void **)(&p_profile_begin)=dlsym(s.core,"d35_profile_begin");','    *(void **)(&p_output_acquire)=dlsym(s.core,"d35_output_acquire");\n    *(void **)(&p_profile_begin)=dlsym(s.core,"d35_profile_begin");')
 edit(p,'        if(p_profile_begin) p_profile_begin(sample);','''        if(p_output_acquire){size_t bytes=0;void *target=board_video_target(&bytes);p_output_acquire(target,bytes);}
        if(p_profile_begin) p_profile_begin(sample);''')
 # Exercise the actual candidate board implementation, with FIFO pressure and
 # cancellation, using both direct publication and persistent-buffer copying.
 p=rt/'display-queue-check.c';s=p.read_text();s=s.replace('    assert(!board_video_submit(pixels,8,8,16));','''    if(value&1){size_t bytes;assert(!board_video_reserve());void *target=board_video_target(&bytes);assert(target&&bytes>=128);memcpy(target,pixels,128);assert(!board_video_submit(target,8,8,16));}
    else assert(!board_video_submit(pixels,8,8,16));''')
 s=s.replace('    assert(drawn==4 && flipped==4','    assert(stats.direct_submitted==2&&stats.copied_payload_bytes==256);\n    assert(drawn==4 && flipped==4')
 s=s.replace('    submit(1);','    assert(!board_video_reserve());size_t cancel_bytes;assert(board_video_target(&cancel_bytes));board_video_cancel();assert(!board_video_target(&cancel_bytes)&&!cancel_bytes);\n    submit(1);')
 write(p,s)
def main():
 assert not OUT.exists();assert sha256((BASE/'plus-a7.so').read_bytes()).hexdigest()==REFERENCE
 # Snapshot every qualified tree, including binaries and scripts, before work.
 frozen={}
 for name in ('common-band-private-v3','fused-toolbox-private-v2','cache-alignment-private-v1','shared-geometry-private-v1'):
  for p in (ROOT/'build'/name).rglob('*'):
   if p.is_file():frozen[p.relative_to(ROOT).as_posix()]=sha256(p.read_bytes()).hexdigest()
 OUT.mkdir();write(OUT/'frozen.json',json.dumps(frozen,indent=2)+'\n')
 for name in ('dma','small','geometry','output','combined'):
  core=OUT/name/'core';shutil.copytree(BASE/'core',core,ignore=shutil.ignore_patterns('*.o','*.so'))
  shutil.copy2(ROOT/'build/demand-stats.h',core/'source/a7_demand_stats.h')
  edit(core/'source/gfx.c','#include "gfx.h"','#include "gfx.h"\n#include "a7_demand_stats.h"')
  if name=='combined':
   for f in ('a7_common_batch.h','a7_common_band.h','a7_partial_kernels.h'):
    shutil.copy2(ROOT/'build/fused-toolbox-private-v2/core/source'/f,core/'source'/f)
   edit(core/'source/gfx.c','batch.mode=7;batch.valid=0;','batch.mode=7;batch.valid=0;batch.depth_policy=0;')
   for f in ('memmap.c','a7_color_cache.h'):
    shutil.copy2(ROOT/'build/cache-alignment-private-v1/core/source'/f,core/'source'/f)
  if name in ('dma','combined'):dma(core)
  if name in ('small','combined'):small(core)
  if name in ('geometry','combined'):geometry(core)
  if name in ('output','combined'):output(core)
  p=core/'libretro.c';s=p.read_text();s+='''
#include "source/a7_demand_stats.h"
unsigned long long d35_demand[DS_FIELDS];
__attribute__((visibility("default"))) void d35_demand_read(unsigned long long *out){memcpy(out,d35_demand,sizeof(d35_demand));memset(d35_demand,0,sizeof(d35_demand));}
''';write(p,s);edit(core/'link.T','global:','global: d35_demand_read;')
  if name=='combined':
   p=core/'source/gfx.c';s=p.read_text();s+='''
#ifdef D35_FUSED_COUNT
unsigned long long d35_fused[32];
__attribute__((visibility("default"))) void d35_fused_read(unsigned long long *p){memcpy(p,d35_fused,sizeof(d35_fused));memset(d35_fused,0,sizeof(d35_fused));}
#endif
''';write(p,s);edit(core/'link.T','global:','global: d35_fused_read;')
  shutil.copytree(core,OUT/name/'counted-core')
 # New harness compares raw pixel/PCM bytes as well as existing checksums.
 s=(ROOT/'build/plus-a7-equivalence.c').read_text()
 s=s.replace('    void *handle;','    void *handle;\n    uint16_t frame_pixels[512*512];int16_t frame_pcm[8192];const void *video_pointer;size_t video_pitch;')
 s=s.replace('    for(y=0;y<h;y++) active->pixels=', '    active->video_pointer=p;active->video_pitch=pitch;\n    assert(w<=512&&h<=512);for(y=0;y<h;y++)memcpy(active->frame_pixels+y*w,(const unsigned char *)p+y*pitch,w*2);\n    for(y=0;y<h;y++) active->pixels=')
 s=s.replace('{ active->pcm=crc32','{ assert((active->samples+n)*2<=8192);memcpy(active->frame_pcm+active->samples*2,p,n*4);active->pcm=crc32')
 write(OUT/'demand-equivalence.c',s)
 s=(BASE/'ordinary-compare.c').read_text().replace('"plus-a7-equivalence.c"','"demand-equivalence.c"')
 s=s.replace('    unsigned char *a=malloc(size),*b=malloc(size);','''    unsigned (*acquire)(void *,size_t);void (*counts)(unsigned long long *);
    *(void **)(&acquire)=dlsym(candidate.handle,"d35_output_acquire");
    *(void **)(&counts)=dlsym(candidate.handle,"d35_demand_read");assert(counts);
    unsigned long long dc[32];counts(dc);
    uint8_t *owned_owner=calloc(1,512*240+256);assert(owned_owner);
    uint8_t *owned=(uint8_t *)(((uintptr_t)owned_owner+63)&~(uintptr_t)63);
    unsigned char *a=malloc(size),*b=malloc(size);''')
 s=s.replace('active=&candidate;candidate.run();','active=&candidate;if(acquire)assert(acquire(owned+64,512*240+64));candidate.run();')
 s=s.replace('        if(reference.pixels!=candidate.pixels','        if(memcmp(reference.frame_pixels,candidate.frame_pixels,reference.w*reference.h*2)||memcmp(reference.frame_pcm,candidate.frame_pcm,reference.samples*4)||reference.pixels!=candidate.pixels')
 s=s.replace('        unsigned long long sc[8]={0};','''        counts(dc);printf("DEMAND %u",frame);for(unsigned j=0;j<32;j++)printf(",%llu",dc[j]);puts("");
        unsigned long long sc[8]={0};''')
 write(OUT/'compare.c',s)
 runtime()
 print('Prepared five isolated/combined source pairs; frozen reference verified; no card access')
if __name__=='__main__':main()
