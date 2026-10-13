"""Verify the immutable returned card archive; never access or alter the card."""
from pathlib import Path
from hashlib import sha256
import json, statistics, sys

ROOT = Path(__file__).resolve().parent.parent
archive = Path(sys.argv[1]).resolve()
assert archive.is_relative_to(ROOT / 'device-evidence')
record = json.loads((archive / 'archive.json').read_text())
assert record['fat_clean'] and record['card_writes'] == 0
for entry in record['all_retro_files']:
    p = archive / entry['path']
    assert p.stat().st_size == entry['bytes']
    assert sha256(p.read_bytes()).hexdigest() == entry['sha256'], entry['path']
release = json.loads((ROOT / 'releases/snes-confuser-gameplay-1/manifest.json').read_text())
base = archive / 'retro/snes-confuser-gameplay1'
for name, expected in release['artifact_sha256'].items():
    p = archive / 'retro/snes-mvp/launch.sh' if name == 'dispatch.sh' else base / name
    assert sha256(p.read_bytes()).hexdigest() == expected, name
assert not list((archive / 'retro').rglob('armed'))
assert (base / 'last-launch').is_file()
before = ROOT / 'device-evidence' / release['archive_before_writes']
protected = json.loads((before / 'archive.json').read_text())['all_retro_files']
unchanged, changed = [], []
for e in protected:
    if e['path'] == 'retro/snes-mvp/launch.sh':
        continue
    p = archive / e['path']
    (unchanged if p.is_file() and sha256(p.read_bytes()).hexdigest() == e['sha256'] else changed).append(e['path'])
assert not [p for p in changed if p != 'retro/swapfile'], changed
s = dict(line.split('=', 1) for line in (base / 'last-progress.txt').read_text().splitlines() if '=' in line)
assert s['core_crc32'] == release['core_crc32'] and int(s['core_bytes']) == release['core_bytes']
assert s['phase'] == 'finished' and not s['error'] and not s['pcm_error_detail']
log = (base / 'startup.log').read_text()
assert 'library exit requested by B' in log and 'process exited status=0 ready=yes' in log
rows = [list(map(int, v.split(','))) for k, v in s.items() if k.startswith('frame_cost_') and k != 'frame_cost_columns']
sample = [list(map(int, v.split(','))) for k, v in s.items() if k.startswith('sample_cost_')]
n = int(s['runs'])
result = {
    'archive': archive.name, 'card_writes': 0, 'fat_clean': True,
    'all_archived_files_verified': len(record['all_retro_files']),
    'payload_and_dispatch_hashes_match': True, 'marker_consumed': True,
    'protected_prior_files_unchanged': len(unchanged), 'changed_prior_files': changed,
    'user_observation': 'Worked beautifully in two fights',
    'effect_identity_retained_in_log': False, 'session_id': s['session_id'],
    'session_seconds': int(s['session_elapsed_ns']) / 1e9,
    'active_seconds': int(s['active_wall_ns']) / 1e9,
    'calls': n, 'active_calls_per_second': n / (int(s['active_wall_ns']) / 1e9),
    'video_submitted': int(s['video_submitted']), 'held': int(s['held']),
    'video_dupes': int(s['video_dupes']), 'write_errors': int(s['write_errors']),
    'xruns': int(s['xrun_count']), 'pauses': int(s['pauses']),
    'snapshot_load_successes': int(s['snapshot_load_successes']),
    'native_frames': int(s['native_audio_frames']),
    'native_frames_per_call': int(s['native_audio_frames']) / n,
    'generated_converted_frames': int(s['resampled_enqueued_frames']),
    'accepted_minus_priming_frames': int(s['output_accepted_frames_including_priming']) - int(s['priming_silence_frames']),
    'running_reported_reserve_min_frames': int(s['pcm_playable_min_running_frames']),
    'final_epoch_pointer_bias_frames': int(s['pcm_appl_ptr']) - int(s['pcm_epoch_transferred_frames']),
    'retained_tail_mean_core_wall_ms': statistics.mean(r[3] for r in rows) / 1e6,
    'retained_tail_mean_core_cpu_ms': statistics.mean(r[4] for r in rows) / 1e6,
    'retained_tail_sample_count': len(rows),
    'retained_sparse_ppu_cpu_ms': [r[6] / 1e6 for r in sample],
    'orderly_library_B_exit_and_worker_close': True,
    'production_unit_cost_gate_passed': False,
    'limits': [
        'One manual session and user-reported two fights; no retained cast identities or exact input replay.',
        'Session cadence is measured; unmatched recent costs are not aligned Confuser savings.',
        'Running reserve minimum is retained aggregate telemetry, not the full effect reserve timeline.',
        'No incremental A7 unit prices, broad effect coverage, or universal crash-free claim.'
    ]
}
assert result['video_submitted'] == n and not result['held'] and not result['video_dupes']
assert not result['write_errors'] and not result['xruns']
assert result['accepted_minus_priming_frames'] == result['generated_converted_frames']
(archive / 'confuser-gameplay-return-analysis.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
