"""Price audio reserve from the returned A7 trace and exact per-tick sample quota."""
import argparse
import csv
import json
from pathlib import Path
import statistics
import struct


PERIOD_NS = 16_688_155
SINK_HZ = 44_100
PRIME = 2823
VENDOR_GUARD = 256


def csv_rows(path):
    with path.open() as stream:
        return list(csv.DictReader(line for line in stream if not line.startswith('#')))


def cumulative_output(count):
    # The first input establishes the interpolator's previous sample.
    return (max(0, count-1)*245+177)//178


def reserve(times, source_counts):
    elapsed = source = delivered = 0
    low = peak = drawdown = 0.0
    peak_tick = 0
    for tick, (duration, samples) in enumerate(zip(times, source_counts, strict=True)):
        elapsed += duration
        # Publish the complete tick's quota at the end of the tick. This models
        # arrivals, including the final tick, without credit for sub-tick writes.
        demand = elapsed*SINK_HZ/1e9
        deficit = demand-delivered
        if deficit > peak:
            peak, peak_tick = deficit, tick
        drawdown = max(drawdown, deficit-low)
        source += samples
        delivered = cumulative_output(source)
        low = min(low, demand-delivered)
    return dict(mean_step_ns=elapsed/len(times), relative_throughput=PERIOD_NS/(elapsed/len(times)),
                peak_initial_deficit_frames=round(peak, 3), peak_tick=peak_tick,
                refill_limited_drawdown_frames=round(drawdown, 3),
                final_deficit_frames=round(elapsed*SINK_HZ/1e9-delivered, 3),
                model_prime_minus_peak_and_vendor_guard_frames=round(PRIME-peak-VENDOR_GUARD, 3))


def report(core_csv, native_csv, oracle):
    samples = list(struct.iter_unpack('<III', oracle.read_bytes()))
    assert len(samples)==1200
    changes = [True]+[a[0]!=b[0] for a,b in zip(samples,samples[1:])]
    source_counts = [n for _,_,n in samples]
    rows = [list(map(int, line.split(','))) for line in core_csv.read_text().splitlines()
            if line.split(',', 1)[0].isdigit()]
    assert [row[0] for row in rows]==list(range(1200))
    core_wall = [row[4]-row[6] for row in rows]
    native = [row for row in csv_rows(native_csv) if row['pointer_valid']=='1' or row['state']=='3']
    assert [int(row['frame']) for row in native]==list(range(len(native))) and len(native)==13
    actual_steps = [int(row['step_ns']) for row in native]
    opening_extra = statistics.mean(actual_steps)-statistics.mean(core_wall[:len(native)])
    scenarios = []
    for extra in (0, 500_000, 1_000_000, 1_500_000, round(opening_extra)):
        for name, repeat_saving, comparison in (
                ('original', 0, 0), ('reuse_low', 500_000, 100_000),
                ('reuse_mid', 1_000_000, 100_000), ('reuse_high', 1_630_000, 100_000)):
            additions = [extra+comparison-(0 if change else repeat_saving) for change in changes]

            def model(saving):
                times = [cost*(1-saving)+addition for cost, addition in zip(core_wall, additions, strict=True)]
                return reserve(times,source_counts)

            def fits(result):
                return (result['final_deficit_frames']<=0 and
                        result['refill_limited_drawdown_frames']<=PRIME-VENDOR_GUARD)

            baseline = model(0)
            low, high = 0.0, 0.5
            assert fits(model(high))
            if not fits(baseline):
                for _ in range(18):
                    middle = (low+high)/2
                    if fits(model(middle)):
                        high = middle
                    else:
                        low = middle
            else:
                high = 0.0
            scenarios.append(dict(case=name, extra_ns=extra, saving_per_repeat_ns=repeat_saving,
                                  compare_per_tick_ns=comparison, **baseline,
                                  required_uniform_core_wall_reduction_percent=round(high*100,3),
                                  sensitivity_at_eight_percent_core_wall_reduction=model(.08)))
    return dict(native_tick_ns=PERIOD_NS, native_sink_hz=SINK_HZ, source_frames=sum(source_counts),
                converted_frames=cumulative_output(sum(source_counts)), repeats=changes.count(False),
                opening_native_steps=len(native), opening_native_step_mean_ns=statistics.mean(actual_steps),
                opening_headless_wall_mean_ns=statistics.mean(core_wall[:len(native)]),
                opening_native_minus_headless_mean_ns=opening_extra,
                full_headless_wall_mean_ns=statistics.mean(core_wall),
                mean_overhead_budget_ns=PERIOD_NS-statistics.mean(core_wall),
                vendor_guard_frames=VENDOR_GUARD, prime_frames=PRIME, scenarios=scenarios)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for field in ('core_csv', 'native_csv', 'oracle'):
        parser.add_argument(field,type=Path)
    args=parser.parse_args()
    print(json.dumps(report(args.core_csv,args.native_csv,args.oracle),indent=2))
