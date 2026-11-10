"""Same-process, alternating-frame timings for the isolated experiments."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent
FIX=ROOT/'build/fivegame-kernel-private-v2'


def run_pairs(out, cores, tasks):
    out.mkdir()
    src=ROOT/'build/snes-throughput-pair.c'
    digest=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    sources={p.name:digest(p) for p in (src,src.with_name('snes-throughput-replay.c'),Path(__file__))}
    flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'.split()
    exe=out/'pair'
    subprocess.run(['arm-linux-gnueabihf-gcc','-std=gnu11','-O2',*flags,'-Wall','-Wextra','-Werror','-no-pie','-nostdlib',
                    '-Ibuild/snes9x2005/libretro-common/include','/usr/arm-linux-gnueabihf/lib/crt1.o',src,'-Lbuild/sysroot/lib',
                    '-Wl,--no-as-needed','-l:libdl-2.30.so','-l:libz.so.1','-l:libc-2.30.so','-l:libgcc_s.so.1','-o',exe],cwd=ROOT,check=True)
    q=json.loads((ROOT/'evidence/2026-10-17/fivegame-replay/qualification.json').read_text())['payload_hashes']
    assert digest(cores['physical'])==q['plus-a7.so']
    for name,h in q.items():
        if name.startswith('cases/'):assert digest(FIX/name)==h
    lanes=list(dict((Path(f'/sys/devices/system/cpu/cpu{i}/topology/thread_siblings_list').read_text(),i)
                    for i in sorted(os.sched_getaffinity(0))).values())
    def run(task, lane):
        g,c,mode=task; a='physical' if c=='baseline' else 'baseline'
        if mode.endswith('-toggle'):
            a=c+'-disabled'
            assert digest(cores[a]) == digest(cores[c])
        argv=['taskset','-c',str(lane),'qemu-arm','-cpu','cortex-a7','-L','build/sysroot','-E','LD_LIBRARY_PATH=build/sysroot/lib',
              exe,cores[a],cores[c],FIX/'cases'/f'{g:03}',str(8656 if g==3 else 0),mode]
        name=f'{g}-{c}-{mode}.log'
        with (out/name).open('w') as f:subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=420)
        print(name,flush=True)
        return dict(game=g,control=a,candidate=c,mode=mode,host_cpu=lane,log=name,sha256=digest(out/name))
    def work(index): return [run(t,lanes[index]) for t in tasks[index::len(lanes)]]
    with ThreadPoolExecutor(max_workers=len(lanes)) as pool:
        results=[r for group in pool.map(work,range(len(lanes))) for r in group]
    (out/'manifest.json').write_text(json.dumps(dict(results=results,physical=False,core_sha256={n:digest(p) for n,p in cores.items()},
        sources=sources,pair_sha256=digest(exe)),indent=2)+'\n')


def main(out, first, followup, offset=None):
    cores={'physical':FIX/'plus-a7.so'}
    cores.update({name: first/name/'snes9x2005_plus_libretro.so' for name in ('baseline','counter','dispatch')})
    cores.update({name: followup/name/'snes9x2005_plus_libretro.so' for name in ('hot','dma-same','dma-delta')})
    tasks=[(3,c,'full') for c in ('counter','dispatch','hot','dma-same','dma-delta')]
    tasks.extend((3,'baseline',mode) for mode in ('cold-off','off','oracle-reuse'))
    tasks.extend((g,'baseline','oracle-reuse') for g in (0,1))
    tasks.extend((g,c,'full') for g in (0,1,4) for c in ('dma-same','dma-delta'))
    if offset:
        mode,=[n for n in ('offset-row','offset-plain') if (offset/n/'snes9x2005_plus_libretro.so').is_file()]
        cores[mode]=offset/mode/'snes9x2005_plus_libretro.so'
        tasks=[(3,mode,'both-cold-off')]
    run_pairs(out, cores, tasks)


def scheduler(out, first, followup):
    candidates = {name: first/name/'snes9x2005_plus_libretro.so' for name in ('apu-clock','apu-noop')}
    candidates['apu-carry'] = followup/'apu-carry/snes9x2005_plus_libretro.so'
    # Batch sizes 2/4/8 diverge in the output oracle. Price each only on a
    # passing example to expose what the correctness trade would have bought.
    rejected = {name: first/name/'snes9x2005_plus_libretro.so' for name in ('apu-slice2','apu-slice4','apu-slice8')}
    tasks = [(game, name, 'both-cold-off' if game==3 else 'full') for game in [3,0,1,2,4] for name in candidates]
    tasks.extend((1, name, 'full') for name in rejected)
    cores = {'physical':FIX/'plus-a7.so', 'baseline':first/'baseline/snes9x2005_plus_libretro.so', **candidates, **rejected}
    run_pairs(out, cores, tasks)


def scheduler_followup(out, first, unity, combined):
    cores = {
        'physical': FIX/'plus-a7.so',
        'baseline': first/'baseline/snes9x2005_plus_libretro.so',
        'apu-noop': first/'apu-noop/snes9x2005_plus_libretro.so',
        'apu-unity': unity/'apu-unity/snes9x2005_plus_libretro.so',
        'apu-service': combined/'apu-service/snes9x2005_plus_libretro.so',
    }
    tasks = [(game, name, 'both-cold-off' if game==3 else 'full') for game in [3,0,1,2,4]
             for name in ('baseline','apu-unity','apu-service')]
    tasks.append((3,'apu-noop','both-cold-off'))
    run_pairs(out, cores, tasks)


def scheduler_candidate(out, first, build, name):
    cores = {
        'physical': FIX/'plus-a7.so',
        'baseline': first/'baseline/snes9x2005_plus_libretro.so',
        name: build/name/'snes9x2005_plus_libretro.so',
    }
    run_pairs(out, cores, [(g, name, 'both-cold-off' if g==3 else 'full') for g in [3,0,1,2,4]])


def raster(out, first, build, names):
    core_file = 'snes9x2005_plus_libretro.so'
    cores = {'physical': FIX/'plus-a7.so', 'baseline': first/'baseline'/core_file}
    cores.update({name: build/name/core_file for name in names if name != 'baseline'})
    for name in names:
        if name.endswith('-toggle'):
            add_raster_control(cores, name)
    tasks = [(game, name, ('both-cold-off' if game == 3 else 'full') +
              ('-toggle' if name.endswith('-toggle') else ''))
             for game in (3, 0, 1, 2, 4) for name in names]
    run_pairs(out, cores, tasks)


def add_raster_control(cores, name):
    disabled = cores[name].with_name('disabled.so')
    shutil.copyfile(cores[name], disabled)
    cores[name+'-disabled'] = disabled


def raster_ablation(out, build, names):
    core_file = 'snes9x2005_plus_libretro.so'
    cores = {'physical': FIX/'plus-a7.so'}
    for name in names:
        cores[name] = build/(name+'-toggle')/core_file
        add_raster_control(cores, name)
    tasks = [(game, name, 'both-cold-off-toggle' if game == 3 else 'full-toggle')
             for game in (3, 0, 1, 2, 4) for name in names]
    run_pairs(out, cores, tasks)


def superfx(out, build, names):
    file = 'snes9x2005_plus_libretro.so'
    cores = {'physical': FIX/'plus-a7.so', 'baseline': build/'raster-offset-full'/file}
    cores.update({n: build/n/file for n in names})
    for name in names:
        if name.endswith('-toggle'):
            add_raster_control(cores, name)
    tasks = [(3, n, 'both-cold-off-fx-toggle' if n.endswith('-toggle') else 'both-cold-off') for n in names]
    run_pairs(out, cores, tasks)


if __name__=='__main__':
    if sys.argv[1]=='--raster':
        raster(*(Path(x).resolve() for x in sys.argv[2:5]), sys.argv[5:])
    elif sys.argv[1]=='--raster-ablation':
        raster_ablation(*(Path(x).resolve() for x in sys.argv[2:4]), sys.argv[4:])
    elif sys.argv[1]=='--superfx':
        superfx(*(Path(x).resolve() for x in sys.argv[2:4]), sys.argv[4:])
    elif sys.argv[1]=='--scheduler':
        scheduler(*(Path(x).resolve() for x in sys.argv[2:]))
    elif sys.argv[1]=='--scheduler-followup':
        scheduler_followup(*(Path(x).resolve() for x in sys.argv[2:]))
    elif sys.argv[1]=='--scheduler-combined':
        scheduler_candidate(*(Path(x).resolve() for x in sys.argv[2:]), 'apu-service')
    elif sys.argv[1]=='--scheduler-port':
        scheduler_candidate(*(Path(x).resolve() for x in sys.argv[2:]), 'apu-port-noop')
    else:
        main(*(Path(x).resolve() for x in sys.argv[1:]))
