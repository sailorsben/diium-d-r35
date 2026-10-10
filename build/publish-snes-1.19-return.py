"""Verify and publish the archived 1.19 failure; never write to the card.

Only text diagnostics and derived counts are published. Games, save bytes,
states, vendor dependencies and full card/flash captures remain private.
"""
from pathlib import Path
from hashlib import sha256
import argparse
import importlib.util
import json
import re
import statistics
import struct
import zlib

ROOT = Path(__file__).resolve().parent.parent
PREFIX = 'evidence/2026-10-10/snes-mvp-1.19-return/'
REARM_ARCHIVE = ROOT / 'device-evidence/snes-mvp-return-20261010T070839Z'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'build' / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def fields(path):
    return dict(line.split('=', 1) for line in path.read_text(encoding='utf-8').splitlines()
                if '=' in line)


def verified_collection(archive):
    collection = json.loads((archive / 'collection.json').read_text(encoding='utf-8'))
    assert collection['complete'] and not collection['read_errors']
    assert collection['card_writes'] == 0 and not collection['armed_present']
    entries = collection['copied_and_hash_verified']
    assert len({e['card_path'] for e in entries}) == len(entries)
    for entry in entries:
        path = archive / entry['archive_path']
        assert path.stat().st_size == entry['bytes'] and digest(path) == entry['sha256']
    lab = json.loads((archive / 'lab-collection.json').read_text(encoding='utf-8'))
    assert lab['card_writes'] == 0 and not lab['lab_armed']
    for entry in lab['copied']:
        path = archive / 'platform-lab' / entry['relative_path']
        assert path.stat().st_size == entry['bytes'] and digest(path) == entry['sha256']
    return collection, lab


def analyze(archive):
    archive = archive.resolve()
    assert archive.parent == (ROOT / 'device-evidence').resolve()
    collection, lab = verified_collection(archive)
    proof = json.loads((archive / 'independent-readback.json').read_text(encoding='utf-8'))
    assert proof['card_writes'] == 0 and proof['current_stock_and_vesper_sd_hashes_match']
    assert proof['normal_init_match'] and proof['all_markers_absent']
    assert proof['firmware_update_trigger_absent']
    assert proof['archived_mvp_progress_files_reread'] == len(collection['copied_and_hash_verified'])
    before, before_lab = verified_collection(REARM_ARCHIVE)
    assert collection['production_hashes'] == before['production_hashes']
    assert lab['copied'] == before_lab['copied']
    expected = json.loads((ROOT / 'releases/snes-mvp-1.19/manifest.json').read_text())
    mvp = archive / 'snes-mvp'
    for name, key in [('snes-mvp', 'binary_sha256'), ('plus-a7.so', 'core_sha256'),
                      ('launch.sh', 'wrapper_sha256')]:
        assert digest(mvp / name) == expected[key]
    old = {e['card_path']: e for e in before['copied_and_hash_verified']}
    new = {e['card_path']: e for e in collection['copied_and_hash_verified']}
    assert set(old) <= set(new), 'A previously archived file is missing'
    assert new['retro/init']['sha256'] == old['retro/init']['sha256']
    progress = [name for name in old if ('/saves/' in name or '/states/' in name)
                and name.endswith(('.srm', '.srm.bak', '.state', '.state.bak'))]
    changes = [name for name in progress if old[name]['sha256'] != new[name]['sha256']]
    assert all(name.endswith(('.srm', '.srm.bak')) for name in changes)
    states = [name for name in progress if name.endswith(('.state', '.state.bak'))]
    for name in states:
        raw = (archive / new[name]['archive_path']).read_bytes()
        assert raw[:8] == b'D35MVP01' and len(raw) == struct.unpack_from('<I', raw, 28)[0] + 40
        assert zlib.crc32(raw[40:]) & 0xffffffff == struct.unpack_from('<I', raw, 32)[0]
    assert all(new[name]['bytes'] == 8192 for name in progress
               if name.endswith(('.srm', '.srm.bak')))

    s = fields(mvp / 'saves/last-session.txt')
    assert s['build_version'] == '1.19' and s['phase'] == 'finished'
    assert re.fullmatch(r'\d+-\d+', s['session_id'])
    unique = mvp / 'saves' / ('failure-' + s['session_id'] + '-session.txt')
    failure = fields(unique)
    # Unique fault persistence follows the final checkpoint; keep raw originals.
    transient = {'checkpoint_kernel_ns', 'session_elapsed_ns',
                 'diagnostic_ram_write_ns', 'diagnostic_ram_writes'}
    assert {k: v for k, v in s.items() if k not in transient} == {
        k: v for k, v in failure.items() if k not in transient}
    ram = fields(mvp / 'last-progress.txt')
    assert {k: v for k, v in ram.items() if k not in transient} == {
        k: v for k, v in s.items() if k not in transient}
    core = (mvp / 'plus-a7.so').read_bytes()
    assert s['core_crc32'] == f'{zlib.crc32(core) & 0xffffffff:08x}'
    assert int(s['core_bytes']) == len(core)
    assert s['write_errors'] == '1' and s['pcm_state'] == '1'
    assert s['error'] == 'Audio publication failed: File descriptor in bad state'
    runs = int(s['runs'])
    assert int(s['held']) == 0 and int(s['video_dupes']) == 0
    assert int(s['video_submitted']) == runs - 1
    bins = [int(v) for k, v in s.items() if re.fullmatch(r'core_wall_bin_\d+ms', k)]
    assert sum(bins) == runs
    assert int(s['resampled_enqueued_frames']) + int(s['priming_silence_frames']) == (
        int(s['output_accepted_frames_including_priming']) + int(s['audio_remaining_frames']))
    pcm = mvp / 'saves' / ('failure-' + s['session_id'] + '-pcm.txt')
    assert pcm.read_bytes() == (mvp / 'last-pcm-fault.txt').read_bytes()
    flight = module('flight_119_return', 'analyze-pcm-flight.py').analyze(pcm, int(s['sink_rate']))
    assert flight['epoch'] == int(s['pcm_epoch'])
    final = flight['final_observation']
    assert final['state'] == int(s['pcm_state']) and final['appl'] == int(s['pcm_appl_ptr'])
    assert final['hw'] == int(s['pcm_hw_ptr']) and final['xfer'] == int(s['pcm_epoch_transferred_frames'])
    rows = [list(map(int, v.split(','))) for k, v in s.items()
            if re.fullmatch(r'frame_cost_\d+', k)]
    assert [x[0] for x in rows] == list(range(runs - len(rows) + 1, runs + 1))
    ordinary = [x for x in rows if not x[2] and x[0] < runs]
    assert not any(x[2] for x in rows), 'Update the phase-sampling limit for this return'
    sampled = [list(map(int, v.split(','))) for k, v in s.items()
               if re.fullmatch(r'sample_cost_\d+', k)]
    assert all(x[0] < rows[0][0] for x in sampled)
    startup = (mvp / 'startup.log').read_text(encoding='utf-8')
    assert startup.count('library game launch requested') == 1
    assert 'library exit requested by B' in startup
    assert 'display worker joined' in startup and 'board close complete' in startup
    assert 'process exited status=255 ready=yes' in startup
    flush = (mvp / 'diagnostic-flush.log').read_text(encoding='utf-8')
    assert 'final_copies=after_child_exit' in flush
    health = (archive / 'chkdsk-return.txt').read_text(encoding='utf-8-sig')
    assert '11EB-1465' in health and 'Windows has scanned the file system and found no problems.' in health
    prior = json.loads((ROOT / 'evidence/2026-10-09/fat-recovery/analysis.json').read_text())
    result = {
        'version': '1.19', 'archive': archive.name,
        'collected_utc': collection['collected_utc'], 'card_writes': 0,
        'mvp_progress_files_hash_verified': len(new), 'lab_files_hash_verified': len(lab['copied']),
        'exact_release_and_stock_init_verified': True, 'fat_read_only_check_clean': True,
        'one_shot_consumed': True, 'all_prior_files_retained': True,
        'private_snapshot_files_unchanged_and_crc_verified': len(states),
        'nonempty_private_sram_files': sum(name.endswith(('.srm', '.srm.bak')) for name in progress),
        'updated_private_sram_generations_archived': len(changes),
        'user_report': 'Bio Blast still crashed the game; exited the menu with B.',
        'observed_exit': {
            'game_launch_requests': 1, 'game_exit': 'native audio error returned to our library',
            'B_exit': 'B left the library after the audio failure; not an in-game Exit game selection',
            'display_worker_joined_and_board_closed': True, 'wrapper_final_copies_completed': True,
            'exit_status': 255,
            'exit_status_meaning': 'Normal process return of rc=-1 inherited from the failed game; not a recorded signal crash',
        },
        'session': {
            'id': s['session_id'], 'runs': runs, 'video_submitted': int(s['video_submitted']),
            'held': int(s['held']), 'duplicates': int(s['video_dupes']),
            'active_seconds': int(s['active_wall_ns']) / 1e9,
            'calls_per_active_second': runs * 1e9 / int(s['active_wall_ns']),
            'snapshot_loads': int(s['snapshot_load_successes']),
            'pauses': int(s['pauses']), 'audio_error': s['error'], 'pcm_detail': s['pcm_error_detail'],
            'audio_remaining_frames': int(s['audio_remaining_frames']), 'recorded_xruns': int(s['xrun_count']),
            'ordinary_final_calls': len(ordinary),
            'ordinary_final_mean_wall_ms': statistics.mean(x[3] for x in ordinary) / 1e6,
            'ordinary_final_mean_main_cpu_ms': statistics.mean(x[4] for x in ordinary) / 1e6,
            'native_frame_budget_ms': 1000 / float(s['fps']),
            'sampled_ppu_apu_limit': 'No phase sample falls in the final 24-call window; earlier inclusive samples do not price its PPU/APU split.',
            'finished_reports_differ_only_in': sorted(transient),
        },
        'pcm': flight,
        'historical_1_18_context_not_controlled_speed_comparison': {
            'ordinary_final_mean_wall_ms': prior['recovered_session']['ordinary_final_mean_wall_ms'],
            'ordinary_final_mean_main_cpu_ms': prior['recovered_session']['ordinary_final_mean_main_cpu_ms'],
            'accepted_frames_per_second': prior['pcm']['matched_large_batch_interval']['accepted_frames_per_second'],
            'limit': 'Different physical run, call history and encounter timing; similar costs do not establish the cache speed delta.',
        },
        'inference': 'The 1.19 palette work reduction did not prevent physical Bio Blast audio failure. Production falls below the sink near failure, before a total 384-frame unexplained application-pointer difference and SETUP/EBADFD. The leading trigger remains transient underproduction.',
        'limits': 'No attribution of pointer changes to a specific owner, kernel stop mechanism, exact expensive-phase CPU subsystem, save payload semantics or general hard-power-off safety. No core signal crash or controlled 1.18/1.19 speed comparison established.',
        'next_action': 'Keep failed 1.19 unarmed. Attribute the expensive phase using a bounded RAM-only PPU/APU/core/callback profile before another optimization; do not rearm the unchanged failure or infer A7 speed from palette work counts.',
    }
    path = archive / 'analysis.json'
    path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result, unique, pcm


def publish(archive):
    result, unique, pcm = analyze(archive)
    archive = archive.resolve()
    publisher = module('publisher_119_return', 'publish-snes-1.19.py')
    selected = {'analysis.json': archive / 'analysis.json',
                'session-failure.txt': unique, 'pcm-failure.txt': pcm,
                'startup.log': archive / 'snes-mvp/startup.log',
                'last-run.log': archive / 'snes-mvp/last-run.log',
                'diagnostic-flush.log': archive / 'snes-mvp/diagnostic-flush.log',
                'chkdsk.txt': archive / 'chkdsk-return.txt',
                'independent-readback.json': archive / 'independent-readback.json'}
    manifest = ROOT / 'evidence/manifest.json'
    raw = manifest.read_bytes()
    entries = json.loads(raw)['entries']
    existing = {e['published']: e for e in entries if e['published'].startswith(PREFIX)}
    assert set(existing) <= {PREFIX + name for name in selected}, 'Unexpected published return file'
    for entry in entries:
        assert digest(ROOT / entry['published']) == entry['published_sha256']
    prepared = []
    for name, source in selected.items():
        original = source.read_bytes()
        output = publisher.public_text(original)
        for forbidden in (b'GITHUB_TOKEN', b'Bearer ', b'github_pat_', b'ghp_', b'C:\\Users',
                          b'.codex/attachments', b'D35MVP01', b'D35PLUS1'):
            assert forbidden not in output, (name, forbidden)
        target = ROOT / PREFIX / name
        entry = {
            'source': source.relative_to(ROOT).as_posix(), 'published': target.relative_to(ROOT).as_posix(),
            'source_sha256': sha256(original).hexdigest(), 'published_sha256': sha256(output).hexdigest(),
            'bytes': len(output), 'normalized': original != output,
        }
        if entry['published'] in existing:
            assert existing[entry['published']] == entry and target.read_bytes() == output
            continue
        assert not target.exists(), 'Preserve published evidence'
        prepared.append((target, output, entry))
    for target, output, entry in prepared:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output)
        assert digest(target) == entry['published_sha256']
    if prepared:
        manifest.write_bytes(publisher.append_manifest(raw, [entry for _, _, entry in prepared]))
    print(json.dumps({'published_files': len(prepared), 'historical_entries_verified': len(entries),
                      'session': result['session'], 'changed_sram_generations': result['updated_private_sram_generations_archived'],
                      'fat_clean': True, 'card_writes': 0, 'one_shot_consumed': True}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    if args.publish:
        publish(args.archive)
    else:
        result, _, _ = analyze(args.archive)
        print(json.dumps(result, indent=2))
