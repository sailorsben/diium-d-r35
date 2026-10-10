"""Offline ARM qualification for the first-splash candidate; no device access."""
from pathlib import Path
from hashlib import sha256
import argparse, importlib.util, json, os, subprocess

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ['build/prepare-vesper-static.py', 'build/check-vesper-static.py',
           'build/check-static-splash.c', 'build/check-boot-loader.c', 'build/check-vendor-updater.c']
VENDOR_SHA = '8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'


def check(directory, vendor):
    private = (ROOT / 'device-evidence').resolve()
    assert directory.resolve().is_relative_to(private) and vendor.resolve().is_relative_to(private)
    assert sha256(vendor.read_bytes()).hexdigest() == VENDOR_SHA
    report = json.loads((directory / 'preparation.json').read_text())
    assert report['baseline_sha256'] == 'd20301be923288e6ace49b43dd8cce306855ded8cd961643e5ee14854d9e6f03'
    assert report['candidate_sha256'] == '9f99ec3984f19b38d216cef2cad38eacb2bad9792046900d8fa91262a6e772b9'
    assert report['expected_after_vendor_sha256'] == '509cdc305deca2654fbf48184eb16d523b4b6cae0effffc4a3cba6845622d9fd'
    for name, item in report['files'].items():
        assert Path(name).name == name
        raw = (directory / name).read_bytes()
        assert len(raw) == item['bytes'] and sha256(raw).hexdigest() == item['sha256']
    prefix = ['wsl'] if os.name == 'nt' else []
    destination = ROOT / 'build/static-splash-check'
    destination.mkdir(exist_ok=True)

    def run(args):
        result = subprocess.run(prefix + args, cwd=ROOT, capture_output=True, timeout=60)
        assert result.returncode == 0, (args, result.stderr.decode('utf-8', errors='replace'))
        return result.stdout.decode('utf-8')

    def relative(path):
        return path.resolve().relative_to(ROOT).as_posix()

    for name, libraries in [('check-static-splash', []), ('check-boot-loader', []), ('check-vendor-updater', ['-ldl'])]:
        run(['arm-linux-gnueabihf-gcc', '-mcpu=cortex-a7', '-marm', '-O2', '-Wall', '-Wextra', '-Werror',
             '-no-pie', '-Wl,-Ttext-segment=0x10000000', f'build/{name}.c', *libraries,
             '-o', f'build/static-splash-check/{name}'])
    qemu = ['qemu-arm', '-cpu', 'cortex-a7', '-L', '/usr/arm-linux-gnueabihf']
    results = []
    baseline = directory / 'baseline-installed.bin'
    candidate = directory / 'spi-vesper-static.bin'
    for label, image in [('installed Vesper baseline', baseline), ('new static Vesper candidate', candidate)]:
        for helper in ['check-static-splash', 'check-boot-loader']:
            stdout = run(qemu + ['-B', '0x40000000', 'build/static-splash-check/' + helper, relative(image)])
            assert stdout.startswith('PASS ')
            results.append({'test': helper + ': ' + label, 'passed': True, 'stdout': stdout})
    fixtures = [('compatible first-splash update', baseline, 'fixture-compatible.bkp', 1),
                ('incompatible family', baseline, 'fixture-incompatible.bkp', 0),
                ('consistent wrong ZIP CRC', baseline, 'fixture-consistent-bad-crc.bkp', 0),
                ('missing WQW prefix', baseline, 'fixture-missing-prefix.bkp', 0),
                ('already-recorded CRC', directory / 'fixture-already-recorded-baseline.bin', 'fixture-compatible.bkp', 0)]
    for label, image, package, want in fixtures:
        stdout = run(qemu + ['build/static-splash-check/check-vendor-updater', relative(vendor),
                            relative(image), relative(candidate), relative(directory / package), str(want)])
        assert stdout.startswith('PASS ') and f'accepted={want}' in stdout
        if want:
            assert 'erases=10 pages=2560 metadata=17e40b24/5d4a6000' in stdout
            assert 'erased_blocks=000000,010000,020000,030000,040000,050000,060000,070000,080000,090000' in stdout
        else:
            assert 'erases=0 pages=0' in stdout
        results.append({'test': 'Exact vendor updater: ' + label, 'passed': True, 'stdout': stdout})
    spec = importlib.util.spec_from_file_location('prepare_static', ROOT / 'build/prepare-vesper-static.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.prepare(ROOT / 'releases/forbidden-static-test')
    except ValueError:
        pass
    else:
        raise AssertionError('Public vendor-image path accepted')
    assert not (ROOT / 'releases/forbidden-static-test').exists()
    results.append({'test': 'Private firmware output guard', 'passed': True})
    result = {'version': 1, 'all_checks_passed': True, 'checks': results,
              'baseline_sha256': report['baseline_sha256'], 'candidate_sha256': report['candidate_sha256'],
              'expected_after_vendor_sha256': report['expected_after_vendor_sha256'],
              'package_sha256': report['package_sha256'], 'vendor_sha256': VENDOR_SHA,
              'ram_erase_blocks': 10, 'ram_page_programs': 2560,
              'ram_result_matches_vendor_mutated_candidate': True,
              'boot_code_erase_blocks_rewritten': ['0x0'],
              'bitmap_scope': 'Exact Thumb pointer/dimension stores into anonymous RAM and 614400 referenced bytes. GPIO/display setup, boot ROM and physical panel not executed.',
              'loader_scope': 'Exact section parser/getter, GPAP selection, kernel/rootfs/DT loads with intercepted SPI. No kernel execution.',
              'updater_scope': 'Exact captured UpdateROM/UpdateROMProc and ZIP decoder. Device/display/reboot seams intercepted; only RAM erased/programmed.',
              'boot_rom_integrity_contract': 'unknown; no matching public primary documentation found; header and executable bytes remain unchanged',
              'device_access': False, 'physical_update': 'pending', 'external_recovery_qualified': False,
              'source_sha256': {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}}
    (directory / 'qualification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    p.add_argument('vendor', type=Path)
    args = p.parse_args()
    print(json.dumps(check(args.directory, args.vendor), indent=2))
