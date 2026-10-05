"""Analyze an archived MVP report without claiming unsampled playback/presents."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import math
import re
import zlib


def analyze(path, core_path=None):
    raw = path.read_bytes()
    fields = {}
    bins = {}
    for line in raw.decode('utf-8').splitlines():
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        match = re.fullmatch(r'core_wall_bin_(\d+)ms', key)
        if match:
            bins[int(match[1])] = int(value)
        else:
            fields[key] = value
    if core_path is not None:
        core = core_path.read_bytes()
        if (fields.get('core_crc32') != f'{zlib.crc32(core) & 0xffffffff:08x}'
                or fields.get('core_bytes') != str(len(core))):
            raise ValueError('Session report does not match the supplied core; '
                             'preserve it as historical evidence, not this run')
    integer = lambda key: int(fields[key])
    runs = integer('runs')
    assert runs > 0 and sum(bins.values()) == runs, 'Incomplete histogram'
    assert integer('held') + integer('video_submitted') == runs
    fps = float(fields['fps'])
    rate = integer('sink_rate')
    period_ms = 1000 / fps

    def percentile(p):
        rank = math.ceil(runs * p)
        cumulative = 0
        for lower, count in sorted(bins.items()):
            cumulative += count
            if cumulative >= rank:
                return {'lower_inclusive_ms': lower,
                        'upper_exclusive_ms': lower + 1 if lower < 127 else None}
        raise AssertionError('Missing percentile')

    definitely_over = sum(count for lower, count in bins.items() if lower > period_ms)
    ambiguous = sum(count for lower, count in bins.items()
                    if lower <= period_ms < lower + 1)
    result = {
        'report_sha256': sha256(raw).hexdigest(),
        'raw_fields': fields,
        'histogram_count': sum(bins.values()),
        'native_period_ms': period_ms,
        'nominal_simulated_seconds_not_measured_elapsed': runs / fps,
        'held_percent': integer('held') * 100 / runs,
        'mean_core_wall_ms_including_callbacks': integer('core_wall_ns') / runs / 1e6,
        'mean_core_thread_cpu_ms_including_callbacks': integer('core_thread_cpu_ns') / runs / 1e6,
        'mean_wall_minus_thread_cpu_ms_not_isolated_display_wait':
            (integer('core_wall_ns') - integer('core_thread_cpu_ns')) / runs / 1e6,
        'mean_video_callback_ms_per_submission':
            integer('video_callback_ns') / integer('video_submitted') / 1e6,
        'mean_audio_callback_ms_per_run': integer('audio_callback_ns') / runs / 1e6,
        'core_thread_cpu_fraction_of_nominal_time_not_actual_utilization':
            integer('core_thread_cpu_ns') / 1e9 / (runs / fps),
        'definitely_over_period_calls': definitely_over,
        'definitely_over_period_percent': definitely_over * 100 / runs,
        'period_straddling_bin_calls': ambiguous,
        'core_wall_percentile_intervals':
            {name: percentile(p) for name, p in (('p50', .5), ('p95', .95), ('p99', .99))},
        'max_core_wall_ms': integer('max_run_ns') / 1e6,
        'max_video_callback_ms': integer('max_video_ns') / 1e6,
        'software_ring_high_percent_of_8192_capacity': integer('software_ring_high_frames') * 100 / 8192,
        'sampled_device_queue_ms': {
            'min': integer('device_queue_min_frames') * 1000 / rate,
            'max': integer('device_queue_max_frames') * 1000 / rate,
        },
        'produced_plus_priming_minus_accepted_frames_not_isolated_loss':
            integer('resampled_enqueued_frames') + integer('priming_silence_frames')
            - integer('output_accepted_frames_including_priming'),
        'limitations': [
            'Adaptive internal drawing makes the mean a mixed workload, not full-render cost.',
            'Core-call CPU includes callbacks; worker/kernel CPU is not included.',
            'Nominal simulated time is not measured gameplay wall duration or achieved speed.',
            'Device queue is sampled once per 60 calls; brief starvation can be missed.',
            'OSS write success is not a hardware underrun count.',
            'Transitions clear/reset audio; reports omit cleared and ending queued frames.',
            'Video submission is not an optical panel presentation count.',
        ],
    }
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--core', type=Path,
                        help='Actual returned core; reject stale session reports')
    args = parser.parse_args()
    try:
        result = analyze(args.report, args.core)
    except ValueError as error:
        parser.error(str(error))
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in (
        'histogram_count', 'held_percent', 'mean_core_wall_ms_including_callbacks',
        'mean_core_thread_cpu_ms_including_callbacks', 'core_wall_percentile_intervals',
        'definitely_over_period_calls', 'definitely_over_period_percent')}, indent=2))
