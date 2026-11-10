"""Build and exercise an isolated controller that omits hidden replay pixels."""
import csv
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'build/fivegame-kernel-private-v2'


def digest(p): return sha256(p.read_bytes()).hexdigest()


def edit(path, old, new):
    s=path.read_text()
    assert s.count(old)==1, (path,old)
    path.write_text(s.replace(old,new),newline='\n')


def kv(path): return dict(l.split('=',1) for l in path.read_text().splitlines() if '=' in l)


def main(out, report):
    out.mkdir()
    qualified=json.loads((ROOT/'evidence/2026-10-17/fivegame-replay/qualification.json').read_text())
    pinned=qualified['payload_hashes']
    for name in ['plus-a7.so','cases/003/game.sfc','cases/003/input.txt','cases/003/warmup.txt','cases/003/expected.bin']:
        assert digest(BASE/name)==pinned[name],name
    # No ROM/state copy; the isolated controller reads these frozen inputs.
    (out/'plus-a7.so').symlink_to(BASE/'plus-a7.so')
    (out/'cases').symlink_to(BASE/'cases',target_is_directory=True)
    rt=out/'runner'
    shutil.copytree(BASE/'runner',rt,ignore=shutil.ignore_patterns('*.o'))
    for n in ['main.c','identity.h','fivegame-replay-progress.h','plus-a7-profile.h','presentation-burst.h']:
        shutil.copyfile(BASE/n,out/n)
    edit(out/'identity.h',re.search(r'ffvi_runs\[\]=\{.*\};',(out/'identity.h').read_text())[0],
         'ffvi_runs[]={{3,0,0,0}};')
    edit(rt/'runner.c','static bool environment(unsigned cmd,void *data)',
         'static unsigned cold_replay_raster_off;\nstatic bool environment(unsigned cmd,void *data)')
    edit(rt/'runner.c','        if(data) *(int *)data=3;','        if(data) *(int *)data=cold_replay_raster_off?2:3;')
    edit(rt/'fivegame-warmup.h','    while(fgets(line,sizeof(line),f)){',
         '    cold_replay_raster_off=1;\n    while(fgets(line,sizeof(line),f)){')
    edit(rt/'fivegame-warmup.h','done:\n    if(f)fclose(f);','done:\n    cold_replay_raster_off=0;\n    if(f)fclose(f);')
    edit(rt/'fivegame-warmup.h','audio_discarded_before_native_open=1\\n',
         'audio_discarded_before_native_open=1\\ncold_replay_raster_disabled=1\\n')
    flags='-DD35_PLUS_A7 -DD35_NATIVE_PCM -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32 -std=gnu99 -O3 -flto=4 -Wall -Wextra -Werror -Wno-misleading-indentation -no-pie -nostdlib -Ibuild -Ibuild/snes9x2005/libretro-common/include /usr/arm-linux-gnueabihf/lib/crt1.o'.split()
    libs=['-Lbuild/sysroot/lib','-Wl,--no-as-needed']+['-l:'+n for n in ('libdl-2.30.so','libz.so.1','libpthread-2.30.so','librt-2.30.so','libm-2.30.so','libc-2.30.so','libgcc_s.so.1','ld-2.30.so')]
    sources=[out/'main.c',*[rt/n for n in ('board.c','runner.c','audio-owner.c','native-pcm.c','startup.c','platform.c','timing.c','ui.c')],ROOT/'build/glibc230-stat-compat.c']
    exe=out/'candidate'
    with (out/'build.log').open('w') as log:
        subprocess.run(['arm-linux-gnueabihf-gcc',*flags,*map(str,sources),*libs,'-o',str(exe)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    abi=subprocess.check_output(['arm-linux-gnueabihf-readelf','-V',exe],text=True)
    assert all(tuple(map(int,m))<=(2,30) for m in re.findall(r'GLIBC_(\d+)\.(\d+)',abi))
    mock=out/'mock'; mock.mkdir()
    env={**os.environ,'D35_ABILITY_MOCK':'1','D35_MVP_NO_PACING':'1','D35_FULL_HOST_FIXTURE':'1','D35_FIVE_ORACLE':'1'}
    with (out/'oracle.log').open('w') as log:
        subprocess.run(['qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib',exe,
                        '--supervise',mock,out,'unused'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=420)
    d=mock/'run-000'
    warm=kv(d/'warmup.txt'); last=kv(d/'last-session.txt'); oracle=kv(d/'input.csv'); head=kv(d/'headroom.txt')
    rows=list(csv.DictReader(l for l in (d/'frames.csv').read_text().splitlines() if not l.startswith('#')))
    assert warm['cold_boot_calls']=='8656' and warm['status']=='completed' and warm['cold_replay_raster_disabled']=='1'
    assert warm['measured_metrics_reset_before_audio']=='1' and len(rows)==1200 and head['physical']=='0'
    assert last['runs']==last['rendered_frames']==last['video_submitted']=='1200' and not last['error']
    assert oracle['#oracle_checks']=='1200' and oracle['#oracle_enabled']=='1'
    assert kv(d/'result.txt')['runner_rc']=='0' and kv(mock/'supervisor.txt')['reaped']=='1'
    assert kv(mock/'supervisor.txt')['forced']=='0'
    proof=dict(candidate_sha256=digest(exe),core_sha256=pinned['plus-a7.so'],script_sha256=digest(Path(__file__)),
               cold_calls=8656,measured_pixel_pcm_count_matches=1200,all_measured_frames_submitted=True,
               media_write=False,physical=False,production_gate=False,
               verified_final_audio_accounting=last['audio_remaining_frames']==last['audio_cleared_frames']=='0',
               source_hashes={p.name:digest(p) for p in [rt/'runner.c',rt/'fivegame-warmup.h',out/'identity.h']})
    assert proof['verified_final_audio_accounting']
    report.write_text(json.dumps(proof,indent=2)+'\n')
    print('PASS actual controller: 8,656 hidden replay calls, 1,200 original pixel/PCM/count matches, every measured frame submitted')


if __name__=='__main__':
    main(*(Path(p).resolve() for p in sys.argv[1:]))
