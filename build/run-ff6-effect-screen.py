"""Bounded independent ARM comparisons. Run under WSL; no card access."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse, json, subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/ff6-effect-screen-private-v1'
p = argparse.ArgumentParser()
p.add_argument('--cases', default='all')
p.add_argument('--frames', type=int, default=1200)
p.add_argument('--group', default='cases')
p.add_argument('--exclude', default='')
p.add_argument('--workers', type=int, default=2)
p.add_argument('--variant', choices=['current','trace-current','general','fixed-unused'], default='current')
args = p.parse_args()
assert 600 <= args.frames <= 10000
assert args.group.replace('-', '').isalnum()
assert 1 <= args.workers <= 4
catalog = json.loads((OUT / 'catalog.json').read_text())
ids = list(range(len(catalog))) if args.cases == 'all' else [int(x) for x in args.cases.split(',')]
excluded = {int(x) for x in args.exclude.split(',') if x}
ids = [i for i in ids if i not in excluded]
assert len(ids) == len(set(ids)) and all(0 <= x < len(catalog) for x in ids)
dest = (OUT if args.variant=='current' else OUT/args.variant) / args.group
dest.mkdir(exist_ok=True)
Q = ['qemu-arm', '-cpu', 'cortex-a7', '-L', 'build/sysroot', '-E', 'LD_LIBRARY_PATH=build/sysroot/lib']
def run(index):
    log = dest / f'{index:03d}.log'
    receipt = dest / f'{index:03d}.json'
    # A broad sweep resumes only completed identities; no unchanged proof reruns.
    if receipt.exists():
        r = json.loads(receipt.read_text())
        assert r['frames_requested'] == args.frames and r['index'] == index
        return r
    assert not log.exists(), f'Incomplete evidence retained; use a distinct group: {log}'
    executable=OUT/('screen' if args.variant=='current' else 'trace-screen')
    core=OUT/('core' if args.variant=='current' else args.variant+'/core')/'snes9x2005_plus_libretro.so'
    command = Q + [str(executable.relative_to(ROOT)), 'build/plus-a7-out/plus-a7.so',
        str(core.relative_to(ROOT)),
        'build/plus-a7-out/ff6.sfc', 'build/magitek-bio-private/scene.state',
        str(args.frames), 'magitek-bio', str(index)]
    with log.open('x') as f:
        try:
            result = subprocess.run(command, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, timeout=180)
            code, timeout = result.returncode, False
        except subprocess.TimeoutExpired:
            code, timeout = None, True
    text = log.read_text(errors='replace')
    r = {'index': index, 'name': catalog[index]['name'], 'frames_requested': args.frames,
         'exit_code': code, 'host_timeout': timeout,
         'exact_output_pass': code == 0 and f'PASS: {args.frames} frames exact visible pixels' in text,
         'identity_verified': 'IDENTITY init_hits=' in text,
         'frames_retained': sum(x.startswith('ROW ') and not x.startswith('ROW columns=') for x in text.splitlines()),
         'context': '14-byte in-memory animation substitution; original Bio Blast mechanics and single-enemy target'}
    receipt.write_text(json.dumps(r, indent=2)+'\n')
    return r
with ThreadPoolExecutor(max_workers=args.workers) as pool:
    futures = [pool.submit(run, index) for index in ids]
    for f in as_completed(futures):
        r = f.result()
        print(f"{r['index']:03d} {r['name']} exact={r['exact_output_pass']} identity={r['identity_verified']} rows={r['frames_retained']} exit={r['exit_code']}", flush=True)
