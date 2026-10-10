"""Fresh measurement copy of shipping1.19; never install the window renderer.

The actual source blocks are benchmarked in their actual calling state. Their
outputs remain live, each loop has a memory barrier, and the unmeasured original
block still executes. Mode1 normal-resolution guards exclude stateful fallback
work from repeated setup; phase attribution still includes those fallbacks.
"""
from pathlib import Path
from hashlib import sha256
import json, shutil, sys, re
ROOT=Path(__file__).resolve().parent.parent
name=sys.argv[1] if len(sys.argv)>1 else 'a7-cost-private'
assert re.fullmatch(r'a7-cost-private(?:-[a-z0-9]+)?',name)
OUT=ROOT/'build'/name
assert not OUT.exists(), 'Preserve experiments; do not overwrite an earlier suite'
CORE=OUT/'core'
shutil.copytree(ROOT/'build/snes9x2005',CORE,ignore=shutil.ignore_patterns('.git','*.o','*.so'))
for src,dest in [('a7-cost.h','a7_cost.h'),('a7-cost-core.c','a7_cost.c'),
                 ('plus-a7-window.h','a7_window.h')]:
    shutil.copy2(ROOT/'build'/src,CORE/'source'/dest)
def replace(s,old,new):
    assert s.count(old)==1, old[:100]
    return s.replace(old,new)
def function(s,start):
    at=s.index(start);end=s.index('\n}\n',at)+3
    return at,end,s[at:end]
def bench(kind,body,shape='0',guard='1'):
    return f'\n   if({guard}) D35_COST_BENCH({kind},{shape},{{\n{body}\n   }});\n'
p=CORE/'source/gfx.c';s=p.read_text()
s='#include "a7_cost.h"\n'+s
s=replace(s,'#include "gfx.h"','#include "gfx.h"\n#define D35_WINDOW_IMPLEMENTATION\n#include "a7_window.h"')
# Capture candidate mask state without changing any flush or rendered pixel.
s=replace(s,'void S9xStartScreenRefresh(void)\n{','void S9xStartScreenRefresh(void)\n{\n   d35_window_reset();\n   for(unsigned q=0;q<4;q++) { D35_COST_BENCH(D35_B_RESET,256,{d35_window_reset();}); }')
s=replace(s,'void RenderLine(uint8_t C)\n{','void RenderLine(uint8_t C)\n{\n   d35_window_capture(C);\n   D35_COST_BENCH(D35_B_CAPTURE,C,{d35_window_capture(C);});')
a,z,body=function(s,'void S9xUpdateScreen(void)\n{')
body=replace(body,'   int32_t x2 = 1;', '   unsigned d35_old=d35_cost_push(D35_COST_SETUP);\n   d35_cost_ppu_entry();\n   int32_t x2 = 1;')
prefix=body[body.index('   GFX.S = GFX.Screen;'):body.index('   black = BLACK')]
# OBJ/clip flags have already been consumed when the benchmark runs. Exclude
# their conditional work from e, and price ComputeClipWindows as its own phase.
prefix=prefix.replace('      S9xSetupOBJ();','      { /* separately attributed */ }')
prefix=prefix.replace('      ComputeClipWindows();','      { /* separately attributed */ }')
body=replace(body,'      S9xSetupOBJ();','      { unsigned t=d35_cost_push(D35_COST_PIXEL);S9xSetupOBJ();d35_cost_pop(t); }')
body=replace(body,'      ComputeClipWindows();','      { unsigned t=d35_cost_push(D35_COST_WINDOW);ComputeClipWindows();d35_cost_pop(t); }')
guard='PPU.BGMode==1 && !IPPU.Interlace && !IPPU.DoubleHeightPixels'
body=replace(body,'   black = BLACK',bench('D35_B_ENTRY',prefix+'\n   __asm__ volatile("" : "+r"(starty),"+r"(endy),"+r"(x2) :: "memory");','GFX.EndY-GFX.StartY+1',guard)+'   d35_cost_switch(D35_COST_PIXEL);\n   black = BLACK')
body=body[:-2]+'   d35_cost_pop(d35_old);\n}\n'
s=s[:a]+body+s[z:]
for signature,split,kind,shape,guard in [
 ('static void RenderScreen(uint8_t* Screen, bool sub, bool force_no_add, uint8_t D)\n{','   switch (PPU.BGMode)','D35_B_SCREEN','sub','PPU.BGMode==1'),
 ('static void DrawBackground(uint32_t BGMode, uint32_t bg, uint8_t Z1, uint8_t Z2)\n{','   for (Y = GFX.StartY','D35_B_BACKGROUND','bg','BGMode==1 && !(PPU.BGMosaic[bg] && PPU.Mosaic>1)'),
 ('static void DrawOBJS(bool OnMain, uint8_t D)\n{','   for (Y = GFX.StartY','D35_B_OBJECT','GFX.pCurrentClip->Count[4]','PPU.BGMode==1')]:
    a,z,body=function(s,signature)
    start=body.index('   GFX.S = Screen;' if kind=='D35_B_SCREEN' else '   GFX.PixSize = 1;' if kind=='D35_B_BACKGROUND' else '   BG.BitShift = 4;')
    prefix=body[start:body.index(split)]
    # Background fallback returns must close the nested attribution first.
    body=body.replace('      return;','      d35_cost_pop(d35_old);return;')
    body=replace(body,signature,signature+'\n   unsigned d35_old=d35_cost_push(D35_COST_SETUP);'+('\n   bool d35_sub=sub;' if kind=='D35_B_SCREEN' else ''))
    if kind=='D35_B_SCREEN':prefix='   sub=d35_sub;\n'+prefix+'\n   __asm__ volatile("" : "+r"(BG0),"+r"(BG1),"+r"(BG2),"+r"(BG3),"+r"(OB) :: "memory");'
    if kind=='D35_B_BACKGROUND':prefix+='\n   __asm__ volatile("" : "+r"(SC0),"+r"(SC1),"+r"(SC2),"+r"(SC3),"+r"(OffsetMask),"+r"(OffsetShift) :: "memory");'
    if kind=='D35_B_OBJECT':prefix+='\n   __asm__ volatile("" :: "m"(Windows),"r"(clipcount) : "memory");'
    body=replace(body,split,bench(kind,prefix,shape,guard)+'   d35_cost_switch(D35_COST_PIXEL);\n'+split)
    body=body[:-2]+'   d35_cost_pop(d35_old);\n}\n'
    s=s[:a]+body+s[z:]
# Selector pointer writes are entry work, not pixels.
start='static void SelectTileRenderer(bool8 normal)\n{'
if start not in s:
    import re
    start=re.search(r'(?:static )?void SelectTileRenderer\([^\n]*\)\n\{',s).group()
a,z,body=function(s,start);prefix=body[len(start):-2]
body=replace(body,start,start+'\n   unsigned d35_old=d35_cost_push(D35_COST_SETUP);')
body=body[:-2]+bench('D35_B_SELECT',prefix,'normal','PPU.BGMode==1')+'   d35_cost_pop(d35_old);\n}\n'
s=s[:a]+body+s[z:]
# Shadow candidate band helpers; never select their output for drawing.
needle='      uint32_t VOffset = LineData [Y].BG[bg].VOffset;'
pos=s.index('static void DrawBackground(uint32_t BGMode')
before=s[:pos];region=s[pos:]
region=replace(region,needle,'''      if(bg==0) {
         struct d35_window_clip q;
         D35_COST_BENCH(D35_B_FETCH,Y,{(void)d35_window_fetch(Y,GFX.pCurrentClip==&IPPU.Clip[1],&q);__asm__ volatile("" :: "m"(q) : "memory");});
         D35_COST_BENCH(D35_B_SAME,Y,{unsigned q=d35_window_same(Y,Y+1);__asm__ volatile("" :: "r"(q) : "memory");});
      }
'''+needle)
# Clip-bound selection stays separate from the tile/pixel compositor. Empty
# clip spans must close the attribution region before continuing the loop.
needle='      for (clip = 0; clip < clipcount; clip++)\n      {'
at,end,draw=function(region,'static void DrawBackground(uint32_t BGMode')
draw=replace(draw,needle,needle+'\n         unsigned d35_clip_old=d35_cost_push(D35_COST_WINDOW);')
draw=replace(draw,'            if (Right <= Left)\n               continue;',
             '            if (Right <= Left) { d35_cost_pop(d35_clip_old);continue; }')
draw=replace(draw,'         s = Left * GFX.PixSize','         d35_cost_pop(d35_clip_old);\n         s = Left * GFX.PixSize')
region=region[:at]+draw+region[end:]
s=before+region;p.write_text(s,encoding='utf-8',newline='\n')
p=CORE/'source/ppu.c';s='#include "a7_cost.h"\n#include "a7_window.h"\n'+p.read_text()
for address in ('0x2128','0x2129'):
    at=s.index('      case '+address+':');end=s.index('         break;',at)
    body=s[at:end]
    body=replace(body,'            FLUSH_REDRAW();','''            D35_COST_BENCH(D35_B_DEFER,(unsigned)IPPU.CurrentLine-IPPU.PreviousLine,{unsigned q=d35_window_defer();__asm__ volatile("" :: "r"(q) : "memory");});
            FLUSH_REDRAW();''')
    s=s[:at]+body+s[end:]
p.write_text(s,encoding='utf-8',newline='\n')
p=CORE/'source/a7_color_cache.h';s='#include "a7_cost.h"\n'+p.read_text()
needle='    struct d35_color_entry *entry=&d35_color_entries[d35_color_bucket(tile)];'
# First occurrence is row function, second is the whole-tile oracle.
at=s.index(needle);s=s[:at]+'    unsigned d35_row_sample=d35_cost_row_gate();\n    unsigned d35_old=d35_row_sample?d35_cost_push(D35_COST_CACHE):D35_COST_PHASES;\n'+s[at:]
needle='        d35_palette_t table=d35_palette(palette,bits);'
missbody=s[s.index(needle):s.index('        entry->bits|=valid;')+len('        entry->bits|=valid;')]
s=replace(s,needle,'        unsigned d35_row_old=d35_row_sample?d35_cost_push(D35_COST_ROW):D35_COST_PHASES;\n        d35_cost_row(1);\n'+needle)
s=replace(s,'        entry->bits|=valid;', '        entry->bits|=valid;\n        if(d35_row_sample)d35_cost_pop(d35_row_old);')
s=replace(s,'    return entry->pixels+row*8;', '''    else d35_cost_row(0);
    if(d35_cost_bench_active(D35_B_ROW_MISS)) {
        struct d35_color_entry saved=*entry;
        D35_COST_BENCH(D35_B_ROW_MISS,(bits<<8)|row,{entry->bits&=~valid;
'''+missbody+'''
        });
        D35_COST_BENCH(D35_B_ROW_HIT,(bits<<8)|row,{unsigned q=entry->bits&valid;__asm__ volatile("" :: "r"(q) : "memory");});
        *entry=saved;
    }
    if(d35_row_sample)d35_cost_pop(d35_old);
    return entry->pixels+row*8;''')
p.write_text(s,encoding='utf-8',newline='\n')
p=CORE/'libretro.c';s=p.read_text();s='#include "source/a7_cost.c"\n'+s
p.write_text(s,encoding='utf-8',newline='\n')
p=CORE/'link.T';p.write_text(p.read_text().replace('d35_profile_end;','d35_profile_end; d35_cost_begin; d35_cost_end;'),newline='\n')
shutil.copytree(ROOT/'build/snes-mvp',OUT/'runner',ignore=shutil.ignore_patterns('out','*.o','__pycache__'))
shutil.copy2(ROOT/'build/a7-cost.h',OUT/'a7-cost.h')
shutil.copy2(ROOT/'build/plus-a7-profile.h',OUT/'plus-a7-profile.h')
shutil.copy2(ROOT/'build/a7-cost-host.h',OUT/'runner/cost-host.h')
p=OUT/'runner/runner.c';s=p.read_text()
s=replace(s,'#include "runner.h"','#include "runner.h"\n#include "cost-host.h"')
s=replace(s,'static void (*p_profile_end)(struct d35_core_profile *);','''static void (*p_profile_end)(struct d35_core_profile *);
static void (*cost_begin)(unsigned);
static void (*cost_end)(struct d35_cost_frame *);''')
s=replace(s,'    if(p_retro_api_version()!=RETRO_API_VERSION)', '''    *(void **)(&cost_begin)=dlsym(s.core,"d35_cost_begin");
    *(void **)(&cost_end)=dlsym(s.core,"d35_cost_end");
    if(!cost_begin || !cost_end) { fail("Measurement core ABI missing");goto done; }
    if(p_retro_api_version()!=RETRO_API_VERSION)''')
s=replace(s,'    save_ready=true;', '''    /* Only diagnostic progress directory is writable. Load a separately
     * identified, output-qualified copy of the private replay snapshot. */
    value=getenv("D35_COST_STATE");
    if(!value || strlen(value)>=sizeof(s.state_path)) { fail("Measurement snapshot missing");goto done; }
    strcpy(s.state_path,value);
    if(!load_state()) { fail("Measurement snapshot identity rejected");goto done; }
    save_ready=false;
    cost_host_start();
    limit=500;''')
s=replace(s,'        s.buttons=board_poll_input(); /* fresh input after admission */', '''        s.buttons=(s.runs<8 || (s.runs>=28 && s.runs<36))?1u<<RETRO_DEVICE_ID_JOYPAD_A:0;
        /* Physical input can abort a diagnostic; it cannot alter replay input. */
        if(board_poll_input()&BOARD_MENU) break;''')
s=replace(s,'        if(p_profile_begin) p_profile_begin(sample);','''        cost_host_before((unsigned)s.runs);
        cost_begin(s.runs>=277 && s.runs<=438?(cost_host_mode((unsigned)s.runs)|((unsigned)s.runs*17u%64u)<<8):0);
        if(s.runs>=277 && s.runs<=438 && (cost_host_mode((unsigned)s.runs)==1 || cost_host_mode((unsigned)s.runs)==3)) {
            sample=1;s.focus_active=1;s.focus_reason=3;
        }
        if(p_profile_begin) p_profile_begin(sample);''')
s=replace(s,'        if(p_profile_end) p_profile_end(&profile);','''        if(p_profile_end) p_profile_end(&profile);
        cost_host_after(cost_end,(unsigned)s.runs-1,elapsed,cpu_end-cpu_start,profile.ppu_cpu_ns);''')
s=replace(s,'    if(s.loaded) p_retro_unload_game();','''    /* Both worker owners have stopped; SD flushing cannot steal live PCM time. */
    pcm_cost_flush(s.save_dir);
    cost_host_finish(s.save_dir,board_is_null(),s.failed,s.runs);
    if(s.loaded) p_retro_unload_game();''')
s=s.replace('build_version=1.19-focus1','build_version=1.19-cost1')
p.write_text(s,encoding='utf-8',newline='\n')
p=OUT/'runner/runner.c';s=p.read_text();s=replace(s,'#include "cost-host.h"','#include "cost-host.h"\n#include "native-pcm.h"');p.write_text(s,newline='\n')
p=OUT/'runner/native-pcm.h';s=p.read_text();s=replace(s,'int pcm_open(unsigned requested);','int pcm_open(unsigned requested);\nvoid pcm_cost_flush(const char *dir);');p.write_text(s,newline='\n')
p=OUT/'runner/native-pcm.c';s=p.read_text()
s=replace(s,'#define PCM_TRACE_COUNT 96u','#define PCM_TRACE_COUNT 32768u')
at,end,body=function(s,'static int pcm_dump_fault(void)\n{')
new='''static char pcm_cost_failure[512],pcm_cost_kernel[16384];
static int pcm_cost_kernel_bytes,pcm_cost_kernel_errno;
static int pcm_dump_fault(void)
{
    snprintf(pcm_cost_failure,sizeof(pcm_cost_failure),"%s",pcm.failure);
    pcm_cost_kernel_bytes=(int)syscall(SYS_syslog,3,pcm_cost_kernel,sizeof(pcm_cost_kernel));
    pcm_cost_kernel_errno=pcm_cost_kernel_bytes<0?errno:0;
    pcm_capture_bytes=pcm_capture_synced=0;
    return 0; /* No SD flush while either real worker remains alive. */
}
void pcm_cost_flush(const char *dir)
{
    char path[1300];uint64_t first=pcm_trace_count>PCM_TRACE_COUNT?pcm_trace_count-PCM_TRACE_COUNT:0;
    FILE *f;snprintf(path,sizeof(path),"%s/pcm-full.txt",dir);f=fopen(path,"w");if(!f)return;
    fprintf(f,"D35 full diagnostic PCM history cost1\\nentries_total=%llu\\nretained_from=%llu\\ncapacity=%u\\nfailure=%s\\nflush=after_audio_and_display_worker_stop\\n",
        (unsigned long long)pcm_trace_count,(unsigned long long)first,PCM_TRACE_COUNT,pcm_cost_failure);
    for(uint64_t i=first;i<pcm_trace_count;i++) {
        const struct pcm_trace_entry *t=&pcm_trace[i%PCM_TRACE_COUNT];
        fprintf(f,"seq=%llu ns=%llu op=%s arg=%u result=%d state=%u queued=%u appl=%u hw=%u epoch=%u xfer=%llu\\n",
            (unsigned long long)i,(unsigned long long)t->ns,t->op,t->argument,t->result,
            t->state,t->queued,t->appl,t->hw,t->epoch,(unsigned long long)t->xfer);
    }
    fprintf(f,"kernel_read_all_bytes=%d errno=%d\\n",pcm_cost_kernel_bytes,pcm_cost_kernel_errno);
    if(pcm_cost_kernel_bytes>0)fwrite(pcm_cost_kernel,1,(size_t)pcm_cost_kernel_bytes,f);
    fflush(f);fsync(fileno(f));fclose(f);
}
'''
s=s[:at]+new+s[end:]
s=replace(s,'    pcm_trace_count=0;','''    pcm_trace_count=0;pcm_cost_failure[0]=0;
    pcm_cost_kernel_bytes=pcm_cost_kernel_errno=0;''')
p.write_text(s,encoding='utf-8',newline='\n')
(OUT/'prepared.json').write_text(json.dumps({'shipping_core_sha256':sha256((ROOT/'build/plus-a7-out/plus-a7.so').read_bytes()).hexdigest(),
    'window_rendering_installed':False,'source':'owned isolated baseline measurement copy'},indent=2)+'\n')
s=(ROOT/'build/plus-a7-equivalence.c').read_text()
s=replace(s,'#include "plus-a7-profile.h"','#include "plus-a7-profile.h"\n#include "a7-cost.h"')
s=replace(s,'    unsigned samples=0;', '''    unsigned samples=0,bench_iterations=0,phase_frames=0;
    void (*cost_begin)(unsigned);void (*cost_end)(struct d35_cost_frame *);
    *(void **)(&cost_begin)=dlsym(candidate.handle,"d35_cost_begin");
    *(void **)(&cost_end)=dlsym(candidate.handle,"d35_cost_end");assert(cost_begin && cost_end);''')
s=replace(s,'            profile_begin(f%64==3); candidate.run(); profile_end(&costs);', '''            struct d35_cost_frame units;
            cost_begin(f%3);profile_begin(f%64==3); candidate.run(); profile_end(&costs);cost_end(&units);
            assert(units.abi==1 && units.bytes==sizeof(units) && units.mode==f%3);
            assert(!units.overflow && !units.clock_errors);
            if(f%3==1) { ++phase_frames;assert(units.cpu_ns[D35_COST_PIXEL]>0); }
            for(unsigned k=0;k<units.samples;k++)bench_iterations+=units.sample[k].iterations;''')
s=replace(s,'    return 0;\n}', '''    assert(bench_iterations>1000 && phase_frames>100);
    printf("PASS: all three diagnostic modes preserve outputs and state; %u benchmark iterations; %u disjoint phase frames; no clock errors/record overflow\\n",bench_iterations,phase_frames);
    return 0;
}''')
s=replace(s,'    assert(magitek_bio_replay?split_frames>iterations-10:split_frames>iterations);','    assert(!split_frames);')
s=s.replace('PASS: earlier PCM publication splits %u frames into multiple byte-equivalent batches',
            'PASS: measurement leaves native callback batching unchanged; extra split frames=%u')
(OUT/'equivalence.c').write_text(s,encoding='utf-8',newline='\n')
s=(ROOT/'build/snes-mvp/native-runner-check.c').read_text()
s=s[:s.index('static int native_menu(')]
s=s.replace('menu_visits,menu_action,next_menu,deficit_mode','menu_visits,next_menu,deficit_mode')
s+='\n'+(ROOT/'build/a7-cost-native-check.c').read_text()
(OUT/'runner/cost-native-check.c').write_text(s,encoding='utf-8',newline='\n')
print('Prepared isolated baseline core with disjoint regions and bounded actual-path benchmarks')
