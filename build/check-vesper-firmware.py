"""Hash-bound offline checks of exact captured ARM loader/updater under QEMU.

No SD staging, physical device access, persistent writes or recovery qualification.
"""
from pathlib import Path
from hashlib import sha256
import argparse, json, os, subprocess

ROOT = Path(__file__).resolve().parent.parent
BASELINE = '5c4ea86ca5c497a26136ee9a59d8a31085e15c8d1dc5f063b874a20c400d9e2b'
VENDOR = '8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
CANDIDATE = '246a46afa5cda655b47db787dff94e430bbf7f8a897b751cfca28ddc79f68ff7'


def check(image, vendor, directory):
    for p in [image, vendor, directory]:
        assert p.resolve().is_relative_to((ROOT / 'device-evidence').resolve())
    assert sha256(image.read_bytes()).hexdigest() == BASELINE
    assert sha256(vendor.read_bytes()).hexdigest() == VENDOR
    preparation = json.loads((directory / 'preparation.json').read_text(encoding='utf-8'))
    assert preparation['candidate_sha256'] == CANDIDATE
    for name, expected in preparation['files'].items():
        assert Path(name).name == name
        data = (directory / name).read_bytes()
        assert len(data) == expected['bytes'] and sha256(data).hexdigest() == expected['sha256']
    # Require an exact restorable build recipe, not a stale helper executable.
    prefix = ['wsl'] if os.name == 'nt' else []
    destination = ROOT / 'build/boot-loader-check'
    destination.mkdir(exist_ok=True)

    def run(args, expected_exit=0):
        result = subprocess.run(prefix+args, cwd=ROOT, capture_output=True, timeout=60)
        if result.returncode != expected_exit:
            raise RuntimeError(f'Offline command failed ({result.returncode}): {args}\n'+result.stderr.decode('utf-8'))
        return result.stdout.decode('utf-8')

    for name, libraries in [('check-boot-loader', []), ('check-vendor-updater', ['-ldl'])]:
        run(['arm-linux-gnueabihf-gcc', '-mcpu=cortex-a7', '-marm', '-O2', '-Wall', '-Wextra', '-Werror',
             '-no-pie', '-Wl,-Ttext-segment=0x10000000', f'build/{name}.c', *libraries,
             '-o', f'build/boot-loader-check/{name}'])

    def relative(p):
        return p.resolve().relative_to(ROOT).as_posix()

    candidate = directory / 'spi-vesper-offline.bin'
    qemu = ['qemu-arm', '-cpu', 'cortex-a7', '-L', '/usr/arm-linux-gnueabihf']
    results = []
    for label, path in [('original', image), ('Vesper candidate', candidate)]:
        stdout = run(qemu+['-B', '0x40000000', 'build/boot-loader-check/check-boot-loader', relative(path)])
        assert stdout.startswith('PASS ') and 'DT initrd bounds' in stdout
        results.append({'test': f'Exact Thumb loader: {label}', 'passed': True, 'stdout': stdout})
    fixtures = [('compatible', image, 'fixture-compatible.bkp', 1),
                ('incompatible family', image, 'fixture-incompatible.bkp', 0),
                ('bad first-item CRC with matching local/central declarations', image, 'fixture-consistent-bad-crc.bkp', 0),
                ('inconsistent local/central CRC', image, 'fixture-bad-crc.bkp', 2),
                ('missing WQW prefix', image, 'fixture-missing-prefix.bkp', 0),
                ('already recorded CRC', directory / 'fixture-already-recorded-baseline.bin', 'fixture-compatible.bkp', 0)]
    for label, baseline, package, want in fixtures:
        stdout = run(qemu+['build/boot-loader-check/check-vendor-updater', relative(vendor), relative(baseline),
                          relative(candidate), relative(directory / package), str(want)], expected_exit=89 if want==2 else 0)
        if want==2:
            assert 'NULL image+0x108' in stdout and 'erase/program_calls=0' in stdout
            results.append({'test': f'Exact vendor updater: {label}', 'passed': True,
                            'observed_vendor_fault': 'NULL image dereference at ARM 0x13920, address 0x108',
                            'safe_rejection': False, 'stdout': stdout})
            continue
        assert stdout.startswith('PASS ') and f'accepted={want}' in stdout
        if want:
            assert 'erases=55 pages=14080' in stdout and 'metadata=f2914d07/5d496000' in stdout
        else:
            assert 'erases=0 pages=0' in stdout
        results.append({'test': f'Exact vendor updater: {label}', 'passed': True, 'stdout': stdout})
    # Output guard is exercised before any image is read or file is created.
    import importlib.util
    spec = importlib.util.spec_from_file_location('prepare', ROOT / 'build/prepare-vesper-firmware.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.prepare(image, image, ROOT / 'releases/forbidden-firmware-test')
    except ValueError:
        pass
    else:
        raise AssertionError('Public vendor-output path accepted')
    assert not (ROOT / 'releases/forbidden-firmware-test').exists()
    results.append({'test': 'Private vendor-image output guard', 'passed': True})
    report = {'version': 1, 'all_checks_passed': True, 'checks': results,
        'flash_baseline_sha256': BASELINE, 'vendor_sha256': VENDOR, 'candidate_sha256': CANDIDATE,
        'loader_scope': 'Exact Thumb table parser/getter, GPAP copy selection, three-section loading and patched DT initrd bounds; SPI callback reads private files into RAM. No boot main or kernel execution.',
        'updater_scope': 'Exact ARM UpdateROM/UpdateROMProc and bundled ZIP decoder. All hardware/display/process-control seams intercepted; erase/program callbacks change RAM only.',
        'updater_container': 'WQW + single-member ZIP; first item contains full 8 MiB SPI image; member filename SPI_ROM.bin works offline but is not proven mandatory.',
        'updater_metadata': {'crc_offset': '0x100', 'zip_dos_time_offset': '0x104', 'compatibility_offset': '0x108',
                             'compatibility_rule': 'unsigned candidate word / 10 == unsigned existing word / 10',
                             'written_crc': '0xf2914d07', 'written_zip_dos_time': '0x5d496000'},
        'updater_ram_dry_run': {'erase_blocks': 55, 'page_programs': 14080,
                               'boot_code_block_0_rewritten': True, 'all_simulated_flash_bytes_match_mutated_candidate': True},
        'malformed_zip_fault_observed': True,
        'device_access': False, 'staged_to_card': False, 'physical_flash_write': False, 'recovery_qualified': False,
        'limits': 'Offline acceptance and a RAM-only erase/program simulation. Does not prove physical SPI writes, recovery, kernel execution, gzip extraction by this running kernel or on-device original-animation replacement.',
        'source_sha256': {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in
                          ['build/check-boot-loader.c', 'build/check-vendor-updater.c',
                           'build/prepare-vesper-firmware.py', 'build/check-vesper-firmware.py']}}
    (directory / 'qualification.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('image', type=Path)
    p.add_argument('vendor', type=Path)
    p.add_argument('candidate_directory', type=Path)
    args = p.parse_args()
    print(json.dumps(check(args.image, args.vendor, args.candidate_directory), indent=2))
