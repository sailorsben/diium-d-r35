"""Summarize a returned hardware lab; queue samples never become xrun counts."""
from pathlib import Path
import argparse
import csv
import json
import shlex

def audio_observations(samples, rate):
    successful = [s for s in samples if s['delay_rc'] == '0' and int(s['accepted_bytes']) > 0]
    delays = [int(s['delay_bytes']) for s in successful]
    intervals = [int(b['begin_ns']) - int(a['begin_ns']) for a, b in zip(samples, samples[1:])]
    usable = [s for s in samples if s['ptr_rc'] == '0']
    result = {
        'sample_count': len(samples),
        'negative_free_space_samples': sum(s['space_rc'] == '0' and int(s['free_bytes']) < 0 for s in samples),
        'query_errors': {name: sum(s[name + '_rc'] != '0' for s in samples)
                         for name in ('delay', 'space', 'ptr')},
        'pointer_supported_samples': len(usable),
        'pointer_backward_samples': sum(int(b['ptr_bytes']) < int(a['ptr_bytes']) for a, b in zip(usable, usable[1:])),
        'pointer_qualified_as_scheduling_clock': False,
    }
    if delays:
        result['steady_delay_min_bytes'] = min(delays)
        result['steady_delay_max_bytes'] = max(delays)
        result['steady_delay_min_ms_at_negotiated_rate'] = min(delays) * 1000 / (rate * 4)
    if intervals:
        result['sample_interval_mean_ms'] = sum(intervals) / len(intervals) / 1e6
        result['sample_interval_max_ms'] = max(intervals) / 1e6
    if len(usable) > 1:
        first, last = usable[0], usable[-1]
        result['raw_pointer_first_bytes'] = int(first['ptr_bytes'])
        result['raw_pointer_last_bytes'] = int(last['ptr_bytes'])
        # Non-mmap upstream4.19 masks the byte count with INT_MAX, not UINT_MAX.
        # Unknown vendor changes/resets mean neither wrap modulus is qualified.
        result['raw_pointer_delta_no_wrap_bytes'] = (
            int(last['ptr_bytes']) - int(first['ptr_bytes'])
            if result['pointer_backward_samples'] == 0 else None)
        result['pointer_sample_interval_ns'] = int(last['begin_ns']) - int(first['begin_ns'])
    return result

def analyze(folder):
    records = [dict(p.split('=', 1) for p in shlex.split(line) if '=' in p)
               for line in (folder / 'results.log').read_text().splitlines()]
    runs = [r for r in records if r['event'] == 'run_begin']
    assert len(runs) == 1 and runs[0]['version'] == 'lab1', 'Require one identified lab run'
    simulated = runs[0]['null'] == '1'
    kernels = []
    for r in records:
        if r['event'] != 'kernel': continue
        draws = int(r['draws']); cpu = int(r['cpu_ns'])
        hits, misses = int(r['hits']), int(r['misses'])
        kernels.append({'mode': r['mode'], 'scenario': int(r['scenario']),
                        'draws': draws, 'cpu_ns_per_draw': cpu / draws,
                        'wall_ns_per_draw': int(r['wall_ns']) / draws,
                        'cache_hit_fraction': hits / (hits + misses) if hits + misses else None,
                        'cache_bytes': int(r['cache_bytes'])})
    pipelines = []
    for r in records:
        if r['event'] != 'pipeline': continue
        frames = int(r['frames']); elapsed = int(r['active_ns'])
        item = {'name': r['name'], 'submitted_jobs': int(r['submitted']),
                'completed_vendor_flips': int(r['flipped']),
                'producer_iterations_per_second': frames * 1e9 / elapsed,
                'producer_cpu_ms_per_iteration': int(r['producer_cpu_ns']) / max(frames, 1) / 1e6,
                'scaler_mean_ms': int(r['scale_ns']) / max(int(r['scaled']), 1) / 1e6,
                'flip_mean_ms': int(r['flip_ns']) / max(int(r['flipped']), 1) / 1e6,
                'display_worker_cpu_ms': int(r['worker_cpu_ns']) / 1e6,
                'reserve_wait_ms': int(r['reserve_ns']) / 1e6,
                'max_start_lateness_ms': int(r['max_late_ns']) / 1e6}
        audio = next((a for a in records if a['event'] == 'audio_end' and a['name'] == r['name']), None)
        if audio:
            item['audio'] = {k: int(audio[k]) for k in
                             ('accepted_bytes', 'worker_cpu_ns', 'short_writes',
                              'eagain', 'zero_delay_samples', 'error')}
            item['audio']['max_write_gap_ms'] = int(audio['max_write_gap_ns']) / 1e6
            sample_file = folder / ('audio-' + r['name'] + '.csv')
            with sample_file.open(newline='') as f:
                samples = list(csv.DictReader(f))
            phase_index = records.index(r)
            configs = [c for c in records[:phase_index] if c['event'] == 'audio_config']
            rate = int(configs[-1]['accepted_rate'])
            item['audio'].update(audio_observations(samples, rate))
        pipelines.append(item)
    wake = next((r for r in records if r['event'] == 'wake'), None)
    return {'version': 'lab1', 'simulated': simulated,
            'complete': any(r['event'] == 'run_end' and r['status'] == 'complete' for r in records),
            'wake': {'nominal_deadline_spacing_ns': int(wake['requested_ns']),
                     'samples': int(wake['samples']),
                     'mean_deadline_lateness_ms': int(wake['sum_late_ns']) / int(wake['samples']) / 1e6 if int(wake['samples']) else None,
                     'maximum_deadline_lateness_ms': int(wake['max_late_ns']) / 1e6,
                     'method': 'Advancing nominal deadlines; expired waits return immediately. Not individual5ms sleep durations.'} if wake else None,
            'kernels': kernels, 'pipelines': pipelines,
            'limits': ['Synthetic CPU/tiles do not establish whole-game speed.',
                       'Vendor flip completion is not optical panel cadence.',
                       'GETODELAY zero and write gaps are not measured xruns.',
                       'GETOPTR is unqualified raw data, not yet a scheduling clock.',
                       'Negative GETOSPACE and OSS staging must not be clamped into a fabricated physical queue.',
                       'All CPU threads share one Cortex-A7; worker wall times overlap.',
                       'Null/QEMU times are not physical performance evidence.']}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(analyze(args.folder), indent=2) + '\n'
    if args.output: args.output.write_text(result)
    print(result)
