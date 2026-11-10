"""Summarize Super FX loop batching after exact replay and paired host timing."""
from importlib import import_module
import json
from pathlib import Path
import re
from statistics import mean
import sys


ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT/'evidence/2026-11-10'
report = import_module('report-snes-throughput')


def read_json(path):
    return json.loads(path.read_text())


def cohort():
    device = read_json(EVIDENCE/'snes-raster-batches/device-return.json')
    row, = (p for p in device['pairs'] if p['game'] == 'Star Fox' and p['variant'] == 'raster-offset-full')
    archive = ROOT/'device-evidence'/device['archive']
    csv, = (archive/'retro/snes-raster-test1/results').glob('run-*/003-raster-offset-full.csv')
    assert report.sha(csv) == row['csv_sha256']
    slow = set()
    for line in csv.read_text().splitlines()[121:1201]:
        tick, _, cpu, _, _, _, observer = map(int, line.split(','))
        if cpu-observer > row['native_period_ns']:
            slow.add(tick)
    return slow


def main(profile, verify, timings, counted, output):
    verification = report.replay(verify)
    assert len(verification['results']) == 8
    assert all(row['verified'] == row['rendered'] == 1200 and not row['mismatch']
               for row in verification['results'])
    offline = read_json(EVIDENCE/'snes-raster-batches/analysis.json')
    reference = {row['game']: row for row in offline['verified_replays'] if row['core'] == 'physical'}
    for row in verification['results']:
        ref = reference[row['game']]
        assert row['audio_frames'] == ref['audio_frames'] and row['callback_layout_crc32'] == ref['callback_layout_crc32']

    timing = report.paired(timings)
    assert len(timing['results']) == 4
    cores = timing['meta']['core_sha256']
    assert cores['baseline'] == offline['verified_core_sha256']['raster-offset-full']
    assert cores['fx-batch-toggle'] == cores['fx-batch-toggle-disabled']
    for name, sha in verification['meta']['core_sha256'].items():
        assert cores[name] == sha
    slow = cohort()
    for row in timing['results']:
        csv = timings/row['log']
        samples = [tuple(map(int, line.split(','))) for line in csv.read_text().splitlines()[121:1201]]
        for name, group in (('slow', [r for r in samples if r[0] in slow]),
                            ('other', [r for r in samples if r[0] not in slow])):
            before, after = (mean(r[column] for r in group) for column in (1, 2))
            row[name+'_ticks'] = dict(count=len(group), mean_cpu_ns=[round(before), round(after)],
                                      saved_pct=round(100*(1-after/before), 2))
    lines = profile.read_text()
    census = read_json(EVIDENCE/'snes-throughput/analysis.json')['offline_verify']['results']
    star, = (row for row in census if row['core'] == 'census' and row['game'] == 3)
    loops = []
    for loc, target, shape, visits in re.findall(r'^loop ([0-9a-f]+) ([0-9a-f]+) ([0-9a-f]+) (\d+)$', lines, re.M):
        loops.append((int(loc,16)&65535, int(target,16), int(shape,16), int(visits)))
    fill = [n for loc, target, shape, n in loops if loc == target+3 and shape == 0x3cd131d1]
    plot = [n for loc, target, shape, n in loops if loc == target+1 and shape&0xffffff == 0x4c3c4c]
    all_visits = sum(n for _, _, _, n in loops)
    assert all_visits == dict(star['top_gsu_ops'])[0x3c] and fill and plot
    count_text = counted.read_text()
    for log in (lines, count_text):
        assert 'callback_layout=7a9a7371\n' in log
        assert 'published=1200 audio_frames=641626 verified=1200 mismatched=0' in log
    counts, = re.findall(r'^fx_batch (.+)$', count_text, re.M)
    coverage = dict((key, int(value)) for key, value in (part.split('=') for part in counts.split()))
    assert 0 < coverage['fill_guest_ops'] <= sum(fill)*4
    assert 0 < coverage['plot_guest_ops'] <= sum(plot)*2
    coverage.update(loop_visits=all_visits, word_fill_loop_visits=sum(fill), plot_loop_visits=sum(plot),
                    guest_ops_total=star['gsu_ops'])
    output.write_text(json.dumps(dict(
        physical=False, profile_sha256=report.sha(profile), counted_sha256=report.sha(counted),
        coverage=coverage, verification=verification, paired_qemu=timing,
    ), indent=2)+'\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main(*(Path(p).resolve() for p in sys.argv[1:]))
