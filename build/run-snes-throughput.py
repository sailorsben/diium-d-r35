"""Replay frozen five-game inputs; pair host CPU timings on isolated lanes."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / 'build/fivegame-kernel-private-v2'
PHYSICAL_CORE = 'd7988b2861500eb923b827ad412c14ae841c03dd44e4099f2616a637bf88f62a'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inputs():
    plan = json.loads((FIX / 'plan.json').read_text())
    pinned = json.loads((ROOT/'evidence/2026-10-17/fivegame-replay/qualification.json').read_text())['payload_hashes']
    assert sha(FIX / 'plus-a7.so') == plan['core_sha256'] == PHYSICAL_CORE
    for c in plan['cases']:
        p = FIX / 'cases' / f"{c['game']:03}"
        for file, key in [('game.sfc', 'ROM_sha256'), ('input.txt', 'input_sha256'), ('expected.bin', 'expected_sha256')]:
            assert sha(p / file) == c[key]
        if c['game'] == 3:
            assert sha(p / 'warmup.txt') == pinned['cases/003/warmup.txt']
        else:
            assert hashlib.sha256((p / 'scene.state').read_bytes()[40:]).hexdigest() == c['source_fixture']['state_sha256']


def main(out, batch):
    script_hash=sha(Path(__file__))
    retry=batch.endswith('-retry')
    batch=batch.removesuffix('-retry')
    verify_inputs()
    run_dir = out / batch
    if not retry: run_dir.mkdir()
    names = {'reuse-verify':('reuse-census',),'span-verify':('span-census',),'offset-verify':('offset-row','offset-census'),
             'plain-verify':('offset-plain','offset-plain-census')}.get(batch)
    if batch in ('scheduler-verify', 'raster-verify'):
        prefix = 'apu' if batch == 'scheduler-verify' else 'raster'
        names = tuple(d.name for d in sorted(out.glob(prefix+'-*')) if (d/'snes9x2005_plus_libretro.so').is_file())
        assert names
    if names is None:
        names = ('baseline','hot','dma-same','dma-delta','dma-census') if batch.startswith('followup') else ('baseline','counter','dispatch','census')
    cores = {name: out / name / 'snes9x2005_plus_libretro.so' for name in names}
    cores['physical'] = FIX / 'plus-a7.so'
    qemu = ['qemu-arm','-cpu','cortex-a7','-L',str(ROOT/'build/sysroot'),'-E','LD_LIBRARY_PATH='+str(ROOT/'build/sysroot/lib'),str(out/'replay')]
    modes = ('full','cold-off','cold-tail','off','half','no-target')
    # Distinct sibling sets avoid pairing two timing workers on one physical core.
    allowed = sorted(os.sched_getaffinity(0))
    lanes = list(dict((Path(f'/sys/devices/system/cpu/cpu{i}/topology/thread_siblings_list').read_text(), i) for i in allowed).values())

    timed = batch in ('timing','followup-timing')
    def replay(task, affinity=None):
        rep, core, game, mode = task
        case = FIX / 'cases' / f'{game:03}'
        args = qemu + [str(cores[core]),str(case),'8656' if game==3 else '0',mode,'time' if timed else 'verify']
        if affinity is not None: args = ['taskset','-c',str(affinity)] + args
        with (run_dir/f'{rep}-{core}-{game}-{mode}.log').open('w') as log:
            rc = subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=420).returncode
        print(rep,core,game,mode,rc,flush=True)
        return dict(rep=rep,core=core,game=game,mode=mode,returncode=rc)

    if retry:
        assert timed
        manifest=run_dir/'manifest.json'
        meta=json.loads(manifest.read_text())
        failed=[r for r in meta['results'] if r['returncode']!=0]
        assert failed and all(r['returncode']==-7 for r in failed)
        for row in failed:
            p=run_dir/('{rep}-{core}-{game}-{mode}.log'.format(**row))
            assert not p.with_suffix('.interrupted').exists()
            p.rename(p.with_suffix('.interrupted'))
        def repair(row):
            rep,core,game,mode=(row[k] for k in ('rep','core','game','mode'))
            i=rep*2 if batch=='timing' else 6
            ret=replay((rep,core,game,mode),lanes[i%len(lanes)])
            assert ret['returncode']==0,ret
            row.update(ret,retried_after_sigbus=True)
        with ThreadPoolExecutor(max_workers=len(failed)) as pool:
            list(pool.map(repair,failed))
        meta['retry_script_sha256']=script_hash
        manifest.write_text(json.dumps(meta,indent=2)+'\n')
        return
    if batch == 'verify':
        tasks = [(0,c,3,m) for c,m in [('physical',m) for m in modes] + [('baseline','full'),('counter','full'),('dispatch','full'),('census','full')]]
        tasks += [(0,c,g,m) for g in [0,1,2,4] for c,m in [('physical','full'),('baseline','full'),('counter','full'),('dispatch','full'),('physical','off'),('physical','no-target')]]
        with ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(replay,tasks))
    elif batch == 'timing':
        star = [('physical',m) for m in ('full','cold-off','cold-tail','off','half')] + [('baseline','full'),('counter','full'),('dispatch','full')]
        ordinary = [('physical',m) for m in ('full','off','no-target')]
        assert len(lanes)>=4
        groups = []
        for rep in range(3):
            for matrix in (star[:5],star[5:]):
                groups.append([(rep,c,3,m) for c,m in (matrix if rep%2==0 else reversed(matrix))])
        groups.append([(rep,c,g,m) for rep in range(3) for g in [0,1,2,4]
                       for c,m in (ordinary if rep%2==0 else reversed(ordinary))])
        def pair(group, cpu):
            return [replay(t,cpu) for t in group]
        with ThreadPoolExecutor(max_workers=min(len(lanes),len(groups))) as pool:
            pending = [pool.submit(pair,g,lanes[i%len(lanes)]) for i,g in enumerate(groups)]
            results = [r for f in pending for r in f.result()]
    elif batch == 'followup-verify':
        tasks = [(0,c,3,'cold-off') for c in names]
        tasks += [(0,c,g,'full') for c in names for g in [0,1,2,4]]
        tasks += [(0,'physical',g,'oracle-reuse') for g in range(5)]
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(replay,tasks))
    elif batch in ('reuse-verify','span-verify'):
        tasks = [(0,names[0],g,'cold-off' if g==3 else 'full') for g in [3,0,1,2,4]]
        with ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(replay,tasks))
    elif batch in ('offset-verify','plain-verify'):
        tasks = [(0,c,g,'cold-off' if g==3 else 'full') for c in names for g in [3,0,1,2,4]]
        with ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(replay,tasks))
    elif batch in ('scheduler-verify', 'raster-verify'):
        tasks = [(0,c,g,'cold-off' if g==3 else 'full') for g in [3,0,1,2,4] for c in ('physical',*names)]
        with ThreadPoolExecutor(max_workers=7) as pool:
            results = list(pool.map(replay,tasks))
    elif batch == 'followup-timing':
        groups = [[(i*2+rep,c,3,'cold-off') for c in (('baseline',candidate) if rep==0 else (candidate,'baseline'))]
                  for i,candidate in enumerate(['hot','dma-same','dma-delta']) for rep in range(2)]
        groups.append([(rep,'physical',g,m) for rep in range(2) for g in [3,1,0]
                       for m in (('full','oracle-reuse') if rep==0 else ('oracle-reuse','full'))])
        with ThreadPoolExecutor(max_workers=min(len(lanes),len(groups))) as pool:
            pending = [pool.submit(lambda group,cpu:[replay(t,cpu) for t in group],g,lanes[i%len(lanes)]) for i,g in enumerate(groups)]
            results = [r for f in pending for r in f.result()]
    else:
        raise ValueError(batch)
    (run_dir/'manifest.json').write_text(json.dumps(dict(results=results,core_sha256={n:sha(p) for n,p in cores.items()},
        source_sha256=script_hash,replay_sha256=sha(out/'replay'),timing_affinity=lanes if timed else None, physical=False),indent=2)+'\n')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(),sys.argv[2])
