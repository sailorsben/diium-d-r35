"""Compare ordinary control/candidate to frozen v3 on all original inputs."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, os, subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/draw-order-private-v1'

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def main():
    assert not (OUT / 'qualification.json').exists()
    identity = json.loads((OUT / 'build-identity.json').read_text())
    cases = json.loads((ROOT / 'build/ability-regression-private-v1/plan.json').read_text())['cases']
    (OUT / 'exact').mkdir()
    env = {**os.environ, 'LD_LIBRARY_PATH': str(ROOT / 'build/sysroot/lib')}
    def run(job):
        label, case = job
        core = OUT / label / 'snes9x2005_plus_libretro.so'
        assert digest(core) == identity['cores'][label]
        log = OUT / f"exact/{label}-{case['seq']:03d}.log"
        args = ['qemu-arm', '-cpu', 'cortex-a7', '-L', str(ROOT / 'build/sysroot'), str(OUT / 'compare'),
                str(ROOT / 'build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so'), str(core),
                str(ROOT / 'build/plus-a7-out/ff6.sfc'),
                str(ROOT / f"build/ability-regression-private-v1/cases/{case['seq']:03d}/scene.state"),
                str(ROOT / f"build/ability-regression-private-v1/cases/{case['seq']:03d}/input.txt"),
                str(case['observed_effect_id']), '1200']
        with log.open('x') as f:
            subprocess.run(args, env=env, stdout=f, stderr=subprocess.STDOUT, check=True, timeout=600)
        assert 'PASS 1200 calls' in log.read_text()
        return {'label': label, 'case': case['seq'], 'name': case['name'], 'calls': 1200,
                'core_sha256': digest(core), 'log_sha256': digest(log)}
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(run, (label, case)) for label in ('boundary', 'priority') for case in cases]
        for f in as_completed(jobs):
            r = f.result()
            results.append(r)
            print('PASS', r['label'], r['name'], len(results), '/ 36', flush=True)
    for n, h in json.loads((OUT / 'frozen.json').read_text()).items():
        assert digest(ROOT / n) == h, n
    results.sort(key=lambda r: (r['label'], r['case']))
    (OUT / 'qualification.json').write_text(json.dumps({'passed': True, 'comparisons': results,
        'raw_graphics_PCM_geometry_calls': 43200, 'normalized_state_every': 30, 'APU_object_sha256': identity['APU_object_sha256'],
        'A7_saving_measured': False, 'production_gate_passed': False, 'card_writes': 0}, indent=2) + '\n')

if __name__ == '__main__':
    main()
