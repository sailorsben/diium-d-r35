"""Validate the archived physical UART state1 return; never writes the card."""
from pathlib import Path
from hashlib import sha256
from collections import Counter
import json
import sys

ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def fields(line):
    words = line.split()
    pairs = [w.split('=', 1) for w in words if '=' in w]
    result = dict(pairs)
    assert len(result) == len(pairs), 'duplicate fields'
    return result


def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to(ROOT / 'device-evidence')
    metadata = json.loads((archive / 'archive.json').read_text())
    assert metadata['card'] == 'I:' and metadata['fat_clean'] and metadata['card_writes'] == 0
    health = (archive / 'chkdsk-before.txt').read_text()
    assert '11EB-1465' in health and 'Windows has scanned the file system and found no problems.' in health
    entries = {e['path']: e for e in metadata['all_retro_files']}
    assert len(entries) == len(metadata['all_retro_files'])
    for name, entry in entries.items():
        assert digest(archive / name) == entry['sha256'], name
    assert not list((archive / 'retro').rglob('armed'))
    installation_path = ROOT / 'evidence/2026-10-14/uart-state/installation.json'
    install = json.loads(installation_path.read_text())
    base = archive / 'retro/uart-state1'
    for name, expected in install['payload_hashes'].items():
        assert digest(base / name) == expected, name
    assert digest(archive / 'retro/snes-mvp/launch.sh') == install['dispatch_sha256']
    assert (base / 'last-launch').read_bytes() == b'UART state1 snapshot preflight only; no emulator change\n'
    assert (base / 'startup.log').read_text() == 'UART state1 snapshot-only preflight; marker consumed\nowner_exit=0; returning to stock startup\n'
    assert (base / 'owner.err').read_bytes() == b''
    previous = ROOT / 'device-evidence' / install['archive']
    old = json.loads((previous / 'archive.json').read_text())['all_retro_files']
    changed, missing = [], []
    protected = [e for e in old if e['path'] != 'retro/snes-mvp/launch.sh']
    for entry in protected:
        name = entry['path']
        if name not in entries:
            missing.append(name)
        elif entries[name]['sha256'] != entry['sha256']:
            changed.append(name)
    assert not missing and set(changed) <= {'retro/swapfile'}, (changed, missing)
    lines = (base / 'observer.txt').read_text().splitlines()
    assert lines[0] == 'version=uart-state1 clock=kernel_syscall module_flags=0 unload_flags=O_NONBLOCK'
    assert lines[1].startswith('phase=before_load kernel=4.19.128 pid=')
    assert lines[-1] == 'phase=complete result=0 cancelled=0 module_remains=0'
    assert lines.count('load_result=0 load_errno=0') == 1
    assert lines.count('unload_result=0 unload_errno=0') == 1
    assert len(lines) == 111
    assert lines[4] == 'load_result=0 load_errno=0'
    assert all(line.startswith('sample=') for line in lines[6:106])
    assert lines[107] == 'unload_result=0 unload_errno=0'
    live_path = archive / 'live-protected-verification.json'
    live = json.loads(live_path.read_text())
    assert live['read_only'] and set(live['checks']) == {
        'retro/main', 'retro/vrtemu', 'retro/driver.so', 'retro/showlogo',
        'retro/libs/emu_sfc.so', 'retro/libs/emu_sfc_plus.so', 'retro/init', 'FFVI_ROM'}
    assert all(value is True for value in live['checks'].values())
    samples = [fields(line) for line in lines if line.startswith('sample=')]
    assert len(samples) == 100
    durations = []
    for i, s in enumerate(samples):
        assert int(s['sample']) == i and int(s['read']) == i + 1
        assert s['version'] == '1' and s['result'] == '0' and s['irq'] == '19'
        ctrl, flags = int(s['ctrl'], 16), int(s['flags'], 16)
        hw, sw = bool(ctrl & 0x4000), bool(flags & 2)
        assert int(s['tx_hw']) == hw and int(s['tx_sw']) == sw
        assert int(s['mismatch']) == (hw != sw)
        assert int(s['empty']) == (s['head'] == s['tail'])
        start, stop, owner = (int(s[k]) for k in ['start_ns', 'stop_ns', 'owner_ns'])
        assert start <= stop <= owner
        if i:
            assert start > int(samples[i - 1]['owner_ns'])
            assert int(s['tx']) >= int(samples[i - 1]['tx'])
            assert int(s['rx']) >= int(samples[i - 1]['rx'])
        durations.append(stop - start)
    snapshots = [fields(line) for line in lines if line.startswith('irq ')]
    assert [s['phase'] for s in snapshots] == ['before_baseline', 'after_baseline', 'before_snapshots', 'after_snapshots', 'before_final_baseline', 'after_final_baseline']
    windows = {}
    for label, a, b in zip(['before_load', 'observer_loaded', 'after_unload'], snapshots[::2], snapshots[1::2]):
        assert a['valid'] == b['valid'] == '1'
        amin, amax, bmin, bmax = [int(s[k]) for s in (a, b) for k in ('begin_ns', 'end_ns')]
        assert amin <= amax < bmin <= bmax
        delta = int(b['count']) - int(a['count'])
        assert delta > 0
        duration = ((bmin + bmax) - (amin + amax)) / 2e9
        windows[label] = {'interrupts': delta, 'midpoint_seconds': duration,
            'per_second': delta / duration,
            'endpoint_time_rate_bounds': [delta * 1e9 / (bmax - amin), delta * 1e9 / (bmin - amax)]}
    span = (int(samples[-1]['start_ns']) - int(samples[0]['start_ns'])) / 1e9
    report = {'version': 'uart-state1-physical-return', 'physical_archive': archive.name,
        'installed_source_commit': install['source_commit'], 'mock': False,
        'archive_files_verified': len(entries), 'archive_bytes': sum(e['bytes'] for e in entries.values()),
        'fat_clean': True, 'one_shot_consumed': True, 'card_writes': 0,
        'payloads_verified': len(install['payload_hashes']), 'protected_prior_files': len(protected),
        'stock_boot_and_ROM_verified': True, 'original_progress_unchanged': True,
        'protected_unchanged': len(protected) - len(changed), 'protected_changed': changed,
        'module_loaded_unloaded': True, 'cancelled': False, 'owner_exit': 0,
        'valid_snapshots': len(samples), 'irq_windows': windows,
        'control_distribution': dict(Counter(s['ctrl'] for s in samples)),
        'flags_distribution': dict(Counter(s['flags'] for s in samples)),
        'tx_hardware_enabled_samples': sum(int(s['tx_hw']) for s in samples),
        'tx_software_enabled_samples': sum(int(s['tx_sw']) for s in samples),
        'tx_mismatch_samples': sum(int(s['mismatch']) for s in samples),
        'empty_queue_samples': sum(int(s['empty']) for s in samples),
        'sample_span_seconds': span, 'tx_delta': int(samples[-1]['tx']) - int(samples[0]['tx']),
        'rx_delta': int(samples[-1]['rx']) - int(samples[0]['rx']),
        'tx_per_second_over_sample_span': (int(samples[-1]['tx']) - int(samples[0]['tx'])) / span,
        'snapshot_scope_ns': {'min': min(durations), 'max': max(durations), 'total': sum(durations)},
        'persistent_TX_mismatch_supported': False,
        'interrupt_status_observed': False, 'handler_duration_measured': False,
        'A7_saving_measured': False, 'production_gate': False,
        'limits': ['Idle pre-stock capture only; transient or emulation-only TX states are not excluded.',
            'Counter-read endpoint timing bounds do not remove sequential procfs read uncertainty.',
            'Snapshot times are observer scope, not IRQ handler duration.',
            'Successful wrapper return does not independently prove stock launcher visual operation.'],
        'input_sha256': {p.relative_to(archive).as_posix(): digest(p) for p in
            [archive / 'archive.json', archive / 'chkdsk-before.txt', live_path, base / 'observer.txt', base / 'startup.log', base / 'owner.err', base / 'last-launch']},
        'installation_receipt_sha256': digest(installation_path)}
    output = archive / 'uart-state-return.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
