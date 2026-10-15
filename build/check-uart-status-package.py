"""Qualify the preflight owner/wrapper and bind a private, unarmed package."""
from pathlib import Path
from hashlib import sha256
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/uart-status-private'


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main():
    sys.path.insert(0, str(ROOT / 'build/lab2-inspection-tools'))
    from elftools.elf.elffile import ELFFile
    with (OUT / 'uart-status-owner').open('rb') as stream:
        elf = ELFFile(stream)
        assert elf.elfclass == 32 and elf.little_endian and elf['e_machine'] == 'EM_ARM'
        assert elf['e_flags'] & 0x400  # ARM hard-float userspace ABI.
        versions = [aux.name for _, auxiliaries in elf.get_section_by_name('.gnu.version_r').iter_versions() for aux in auxiliaries]
        assert set(versions) == {'GLIBC_2.4', 'GCC_3.5'}, versions
    tool = ['wsl', '--exec'] if os.name == 'nt' else []
    def run(args, **kw):
        return subprocess.run(tool + args, cwd=ROOT, capture_output=True, text=True, **kw)
    wrapped = ['syscall', 'uname', 'geteuid', 'access', 'open', 'read', 'close', 'fsync']
    binary = 'build/uart-status-private/owner-fixture'
    built = run(['arm-linux-gnueabihf-gcc', '-O2', '-Wall', '-Wextra', '-Werror', '-marm', '-no-pie', '-static',
                 '-U_TIME_BITS', '-D_TIME_BITS=32', '-U_FILE_OFFSET_BITS', '-D_FILE_OFFSET_BITS=32', '-fno-stack-protector',
                 'build/uart-status-owner.c', 'build/uart-status-owner-fixture.c',
                 *['-Wl,--wrap=' + n for n in wrapped], '-o', binary])
    assert built.returncode == 0, built.stderr
    cases = OUT / 'owner-cases'
    cases.mkdir(exist_ok=True)
    module = cases / 'module-fixture'
    module.write_bytes(b'offline fixture, never passed to a real module loader\n')
    results = []
    for mode, expected in [('normal', 0), ('wrong_kernel', 3), ('already_loaded', 4), ('load_fail', 8),
                           ('unload_fail', 10), ('read_fail', 9), ('observer_refuses', 13), ('cancel', 0), ('sync_fail', 6), ('existing', 5), ('stop_fail', 10), ('stop_refuses', 10), ('frozen_fail', 9), ('frozen_refuses', 13)]:
        report = cases / (mode + '.txt')
        if report.exists():
            assert report.is_file() and report.parent == cases
            report.unlink()
        if mode == 'existing':
            report.write_bytes(b'preserve existing report\n')
        proc = run(['env', 'D35_OWNER_CASE=' + mode, 'qemu-arm', binary,
                    module.relative_to(ROOT).as_posix(), report.relative_to(ROOT).as_posix()])
        assert proc.returncode == expected, (mode, proc.returncode, proc.stdout, proc.stderr)
        text = report.read_text() if report.exists() else ''
        if mode == 'normal':
            assert text.count('\nsample=') == 2 and 'module_remains=0' in text and 'unload_result=0' in text
        if mode in ('stop_fail', 'stop_refuses'):
            assert 'module_remains=1' in text and 'unload_errno=16' in text
        if mode == 'normal':
            assert 'stop_result=0 restored=1 attached=0' in text and 'phase=frozen' in text
        if mode == 'cancel':
            assert text.count('\nsample=') == 1 and 'cancelled=1 module_remains=0' in text
        if mode == 'unload_fail':
            assert 'module_remains=1' in text and 'unload_errno=16' in text
        if mode == 'read_fail':
            assert 'read_errno=5' in text and 'module_remains=0' in text
        if mode == 'observer_refuses':
            assert text.count('\nsample=') == 1 and 'result=-19' in text and 'module_remains=0' in text
        if mode == 'load_fail':
            assert 'load_errno=22' in text and 'unload_result=' not in text
        if mode == 'existing':
            assert text == 'preserve existing report\n'
        results.append({'case': mode, 'exit': expected})
    # Actual firmware shell syntax, not a host-only syntax assumption.
    private = ROOT / 'device-evidence/snes-mvp-return-20261010T003708Z/spi-readback/boot-inspection'
    entry = next(x for x in json.loads((private / 'rootfs-index.json').read_text()) if x['name'] == 'bin/busybox')
    cpio = (private / 'rootfs-stock.cpio').read_bytes()
    busybox = cpio[entry['data_offset']:entry['data_offset'] + entry['bytes']]
    assert sha256(busybox).hexdigest() == '6f974778b29d96a7e825b04c526b0e2948ec4f8497ac5558cb5b4d713f058e2f'
    (OUT / 'firmware-busybox').write_bytes(busybox)
    syntax = run(['qemu-arm', '-0', 'busybox', '-L', 'build/sysroot',
                  'build/uart-status-private/firmware-busybox', 'sh', '-n', 'build/launch-uart-status.sh'])
    assert syntax.returncode == 0, syntax.stderr
    results.append({'case': 'exact_firmware_shell_syntax', 'exit': 0})
    # Execute the actual firmware shell wrapper with a fixture ARM owner, then
    # verify a second invocation cannot replay or overwrite the consumed run.
    base = OUT / 'wrapper-case'
    trigger = base / 'trigger'
    trigger.mkdir(parents=True, exist_ok=True)
    for name in ['last-launch', 'observer.txt', 'owner.err', 'startup.log']:
        path = base / name
        if path.exists():
            assert path.parent == base and path.is_file()
            path.unlink()
    (trigger / 'armed').write_bytes(b'UART status1 fixture once\n')
    (base / 'd35_uart_status.ko').write_bytes(b'fixture only\n')
    (base / 'uart-status-owner').write_bytes(b'#!/bin/sh\nexec qemu-arm build/uart-status-private/owner-fixture "$@"\n')
    permissions = run(['chmod', '+x', base.relative_to(ROOT).as_posix() + '/uart-status-owner'])
    assert permissions.returncode == 0
    command = ['env', 'D35_OWNER_CASE=normal', 'D35_UART_BASE=' + base.relative_to(ROOT).as_posix(),
               'D35_UART_TRIGGER=' + trigger.relative_to(ROOT).as_posix(), 'qemu-arm', '-0', 'busybox',
               '-L', 'build/sysroot', 'build/uart-status-private/firmware-busybox', 'sh', 'build/launch-uart-status.sh']
    first = run(command)
    assert first.returncode == 0, (first.returncode, first.stdout, first.stderr, (base / 'owner.err').read_text())
    assert not (trigger / 'armed').exists() and (base / 'last-launch').read_bytes() == b'UART status1 fixture once\n'
    assert 'owner_exit=0' in (base / 'startup.log').read_text()
    frozen = {name: digest(base / name) for name in ['last-launch', 'observer.txt', 'startup.log']}
    second = run(command)
    assert second.returncode == 0 and all(digest(base / n) == h for n, h in frozen.items())
    results.append({'case': 'exact_firmware_wrapper_execution_and_consumed_reboot', 'exit': 0})
    # A failed detach must not release the synchronous stock-startup barrier.
    for name in ['last-launch', 'observer.txt', 'owner.err', 'startup.log']:
        (base / name).unlink()
    (trigger / 'armed').write_bytes(b'UART status1 fixture failure once\n')
    failed_command = command.copy()
    failed_command[1] = 'D35_OWNER_CASE=stop_refuses'
    failure = run(['timeout', '4s', *failed_command])
    assert failure.returncode == 124, (failure.returncode, failure.stderr)
    assert 'stock withheld; power-cycle and return card' in (base / 'startup.log').read_text()
    assert 'module_remains=1' in (base / 'observer.txt').read_text()
    assert not (trigger / 'armed').exists()
    frozen_failure = {name: digest(base / name) for name in ['last-launch', 'observer.txt', 'startup.log']}
    replay = run(command)
    assert replay.returncode == 0 and all(digest(base / n) == h for n, h in frozen_failure.items())
    results.append({'case': 'exact_firmware_failure_withholds_stock_and_consumed_reboot_preserves_logs', 'exit': 124})
    module_q = json.loads((OUT / 'qualification.json').read_text())
    assert len(module_q['checks']) == 12 and not module_q['installed']
    for n, h in module_q['sources'].items():
        assert digest(ROOT / n) == h, n
    assert digest(OUT / 'd35_uart_status.ko') == module_q['observer_module_sha256']
    package = OUT / 'package'
    package.mkdir(exist_ok=True)
    for src, name in [(OUT / 'd35_uart_status.ko', 'd35_uart_status.ko'),
                      (OUT / 'uart-status-owner', 'uart-status-owner'),
                      (ROOT / 'build/launch-uart-status.sh', 'launch.sh')]:
        shutil.copyfile(src, package / name)
    (package / 'dispatch.sh').write_bytes(b'#!/bin/sh\nexec /bin/sh /usr/retro/uart-status1/launch.sh\n')
    sources = [ROOT / 'build/uart-status-owner.c', ROOT / 'build/uart-status-owner-fixture.c',
               ROOT / 'build/build-uart-status.sh', ROOT / 'build/launch-uart-status.sh',
               ROOT / 'build/install-uart-status.py', Path(__file__).resolve()]
    report = {'version': 'uart-status1', 'original_status_capture': True, 'owner_checks': results,
              'userspace_abi': {'ELF': 'ARM32 little-endian hard-float', 'required_versions': versions},
              'compiled_module_qualification_sha256': digest(OUT / 'qualification.json'),
              'sources': {p.relative_to(ROOT).as_posix(): digest(p) for p in sources},
              'payloads': {p.name: digest(p) for p in package.iterdir() if p.is_file()},
              'physical_result': 'PENDING', 'card_access': False,
              'module_load_unload_physical_result': 'PENDING', 'production_gate': False,
              'nominal_capture_seconds': 7, 'samples': 2, 'frozen_reports': 1,
              'scope': 'Idle original-entry status/branch capture. Temporary guarded IRQ action hook, original status read and original ISR body retained, bounded RAM aggregates. No UART configuration/kernel-text/firmware/core changes or extra status/FIFO reads.'}
    (OUT / 'package-qualification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
