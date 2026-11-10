"""Verify the archived raster run and summarize paired timings from the A7."""

import argparse
import json
import re
import struct
from pathlib import Path
from statistics import mean

from attempt_archive import digest, verify_saved


ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT/'evidence/2026-11-10/snes-raster-batches'
FROZEN_RECEIPT = ROOT/'evidence/2026-10-17/fivegame-replay/qualification.json'
FROZEN_CASES = ROOT/'build/fivegame-kernel-private-v2/cases'
GAMES = ('Mario', 'Metroid', 'F-Zero', 'Star Fox', 'Rendering Ranger R2')
CALLS = 1200
STAR = 3


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def inventory(archive):
    inside = read_json(archive/'archive.json')
    outside = read_json(archive/'outside-retro.json')
    assert inside['fat_clean'] and not inside['update_trigger_present']
    assert inside['card_writes'] == outside['card_writes'] == 0
    verify_saved(archive, inside)
    verify_saved(archive, dict(schema=outside['schema'], all_retro_files=outside['files']))
    entries = inside['all_retro_files'] + outside['files']
    return {row['path']: row for row in entries}, sum(row['new_content_bytes'] for row in entries)


def times_summary(values):
    ordered = sorted(values)
    return {
        'mean': round(mean(values)),
        'p95': ordered[(len(ordered)*95 + 99)//100 - 1],
        'p99': ordered[(len(ordered)*99 + 99)//100 - 1],
        'max': ordered[-1],
    }


def backlog(costs, period, extra):
    """Ideal serial model. No PCM publication times or device queues."""
    queued = peak = 0
    for cost in costs:
        queued = max(0, queued + cost + extra - period)
        peak = max(peak, queued)
    return dict(extra_per_call_ns=extra, peak_ns=peak, final_ns=queued)


def pair(run, name, reference, period, picture_changes):
    game_id, variant = name.split('-', 1)
    game = int(game_id)
    csv, log = (run/f'{name}.{suffix}' for suffix in ('csv', 'log'))
    cold, *body, published, audio, oracle = csv.read_text().splitlines()
    cold_label, *cold_times = cold.split(',')
    cold_cpu = list(map(int, cold_times))
    assert cold_label == 'cold' and len(cold_cpu) == 2
    assert all(x > 0 if game == STAR else x == 0 for x in cold_cpu)
    layout = reference['callback_layout_crc32']
    samples = reference['audio_frames']
    assert published == 'published,1200,1200'
    assert audio == f'audio,{samples},{samples}'
    assert oracle == f'oracle,1200,1200,{layout},{layout}'
    progress = log.read_text().splitlines()
    warmup = 8656 if game == STAR else 0
    assert progress == (
        [f'cold_calls_per_arm={n}' for n in range(1024, warmup, 1024)]
        + [f'cold_calls_per_arm={warmup} gameplay_started']
        + [f'gameplay_calls_per_arm={n}' for n in range(300, CALLS+1, 300)]
    )
    assert len(body) == CALLS
    rows = [tuple(map(int, line.split(','))) for line in body]
    for i, (index, cpu_a, cpu_b, wall_a, wall_b, crc_a, crc_b) in enumerate(rows):
        assert i == index and 0 <= crc_a < cpu_a <= wall_a and 0 <= crc_b < cpu_b <= wall_b
    sides = []
    for arm in range(2):
        cpu, wall, observer = ([row[arm+col] for row in rows] for col in (1, 3, 5))
        core = [t-crc for t, crc in zip(cpu, observer)]
        late = [i for i, t in enumerate(core) if t > period]
        side = {
            'core_ns': times_summary(core),
            'cpu_including_observer_ns': times_summary(cpu),
            'wall_including_observer_ns': times_summary(wall),
            'observer_cpu_mean_ns': round(mean(observer)),
            'wall_less_observer_mean_ns': round(mean(t-crc for t, crc in zip(wall, observer))),
            'core_first_3_mean_ns': round(mean(core[:3])),
            'core_after_first_120_mean_ns': round(mean(core[120:])),
            'core_over_period_calls': len(late),
        }
        if game == STAR:
            side['core_over_period_on_changed_picture_calls'] = sum(picture_changes[i] for i in late)
            side['serial_backlog_model'] = [backlog(core, period, n) for n in (0, 500_000, 1_000_000)]
        sides.append(side)
    baseline, candidate = sides
    return {
        'game': GAMES[game], 'variant': variant, 'native_period_ns': period,
        'verified_calls_per_arm': CALLS, 'audio_frames_per_arm': samples,
        'callback_layout_crc32': layout, 'cold_calls_per_arm': warmup, 'cold_cpu_ns': cold_cpu,
        'baseline': baseline, 'candidate': candidate,
        'core_saving_pct': {
            k: round(100*(1-candidate['core_ns'][k]/baseline['core_ns'][k]), 3)
            for k in ('mean', 'p95')
        },
        'csv_sha256': digest(csv), 'log_sha256': digest(log),
    }


def report(archive):
    install = read_json(EVIDENCE/'device-installation.json')
    offline = read_json(EVIDENCE/'analysis.json')
    target = install['target']
    current, retained = inventory(archive)
    previous, _ = inventory(archive.parent/install['prior_archive'])
    sha = {name: row['sha256'] for name, row in current.items()}
    assert len(previous) == install['prior_files'] and previous.keys() <= sha.keys()
    changed = sorted(p for p in previous if previous[p]['sha256'] != sha[p])
    assert set(changed) <= {'retro/snes-mvp/launch.sh', 'retro/swapfile'}
    assert sha['retro/snes-mvp/launch.sh'] == install['dispatch_sha256']
    assert sha['retro/init'] == install['normal_init_sha256']
    assert not any(Path(p).name.lower() in {'armed', 'code.bkp'} for p in sha)
    for name in ('last-boot-marker', 'last-launch'):
        assert sha[f'{target}/{name}'] == install['marker_sha256']
    for path, expected in install['payload_hashes'].items():
        assert sha[f'{target}/{path}'] == expected
    for path, expected in read_json(FROZEN_RECEIPT)['payload_hashes'].items():
        if path == 'plus-a7.so' or path.startswith('cases/'):
            assert sha[f'retro/snes-fivegame-kernel2/{path}'] == expected
    run, = (archive/target/'results').glob('run-*')
    wrapper = (run/'wrapper.log').read_text()
    assert wrapper.startswith('profile=raster-core-a7-1\nnative_pcm=0\nnative_display=0\nsplash_released')
    names = re.findall(r'^begin (\S+)$', wrapper, re.M)
    assert names == re.findall(r'^end (\S+) rc=0$', wrapper, re.M)
    assert len(names) == install['pairs_armed'] and wrapper.endswith(f'complete pairs={len(names)}\n')
    variants = ('raster-offset', 'raster-offset-full')
    assert set(names) == {f'{g:03}-{v}' for g in range(len(GAMES)) for v in variants} | {
        '000-raster-objects-wide', '002-raster-objects',
    }
    cpu = (run/'cpuinfo.txt').read_text()
    assert re.search(r'^CPU part\s*:\s*0xc07$', cpu, re.M) and 'GPA7XXXA' in cpu
    reference = {r['game']: r for r in offline['verified_replays'] if r['core'] == 'physical'}
    periods = {r['game']: r['period_ns'] for r in offline['prior_physical']}
    oracle = FROZEN_CASES/'003/expected.bin'
    assert digest(oracle) == sha['retro/snes-fivegame-kernel2/cases/003/expected.bin']
    pixels = [rgb for rgb, _, _ in struct.iter_unpack('<III', oracle.read_bytes())]
    assert len(pixels) == CALLS
    picture_changes = [False] + [a != b for a, b in zip(pixels, pixels[1:])]
    pairs = [pair(run, n, reference[int(n[:3])], periods[int(n[:3])], picture_changes) for n in names]
    return {
        'physical_a7': True, 'native_pcm_and_panel_measured': False,
        'archive': archive.name, 'source_commit': install['source_commit'],
        'files_inventoried': len(current), 'new_retained_bytes': retained,
        'changed_preexisting_paths': changed, 'fat_clean': True, 'one_shot_consumed': True,
        'wrapper_sha256': digest(run/'wrapper.log'),
        'cpuinfo_sha256': digest(run/'cpuinfo.txt'), 'meminfo_sha256': digest(run/'meminfo.txt'),
        'verified_pairs': len(pairs), 'verified_calls_both_arms': len(pairs)*CALLS*2,
        'star_fox_changed_picture_transitions': sum(picture_changes), 'pairs': pairs,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(report(args.archive), indent=2)+'\n', encoding='utf-8', newline='\n')
