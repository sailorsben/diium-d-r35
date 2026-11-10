"""Qualify the Star Fox Super FX device package using off-card ARM replays."""
from importlib import import_module
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory

from attempt_archive import digest


raster = import_module('check-snes-raster-device')
ROOT = raster.ROOT
OUT = ROOT/'build/superfx-device-private-v1'
EVIDENCE = ROOT/'evidence/2026-11-10/snes-raster-batches/superfx-experiment.json'
MODES = {'fx-batch': 'both-cold-off-device', 'fx-batch-toggle': 'both-cold-off-fx-toggle-device'}


def main(baseline):
    evidence = json.loads(EVIDENCE.read_text())
    expected = evidence['paired_qemu']['meta']['core_sha256']
    assert digest(baseline) == expected['baseline']
    pinned = json.loads(raster.FROZEN_RECEIPT.read_text())['payload_hashes']
    for name, sha in pinned.items():
        if name.startswith('cases/003/'):
            assert digest(raster.FROZEN/name) == sha

    cores = {n: OUT/'cores'/f'{n}.so' for n in (*MODES, 'fx-batch-toggle-disabled')}
    for name, path in cores.items():
        assert digest(path) == expected[name], name
    assert expected['fx-batch-toggle'] == expected['fx-batch-toggle-disabled']
    assert digest(OUT/'launch.sh') == digest(ROOT/'build/snes-raster-device-launch.sh')
    versions = re.findall(r'GLIBC_(\d+)\.(\d+)', (OUT/'abi.txt').read_text())
    assert versions and all(tuple(map(int, v)) <= (2, 30) for v in versions)

    with TemporaryDirectory(prefix='superfx-wrapper-') as temp:
        tmp = Path(temp)
        (tmp/'bin').mkdir()
        for name in ('sync', 'sleep'):
            exe = tmp/'bin'/name
            exe.write_text('#!/bin/sh\nexit 0\n')
            exe.chmod(0o755)
        scenarios = ('normal', 'mismatch', 'splash-busy', 'unarmed')
        matrix, *_ = [raster.wrapper_check(tmp, s, out=OUT, profile='superfx') for s in scenarios]
        assert matrix == [('003', name) for name in MODES]
        assert len(raster.wrapper_check(tmp, 'normal', out=OUT)) == 12
        lab = tmp/'superfx-normal'
        run, = (lab/'results').glob('run-*')
        for name, mode in MODES.items():
            control = '/usr/retro/snes-raster-test1/cores/raster-offset-full.so'
            if name.endswith('-toggle'):
                control = str(lab/'cores/fx-batch-toggle-disabled.so')
            assert (run/f'003-{name}.csv').read_text().splitlines() == [
                control, str(lab/'cores'/f'{name}.so'), '/usr/retro/snes-fivegame-kernel2/cases/003',
                '8656', mode,
            ]

    reference, = (r for r in json.loads(raster.RASTER.read_text())['verified_replays']
                  if r['game'] == 3 and r['core'] == 'physical')
    pairs = {}
    for name in MODES:
        csv = OUT/'mock-pairs'/f'{name}.csv'
        log = csv.with_suffix('.log')
        control = cores['fx-batch-toggle-disabled'] if name.endswith('-toggle') else baseline
        latest = max(p.stat().st_mtime_ns for p in (OUT/'pair', control, cores[name]))
        assert min(csv.stat().st_mtime_ns, log.stat().st_mtime_ns) >= latest
        assert log.read_text().splitlines()[8] == 'cold_calls_per_arm=8656 gameplay_started'
        pairs[name] = raster.check_pair(csv, log, reference)
        print(name, 'matched pixels, PCM and callback layout on both arms', flush=True)

    payloads = {path.relative_to(OUT).as_posix(): digest(path)
                for path in (*cores.values(), OUT/'launch.sh', OUT/'pair')}
    sources = ['snes-throughput-pair.c', 'snes-throughput-replay.c', 'build-snes-raster-device.sh',
               'snes-raster-device-launch.sh', 'check-snes-raster-device.py', Path(__file__).name]
    (OUT/'qualification.json').write_text(json.dumps({
        'measurement_only': True, 'physical': False, 'baseline_sha256': expected['baseline'],
        'frozen_receipt_sha256': digest(raster.FROZEN_RECEIPT), 'superfx_evidence_sha256': digest(EVIDENCE),
        'pairs': pairs, 'wrapper_cases': scenarios, 'payloads': payloads,
        'sources': {n: digest(ROOT/'build'/n) for n in sources},
    }, indent=2)+'\n')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
