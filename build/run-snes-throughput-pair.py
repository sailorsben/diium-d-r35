"""Same-process, alternating-frame timings for the isolated experiments."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent
FIX=ROOT/'build/fivegame-kernel-private-v2'


def main(out, first, followup, offset=None):
    out.mkdir()
    src=ROOT/'build/snes-throughput-pair.c'
    flags='-DD35_PLUS_A7 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -marm -fno-stack-protector -D_TIME_BITS=32 -D_FILE_OFFSET_BITS=32'.split()
    exe=out/'pair'
    subprocess.run(['arm-linux-gnueabihf-gcc','-std=gnu11','-O2',*flags,'-Wall','-Wextra','-Werror','-no-pie','-nostdlib',
                    '-Ibuild/snes9x2005/libretro-common/include','/usr/arm-linux-gnueabihf/lib/crt1.o',src,'-Lbuild/sysroot/lib',
                    '-Wl,--no-as-needed','-l:libdl-2.30.so','-l:libz.so.1','-l:libc-2.30.so','-l:libgcc_s.so.1','-o',exe],cwd=ROOT,check=True)
    cores={'physical':FIX/'plus-a7.so'}
    cores.update({name: first/name/'snes9x2005_plus_libretro.so' for name in ('baseline','counter','dispatch')})
    cores.update({name: followup/name/'snes9x2005_plus_libretro.so' for name in ('hot','dma-same','dma-delta')})
    if offset:
        mode,=[n for n in ('offset-row','offset-plain') if (offset/n/'snes9x2005_plus_libretro.so').is_file()]
        cores[mode]=offset/mode/'snes9x2005_plus_libretro.so'
    digest=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    q=json.loads((ROOT/'evidence/2026-10-17/fivegame-replay/qualification.json').read_text())['payload_hashes']
    assert digest(cores['physical'])==q['plus-a7.so']
    for name,h in q.items():
        if name.startswith('cases/'):assert digest(FIX/name)==h
    lanes=list(dict((Path(f'/sys/devices/system/cpu/cpu{i}/topology/thread_siblings_list').read_text(),i)
                    for i in sorted(os.sched_getaffinity(0))).values())
    tasks=[(3,c,'full') for c in ('counter','dispatch','hot','dma-same','dma-delta')]
    tasks.extend((3,'baseline',mode) for mode in ('cold-off','off','oracle-reuse'))
    tasks.extend((g,'baseline','oracle-reuse') for g in (0,1))
    tasks.extend((g,c,'full') for g in (0,1,4) for c in ('dma-same','dma-delta'))
    if offset: tasks=[(3,mode,'both-cold-off')]
    def run(task, lane):
        g,c,mode=task; a='physical' if c=='baseline' else 'baseline'
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
        sources={p.name:digest(p) for p in (src,src.with_name('snes-throughput-replay.c'),Path(__file__))}),indent=2)+'\n')


if __name__=='__main__': main(*(Path(x).resolve() for x in sys.argv[1:]))
