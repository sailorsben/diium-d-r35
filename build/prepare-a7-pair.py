"""Fresh isolated, low-observer whole-path A/B suite; no production overwrite."""
from pathlib import Path
from hashlib import sha256
import json, re, shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/a7-pair-private-v1'
assert not OUT.exists(), 'Preserve prior builds/results'
OUT.mkdir()
def change(s,a,b):
    assert s.count(a)==1,a[:100]
    return s.replace(a,b)
CORE=OUT/'core'
shutil.copytree(ROOT/'build/snes9x2005',CORE,ignore=shutil.ignore_patterns('.git','*.o','*.so'))
# Reuse the owned, previously oracle-qualified transformation verbatim.
script=(ROOT/'build/prepare-window-batch.py').read_text()
exec(script[script.index("shutil.copy2(ROOT / 'build/plus-a7-window.h'"):script.index("print('Prepared")],{'ROOT':ROOT,'CORE':CORE,'shutil':shutil})
script=(ROOT/'build/prepare-bio-fast-window.py').read_text()
exec(script[script.index("p=OUT/'core/source/a7_window.h'"):script.index('# Independently compare')],{'OUT':OUT})
p=CORE/'source/tile.c';s=p.read_text()
a=s.index('static INLINE __attribute__((always_inline)) bool d35_render_tile(');b=s.index('\n}\n',a)+3
helper=(ROOT/'build/bio-palette-direct.h').read_text()
helper='\n'.join(line for line in helper.splitlines() if 'd35_census' not in line and 'd35_hyp' not in line)+'\n'
s=s[:a]+helper+s[b:];p.write_text(s,newline='\n')
s=(ROOT/'build/bio-palette-cache.h').read_text()
s=re.sub(r'\+\+d35_hyp\[7\];','',s)
(CORE/'source/a7_color_cache.h').write_text(s,newline='\n')
assert not any('d35_census' in p.read_text(errors='ignore') or 'd35_hyp' in p.read_text(errors='ignore') for p in CORE.glob('source/*.[ch]'))
shutil.copytree(ROOT/'build/snes-mvp',OUT/'runner',ignore=shutil.ignore_patterns('out','*.o','__pycache__'))
shutil.copy2(ROOT/'build/plus-a7-profile.h',OUT/'plus-a7-profile.h')
# Frequency controls from cost1, without its per-region or per-row instrumentation.
s=(ROOT/'build/a7-cost-host.h').read_text();s=s[:s.index('static unsigned cost_host_mode')]+ '\n#endif\n'
s=s.replace('#include "../a7-cost.h"','')
a=s.index('#define D35_HOST_FRAMES');b=s.index('static uint64_t cost_host_ns')
s=s[:a]+'''static struct {
    unsigned mode,started,pinned;int freq_fd;long original_min,pinned_max;
    char policy[256],min_path[300],freq_path[300],pin_status[128];
    char governor[80],cpu_online[80],kernel[256];
} cost_host;
'''+s[b:]
(OUT/'runner/frequency-host.h').write_text(s,newline='\n')
shutil.copy2(ROOT/'build/a7-pair-host.h',OUT/'runner/pair-host.h')
p=OUT/'runner/runner.c';s=p.read_text()
s=change(s,'#include "runner.h"','#include "runner.h"\n#include "pair-host.h"\n#include "native-pcm.h"')
s=change(s,'    if(!p_profile_begin || !p_profile_end) p_profile_begin=NULL,p_profile_end=NULL;',
    '    /* No nested core/callback clocks in this complete-path comparison. */\n    p_profile_begin=NULL;p_profile_end=NULL;')
s=change(s,'    save_ready=true;', '''    value=getenv("D35_PAIR_STATE");
    if(!value || strlen(value)>=sizeof(s.state_path)) { fail("Pair snapshot absent");goto done; }
    strcpy(s.state_path,value);
    if(!load_state()) { fail("Pair snapshot identity rejected");goto done; }
    save_ready=false;pair_begin();
    value=getenv("D35_PAIR_LIMIT");limit=value?(uint64_t)cost_parse(value):0;
    if(!limit || limit>500) { fail("Pair bound invalid");goto done; }''')
s=change(s,'        s.buttons=board_poll_input(); /* fresh input after admission */', '''        if(board_poll_input()&BOARD_MENU) { stop_requested=1;break; }
        unsigned replay_frame=pair_start+(unsigned)s.runs;
        s.buttons=(replay_frame<8 || (replay_frame>=28 && replay_frame<36))?1u<<RETRO_DEVICE_ID_JOYPAD_A:0;''')
s=change(s,'            if(!pause_menu()) break;','            setenv("D35_PAIR_ABORT","1",1);break;')
s=change(s,'static bool pause_menu(void)','static __attribute__((unused)) bool pause_menu(void)')
s=s.replace('if(board_poll_input()&BOARD_MENU) { stop_requested=1;break; }','if(board_poll_input()&BOARD_MENU) { setenv("D35_PAIR_ABORT","1",1);stop_requested=1;break; }')
s=change(s,'        cpu_start=thread_cpu_ns(); began=board_now_ns();','        pair_before();\n        cpu_start=thread_cpu_ns(); began=board_now_ns();')
s=change(s,'        s.active_ns+=board_now_ns()-step_start;', '''        pair_after((unsigned)s.runs-1,cpu_end>=cpu_start?cpu_end-cpu_start:0,elapsed,admission,step_start,s.generated);
        s.active_ns+=board_now_ns()-step_start;''')
s=change(s,'    if(s.loaded) p_retro_unload_game();', '''    /* Both real worker owners have joined before any diagnostic SD flush. */
    pcm_cost_flush(s.save_dir);pair_finish(s.save_dir,board_is_null(),s.failed);
    if(s.loaded) p_retro_unload_game();''')
s=s.replace('build_version=1.19\\n','build_version=1.19-pair1\\n')
p.write_text(s,newline='\n')
# Reuse the already tested deferred native trace implementation unchanged.
for name in ('native-pcm.c','native-pcm.h'):
    shutil.copy2(ROOT/'build/a7-cost-private-v9/runner'/name,OUT/'runner'/name)
s=(ROOT/'build/plus-a7-equivalence.c').read_text()
s=change(s,'static bool magitek_bio_replay;','static bool magitek_bio_replay,pair_late;')
s=change(s,'    if(magitek_bio_replay) {','    if(pair_late)return 0;\n    if(magitek_bio_replay) {')
s=change(s,'    if(argc==7) { assert(!strcmp(argv[6],"magitek-bio"));magitek_bio_replay=true; }',
    '    if(argc==7) { pair_late=!strcmp(argv[6],"pair-late");assert(pair_late || !strcmp(argv[6],"magitek-bio"));magitek_bio_replay=true; }')
s=change(s,'    assert(magitek_bio_replay?split_frames>iterations-10:split_frames>iterations);','    assert(!split_frames);')
s=s.replace('PASS: earlier PCM publication splits','PASS: unchanged native callback batching; extra split')
(OUT/'equivalence.c').write_text(s,newline='\n')
shutil.copy2(ROOT/'build/replay-snes-scene.c',OUT/'replay.c')
# Replay includes the same qualified harness; no benchmark durations are evidence.
shutil.copy2(OUT/'equivalence.c',OUT/'plus-a7-equivalence.c')
s=(ROOT/'build/a7-cost-private-v9/launch.sh').read_text().replace('snes-cost1','snes-pair1').replace('1.19-cost1','1.19-pair1')
s=change(s,'"$BASE/unit-suite" "$BASE" "$BASE/measure-core.so" "$D35_COST_ROM" "$BASE/replay.state"',
              '"$BASE/pair-suite" "$BASE" "$D35_COST_ROM"')
(OUT/'launch.sh').write_text(s,newline='\n')
(OUT/'dispatch.sh').write_text('#!/bin/sh\nexec /usr/retro/snes-pair1/launch.sh\n',newline='\n')
(OUT/'prepared.json').write_text(json.dumps({'baseline_sha256':sha256((ROOT/'build/plus-a7-out/plus-a7.so').read_bytes()).hexdigest(),
    'mechanism':'window batching + palette tables + prefix validity','counter_instrumentation':False,'production_replacement':False},indent=2)+'\n')
print('Prepared separate combined core and frame-only live-worker comparison')
