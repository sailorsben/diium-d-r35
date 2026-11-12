"""Report callback-adjusted handheld CPU measurements from a returned BRR run."""
from importlib import import_module
import json
from pathlib import Path
from statistics import mean
import sys


device = import_module('install-snes-brr-device')


def summarize(pairs):
    if not pairs:
        return None
    control, test = zip(*pairs)
    base = mean(control)
    candidate = mean(test)
    index = (95 * len(pairs) + 99) // 100 - 1
    return dict(ticks=len(pairs), control_mean_ms=base/1e6, candidate_mean_ms=candidate/1e6,
                saved_mean_ms=(base-candidate)/1e6, saved_percent=100*(1-candidate/base),
                control_p95_ms=sorted(control)[index]/1e6, candidate_p95_ms=sorted(test)[index]/1e6)


def report(run):
    assert 'complete pairs=10' in (run/'wrapper.log').read_text().splitlines()
    refs = {r['game']: r for r in device.read(device.replay.RASTER)['verified_replays']
            if r['core'] == 'physical'}
    pairs = []
    for game, arm in device.MATRIX:
        csv = run/f'{game}-{arm}.csv'
        checked = device.check_pair(csv, csv.with_suffix('.log'), refs[int(game)], arm, game)
        blocks, saved, other = [], [], []
        last = 0
        for row in csv.read_text().splitlines()[1:1201]:
            _, a, b, _, _, oa, ob, _, _, active, _ = map(int, row.split(','))
            pair = (a-oa, b-ob)
            blocks.append(pair)
            (saved if active > last else other).append(pair)
            last = active
        pairs.append(dict(**checked, main_cpu=summarize(blocks),
                          sustained_cache_ticks=summarize(saved),
                          other_ticks=summarize(other),
                          quarters=[summarize(blocks[i:i+300]) for i in range(0, 1200, 300)]))
    return dict(run=run.name, measurement='hardware core CPU, no native PCM or LCD',
                native_reserve_verified=False, pairs=pairs)


if __name__ == '__main__':
    print(json.dumps(report(Path(sys.argv[1]).resolve()), indent=2))
