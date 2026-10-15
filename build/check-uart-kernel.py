"""Reproduce archived-code UART checks and publishable metadata locally.

Compilation/execution is offline QEMU only. All outputs remain private until
explicitly copied as metadata by the publication step; no card access.
"""
from pathlib import Path
from hashlib import sha256
import io
import importlib.util
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / 'device-evidence/uart-kernel-offline'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location('uart_inspector', ROOT / 'build/inspect-uart-kernel.py')
    inspector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inspector)
    inspector.inspect()
    tool = ['wsl', '--exec'] if os.name == 'nt' else []
    executable = 'device-evidence/uart-kernel-offline/check-uart'
    command = ['arm-linux-gnueabihf-gcc', '-O2', '-Wall', '-Wextra', '-Werror', '-marm', '-no-pie', '-static',
               'build/check-uart-kernel.c', '-o', executable]
    subprocess.run(tool + command, cwd=ROOT, check=True, capture_output=True)
    output = subprocess.run(tool + ['qemu-arm', executable, 'device-evidence/uart-kernel-offline/kernel.bin'],
                            cwd=ROOT, check=True, capture_output=True, text=True).stdout
    assert len(output.splitlines()) == 7 and '6 archived-code checks passed' in output
    (PRIVATE / 'checks.txt').write_text(output)
    details = json.loads((PRIVATE / 'inspection.json').read_text())
    rr = ROOT / 'device-evidence/snes-mvp-return-20261010T003708Z/spi-readback/boot-inspection'
    entries = json.loads((rr / 'rootfs-index.json').read_text())
    entry = next(x for x in entries if x['name'].endswith('/crc-itu-t.ko'))
    data = (rr / 'rootfs-stock.cpio').read_bytes()
    module = data[entry['data_offset']:entry['data_offset'] + entry['bytes']]
    assert sha256(module).hexdigest() == entry['sha256']
    sys.path.insert(0, str(ROOT / 'build/lab2-inspection-tools'))
    from elftools.elf.elffile import ELFFile
    elf = ELFFile(io.BytesIO(module))
    modinfo = elf.get_section_by_name('.modinfo').data().decode().split('\0')
    rates = {}
    input_paths = [ROOT / x for x in ['build/inspect-uart-kernel.py', 'build/check-uart-kernel.py', 'build/check-uart-kernel.c']]
    for name, relative in [
        ('v2', 'evidence/2026-10-04/hardware-runtime-return-20261004T182651Z/hardware_probe_v2.jsonl'),
        ('v3', 'device-evidence/hardware-console-return-20261004T185838Z/hardware_probe_v3.jsonl')]:
        path = ROOT / relative
        input_paths.append(path)
        records = [json.loads(line) for line in path.read_text().splitlines()]
        def rows(p):
            return [r for r in records if r['kind'] == 'file' and r['path'] == p and r['elapsed'] > 14 and not r['errno'] and not r['truncated']]
        irq, uptime, tty = rows('/proc/interrupts'), rows('/proc/uptime'), rows('/proc/tty/driver/gp serial')
        def irq19(r):
            return int(re.search(r'^\s*19:\s+(\d+)', r['data'], re.M)[1])
        def counters(r):
            line = next(x for x in r['data'].splitlines() if x.startswith('0:'))
            return {k: int(v) for k, v in re.findall(r'(tx|rx|brk):(\d+)', line)}
        first, last = counters(tty[0]), counters(tty[-1])
        delta = irq19(irq[-1]) - irq19(irq[0])
        probe_seconds = irq[-1]['elapsed'] - irq[0]['elapsed']
        # Independent, nearby coarse kernel-uptime endpoints. Reads are not atomic.
        ua = min(uptime, key=lambda r: abs(r['elapsed'] - irq[0]['elapsed']))
        ub = min(uptime, key=lambda r: abs(r['elapsed'] - irq[-1]['elapsed']))
        kernel_seconds = float(ub['data'].split()[0]) - float(ua['data'].split()[0])
        rates[name] = {'irq19_delta': delta, 'probe_interval_seconds': probe_seconds,
                       'nearby_kernel_uptime_interval_seconds': kernel_seconds,
                       'irq_per_probe_second': delta / probe_seconds,
                       'approx_irq_per_kernel_uptime_second': delta / kernel_seconds,
                       'uptime_minus_irq_probe_elapsed_seconds': [ua['elapsed'] - irq[0]['elapsed'], ub['elapsed'] - irq[-1]['elapsed']],
                       'tx_delta': last['tx'] - first['tx'], 'rx_delta': last['rx'] - first['rx'],
                       'brk_delta': last['brk'] - first['brk'],
                       'endpoint_caveat': 'Coarse cross-check only: uptime has 10ms precision and nonmatching read endpoints; not an IRQ duration or exact rate correction.'}
    result = {'version': 1, 'kind': 'offline_exact_kernel_uart_research', 'card_access': False,
              'kernel_sha256': details['kernel_sha256'], 'decoded_kernel_symbols': details['symbol_count'],
              'retained_builtin_runtime_symbols_matched': details['runtime_symbols_matched'],
              'module_abi': {'vermagic': next(x.split('=', 1)[1] for x in modinfo if x.startswith('vermagic=')),
                             'this_module_bytes': elf.get_section_by_name('.gnu.linkonce.this_module')['sh_size'],
                             'versions_section_present': elf.get_section_by_name('__versions') is not None,
                             'qualification': 'Metadata only; no replacement module built or loaded.'},
              'selected_code_hashes': details['functions'], 'checks': output.splitlines()[:-1],
              'tracefs_symbols_found': [n for n in details['trace_related_symbols'] if any(s in n for s in ['tracefs', 'ftrace', 'tracing_', 'irqtime'])],
              'archived_rates': rates,
              'live_irq_cause_proven': False, 'a7_irq_duration_measured': False,
              'inputs': {p.relative_to(ROOT).as_posix(): digest(p) for p in input_paths},
              'private_check_binary_sha256': digest(ROOT / executable)}
    current = ROOT / 'device-evidence/a7-pair-before-20261015T011612Z/retro/snes-draw-order1'
    snapshots = []
    for name in ['runtime-platform.txt', 'runtime-platform-latest.txt']:
        path = current / name
        input_paths.append(path)
        text = path.read_text()
        snapshots.append({'uptime': float(text.splitlines()[1].split()[0]),
                          'irq19': int(re.search(r'^\s*19:\s+(\d+)', text, re.M)[1]),
                          'total_irq': int(re.search(r'^intr (\d+)', text, re.M)[1])})
    a, b = snapshots
    seconds = b['uptime'] - a['uptime']
    result['latest_draw_order_suite'] = {'snapshots': snapshots, 'kernel_uptime_interval_seconds': seconds,
        'irq19_delta': b['irq19'] - a['irq19'], 'irq19_per_second': (b['irq19'] - a['irq19']) / seconds,
        'all_irq_delta': b['total_irq'] - a['total_irq'],
        'irq19_share_of_interrupt_counts_percent': 100 * (b['irq19'] - a['irq19']) / (b['total_irq'] - a['total_irq']),
        'boundary': 'Whole-suite interval includes emulation, startup, inter-epoch flushes and teardown. IRQ and uptime reads are separate; this is an approximate rate and count share, never CPU-time share.'}
    result['inputs'] = {p.relative_to(ROOT).as_posix(): digest(p) for p in input_paths}
    (PRIVATE / 'research.json').write_text(json.dumps(result, indent=2) + '\n')
    print(output)
    print(json.dumps({'archived_rates': rates, 'module_abi': result['module_abi']}))


if __name__ == '__main__':
    main()
