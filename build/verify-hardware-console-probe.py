"""Verify ARM/glibc compatibility, JSON escaping, optional files and output cap.
QEMU execution is functional validation only, never a handheld benchmark.
"""
import json
import os
from pathlib import Path
import subprocess

workspace = Path(__file__).resolve().parent.parent
base = workspace / 'build/hardware-console-probe'
linuxbase = '/mnt/c/' + str(base)[3:].replace('\\', '/')
results = {}
for case in ['sparse', 'capped']:
    wd = base / case
    fixture = wd / 'fixture'
    fixture.mkdir(parents=True, exist_ok=True)
    def put(name, data):
        p = fixture / name.lstrip('/')
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    put('/fixture/kernel-log.txt', b'fixture only: no host kernel read\n')
    put('/proc/cpuinfo', b'fixture Cortex-A7\nquote=" backslash=\\ nul=\x00 high=\xff\n')
    put('/proc/device-tree/compatible', b'generalplus,gpa7740a\x00generalplus,emu\x00')
    put('/proc/kallsyms', b'c0001234 T gp_pscaler_probe\nc0005678 T unrelated_symbol\n')
    put('/dev/dsp', b'fixture only; never opened by collector')
    if case == 'capped':
        payload = b'"\\\x00\xff' * 20000
        for name in ['meminfo', 'cmdline', 'version', 'modules', 'mounts', 'iomem',
                     'interrupts', 'swaps', 'partitions', 'devices', 'fb']:
            put('/proc/' + name, payload)
        put('/sys/firmware/fdt', payload)
        put('/proc/config.gz', payload)
    linuxwd = linuxbase + '/' + case
    command = ['wsl', '--cd', str(wd), '--exec', 'env',
               'D35_PROBE_ROOT=' + linuxwd + '/fixture', 'qemu-arm',
               '-cpu', 'cortex-a7', '-L', linuxbase + '/../sysroot',
               linuxbase + '/hardware_probe', '--quick']
    subprocess.run(command, check=True, timeout=30)
    data = (wd / 'hardware-probe-test.jsonl').read_bytes()
    records = [json.loads(line) for line in data.splitlines()]
    assert records[0]['passive'] is True
    assert records[-1]['kind'] == 'complete'
    assert len(data) <= 512 * 1024
    cpu = next(r for r in records if r.get('path') == '/proc/cpuinfo')
    assert cpu['data'].encode('latin1') == (fixture / 'proc/cpuinfo').read_bytes()
    if case == 'sparse':
        node = next(r for r in records if r.get('path') == '/dev/dsp')
        assert node['errno'] == 0 and node['mode'] & 0o170000 == 0o100000
        assert not records[-1]['report_capped']
    else:
        assert records[-1]['report_capped']
    results[case] = {'bytes': len(data), 'records': len(records), 'complete': records[-1]}

wd = base / 'sparse'
output = wd / 'unarmed-output.jsonl'
command = ['wsl', '--cd', str(wd), '--exec', 'qemu-arm', '-cpu', 'cortex-a7',
           '-L', linuxbase + '/../sysroot', linuxbase + '/hardware_probe',
           '--once', linuxbase + '/sparse/nonexistent-marker',
           linuxbase + '/sparse/unarmed-output.jsonl']
subprocess.run(command, check=True, timeout=30)
assert not output.exists()
sparse_records = [json.loads(line) for line in (base / 'sparse/hardware-probe-test.jsonl').read_bytes().splitlines()]
symbols = next(r for r in sparse_records if r['kind'] == 'kernel_symbols')
assert 'gp_pscaler_probe' in symbols['data'] and 'unrelated_symbol' not in symbols['data']
assert symbols['errno'] == 0 and not symbols['limited']
assert sparse_records[0]['version'] == 3
assert not any(r['kind'] == 'kernel_log' for r in sparse_records)
results['kernel_symbol_filter'] = {'verified': True, 'host_log_not_read_in_fixture': True}
links = [r for r in sparse_records if r['kind'] == 'fd_link']
if links:
    assert links[0]['target'] == '/dev/console' and links[0]['errno'] == 0
    results['fd_symlink'] = {'verified': True, 'target': '/dev/console', 'no_device_open': True}
results['unarmed'] = {'does_not_run': True}
(base / 'verification.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
