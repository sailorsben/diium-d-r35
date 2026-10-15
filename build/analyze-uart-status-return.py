"""Strict physical status1 return analysis. No card writes or probe changes."""
from pathlib import Path
from hashlib import sha256
from functools import reduce
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def fields(line):
    pairs = [word.split('=', 1) for word in line.split() if '=' in word]
    result = dict(pairs)
    assert len(result) == len(pairs)
    return result


def parse_capture(line, histogram):
    raw = fields(line)
    assert raw['version'] == '2' and raw['result'] == '0' and raw['irq'] == '19'
    hex_fields = {'first', 'last', 'bits_or', 'bits_and'}
    result = {k: int(v, 16 if k in hex_fields else 10) for k, v in raw.items()}
    assert all(0 <= n <= (0xffffffffffffffff if k == 'owner_ns' else 0xffffffff) for k, n in result.items())
    assert result['cap'] == 200000 and result['total'] <= result['cap']
    assert result['rx'] + result['tx_only'] + result['neither'] == result['total']
    assert result['rx_then_tx'] <= result['rx']
    assert result['handled'] + result['other_return'] == result['total']
    assert result['attached'] in (0, 1) and result['unique'] == len(histogram) <= 32
    assert sum(histogram.values()) + result['overflow'] == result['total']
    if not result['overflow']:
        assert sum(n for v, n in histogram.items() if v & 0xa000) == result['rx']
        assert sum(n for v, n in histogram.items() if not v & 0xa000 and v & 0x80) == result['tx_only']
        assert sum(n for v, n in histogram.items() if not v & 0xa080) == result['neither']
        assert sum(n for v, n in histogram.items() if v & 0xa000 and v & 0x80) == result['rx_then_tx']
        if result['total']:
            assert result['first'] in histogram and result['last'] in histogram
            assert reduce(lambda a, b: a | b, histogram) == result['bits_or']
            assert reduce(lambda a, b: a & b, histogram) == result['bits_and']
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
    install_path = ROOT / 'evidence/2026-10-14/uart-status/installation.json'
    install = json.loads(install_path.read_text())
    base = archive / 'retro/uart-status1'
    for name, expected in install['payload_hashes'].items():
        assert digest(base / name) == expected, name
    assert digest(archive / 'retro/snes-mvp/launch.sh') == install['dispatch_sha256']
    assert (base / 'last-launch').read_bytes() == b'UART status1 original-entry status and branch capture only\n'
    assert (base / 'startup.log').read_text() == 'UART status1 original-status/branch capture; marker consumed\nowner_exit=0; returning to stock startup\n'
    assert (base / 'owner.err').read_bytes() == b''
    old_path = ROOT / 'device-evidence' / install['archive'] / 'archive.json'
    protected = [e for e in json.loads(old_path.read_text())['all_retro_files'] if e['path'] != 'retro/snes-mvp/launch.sh']
    assert len(protected) == install['protected_files']
    changed = []
    for e in protected:
        assert e['path'] in entries
        if entries[e['path']]['sha256'] != e['sha256']:
            changed.append(e['path'])
    assert set(changed) <= {'retro/swapfile'}, changed
    live_path = archive / 'live-protected-verification.json'
    live = json.loads(live_path.read_text())
    assert live['read_only'] and live['early_probe_copy_matches_full_archive']
    assert set(live['checks']) == {'retro/main', 'retro/vrtemu', 'retro/driver.so', 'retro/showlogo',
        'retro/libs/emu_sfc.so', 'retro/libs/emu_sfc_plus.so', 'retro/init', 'FFVI_ROM'}
    assert all(v is True for v in live['checks'].values())
    lines = (base / 'observer.txt').read_text().splitlines()
    assert lines[0] == 'version=uart-status1 clock=kernel_syscall module_flags=0 unload_flags=O_NONBLOCK'
    assert lines[1].startswith('phase=before_load kernel=4.19.128 pid=')
    assert lines[4] == 'load_result=0 load_errno=0'
    assert lines[-1] == 'phase=complete result=0 cancelled=0 module_remains=0'
    cursor = 6

    def capture(prefix):
        nonlocal cursor
        line = lines[cursor]
        assert line.startswith(prefix), (prefix, line)
        cursor += 1
        histogram = {}
        while cursor < len(lines) and lines[cursor].startswith('status='):
            match = re.fullmatch(r'status=([0-9a-f]{8}) count=([1-9][0-9]*)', lines[cursor])
            assert match
            value, count = int(match[1], 16), int(match[2])
            assert value not in histogram
            histogram[value] = count
            cursor += 1
        return parse_capture(line, histogram), histogram

    initial, hi = capture('sample=0 owner_ns=')
    final, hf = capture('sample=1 owner_ns=')
    assert initial['attached'] == final['attached'] == 1
    assert initial['sample'] == 0 and final['sample'] == 1
    assert initial['owner_ns'] < final['owner_ns']
    assert lines[cursor].startswith('irq phase=after_snapshots ')
    cursor += 1
    assert lines[cursor] == 'version=2 stop_result=0 restored=1 attached=0'
    cursor += 1
    assert lines[cursor] == 'phase=frozen'
    cursor += 1
    frozen, hist = capture('version=2 result=0 irq=19 attached=0 ')
    assert frozen['attached'] == 0
    assert lines[cursor:] == ['unload_result=0 unload_errno=0', lines[-3], lines[-2], lines[-1]]
    counters = ['total', 'rx', 'tx_only', 'neither', 'rx_then_tx', 'handled', 'other_return', 'bypass', 'unique', 'overflow']
    assert all(initial[k] <= final[k] <= frozen[k] for k in counters)
    assert all(hf.get(v, 0) >= n for v, n in hi.items())
    assert all(hist.get(v, 0) >= n for v, n in hf.items())
    irqs = [fields(line) for line in lines if line.startswith('irq ')]
    assert [r['phase'] for r in irqs] == ['before_baseline', 'after_baseline', 'before_snapshots', 'after_snapshots', 'before_final_baseline', 'after_final_baseline']
    assert lines[2].startswith('irq phase=before_baseline ') and lines[3].startswith('irq phase=after_baseline ') and lines[5].startswith('irq phase=before_snapshots ')
    windows = {}
    for label, a, b in zip(['before_load', 'hook_attached', 'after_unload'], irqs[::2], irqs[1::2]):
        assert a['valid'] == b['valid'] == '1'
        amin, amax, bmin, bmax = [int(s[k]) for s in (a, b) for k in ('begin_ns', 'end_ns')]
        assert amin <= amax < bmin <= bmax
        delta = int(b['count']) - int(a['count'])
        assert delta > 0
        duration = ((bmin + bmax) - (amin + amax)) / 2e9
        windows[label] = {'interrupts': delta, 'midpoint_seconds': duration, 'per_second': delta / duration,
            'endpoint_time_rate_bounds': [delta * 1e9 / (bmax - amin), delta * 1e9 / (bmin - amax)]}
    total = frozen['total']
    assert total > 0
    report = {'version': 'uart-status1-physical-return', 'physical_archive': archive.name, 'mock': False,
        'installed_source_commit': install['source_commit'], 'archive_files_verified': len(entries),
        'archive_bytes': sum(e['bytes'] for e in entries.values()), 'fat_clean': True, 'card_writes': 0,
        'payloads_verified': len(install['payload_hashes']), 'one_shot_consumed': True,
        'protected_prior_files': len(protected), 'protected_unchanged': len(protected) - len(changed),
        'protected_changed': changed, 'stock_boot_and_ROM_verified': True, 'original_progress_unchanged': True,
        'owner_exit': 0, 'cancelled': False, 'handler_restored': True, 'module_loaded_unloaded': True,
        'initial': initial, 'final_attached': final, 'frozen': frozen,
        'status_histogram': {f'0x{v:08x}': {'count': n, 'percent': n * 100 / total,
            'branch': 'rx' if v & 0xa000 else 'tx_only' if v & 0x80 else 'neither'} for v, n in hist.items()},
        'unrecognized_percent': frozen['neither'] * 100 / total, 'complete_histogram': frozen['overflow'] == 0,
        'irq_windows': windows,
        'hook_count_matches_bracketed_irq_growth': final['total'] - initial['total'] == windows['hook_attached']['interrupts'],
        'interrupt_status_observed': True, 'handler_duration_measured': False, 'A7_saving_measured': False,
        'production_gate': False, 'electrical_or_enable_bit_origin_proven': False,
        'limits': ['Idle startup capture only; rates differ across sequential phases and observer disturbance is unpriced.',
            'Selections follow captured entry bits and unchanged original tests, not every internal sub-branch.',
            'Histogram includes attached startup/stop margins; counter read time bounds omit procfs enumeration uncertainty.',
            'Unrecognized status plus IRQ_HANDLED identifies the dominant software path, not the electrical source or clearing operation.',
            'Normal wrapper return does not independently establish visual stock-launcher operation.'],
        'input_sha256': {p.relative_to(archive).as_posix(): digest(p) for p in [archive / 'archive.json',
            archive / 'chkdsk-before.txt', live_path, base / 'observer.txt', base / 'startup.log', base / 'owner.err', base / 'last-launch']},
        'installation_receipt_sha256': digest(install_path)}
    (archive / 'uart-status-return.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
