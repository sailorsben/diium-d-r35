"""Derive a bounded physical effect budget from an archived Focus1 return.

No card access. Missing effect onset/recovery remains missing; sampled timing
is never calibrated away and overlapping regions are never added together.
"""
from pathlib import Path
from hashlib import sha256
from statistics import mean
import argparse
import csv
import importlib.util
import json
import math
import re

ROOT = Path(__file__).resolve().parent.parent


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'build' / file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def fields(path):
    result = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            assert key not in result, key
            result[key] = value
    return result


def pcm_rows(path):
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('seq='):
            row = dict(piece.split('=', 1) for piece in line.split())
            rows.append({k: v if k == 'op' else int(v) for k, v in row.items()})
    assert rows and all(b['seq'] == a['seq'] + 1 for a, b in zip(rows, rows[1:]))
    return rows


def summarize(rows):
    columns = ['wall_ns', 'cpu_ns', 'audio_wall_ns', 'video_wall_ns', 'admission_wall_ns']
    result = {'first_run': rows[0]['run'], 'last_run': rows[-1]['run']}
    for label, sampled in [('ordinary', 0), ('profiled', 1)]:
        selected = [r for r in rows if r['sampled'] == sampled]
        keys = columns + (['apu_inclusive_cpu_ns', 'ppu_cpu_ns', 'audio_callback_cpu_ns', 'video_callback_cpu_ns'] if sampled else [])
        result[label] = {'count': len(selected), 'mean_ms': {k: mean(r[k] for r in selected) / 1e6 for k in keys} if selected else {}}
    return result


def analyze(archive):
    archive = archive.resolve()
    assert archive.parent == (ROOT / 'device-evidence').resolve()
    proof = json.loads((archive / 'independent-readback.json').read_text())
    assert proof['passed'] and proof['card_writes'] == 0 and proof['one_shot_consumed']
    for name in ('collection.json', 'lab-collection.json'):
        collection = json.loads((archive / name).read_text())
        entries = collection.get('copied_and_hash_verified', collection.get('copied'))
        for entry in entries:
            path = archive / (entry['archive_path'] if 'archive_path' in entry else 'platform-lab/' + entry['relative_path'])
            assert sha256(path.read_bytes()).hexdigest() == entry['sha256']
    report = archive / 'snes-mvp/saves/last-session.txt'
    s = fields(report)
    focus = module('budget_focus', 'analyze-snes-focus.py').analyze(report)
    assert not focus['mock_backend'] and focus['backend'] == 'native_alsa' and s['phase'] == 'finished'
    assert s['rom_crc32'] == 'a27f1c7a' and s['write_errors'] == '1'
    unique = archive / 'snes-mvp/saves' / ('failure-' + s['session_id'] + '-session.txt')
    transient = {'checkpoint_kernel_ns', 'session_elapsed_ns', 'diagnostic_ram_write_ns', 'diagnostic_ram_writes'}
    for other in (unique, archive / 'snes-mvp/last-progress.txt'):
        other_fields = fields(other)
        assert {k: v for k, v in s.items() if k not in transient} == {k: v for k, v in other_fields.items() if k not in transient}
    assert int(s['resampled_enqueued_frames']) + int(s['priming_silence_frames']) == int(s['output_accepted_frames_including_priming']) + int(s['audio_remaining_frames'])
    trace = archive / 'snes-mvp/last-pcm-fault.txt'
    assert trace.read_bytes() == (archive / 'snes-mvp/saves' / ('failure-' + s['session_id'] + '-pcm.txt')).read_bytes()
    flight = module('budget_pcm', 'analyze-pcm-flight.py').analyze(trace, int(s['sink_rate']))
    rows = pcm_rows(trace)
    sync = [r for r in rows if r['op'] == 'SYNC_OK']
    assert len({r['epoch'] for r in rows}) == 1 and sync[0]['appl'] == sync[0]['xfer']
    first = sync[0]
    divergence = next(r for r in sync if r['appl'] != r['xfer'])
    curve = []
    minimum_hw_deficit = minimum_nominal_deficit = 0
    max_hw_drawdown = max_nominal_drawdown = 0
    for r in sync:
        elapsed = (r['ns'] - first['ns']) / 1e9
        produced = r['xfer'] - first['xfer']
        nominal_deficit = int(s['sink_rate']) * elapsed - produced
        trusted = r['ns'] < divergence['ns'] and r['state'] == 3 and r['appl'] == r['xfer']
        hw_deficit = r['hw'] - first['hw'] - produced
        if trusted:
            max_hw_drawdown = max(max_hw_drawdown, hw_deficit - minimum_hw_deficit)
            minimum_hw_deficit = min(minimum_hw_deficit, hw_deficit)
        if r['state'] == 3:
            max_nominal_drawdown = max(max_nominal_drawdown, nominal_deficit - minimum_nominal_deficit)
            minimum_nominal_deficit = min(minimum_nominal_deficit, nominal_deficit)
        curve.append(dict(seq=r['seq'], elapsed_ms=elapsed * 1000, state=r['state'], accepted_delta=produced,
                          nominal_consumed_delta=int(s['sink_rate']) * elapsed,
                          nominal_deficit=nominal_deficit, reported_hw_deficit=hw_deficit,
                          accepted_minus_hw=r['xfer'] - r['hw'], reported_queued=r['queued'],
                          appl_minus_accepted=r['appl'] - r['xfer'], reserve_trusted=trusted))
    # Model the shipped core's clocks, not a modern core's advertised NTSC rate.
    master = 3579545 * 6
    scanline = int(63.695e-6 * master + 0.5)
    clocks = scanline * 262
    fps = master / clocks
    native_per_call = clocks * 15664 / 328125 / 32
    output_per_call = native_per_call * int(s['sink_rate']) / int(s['native_rate'])
    assert abs(float(s['fps']) - fps) < 1e-8 and int(s['native_rate']) == 32040
    successful = [r for r in focus['frames'] if r['run'] < int(s['runs'])]
    assert len(successful) == 63 and [r['run'] for r in successful] == list(range(1924, 1987)), 'Revisit interval boundaries for a different return'
    groups = {'retained_successful': summarize(successful),
              'early_retained_1924_1938': summarize([r for r in successful if r['run'] <= 1938]),
              'rising_1939_1967': summarize([r for r in successful if 1939 <= r['run'] <= 1967]),
              'late_1968_1986': summarize([r for r in successful if r['run'] >= 1968])}
    samples = [r for r in successful if r['sampled']]
    for r in samples:
        assert r['apu_inclusive_cpu_ns'] + r['ppu_cpu_ns'] <= r['cpu_ns']
    final = samples[-1]
    terminal = focus['frames'][-1]
    budget_ms = 1000 / fps
    reserve_margin = math.ceil(output_per_call) + int(s['pcm_period_frames'])
    trusted_curve = [r for r in curve if r['reserve_trusted']]
    interval = flight['matched_large_batch_interval']
    work = json.loads((ROOT / 'build/ff6-window-batch-private/analysis.json').read_text())['metrics']
    removed = work['ppu_updates']['baseline_mean'] - work['ppu_updates']['candidate_mean']
    added = work['color_row_materializations']['candidate_mean'] - work['color_row_materializations']['baseline_mean']
    result = dict(version='1.19-focus1', session_id=s['session_id'], source_sha256=focus['source_sha256'],
                  groups=groups, sampled_frames=samples, terminal_failure_frame=terminal, pcm=flight,
                  observed_effect_marker='No effect onset/phase marker; intervals are chronological cost windows, not proved ROM script boundaries.',
                  cycles=dict(master_hz=master, master_clocks_per_scanline=scanline, scanlines_per_call=262,
                              master_clocks_per_call=clocks, nominal_fps=fps, native_budget_ms=budget_ms,
                              spc_clocks_per_call=clocks * 15664 / 328125, dsp_clocks_per_stereo_frame=32,
                              expected_native_frames_per_call=native_per_call, expected_sink_frames_per_call=output_per_call,
                              expected_cycle_derived_native_hz=master * 15664 / 328125 / 32,
                              actual_session_native_frames_per_call=int(s['native_audio_frames']) / int(s['runs']),
                              limits='Remainders, snapshot phase, reset, buffers and terminal partial delivery prevent an exact global quota comparison. Emulated clocks are not host instructions or measured A7 cycles.'),
                  historical_deficits=dict(ordinary_final_wall_ms=18.287, over_budget_ms=18.287 - budget_ms,
                                           accepted_rate=38763.739, shortfall_percent=100 * (1 - 38763.739 / 44100),
                                           required_throughput_increase_percent=100 * (44100 / 38763.739 - 1),
                                           label='Previous 1.19 failing interval, not a pre-effect baseline.'),
                  current_deficit=dict(accepted_rate=interval['accepted_frames_per_second'],
                                       required_throughput_increase_percent=100 * (44100 / interval['accepted_frames_per_second'] - 1),
                                       late_successful_ordinary_mean_wall_ms=groups['late_1968_1986']['ordinary']['mean_ms']['wall_ns']),
                  reserve=dict(complete_effect_requirement_measured=False, recovery_captured=False,
                               retained_pcm_elapsed_ms=curve[-1]['elapsed_ms'],
                               trusted_until_elapsed_ms=trusted_curve[-1]['elapsed_ms'],
                               retained_trusted_peak_prefix_deficit=max(r['reported_hw_deficit'] for r in trusted_curve),
                               retained_trusted_peak_drawdown=max_hw_drawdown,
                               running_nominal_peak_drawdown=max_nominal_drawdown,
                               proposed_margin_frames=reserve_margin,
                               margin_policy='One nominal output call rounded up plus one negotiated period; a declared design margin, not a qualified worst-case bound.',
                               partial_drawdown_plus_margin=max_hw_drawdown + reserve_margin,
                               minimum_observed_trusted_reserve=min(r['accepted_minus_hw'] for r in trusted_curve),
                               limit='Only 96 operations survive. Observed peaks are lower bounds. Missing onset/recovery and pointer divergence prohibit a complete-effect buffer sizing claim.'),
                  window_candidate=dict(removed_entries_per_replay_call=removed, added_color_rows_per_replay_call=added,
                                        break_even_row_cost_multiplier=added / removed,
                                        inequality='removed_entries * entry_overhead_us > added_rows * materialization_us + added_bookkeeping_us',
                                        measured_entry_overhead_us=None, measured_materialization_us=None,
                                        measured_added_bookkeeping_us=None, expected_net_saving_us=None,
                                        predicted_deficit_closed_percent=None, installation_gate='NOT MET',
                                        limit='Physical inclusive PPU timing is not a per-entry cost. Replay counters and physical samples are not aligned scenes.'),
                  limits=['Ordinary and sampled calls are different states, not controlled overhead pairs.',
                          'CPU callback timing can overlap inclusive APU timing; no sum of overlapping regions.',
                          'Admission wall is outside retro_run wall and is mostly pacing when production has headroom.',
                          'Main CPU excludes audio/display worker CPU and kernel service; whole-device budget remains unpriced.',
                          'The terminal failed callback includes fault handling/persistence and is excluded from successful means.'])
    for name, value in [('focus-analysis.json', focus), ('pcm-analysis.json', flight), ('effect-budget.json', result)]:
        (archive / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    with (archive / 'reserve-curve.csv').open('w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=list(curve[0])); writer.writeheader(); writer.writerows(curve)
    print(json.dumps({k: result[k] for k in ('groups', 'cycles', 'current_deficit', 'reserve', 'window_candidate')}, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    analyze(parser.parse_args().archive)
