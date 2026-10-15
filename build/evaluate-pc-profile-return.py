"""Evaluate an archived unchanged-core PC diagnostic; never modify the card."""
from pathlib import Path
from hashlib import sha256
from collections import Counter
import bisect, csv, importlib.util, json, os, re, runpy, statistics, subprocess, sys

ROOT = Path(__file__).resolve().parent.parent
CORE = '1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8'
ROM = 'f61af2bd9e3f9b6a2bd543fb176af0b81fd9e5ba4ea0fa0f453371ccb45d3911'

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def kv(p):
    return dict(l.split('=', 1) for l in p.read_text().splitlines() if '=' in l)

def rows(p):
    return list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')))

def mean_ms(data, key):
    return statistics.mean(int(r[key]) for r in data) / 1e6 if data else None

def symbol_census(base, plan, records, classify):
    """Retain all symbol owners and a broader heavy prefix, without time estimates."""
    core = base / 'cores/demand.so'
    command = ['arm-linux-gnueabihf-nm', '-S', '--defined-only', str(core)]
    if os.name == 'nt':
        path = subprocess.check_output(['wsl', 'wslpath', '-a', core.as_posix()], text=True).strip()
        command = ['wsl', 'arm-linux-gnueabihf-nm', '-S', '--defined-only', path]
    symbols = []
    for line in subprocess.check_output(command, text=True).splitlines():
        fields = line.split()
        if len(fields) == 4 and fields[2] in ('t', 'T') and int(fields[1], 16):
            symbols.append((int(fields[0], 16), int(fields[1], 16), fields[3]))
    symbols.sort()
    starts = [s[0] for s in symbols]
    def owner(offset):
        if offset == 0xffffffff:
            return 'OUTSIDE_CORE'
        i = bisect.bisect_right(starts, offset) - 1
        return symbols[i][2] if i >= 0 and offset < symbols[i][0] + symbols[i][1] else 'UNMAPPED_CORE'
    result = []
    for run in plan['runs']:
        if not run['PC_sampling']:
            continue
        data = rows(base / f"run-{run['run']:03d}/main-pc.csv")
        valid = records[run['run']]
        selected = [(int(r['frame']), owner(int(r['ELF_offset'], 16))) for r in data if int(r['frame']) in valid]
        functions = Counter(name for _, name in selected)
        spans = {}
        for label, wanted in (('warm_valid_prefix', range(120, len(valid))),
                              ('common_heavy_prefix_384_487', range(384, 488)),
                              ('heavy_384_575', range(384, 576))):
            hits = Counter(name for frame, name in selected if frame in wanted)
            grouped = Counter()
            for name, count in hits.items():
                grouped['unmapped_core' if name == 'UNMAPPED_CORE' else classify(name)] += count
            spans[label] = {'samples': sum(hits.values()), 'functions': hits.most_common(), 'owners': dict(grouped),
                            'all_requested_frames_valid': all(i in valid for i in wanted),
                            'selected_frame_start': max(120 if label == 'warm_valid_prefix' else 384, 0),
                            'selected_frame_end': min(wanted.stop, len(valid)) - 1,
                            'sparse_below100': sum(hits.values()) < 100}
        result.append({'run': run['run'], 'name': run['name'], 'valid_prefix_frames': len(valid),
                       'selected_samples': len(selected), 'all_functions': functions.most_common(), 'spans': spans})
    return result

def main(archive, live=False):
    archive = archive.resolve()
    assert archive.is_relative_to(ROOT / 'device-evidence')
    a = json.loads((archive / 'archive.json').read_text())
    assert a['fat_clean'] and a['card_writes'] == 0
    for e in a['all_retro_files']:
        assert digest(archive / e['path']) == e['sha256'], e['path']
    base = archive / 'retro/snes-pc-profile1'
    install_path = ROOT / 'evidence/2026-10-14/pc-profile/installation.json'
    inst = json.loads(install_path.read_text())
    for n, h in inst['payload_hashes'].items():
        assert digest(base / n) == h, n
    assert digest(base / 'cores/demand.so') == digest(base / 'cores/reference.so') == CORE
    assert digest(archive / 'retro/snes-mvp/launch.sh') == inst['dispatch_sha256']
    assert (base / 'last-launch').read_bytes() == b'SNES pc-profile1 automatic18-context test, all frames; experimental\n'
    assert not list((archive / 'retro').rglob('armed'))
    assert not (archive / 'retro/update/Code.bkp').exists()
    before = json.loads((ROOT / 'device-evidence' / inst['archive'] / 'archive.json').read_text())
    unchanged, changed = 0, []
    for e in before['all_retro_files']:
        if e['path'] == 'retro/snes-mvp/launch.sh':
            continue
        if (archive / e['path']).is_file() and digest(archive / e['path']) == e['sha256']:
            unchanged += 1
        else:
            changed.append(e['path'])
    assert not [n for n in changed if n != 'retro/swapfile'], changed
    spec = importlib.util.spec_from_file_location('pc_return_guard', ROOT / 'build/package-snes-1.19.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    protected = {**guard.BOOT_EXPECTED, 'retro/init': guard.baseline.HOOK,
                 'retro/snes-mvp/plus-a7.so': '80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'}
    for n, h in protected.items():
        assert digest(archive / n) == h, n
    rom_hash = None
    if live:
        card = Path('I:/')
        assert not list((card / 'retro').rglob('armed'))
        for n, h in protected.items():
            assert digest(card / n) == h, n
        for n, h in inst['payload_hashes'].items():
            assert digest(card / 'retro/snes-pc-profile1' / n) == h, n
        rom_hash = digest(card / '002/Final Fantasy VI.zip')
        assert rom_hash == ROM
    plan = json.loads((base / 'plan.json').read_text())
    assert plan['version'] == '1.19-pc-profile1' and len(plan['runs']) == 4
    assert not plan['frameskip'] and plan['measurement_only']
    suite = kv(base / 'suite-result.txt')
    assert suite['runs'] == suite['planned'] == '4' and suite['stopped'] == '0'
    log = (base / 'startup.log').read_text()
    assert 'display worker joined' in log and 'FreeVFB returned' in log
    reports, records, inputs = [], {}, [archive / 'archive.json', install_path, Path(__file__).resolve(),
                                       ROOT / 'build/analyze-main-pc.py', base / 'plan.json',
                                       base / 'suite-result.txt', base / 'startup.log']
    for run in plan['runs']:
        folder = base / f"run-{run['run']:03d}"
        paths = [folder / n for n in ('begin.txt', 'result.txt', 'frames.csv', 'last-session.txt',
                                      'headroom.txt', 'pcm-full.txt', 'animation.csv')]
        inputs.extend(paths)
        begin, end = kv(paths[0]), kv(paths[1])
        metadata, data, s, h = kv(paths[2]), rows(paths[2]), kv(paths[3]), kv(paths[4])
        assert metadata['#mock'] == s['mock_backend'] == '0', 'Mock telemetry is not physical evidence'
        assert s['audio_backend'] == 'native_alsa'
        identity = (s['core_crc32'] == plan['cores'][run['variant']]['crc32'] and s['build_version'] == plan['version']
                    and begin['run'] == end['run'] == str(run['run']) and begin['fixture'] == str(run['fixture'])
                    and begin['variant'] == run['variant'])
        assert identity, run
        prefix, pa, pv = {}, 0, 0
        for i, r in enumerate(data):
            ca, cv = int(r['audio_worker_cpu_ns']), int(r['video_worker_cpu_ns'])
            if (int(r['frame']) != i or r['pointer_valid'] != '1' or ca < pa or cv < pv
                    or int(r['pace_wait_ns']) > int(r['step_ns'])):
                break
            r['recorded_threads_CPU_ns'] = int(r['main_step_cpu_ns']) + ca - pa + cv - pv
            prefix[i] = r
            pa, pv = ca, cv
        records[run['run']] = prefix
        pcm_path = folder / 'pcm-full.txt'
        pcm, sync, bad = kv(pcm_path), [], []
        boundary, buffer = int(s['pcm_boundary_frames']), int(s['pcm_buffer_frames'])
        pattern = r'seq=(\d+) ns=(\d+) op=(\S+) arg=(\d+) result=(-?\d+) state=(\d+) queued=(\d+) appl=(\d+) hw=(\d+) epoch=(\d+) xfer=(\d+)'
        transactions = list(re.finditer(pattern, pcm_path.read_text()))
        assert len(transactions) == int(pcm['entries_total']) - int(pcm['retained_from'])
        for match in transactions:
            seq, ns, op, arg, rc, state, queued, appl, hw, epoch, xfer = match.groups()
            if op != 'SYNC_OK' or state != '3':
                continue
            good = (boundary > 0 and int(appl) % boundary == int(xfer) % boundary
                    and (int(appl) - int(hw)) % boundary == int(queued) and int(queued) <= buffer)
            if not good:
                bad.append(int(seq))
            elif not bad:
                sync.append({'ns': int(ns), 'queued': int(queued), 'xfer': int(xfer),
                             'hw': int(hw), 'epoch': int(epoch)})
        cumulative = None
        if sync:
            first, last = sync[0], sync[-1]
            assert len({r['epoch'] for r in sync}) == 1
            accepted_growth = (last['xfer'] - first['xfer']) % boundary
            consumed_growth = (last['hw'] - first['hw']) % boundary
            change = last['queued'] - first['queued']
            assert change == accepted_growth - consumed_growth
            cumulative = {'trace_prefix_seconds': (last['ns'] - first['ns']) / 1e9,
                          'initial_observed_reserve_frames': first['queued'],
                          'last_valid_observed_reserve_frames': last['queued'],
                          'accepted_growth_frames': accepted_growth, 'HW_pointer_growth_frames': consumed_growth,
                          'reserve_change_frames': change, 'accounting_identity_exact': True,
                          'scope': 'Complete retained running-sync prefix before the first invalid pointer; vendor logical accounting.'}
        complete = (len(data) == len(prefix) == 1200 and s['runs'] == s['video_submitted'] == s['display_scaled']
                    == s['display_flipped'] == '1200' and s['held'] == s['video_dupes'] == '0'
                    and not s['error'] and end['runner_rc'] == '0')
        accounting = (h['final_PCM_software_accounting_exact'] == '1' and h['final_remaining']
                      == h['final_cleared'] == h['final_audio_error'] == '0')
        joined = end['audio_worker_joined'] == end['display_idle'] == '1'
        effect = int(kv(folder / 'animation.csv').get('#matching_property_samples', '0')) > 0
        clean = complete and accounting and joined and effect and pcm['retained_from'] == '0' and not bad
        warm = [r for i, r in prefix.items() if i >= plan['warmup_calls']]
        windows = [warm[i:i + 16] for i in range(max(0, len(warm) - 15))]
        worst = max(windows, key=lambda w: mean_ms(w, 'recorded_threads_CPU_ns')) if windows else []
        pc_path = folder / 'main-pc.csv'
        if run['PC_sampling']:
            assert pc_path.exists(), run
            inputs.append(pc_path)
        else:
            assert not pc_path.exists(), run
        reports.append({**run, 'identity_verified': identity, 'status': 'CLEAN_BOUNDED_WINDOW' if clean else 'INVALID_OR_INCOMPLETE',
                        'completed_calls': int(s['runs']), 'frame_rows': len(data), 'valid_CPU_prefix_calls': len(prefix),
                        'first_invalid_frame': len(prefix) if len(prefix) < len(data) else None,
                        'submitted': int(s['video_submitted']), 'scaled': int(s['display_scaled']), 'flipped': int(s['display_flipped']),
                        'held': int(s['held']), 'dupes': int(s['video_dupes']), 'error': s['error'],
                        'reported_xruns': int(s['xrun_count']), 'write_errors': int(s['write_errors']),
                        'all_workers_joined': joined, 'effect_properties_observed': effect,
                        'PCM_trace_retained_from': int(pcm['retained_from']), 'PCM_failure': pcm['failure'],
                        'invalid_running_sync_count': len(bad), 'first_invalid_running_sync_sequence': bad[0] if bad else None,
                        'final_pointer_bias_frames': int(s['pcm_appl_ptr']) - int(s['pcm_epoch_transferred_frames']),
                        'valid_prefix_running_sync_samples': len(sync),
                        'valid_prefix_minimum_running_reserve_frames': min((r['queued'] for r in sync), default=None),
                        'cumulative_running_reserve': cumulative,
                        'sink_rate': int(s['sink_rate']), 'PCM_final_software_accounting_exact': accounting,
                        'final_direct_submitted': int(data[-1]['direct_submitted']) if data else None,
                        'final_copied_payload_bytes': int(data[-1]['copied_payload_bytes']) if data else None,
                        'worst16_valid_CPU_frames': [int(r['frame']) for r in worst],
                        'worst16_recorded_threads_CPU_ms': mean_ms(worst, 'recorded_threads_CPU_ns'),
                        'post_last_sample_audio_CPU_ns': int(h['post_last_sample_audio_CPU_ns']),
                        'post_last_sample_video_CPU_ns': int(h['post_last_sample_video_CPU_ns']),
                        'phase_profile_available': int(s['phase_profile_available']),
                        'frequency_values_khz': sorted({int(r[k]) for r in data for k in ('freq_before_khz', 'freq_after_khz')})})
    pc_tool = runpy.run_path(str(ROOT / 'build/analyze-main-pc.py'))
    attribution = pc_tool['analyze'](base, False)
    census = symbol_census(base, plan, records, pc_tool['group'])
    comparisons = []
    for control, sample in ((0, 1), (3, 2)):
        ref, new = records[control], records[sample]
        common = sorted(set(ref) & set(new))
        intervals = {'all_common': common, 'warm_common': [i for i in common if i >= 120],
                     'early': list(range(120, 240)), 'earlier_heavy': list(range(384, 416)),
                     'late_heavy': list(range(496, 536))}
        values = {}
        for label, wanted in intervals.items():
            selected = [i for i in wanted if i in ref and i in new]
            metrics = {key + '_sample_minus_control_ms': statistics.mean(int(new[i][key]) - int(ref[i][key]) for i in selected) / 1e6
                       if selected else None for key in ('cpu_ns', 'main_step_cpu_ns', 'recorded_threads_CPU_ns', 'wall_ns')}
            values[label] = {'calls': len(selected), 'requested_calls': len(wanted), 'interval_complete': selected == wanted,
                             'first_frame': selected[0] if selected else None, 'last_frame': selected[-1] if selected else None, **metrics}
        comparisons.append({'control_run': control, 'sample_run': sample, 'effect': plan['runs'][control]['name'],
                            'intervals': values, 'interpretation': 'Observed disturbance plus run/order variation; one pair, not causal timer calibration.'})
    result = {'version': plan['version'], 'archive': archive.name, 'card_writes': 0, 'FAT_clean': True,
              'archive_files': len(a['all_retro_files']), 'archive_bytes': sum(e['bytes'] for e in a['all_retro_files']),
              'installed_payloads_verified': len(inst['payload_hashes']), 'protected_prior_files_unchanged': unchanged,
              'changed_prior_files': changed, 'ROM_live_sha256': rom_hash, 'marker_consumed': True, 'stock_next_boot': True,
              'same_exact_core_both_variants': True, 'core_sha256': CORE, 'suite': suite, 'epochs': reports,
              'PC_attribution': attribution, 'PC_function_census': census, 'control_sample_comparisons': comparisons,
              'production_gate_passed': False, 'emulator_runtime_changes': False,
              'limits': attribution['limits'] + ['Control/sample comparisons have one pair per effect and reversed order across effects.',
                        'Named PPU buckets are conservative: RenderLine, RenderScreen, WRITE_4PIXELS and some window/geometry helpers remain in core_other. All symbol counts are retained for audit.',
                        'The original classifier includes one Quasar UNMAPPED_CORE sample in core_other; the extended census exposes unmapped_core separately.',
                        'A nominal completion with pointer drift is invalid; no reserve after first drift is certified.',
                        'No independent physical speaker/panel observation was supplied for this diagnostic.',
                        'Recorded CPU excludes other processes and some kernel work; worker residuals remain separate.'],
              'inputs': {p.relative_to(ROOT).as_posix(): digest(p) for p in inputs}}
    target = archive / 'pc-profile-return-evaluation.json'
    target.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'evaluation': str(target), 'epochs': [{k: r[k] for k in ('run', 'status', 'completed_calls', 'first_invalid_frame')} for r in reports],
                      'sampled_runs': len(attribution['runs']), 'protected_files': unchanged, 'changed_prior_files': changed}, indent=2))

if __name__ == '__main__':
    main(Path(sys.argv[1]), '--verify-live' in sys.argv)
