"""Interpret a physical cost1 return without promoting partial kernels to a gate.

Raw captures remain untouched. All clocks/loop overhead stay included. Census
counts are emulated work, never QEMU performance. The numerical warm scenario
is conditional on the unmeasured removed-entry mix and longer candidate spans.
"""
from pathlib import Path
from hashlib import sha256
import argparse
import csv
import json
import math
import re
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
args = parser.parse_args()
out = args.directory
subprocess.run([sys.executable, str(ROOT / 'build/analyze-a7-cost.py'), str(out)], check=True,
               stdout=subprocess.DEVNULL)
base = json.loads((out / 'unit-cost-analysis.json').read_text())
assert base['hardware_measured'] and not base['contracts_only']
KINDS = list(base['unit_paths'])

def dist(values):
    if not values:
        return None
    s = sorted(values)
    return dict(n=len(s), mean=statistics.mean(s), median=statistics.median(s),
                p95=s[math.ceil(.95 * len(s)) - 1], p99=s[math.ceil(.99 * len(s)) - 1],
                min=s[0], max=s[-1])

def mean(values):
    return statistics.mean(list(values))

def session(path):
    return dict(l.split('=', 1) for l in path.read_text().splitlines() if '=' in l)

def census(path):
    result = []
    for line in path.read_text().splitlines():
        f = line.split()
        assert f[:2] == ['CENSUS', f'frame={len(result)+1}']
        result.append(list(map(int, f[2:])))
    assert len(result) == 1200 and all(len(r) == 128 for r in result)
    return result

baseline_path = ROOT / 'build/magitek-lazy-candidate-private/census.txt'
candidate_path = ROOT / 'build/ff6-window-batch-private/census.txt'
baseline = census(baseline_path)
candidate = census(candidate_path)
captures = []
all_rows = {}
pcm_rows = []
for capture in base['captures']:
    name = capture['directory']
    path = out / name
    rows = [{k: int(v) if k != 'type' else v for k, v in r.items()}
            for r in csv.DictReader(l for l in (path / 'unit-cost.csv').read_text().splitlines()
                                   if not l.startswith('#'))]
    by_frame = {}
    for r in rows:
        by_frame.setdefault(r['frame'], {}).setdefault(r['type'], []).append(r)
    all_rows[name] = by_frame
    report = session(path / 'last-session.txt')
    complete = int(report['video_submitted'])
    assert complete <= len(by_frame) <= complete + 1
    assert report['build_version'] == '1.19-cost1' and report['core_crc32'] == 'b5aa1b93'
    alignment = {'ppu_entry_mismatches': [], 'row_request_total_mismatches': [],
                 'color_cache_split_mismatches': 0, 'effect_miss_delta_values': set()}
    for f, record in by_frame.items():
        c = record['counts'][0]
        if c['iterations'] != baseline[f][0]:
            alignment['ppu_entry_mismatches'].append(f)
        if c['shape'] + c['warm'] != baseline[f][46] + baseline[f][47]:
            alignment['row_request_total_mismatches'].append(f)
        if (c['shape'], c['warm']) != (baseline[f][46], baseline[f][47]):
            alignment['color_cache_split_mismatches'] += 1
        if 277 <= f <= 438:
            alignment['effect_miss_delta_values'].add(c['shape'] - baseline[f][46])
    alignment['effect_miss_delta_values'] = sorted(alignment['effect_miss_delta_values'])
    assert not alignment['ppu_entry_mismatches'] and not alignment['row_request_total_mismatches']
    common = [by_frame[f]['frame'][0] for f in range(277, min(285, complete))]
    assert len(common) == 8
    timers = [r for r in rows if r['type'] == 'timer_control' and r['cpu_ns']]
    benches = [r for r in rows if r['type'] == 'bench']
    capture.update(successful_complete_calls=complete, terminal_call_excluded=len(by_frame) > complete,
                   effect_successful_calls=max(0, min(complete, 439) - 277),
                   effect_frame_last=complete - 1, alignment=alignment,
                   common_277_284={k: dist([r[k] / 1000 for r in common])
                                   for k in ('cpu_ns', 'wall_ns', 'observer_ns')},
                   timer_control_cpu_us_per_clock=dist([r['cpu_ns'] / 64 / 1000 for r in timers]),
                   unit_paths={KINDS[k]: {str(n): dist([r['cpu_ns'] / n / 1000 for r in benches
                                                      if r['kind'] == k and r['iterations'] == n])
                                          for n in (1, 32)} for k in range(13)},
                   native_quota_percent=100 * int(report['native_audio_frames']) / len(by_frame) / 534.688402,
                   error=report['error'], pcm_state=int(report['pcm_state']),
                   xrun_count=int(report['xrun_count']),
                   worker_cpu_us={k: int(report[k]) / 1000 for k in ('audio_worker_cpu_ns', 'display_worker_cpu_ns')})
    lines = (path / 'pcm-full.txt').read_text().splitlines()
    meta = dict(l.split('=', 1) for l in lines[1:] if '=' in l and not l.startswith(('seq=', '<')))
    events = []
    for line in lines:
        if line.startswith('seq='):
            event = dict(word.split('=', 1) for word in line.split())
            event = {k: v if k == 'op' else int(v) for k, v in event.items()}
            events.append(event)
    assert int(meta['retained_from']) == 0 and len(events) == int(meta['entries_total'])
    assert [e['seq'] for e in events] == list(range(len(events)))
    syncs = [e for e in events if e['op'] == 'SYNC_OK' and e['state'] == 3]
    first_bad = next((e for e in syncs if e['appl'] != e['xfer']), None)
    trusted = [e for e in syncs if first_bad is None or e['seq'] < first_bad['seq']]
    assert trusted and all(e['appl'] == e['xfer'] and e['epoch'] == 1 for e in trusted)
    origin = trusted[0]
    low = 0
    max_drawdown = 0
    last_deficit = 0
    for e in syncs:
        valid = first_bad is None or e['seq'] < first_bad['seq']
        elapsed = (e['ns'] - origin['ns']) / 1e9
        produced = e['xfer'] - origin['xfer']
        demand = 44100 * elapsed
        deficit = e['hw'] - origin['hw'] - produced
        if valid:
            low = min(low, deficit)
            max_drawdown = max(max_drawdown, deficit - low)
            last_deficit = deficit
        pcm_rows.append(dict(capture=name, seq=e['seq'], elapsed_ms=elapsed * 1000,
                             produced_frames=produced, nominal_demand_frames=demand,
                             hw_demand_frames=e['hw'] - origin['hw'],
                             reported_queued=e['queued'], accepted_minus_hw=e['xfer'] - e['hw'],
                             appl_minus_accepted=e['appl'] - e['xfer'], pointer_trusted=int(valid)))
    fault = next((e for e in events if e['op'] == 'SYNC_OBSERVE'), None)
    # Native PCM records use the failing operation name as the op.
    if fault is None:
        fault = next((e for e in events if e['result'] == -77), None)
    assert fault is not None
    capture['pcm_history'] = dict(events=len(events), retained_from=0, complete_until_fault=True,
                                 complete_effect_and_recovery=False, fault=fault,
                                 first_pointer_divergence=first_bad,
                                 min_trusted_reserve=min(e['xfer'] - e['hw'] for e in trusted),
                                 max_trusted_reserve=max(e['xfer'] - e['hw'] for e in trusted),
                                 trusted_peak_to_trough_frames=max_drawdown,
                                 net_trusted_consumption_minus_production=last_deficit,
                                 provisional_partial_reserve_lower_bound_frames=max_drawdown + 864)
    if capture['metadata']['mode'] == '0':
        start = by_frame[277]['checkpoint'][0]['cpu_ns']
        stop = by_frame[complete]['checkpoint'][0]['cpu_ns']
        seconds = (stop - start) / 1e9
        nominal_frames = (complete - 277) * 735.947520
        capture['successful_effect_prefix_cadence'] = dict(
            calls=complete - 277, elapsed_ms=seconds * 1000,
            nominal_output_frames=nominal_frames, nominal_output_hz=nominal_frames / seconds,
            nominal_demand_minus_output_frames=44100 * seconds - nominal_frames,
            boundary='kernel before-call timestamps; quota-based model, not accepted-write anchors')
    captures.append(capture)

for phase in base['phase_runs']:
    c = next(c for c in captures if c['directory'] == phase['capture'])
    phase['terminal_call'] = phase['frame'] >= c['successful_complete_calls']
    phase['setup_quotient_is_removable_e'] = False
    frame = all_rows[phase['capture']][phase['frame']]
    phase['phase_region_entries'] = {str(r['kind']): r['iterations'] for r in frame['phase']}
    phase['clock_calls'] = frame['counts'][0]['cpu_ns']
    phase['sampled_misses'] = frame['row_sampling'][0]['iterations']
    phase['sampled_hits'] = frame['row_sampling'][0]['shape']

mode2 = [c for c in captures if c['metadata']['mode'] == '2']
including_terminal_units = json.loads(json.dumps(base['unit_paths']))
for c in mode2:
    c['unit_paths_including_terminal'] = c['unit_paths']
    benches = [r for f, frame in all_rows[c['directory']].items()
               if f < c['successful_complete_calls'] for r in frame.get('bench', [])]
    c['unit_paths'] = {KINDS[k]: {str(n): dist([r['cpu_ns'] / n / 1000 for r in benches
                                              if r['kind'] == k and r['iterations'] == n])
                                for n in (1, 32)} for k in range(13)}
for k, label in enumerate(KINDS):
    complete_benches = []
    terminal_benches = []
    for c in mode2:
        for f, frame in all_rows[c['directory']].items():
            target = complete_benches if f < c['successful_complete_calls'] else terminal_benches
            target.extend(r for r in frame.get('bench', []) if r['kind'] == k)
    for width in (1, 32):
        data = [r for r in complete_benches if r['iterations'] == width]
        base['unit_paths'][label]['distributions_by_batch_width'][str(width)] = dict(
            samples=len(data), timed_iterations=len(data) * width,
            cpu_us_per_operation=dist([r['cpu_ns'] / width / 1000 for r in data]),
            wall_us_per_operation=dist([r['wall_ns'] / width / 1000 for r in data]))
    base['unit_paths'][label]['shapes_observed'] = sorted({r['shape'] for r in complete_benches})
    base['unit_paths'][label]['terminal_observations_excluded_from_model'] = len(terminal_benches)
path_totals = [0] * 13
entry_total = 0
frame_total = 0
for c in mode2:
    frames = all_rows[c['directory']]
    for f in range(277, min(c['successful_complete_calls'], 439)):
        entry_total += frames[f]['counts'][0]['iterations']
        frame_total += 1
        for r in frames[f]['calls']:
            path_totals[r['kind']] += r['iterations']
weights = [n / entry_total for n in path_totals[:5]]
helpers = {KINDS[k]: path_totals[k] / frame_total for k in range(7, 11)}
helpers['mask_reset'] = 1  # Four diagnostic reset batches represent one production reset.
deferral_shapes = {}
for c in mode2:
    for frame in all_rows[c['directory']].values():
        for r in frame.get('bench', []):
            if r['kind'] == 8 and r['iterations'] == 32:
                deferral_shapes.setdefault(r['shape'], []).append(r['cpu_ns'] / 32 / 1000)
scenarios = {}
for statistic in ('mean', 'median', 'p95', 'p99'):
    units = {k: v['distributions_by_batch_width']['32']['cpu_us_per_operation'][statistic]
             for k, v in base['unit_paths'].items()}
    e = sum(weights[k] * units[KINDS[k]] for k in range(5))
    r = units['row_materialization_payload']
    b = sum(n * units[k] for k, n in helpers.items())
    credit = 106.246914 * e
    debit = 1423.919753 * r
    S0, S = credit - debit, credit - debit - b
    T = base['scorecard']['production_cadence_proxy_us']
    P = 735.947520 / ((T - S) / 1e6)
    scenarios[statistic] = dict(e_warm_us=e, r_payload_us=r, b_short_shadow_us=b,
                               setup_credit_us=credit, extra_row_debit_us=debit,
                               S_if_b_zero_us=S0, S_with_short_shadow_us=S,
                               late_deadline_remaining_us=1514.283 - S,
                               required_e_if_b_zero_us=(1514.283 + debit) / 106.246914,
                               required_e_with_short_shadow_us=(1514.283 + debit + b) / 106.246914,
                               conditional_production_hz=P, conditional_deficit_hz=44100 - P,
                               conditional_production_hz_if_b_zero=735.947520 / ((T - S0) / 1e6),
                               pcm_cadence_remaining_saving_us=base['scorecard']['saving_to_close_that_pcm_cadence_us'] - S,
                               conditional_pcm_cadence_us=T - S,
                               conditional_late_core_and_admission_us=18202.4375 - S)
controls = [c for c in captures if c['metadata']['mode'] == '0' and c['directory'] != 'pass-00-mode-0']
comparisons = []
for c in captures:
    if c['metadata']['mode'] not in ('1', '2'):
        continue
    frames = all_rows[c['directory']]
    for f in (277, 285) if c['metadata']['mode'] == '1' else range(277, 285):
        if f >= c['successful_complete_calls']:
            continue
        actual = frames[f]['frame'][0]
        reference = [all_rows[ref['directory']][f]['frame'][0] for ref in controls]
        # This compares live runs; it does not subtract a timer calibration.
        comparisons.append(dict(capture=c['directory'], frame=f,
                                cpu_growth_us=actual['cpu_ns'] / 1000 - mean(r['cpu_ns'] / 1000 for r in reference),
                                wall_growth_us=actual['wall_ns'] / 1000 - mean(r['wall_ns'] / 1000 for r in reference)))

result = dict(version='cost1-physical-return-analysis-1', gate='NOT MET', card_writes=0,
              captures=captures, unit_paths=base['unit_paths'], phase_runs=base['phase_runs'],
              unit_paths_including_terminal=including_terminal_units,
              phase_distributions=base['phase_distributions'],
              phase_distributions_by_terminal={str(terminal): {
                  label: dist([p['phases_us'][label] for p in base['phase_runs']
                               if p['terminal_call'] == terminal])
                  for label in base['phase_distributions']} for terminal in (False, True)},
              dense_phase_samples=sum(p['dense'] for p in base['phase_runs']),
              frequency='unavailable: all before/after readings -1; governor ENOENT; no pin',
              timer_calibration_subtracted=False,
              observer_comparisons=comparisons,
              observer_growth_distributions={mode: {k: dist([r[k] for r in comparisons
                                                             if next(c for c in captures if c['directory'] == r['capture'])['metadata']['mode'] == mode])
                                                    for k in ('cpu_growth_us', 'wall_growth_us')}
                                             for mode in ('1', '2')},
              scorecard=dict(base['scorecard'], gate_complete_e_r_b_measured=False,
                             observed_baseline_subpath_weights=weights,
                             observed_short_span_helper_calls_per_frame=helpers,
                             modeled_complete_benchmark_frames=frame_total,
                             deferral_cpu_us_by_short_span={str(k): dist(v) for k, v in sorted(deferral_shapes.items())},
                             conditional_warm_scenarios=scenarios,
                             scenario_limits=[
                                 'Only frames277..286 complete in benchmarks; the162-call effect is not measured.',
                                 'Baseline subpath mix is a hypothesis for removed entries, not candidate weighting.',
                                 'Warm materialization payload includes timers; full incremental cache cost is not measured.',
                                 'Short baseline pending spans underprice longer candidate deferral scans.',
                                 'Model excludes changed band population and whole-candidate cache interactions.',
                                 'p95/p99 columns combine marginal batch-mean quantiles, not a saving confidence interval.',
                                 'CPU service saving is hypothetically treated as wall saving; contention may change that mapping.',
                                 'The Focus1 production cadence is another encounter and cannot be qualified by this replay.']),
              private_census_input_hashes={p.relative_to(ROOT).as_posix(): sha256(p.read_bytes()).hexdigest()
                                          for p in (baseline_path, candidate_path)},
              predictions=[
                  'The measured warm fixed work alone does not close the known deadline or PCM deficit.',
                  'A production pass based on the full raw setup/entry quotient would credit observer clocks.',
                  'A similarly instrumented replay is expected to stop before frame320, so repeating it cannot obtain the dense sample.',
                  'A viable candidate needs additional measured savings outside the currently priced fixed setup, or materially cheaper added work.',
                  'Compositor/cache study targets the large PPU remainder, but this return cannot isolate pure pixel or full color cost.'])
(out / 'return-analysis.json').write_text(json.dumps(result, indent=2) + '\n')
with (out / 'reserve-curve.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(pcm_rows[0]))
    writer.writeheader()
    writer.writerows(pcm_rows)
print(json.dumps(dict(captures=len(captures), all_failed=all(c['metadata']['failed'] == '1' for c in captures),
                      dense_phase_samples=result['dense_phase_samples'],
                      warm_mean_scenario=scenarios['mean'], gate=result['gate']), indent=2))
