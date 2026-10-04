"""Verify ARM/glibc compatibility, JSON escaping, optional files and output cap.
QEMU execution is functional validation only, never a handheld benchmark.
"""
import json
import os
from pathlib import Path
import subprocess

workspace = Path(__file__).resolve().parent.parent
base = workspace / 'build/hardware-inventory'
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
    put('/proc/cpuinfo', b'fixture Cortex-A7\nquote=" backslash=\\ nul=\x00 high=\xff\n')
    put('/proc/device-tree/compatible', b'generalplus,gpa7740a\x00generalplus,emu\x00')
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
results['unarmed'] = {'does_not_run': True}
(base / 'verification.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
