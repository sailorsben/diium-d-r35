"""Price the returned Star Fox burst and decode the vendor's PCM constraints."""
import argparse
from hashlib import sha256
from importlib import import_module
import json
import math
from pathlib import Path
import re
import statistics
import struct


native = import_module('report-snes-native-reserve')
KERNEL_BASE = 0xc0008000
KERNEL_HASH = '21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321'
DMA_HARDWARE = 0xc0549d80
PCM_FIELDS = ('info', 'formats_low', 'formats_high', 'rates_mask', 'rate_min',
              'rate_max', 'channels_min', 'channels_max', 'buffer_bytes_max',
              'period_bytes_min', 'period_bytes_max', 'periods_min', 'periods_max')


def pcm_constraints(kernel):
    data = kernel.read_bytes()
    assert sha256(data).hexdigest() == KERNEL_HASH
    # ARM EABI places the 64-bit formats field at +8, after 4 bytes of padding.
    values = struct.unpack_from('<I4x12I', data, DMA_HARDWARE - KERNEL_BASE)
    limits = dict(zip(PCM_FIELDS, values, strict=True))
    # Linux 4.19's SNDRV_PCM_RATE_* bits 0 through 12.
    rates = (5512, 8000, 11025, 16000, 22050, 32000, 44100, 48000,
             64000, 88200, 96000, 176400, 192000)
    return dict(kernel_sha256=KERNEL_HASH, hardware_address=hex(DMA_HARDWARE),
                **limits, rates=[rate for i, rate in enumerate(rates) if limits['rates_mask'] & (1 << i)],
                s16_stereo_ring_frames_ceiling=limits['buffer_bytes_max'] // 4)


def durations(path):
    rows = native.csv_rows(path)
    return [int(row['step_ns']) - int(row['pace_wait_ns']) for row in rows]


def candidate(times, samples, guard, period, available=None):
    model = native.reserve(times, samples)
    needed = model['refill_limited_drawdown_frames']
    return dict(mean_service_ms=round(statistics.mean(times) / 1e6, 4),
                prime_frames=math.ceil(needed) + guard,
                reserve_ms=round((needed + guard) * 1000 / native.SINK_HZ, 3),
                ring_frames_rounded=math.ceil((needed + guard + period) / period) * period,
                margin_at_selected_prime_frames=None if available is None else round(available - guard - needed, 3),
                **{k: model[k] for k in ('peak_initial_deficit_frames', 'peak_tick',
                                        'refill_limited_drawdown_frames', 'final_deficit_frames')})


def savings_for_budget(times, samples, available, guard, per_tick_cost):
    def fits(saving):
        result = native.reserve([t + per_tick_cost - saving for t in times], samples)
        return (result['refill_limited_drawdown_frames'] <= available - guard and
                result['final_deficit_frames'] <= 0)

    low, high = 0.0, 5_000_000.0
    if fits(low):
        return 0.0
    assert fits(high)
    for _ in range(24):
        middle = (low + high) / 2
        if fits(middle):
            high = middle
        else:
            low = middle
    return round(high / 1e6, 4)


def report(reuse, control, native_reuse, native_control, oracle, kernel):
    fixture = list(struct.iter_unpack('<III', oracle.read_bytes()))
    source = [samples for _, _, samples in fixture]
    repeated = [False] + [a[0] == b[0] for a, b in zip(fixture, fixture[1:])]
    reuse_times, control_times = durations(reuse), durations(control)
    assert len(source) == len(reuse_times) == len(control_times) == 1200
    observed_extra = {}
    for name, path, silent in (('reuse', native_reuse, reuse_times),
                               ('control', native_control, control_times)):
        playback = native.csv_rows(path)
        rows = [row for row in playback if row['pointer_valid'] == '1' and row['state'] == '3']
        n = len(rows)
        assert [int(row['frame']) for row in rows] == list(range(n)) and n > 0
        observed_extra[name] = dict(ticks=n,
            step_minus_silent_ms=round((statistics.mean(int(row['step_ns']) for row in rows) -
                                       statistics.mean(silent[:n])) / 1e6, 4))

    extras = (0, 500_000, 1_000_000, 1_500_000)
    primes = (2823, 4410, 6615, 8820, 16_384, 20_480, 24_576)
    reserve = []
    for extra in extras:
        prices = [t + extra for t in reuse_times]
        reserve.append(dict(assumed_native_extra_ms=extra / 1e6,
            sizing=candidate(prices, source, 1024, 512, 20_480),
            required_constant_saving_ms={prime: savings_for_budget(reuse_times, source, prime,
                256 if prime < 16_384 else 1024, extra) for prime in primes},
            forecast_for_150ms_prime={saving / 1e6: candidate([t - saving for t in prices], source, 256, 128, 6615)
                                     for saving in (800_000, 1_000_000, 1_300_000)}))

    repeat_only = []
    for saving in (0.5, 1.0, 1.5, 2.0, 3.0):
        cost = [t + 1_000_000 - int(r * saving * 1e6) for t, r in zip(reuse_times, repeated, strict=True)]
        repeat_only.append(dict(saving_per_repeat_ms=saving, **candidate(cost, source, 256, 128, 2823)))
    return dict(pcm=pcm_constraints(kernel), repeat_ticks=sum(repeated), matched_native_prefix=observed_extra,
                silent_control=candidate(control_times, source, 256, 128, 2823),
                silent_reuse=candidate(reuse_times, source, 256, 128, 2823),
                native_sensitivity=reserve, repeat_only_with_1ms_native_extra=repeat_only)


def replay_summary(folder):
    core = sha256((folder / 'candidate.so').read_bytes()).hexdigest()
    assert core == sha256((folder / 'control.so').read_bytes()).hexdigest()
    games = []
    for index in range(5):
        prefix = f'{index:03}'
        timing = folder / f'{prefix}-time.log'
        proof = folder / f'{prefix}-verify.log'
        if not timing.exists():
            timing = folder / f'{index}-time.log'
            proof = folder / f'{index}-verify.log'
        text = proof.read_text()
        assert 'published=1200' in text and 'verified=1200 mismatched=0' in text
        rows = [tuple(map(int, line.split(','))) for line in timing.read_text().splitlines()
                if line.split(',', 1)[0].isdigit()]
        assert [i for i, _, _ in rows] == list(range(1200))
        _, control, candidate = zip(*rows)

        def saving(a, b):
            return round((1 - b / a) * 100, 3)

        summary = dict(game_index=index, source_identity_checks=1200,
                       mean_control_ns=round(statistics.mean(control)), mean_candidate_ns=round(statistics.mean(candidate)),
                       mean_saving_pct=saving(sum(control), sum(candidate)),
                       p95_saving_pct=saving(sorted(control)[1139], sorted(candidate)[1139]),
                       quarter_mean_saving_pct=[saving(sum(control[i:i+300]), sum(candidate[i:i+300]))
                                                for i in range(0, 1200, 300)],
                       timing_sha256=sha256(timing.read_bytes()).hexdigest(),
                       verification_sha256=sha256(proof.read_bytes()).hexdigest())
        span = re.search(r'(?:span|mode2)_key calls=(\d+) eligible=(\d+) rows=(\d+) hits=(\d+) hit_rows=(\d+)', text)
        if span:
            summary['span_counts'] = dict(zip(('calls', 'eligible', 'rows', 'hits', 'hit_rows'),
                                              map(int, span.groups()), strict=True))
        games.append(summary)
    result = dict(identical_control_and_candidate_sha256=core, arm_under_qemu=True, games=games)
    if (folder / 'heldout-candidate.identity').is_file():
        checks = {}
        for name, lines in (('canonical', 42), ('heldout', 1242)):
            output = (folder / f'{name}-candidate.identity').read_bytes()
            assert output == (folder / f'{name}-control.identity').read_bytes()
            assert len(output.splitlines()) == lines
            checks[name] = dict(normalized_state_checks=41, output_and_pcm_checks=1200,
                                callback_layout_matches=True, identity_sha256=sha256(output).hexdigest())
        result['star_fox_separate_process_checks'] = checks
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('reuse', 'control', 'native_reuse', 'native_control', 'oracle', 'kernel'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--pair', nargs=2, metavar=('EXPERIMENT', 'OUTPUT'), action='append', default=[])
    args = vars(parser.parse_args())
    pairs = args.pop('pair')
    results = report(**args)
    if pairs:
        results['offline_experiments'] = {name: replay_summary(Path(folder)) for name, folder in pairs}
    print(json.dumps(results, indent=2))
