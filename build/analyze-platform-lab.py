"""Summarize a returned hardware lab; queue samples never become xrun counts."""
from pathlib import Path
import argparse
import csv
import json
import shlex

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
            samples = list(csv.DictReader(sample_file.open(newline='')))
            usable = [s for s in samples if s['ptr_rc'] == '0']
            item['audio']['pointer_supported_samples'] = len(usable)
            # Preserve raw unsigned counter movement. Resets/wraps/jumps must be
            # qualified against acceptance, queue and driver semantics by a human.
            if len(usable) > 1:
                first, last = usable[0], usable[-1]
                item['audio']['raw_pointer_delta_bytes_mod_2_32'] = (
                    int(last['ptr_bytes']) - int(first['ptr_bytes'])) & 0xffffffff
                item['audio']['pointer_sample_interval_ns'] = int(last['begin_ns']) - int(first['begin_ns'])
        pipelines.append(item)
    return {'version': 'lab1', 'simulated': simulated,
            'complete': any(r['event'] == 'run_end' and r['status'] == 'complete' for r in records),
            'kernels': kernels, 'pipelines': pipelines,
            'limits': ['Synthetic CPU/tiles do not establish whole-game speed.',
                       'Vendor flip completion is not optical panel cadence.',
                       'GETODELAY zero and write gaps are not measured xruns.',
                       'GETOPTR is unqualified raw data, not yet a scheduling clock.',
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
