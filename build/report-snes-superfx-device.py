"""Validate the archived Super FX return and compare A7 core timings."""
import argparse
from importlib import import_module
import json
from pathlib import Path
import struct
from statistics import mean

from attempt_archive import digest, verify_saved


raster = import_module('report-snes-raster-device')
ROOT, EVIDENCE = raster.ROOT, raster.EVIDENCE
CASES = ('003-fx-batch', '003-fx-batch-toggle')


def measurements(csv):
    rows = [tuple(map(int, line.split(','))) for line in csv.read_text().splitlines()[1:1201]]
    assert [r[0] for r in rows] == list(range(1200))
    return [[r[c]-r[c+4] for r in rows] for c in (1, 2)]


def report(archive):
    install = raster.read_json(EVIDENCE/'superfx-device-installation.json')
    baseline = raster.read_json(EVIDENCE/'device-return.json')
    assert install['prior_archive'] == baseline['archive']
    earlier, _ = raster.inventory(archive.parent/install['prior_archive'])
    inside = raster.read_json(archive/'archive.json')
    outside = raster.read_json(archive/'outside-retro.json')
    assert inside['card_writes'] == outside['card_writes'] == 0 and not inside['update_trigger_present']
    verify_saved(archive, inside)
    verify_saved(archive, dict(schema=outside['schema'], all_retro_files=outside['files']))
    entries = inside['all_retro_files'] + outside['files']
    sha = {row['path']: row['sha256'] for row in entries}
    target = install['target']
    assert len(earlier) == install['prior_files']
    assert not any(Path(p).name.lower() in {'armed', 'code.bkp'} for p in sha)
    assert sha['retro/init'] == install['normal_init_sha256']
    assert sha['retro/snes-mvp/launch.sh'] == install['dispatch_sha256']
    assert sha[install['baseline_path']] == install['baseline_sha256']
    for name in ('last-boot-marker', 'last-launch'):
        assert sha[f'{target}/{name}'] == install['marker_sha256']
    for path, expected in install['payload_hashes'].items():
        assert sha[f'{target}/{path}'] == expected
    for path, expected in raster.read_json(raster.FROZEN_RECEIPT)['payload_hashes'].items():
        if path.startswith('cases/003/'):
            assert sha[f'retro/snes-fivegame-kernel2/{path}'] == expected

    run, = (archive/target/'results').glob('run-*')
    wrapper = (run/'wrapper.log').read_text().splitlines()
    assert wrapper[:3] == ['profile=superfx-core-a7-1', 'native_pcm=0', 'native_display=0']
    assert wrapper[3].startswith('splash_released waited=')
    assert wrapper[4:] == [s for name in CASES for s in (f'begin {name}', f'end {name} rc=0')] + ['complete pairs=2']
    assert '0xc07' in (run/'cpuinfo.txt').read_text()
    ref, = (p for p in baseline['pairs'] if p['game'] == 'Star Fox' and p['variant'] == 'raster-offset-full')
    period = ref['native_period_ns']
    old_csv, = (archive.parent/baseline['archive']/'retro/snes-raster-test1/results').glob(
        'run-*/003-raster-offset-full.csv')
    assert digest(old_csv) == ref['csv_sha256']
    _, old_candidate = measurements(old_csv)
    slow = [i for i, n in enumerate(old_candidate) if n > period]
    assert len(slow) == ref['candidate']['core_over_period_calls']
    oracle = raster.FROZEN_CASES/'003/expected.bin'
    assert digest(oracle) == sha['retro/snes-fivegame-kernel2/cases/003/expected.bin']
    rgb = [image for image, _, _ in struct.iter_unpack('<III', oracle.read_bytes())]
    picture_changes = [False] + [a != b for a, b in zip(rgb, rgb[1:])]

    pairs = []
    reference = {'audio_frames': ref['audio_frames_per_arm'], 'callback_layout_crc32': ref['callback_layout_crc32']}
    for name in CASES:
        pair = raster.pair(run, name, reference, period, picture_changes)
        a, b = measurements(run/f'{name}.csv')
        pair['prior_slow_cohort'] = {
            'calls': len(slow), 'baseline_mean_ns': round(mean(a[i] for i in slow)),
            'candidate_mean_ns': round(mean(b[i] for i in slow)),
            'mean_saved_ns': round(mean(a[i]-b[i] for i in slow)),
        }
        pairs.append(pair)
    changes = [p for p in earlier if sha.get(p) != earlier[p]['sha256']]
    progress_changes = [p for p in changes if Path(p).suffix.lower() in {'.srm', '.sav', '.state', '.sram'}
                        or {'saves', 'states'} & set(Path(p).parts)]
    filesystem = {k: inside[k] for k in ('fat_clean', 'filesystem_scan_clean', 'dirty_bit', 'chkdsk_exit_code')}
    filesystem['scan_volume_in_use'] = 'The volume is in use' in (archive/'chkdsk-return.txt').read_text()
    event_file = archive/'drive-events.json'
    if event_file.exists():
        drive_events = raster.read_json(event_file)
        filesystem.update(volume_health=drive_events['health'], volume_status=drive_events['operational'],
                          disk_event_ids=[e['id'] for e in drive_events['events']],
                          drive_events_sha256=digest(event_file))
    return {
        'archive': archive.name, 'physical_a7': True, 'native_pcm_and_panel_measured': False,
        'source_commit': install['source_commit'], 'files_inventoried': len(sha),
        'archive_new_content_bytes': sum(r['new_content_bytes'] for r in entries),
        'preexisting_files_changed': len(changes), 'save_or_state_files_changed': len(progress_changes),
        'swapfile_changed': 'retro/swapfile' in changes,
        'dispatcher_changed': 'retro/snes-mvp/launch.sh' in changes,
        'one_shot_consumed': True, 'card_writes': 0, 'verified_calls_both_arms': 4800,
        'filesystem': filesystem,
        'chkdsk_sha256': digest(archive/'chkdsk-return.txt'), 'dirty_query_sha256': digest(archive/'fsutil-dirty.txt'),
        'wrapper_sha256': digest(run/'wrapper.log'), 'pairs': pairs,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(report(args.archive), indent=2)+'\n', encoding='utf-8', newline='\n')
