"""Verify the exact card runner and wrapper with the frozen inputs, off-card."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory

from attempt_archive import digest


ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT/'build'
OUT = BUILD/'raster-device-private-v1'
FROZEN = BUILD/'fivegame-kernel-private-v2'
RASTER = ROOT/'evidence/2026-11-10/snes-raster-batches/analysis.json'
FROZEN_RECEIPT = ROOT/'evidence/2026-10-17/fivegame-replay/qualification.json'
QEMU = ['qemu-arm', '-cpu', 'cortex-a7', '-L', 'build/sysroot']
BUSYBOX = [*QEMU, '-0', 'busybox', BUILD/'uart-fix-private/firmware-busybox', 'sh']


def wrapper_check(tmp, scenario):
    lab = tmp/scenario
    mvp, proc = lab/'mvp', lab/'proc'
    mvp.mkdir(parents=True)
    proc.mkdir()
    if scenario != 'unarmed':
        for p in (lab, mvp):
            (p/'armed').write_text('fixture\n')
    if scenario == 'splash-busy':
        p = proc/'123'
        p.mkdir()
        (p/'comm').write_text('showlogo\n')
        (p/'status').write_text('State: S\n')
    pair = lab/'pair'
    pair.write_text('#!/bin/sh\nexit '+('3' if scenario == 'mismatch' else '0')+'\n')
    pair.chmod(0o755)
    env = dict(os.environ, PATH=f"{tmp/'bin'}:{os.environ['PATH']}",
               D35_RASTER_LAB=str(lab), D35_RASTER_MVP=str(mvp),
               D35_RASTER_PROC=str(proc), D35_RASTER_SPLASH_STOP=str(lab/'stop'))
    args = [*BUSYBOX, OUT/'launch.sh']
    rc = subprocess.run(args, cwd=ROOT, env=env, timeout=15).returncode
    assert rc == {'normal': 0, 'mismatch': 3, 'splash-busy': 1, 'unarmed': 0}[scenario]
    assert not (lab/'armed').exists() and not (mvp/'armed').exists()
    runs = list((lab/'results').glob('run-*'))
    assert len(runs) == (0 if scenario == 'unarmed' else 1)
    if not runs:
        return []
    log = (runs[0]/'wrapper.log').read_text()
    assert ('complete pairs=12' in log) == (scenario == 'normal')
    assert ('splash_timeout' in log) == (scenario == 'splash-busy')
    assert ('end 003-raster-offset rc=3' in log) == (scenario == 'mismatch')
    if scenario == 'normal':
        subprocess.run(args, cwd=ROOT, env=env, timeout=10, check=True)
        assert list((lab/'results').glob('run-*')) == runs
    return re.findall(r'^begin (\d+)-(\S+)$', log, re.M)


def main():
    raster = json.loads(RASTER.read_text())
    pinned = json.loads(FROZEN_RECEIPT.read_text())['payload_hashes']
    for name, sha in pinned.items():
        if name == 'plus-a7.so' or name.startswith('cases/'):
            assert digest(FROZEN/name) == sha, name
    payloads = {p.relative_to(OUT).as_posix(): digest(p) for p in (OUT/'cores').glob('*.so')}
    assert len(payloads) == 6
    for name, sha in payloads.items():
        assert raster['verified_core_sha256'][Path(name).stem] == sha, name
    assert digest(OUT/'launch.sh') == digest(BUILD/'snes-raster-device-launch.sh')
    payloads.update({n: digest(OUT/n) for n in ('pair', 'launch.sh')})
    versions = re.findall(r'GLIBC_(\d+)\.(\d+)', (OUT/'abi.txt').read_text())
    assert versions and all(tuple(map(int, v)) <= (2, 30) for v in versions)
    with TemporaryDirectory(prefix='raster-wrapper-') as temp:
        tmp = Path(temp)
        (tmp/'bin').mkdir()
        for name in ('sync', 'sleep'):
            p = tmp/'bin'/name
            p.write_text('#!/bin/sh\nexit 0\n')
            p.chmod(0o755)
        scenarios = ('normal', 'mismatch', 'splash-busy', 'unarmed')
        matrix, *_ = [wrapper_check(tmp, s) for s in scenarios]
    assert len(matrix) == len(set(matrix)) == 12
    assert set(matrix) == {(f'{g:03}', n) for g in range(5) for n in ('raster-offset', 'raster-offset-full')} | {
        ('000', 'raster-objects-wide'), ('002', 'raster-objects')}
    result_dir = OUT/'mock-pairs'
    result_dir.mkdir()

    def replay(row):
        game, variant = row
        args = [*QEMU, '-E', 'LD_LIBRARY_PATH=build/sysroot/lib', OUT/'pair', FROZEN/'plus-a7.so',
                OUT/'cores'/f'{variant}.so', FROZEN/'cases'/game,
                '8656' if game == '003' else '0', 'both-cold-off-device' if game == '003' else 'device']
        csv = result_dir/f'{game}-{variant}.csv'
        log = csv.with_suffix('.log')
        with csv.open('w') as data, log.open('w') as trace:
            subprocess.run(args, cwd=ROOT, stdout=data, stderr=trace, timeout=420, check=True)
        lines = csv.read_text().splitlines()
        assert len(lines) == 1204 and lines[-3] == 'published,1200,1200'
        for i, line in enumerate(lines[1:1201]):
            frame, base, test, wb, wt, ob, ot = map(int, line.split(','))
            assert frame == i and 0 <= ob < base <= wb and 0 <= ot < test <= wt
        _, left, right, a, b = lines[-1].split(',')
        assert left == right == '1200' and a == b
        reference, = (r for r in raster['verified_replays']
                      if r['game'] == int(game) and r['core'] == 'physical')
        assert a == reference['callback_layout_crc32']
        assert lines[-2] == f"audio,{reference['audio_frames']},{reference['audio_frames']}"
        print(game, variant, 'verified on both arms', flush=True)
        return dict(game=int(game), variant=variant, calls_per_arm=1200, callback_layout=a,
                    csv_sha256=digest(csv), log_sha256=digest(log))

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(replay, matrix))
    sources = ['snes-throughput-pair.c', 'snes-throughput-replay.c',
               'build-snes-raster-device.sh', 'snes-raster-device-launch.sh',
               'check-snes-raster-device.py']
    (OUT/'qualification.json').write_text(json.dumps({
        'measurement_only': True, 'production_gate': False, 'device_execution': False,
        'wrapper_cases': scenarios, 'pairs': results, 'payloads': payloads,
        'sources': {n: digest(BUILD/n) for n in sources},
        'raster_receipt_sha256': digest(RASTER), 'frozen_receipt_sha256': digest(FROZEN_RECEIPT),
    }, indent=2)+'\n')


if __name__ == '__main__':
    main()
