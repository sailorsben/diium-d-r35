"""Build the isolated Star Fox LCD zoom over the qualified 150 ms runner."""
from importlib import import_module
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory


base = import_module('install-starfox-150-test')
ROOT = base.ROOT
OUT = ROOT / 'build/starfox-fullscreen-private-v2'
CORE = '70d885151b7d3cac05ae69fc9653974c420b49d5cb20f95b09af547f319a8936'
replace = base.probe.replace_once


def prepare_board(runner):
    path = runner / 'board.c'
    s = replace(path.read_text(), '#include "snes-rgb565-reuse.h"',
                '#include "snes-rgb565-reuse.h"\n#include "starfox-viewport.h"')
    s = replace(s, 'unsigned width, height; } slots[SOURCE_SLOTS];',
                'unsigned width, height; bool expanded; } slots[SOURCE_SLOTS];')
    s = replace(s, 'int board_video_submit(const void *rgb565,unsigned width,unsigned height,size_t pitch)',
                'static int submit_frame(const void *rgb565,unsigned width,unsigned height,size_t pitch,bool expanded)')
    s = replace(s, '    int previous=b.previous;\n    uint64_t comparison=0;', '''    /* The scaler reads the front of the owned slot. Retain the exact raw
     * crop after it so repeat pictures can skip expansion and scaler work. */
    unsigned out_width=expanded?D35_STARFOX_WIDTH:width;
    unsigned out_height=expanded?D35_STARFOX_HEIGHT:height;
    size_t raw_offset=expanded?D35_STARFOX_FRAME_BYTES:0;
    int previous=b.previous;
    uint64_t comparison=0;''')
    s = replace(s, '    if(previous>=0 && b.slots[previous].width==width && b.slots[previous].height==height) {',
                '''    if(previous>=0 && b.slots[previous].width==out_width &&
       b.slots[previous].height==out_height && b.slots[previous].expanded==expanded) {''')
    s = replace(s, 'b.pixels+(unsigned)previous*SLOT_BYTES+32,width,height',
                'b.pixels+(unsigned)previous*SLOT_BYTES+32+raw_offset,width,height')
    s = replace(s, '    unsigned direct=rgb565==target&&pitch==(size_t)width*2u;\n'
                '    if(!direct)for(y=0;y<height;++y)\n'
                '        memcpy(target+(size_t)y*width*2u,(const uint8_t *)rgb565+(size_t)y*pitch,(size_t)width*2u);',
                '''    uint8_t *raw=target+raw_offset;
    unsigned direct=!expanded&&rgb565==target&&pitch==(size_t)width*2u;
    if(!direct)for(y=0;y<height;++y)
        memcpy(raw+(size_t)y*width*2u,(const uint8_t *)rgb565+(size_t)y*pitch,(size_t)width*2u);
    if(expanded) d35_starfox_expand((uint16_t *)target,(const uint16_t *)raw);''')
    s = replace(s, '    b.slots[slot].width=width; b.slots[slot].height=height;',
                '    b.slots[slot].width=out_width; b.slots[slot].height=out_height;\n'
                '    b.slots[slot].expanded=expanded;')
    s = replace(s, 'uint32_t board_poll_input(void)', '''int board_video_submit(const void *rgb565,unsigned width,unsigned height,size_t pitch)
{
    return submit_frame(rgb565,width,height,pitch,false);
}

int board_video_submit_starfox(const void *view,size_t pitch)
{
    _Static_assert(D35_STARFOX_FRAME_BYTES + D35_STARFOX_VIEW_WIDTH * D35_STARFOX_VIEW_HEIGHT * 2u
                   <= SLOT_BYTES - 64u, "Star Fox crop and output must fit in one slot");
    return submit_frame(view,D35_STARFOX_VIEW_WIDTH,D35_STARFOX_VIEW_HEIGHT,pitch,true);
}

uint32_t board_poll_input(void)''')
    path.write_text(s, newline='\n')
    path = runner / 'board.h'
    s = replace(path.read_text(), 'int board_video_reserve(void);',
                'int board_video_submit_starfox(const void *view, size_t pitch);\nint board_video_reserve(void);')
    path.write_text(s, newline='\n')


def prepare():
    payload = OUT / 'payload'
    base.probe.prepare(ROOT / 'build/stock-shell-display-private-v2', payload)
    runner = payload / 'runner'
    shutil.copyfile(ROOT / 'build/starfox-viewport.h', runner / 'starfox-viewport.h')
    prepare_board(runner)
    path = runner / 'runner.c'
    s = replace(path.read_text(), '#include "board.h"', '#include "board.h"\n#include "starfox-viewport.h"')
    s = replace(s, '    unsigned presentation_policy, skip_presentation;',
                '    unsigned presentation_policy, skip_presentation;\n'
                '    bool starfox_fullscreen, starfox_verify_border;\n    unsigned starfox_cropped;')
    s = replace(s, '    int submitted=board_video_submit(data,w,h,pitch);', '''    const void *view=data;
    if (s.starfox_fullscreen) {
        view=d35_starfox_viewport(data,pitch,&w,&h);
        if (s.starfox_verify_border && (view==data || !d35_starfox_border_is_black(data,pitch))) {
            board_video_cancel();
            fail("Star Fox viewport would remove visible pixels or received unexpected geometry");
            return;
        }
        if (view!=data) ++s.starfox_cropped;
    }
    int submitted=view!=data ? board_video_submit_starfox(view,pitch) : board_video_submit(data,w,h,pitch);''')
    s = replace(s, '    value=getenv("D35_IDENTICAL_VIDEO_REUSE");', '''    value=getenv("D35_STARFOX_FULLSCREEN");
    s.starfox_fullscreen=value && !strcmp(value,"1");
    s.starfox_verify_border=getenv("D35_FIVE_ORACLE")!=NULL;
    if (s.starfox_fullscreen)
        fprintf(stderr,"Star Fox viewport source=%ux%u left=%u top=%u size=%ux%u scaler=256x224\\n",
                D35_STARFOX_WIDTH,D35_STARFOX_HEIGHT,D35_STARFOX_LEFT,D35_STARFOX_TOP,
                D35_STARFOX_VIEW_WIDTH,D35_STARFOX_VIEW_HEIGHT);
    value=getenv("D35_IDENTICAL_VIDEO_REUSE");''')
    s = replace(s, '''            void *target=s.skip_presentation?(uint8_t *)s.render_scratch+32:board_video_target(&bytes);
            if(s.skip_presentation) bytes=512u*240u+32u;''', '''            /* The cropped source must never overlap the chunk destination. */
            bool use_scratch=s.skip_presentation || s.starfox_fullscreen;
            void *target=use_scratch?(uint8_t *)s.render_scratch+32:board_video_target(&bytes);
            if(use_scratch) bytes=512u*240u+32u;''')
    s = replace(s, '    if (read_memo && s.save_dir[0]) {', '''    if (s.starfox_fullscreen)
        fprintf(stderr,"Star Fox cropped callbacks=%u rendered=%llu\\n",s.starfox_cropped,
                (unsigned long long)s.rendered);
    if (read_memo && s.save_dir[0]) {''')
    path.write_text(s, newline='\n')

    # The pinned measurement main contains only fixture 003. Keep this scope
    # explicit even if its fixture list changes in a subsequent base runner.
    main = payload / 'main.c'
    point = '  const struct ffvi_run *r=&ffvi_runs[seq];'
    main.write_text(replace(main.read_text(), point, point + '''
  if(r->fixture!=3 && getenv("D35_STARFOX_FULLSCREEN")) {failed++;break;}'''), newline='\n')

    launch = base.wrapper().replace('starfox-150', 'starfox-fullscreen2')
    launch = replace(launch, 'D35_IDENTICAL_VIDEO_REUSE=1',
                     'D35_STARFOX_FULLSCREEN=1 D35_IDENTICAL_VIDEO_REUSE=1')
    start = launch.index('run_window pcm-cache')
    end = launch.index("printf 'complete\\n'", start)
    launch = launch[:start] + 'run_window pcm-fullscreen 0 1\nhandle_result "$?" || exit 1\n' + launch[end:]
    (payload / 'launch.sh').write_text(launch, newline='\n')
    core = base.OUT / 'plus-a7.so'
    if base.previous.digest(core) != CORE:
        raise ValueError('Expected the handheld-qualified 16-entry core')
    shutil.copyfile(core, payload / 'plus-a7.so')
    subprocess.run(['sh', 'build/check-snes-native-reuse.sh', payload, 'build/check-starfox-viewport.c'],
                   cwd=ROOT, check=True)
    (payload / 'candidate').rename(payload / 'display-runner')
    return payload


def check_wrapper(launch):
    busybox = ROOT / 'build/uart-fix-private/firmware-busybox'
    shell = ['qemu-arm', '-0', 'busybox', '-L', ROOT / 'build/sysroot', busybox, 'sh']
    subprocess.run([*shell, '-n', launch], check=True)
    with TemporaryDirectory() as temp:
        root = Path(temp)
        lab, mvp = root / 'lab', root / 'mvp'
        lab.mkdir()
        mvp.mkdir()
        runner = lab / 'display-runner'
        runner.write_text('''#!/bin/sh
[ "$D35_STARFOX_FULLSCREEN:$D35_PCM_DIAGNOSTIC_RESERVE:$D35_AUDIT_MODE2_MEMO" = 1:150:1 ] || exit 1
[ "$D35_MEASURE_DISPLAY:$D35_IDENTICAL_VIDEO_REUSE" = 0:1 ] || exit 1
[ ! -e "$D35_DISPLAY_LAB/armed" ] && [ ! -e "$D35_DISPLAY_MVP/armed" ] || exit 1
[ -f "$D35_DISPLAY_STOP" ] || exit 1
[ "${2##*/}" = pcm-fullscreen ] || exit 1
echo ran >> "$D35_DISPLAY_LAB/calls"
''')
        runner.chmod(0o755)
        env = dict(os.environ, D35_DISPLAY_LAB=str(lab), D35_DISPLAY_MVP=str(mvp),
                   D35_DISPLAY_PROC=str(root / 'proc'), D35_DISPLAY_STOP=str(root / 'stop'))
        command = [*shell, launch]
        subprocess.run(command, env=env, check=True, timeout=20)
        assert not (lab / 'calls').exists()
        for path in (lab, mvp):
            (path / 'armed').touch()
        for _ in range(2):
            subprocess.run(command, env=env, check=True, timeout=20)
        assert (lab / 'calls').read_text() == 'ran\n'


def verify_replay(payload):
    fixtures = ROOT / 'build/fivegame-kernel-private-v2'
    pinned = base.previous.read_json(base.SUP.FROZEN_RECEIPT)['payload_hashes']
    for name in base.previous.FIXTURE_FILES:
        assert base.previous.digest(fixtures / name) == pinned[name], name
    sysroot = ROOT / 'build/sysroot'
    result = OUT / 'replay-fullscreen'
    result.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith('D35_')}
    env.update(D35_ABILITY_MOCK='1', D35_MVP_NO_PACING='1', D35_FULL_HOST_FIXTURE='1',
               D35_FIVE_ORACLE='1', D35_IDENTICAL_VIDEO_REUSE='1', D35_MEASURE_DISPLAY='1',
               D35_DISPLAY_FIXTURES=str(fixtures), D35_AUDIT_MODE2_MEMO='1',
               D35_PCM_DIAGNOSTIC_RESERVE='150', D35_STARFOX_FULLSCREEN='1')
    log = result / 'console.log'
    with log.open('w') as out:
        subprocess.run(['qemu-arm', '-cpu', 'cortex-a7', '-L', sysroot, '-E',
                        f'LD_LIBRARY_PATH={sysroot}/lib', payload / 'display-runner',
                        '--supervise', result, payload, 'unused'],
                       env=env, stdout=out, stderr=subprocess.STDOUT, check=True, timeout=420)
    trace = result / 'run-000'
    assert '#oracle_checks=1200' in (trace / 'input.csv').read_text()
    assert 'cold_boot_calls=8656' in (trace / 'warmup.txt').read_text()
    assert 'final_PCM_software_accounting_exact=1' in (trace / 'headroom.txt').read_text()
    assert 'reused_rows=165006' in (trace / 'mode2-cache.txt').read_text()
    assert 'reaped=1\nforced=0' in (result / 'supervisor.txt').read_text()
    assert 'Star Fox cropped callbacks=1200 rendered=1200' in log.read_text()
    base.previous.write_json(payload / 'qualification.json', {
        'hardware_runs': 0, 'frameskip': 0, 'replay_oracle_calls': 1200,
        'viewport': [16, 16, 226, 190], 'scaler_input': [256, 224], 'reserve_ms': 150, 'cache_entries': 16,
        'fixtures': {name: pinned[name] for name in base.previous.FIXTURE_FILES},
        'payloads': {name: base.previous.digest(payload / name) for name in base.FILES},
    })
    print('PASS supervised Star Fox replay with 1200 cropped callbacks and exact core output')


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    built = prepare()
    check_wrapper(built / 'launch.sh')
    verify_replay(built)
