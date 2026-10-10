"""Check private boot extraction against independent libarchive and GNU gzip."""
from pathlib import Path
from hashlib import sha256
import argparse, importlib.util, json, os, shutil, subprocess, zlib

ROOT = Path(__file__).resolve().parent.parent


def check(base, image):
    spec = importlib.util.spec_from_file_location('boot_inspector', ROOT / 'build/inspect-spi-boot.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = json.loads((base / 'inspection.json').read_text())
    checks = []
    tar = shutil.which('tar')
    assert tar, 'Independent libarchive/GNU tar required'
    for name, expected in [('rootfs-stock.cpio', module.STOCK), ('rootfs-vesper.cpio', module.PATCHED)]:
        listing = subprocess.run([tar, '-tf', str(base / name)], capture_output=True, check=True)
        assert len(listing.stdout.splitlines()) == 558
        logo = subprocess.run([tar, '-xOf', str(base / name), 'showlogo'], capture_output=True, check=True).stdout
        assert len(logo) == 198408 and sha256(logo).hexdigest() == expected
    checks.append('Independent tar lists both archives and extracts exact original/replacement showlogo')
    relative = base.relative_to(ROOT).as_posix() + '/rootfs-vesper.cpio.gz'
    command = (['wsl'] if os.name == 'nt' else []) + ['gzip', '-dc', relative]
    expanded = subprocess.run(command, cwd=ROOT, capture_output=True, check=True).stdout
    assert sha256(expanded).hexdigest() == report['candidate']['rootfs_sha256']
    assert expanded == (base / 'rootfs-vesper.cpio').read_bytes()
    checks.append('Independent GNU gzip verifies trailer and expands the exact candidate cpio')
    original = (base / 'rootfs-stock.cpio').read_bytes()
    entries = module.newc(original)
    candidate = (base / 'rootfs-vesper.cpio').read_bytes()
    assert len(original) == len(candidate)
    logo = next(e for e in entries if e['name'] == 'showlogo')
    start, end = logo['data_offset'] + 0x7180, logo['data_offset'] + 0x29bf4
    assert original[:start] == candidate[:start] and original[end:] == candidate[end:]
    assert [a['name'] for a, b in zip(entries, module.newc(candidate)) if a != b] == ['showlogo']
    checks.append('All cpio bytes outside the qualified showlogo ZIP span stay exact, including duplicate directories')

    def refuses(action):
        try:
            action()
        except (ValueError, AssertionError, zlib.error):
            return
        raise AssertionError('Damaged input accepted')

    refuses(lambda: module.newc(original[:100]))
    refuses(lambda: module.newc(original[:logo['data_offset'] + 5]))
    damaged = bytearray(original)
    damaged[94:102] = b'ffffffff'  # namesize in the first physical newc record
    refuses(lambda: module.newc(damaged))
    damaged = bytearray(original)
    damaged[logo['header_offset'] + 110] = ord('/')
    refuses(lambda: module.newc(damaged))
    damaged = bytearray(original)
    damaged[-1] = 1
    refuses(lambda: module.newc(damaged))
    checks.append('Physical-archive truncation, oversized name, unsafe path and trailing-junk refusals')
    gzip_data = (base / 'rootfs-vesper.cpio.gz').read_bytes()
    refuses(lambda: module.gunzip(gzip_data[:-1]))
    damaged = bytearray(gzip_data)
    damaged[-8] ^= 1
    refuses(lambda: module.gunzip(damaged))
    oversized = zlib.compressobj(1, zlib.DEFLATED, 31)
    bomb = oversized.compress(bytes(module.MAX_OUTPUT + 1)) + oversized.flush()
    refuses(lambda: module.gunzip(bomb))
    checks.append('Truncated/bad-CRC/over-budget compressed-stream refusals')
    refuses(lambda: module.inspect(image, ROOT / 'releases/vendor-output-must-not-exist'))
    assert not (ROOT / 'releases/vendor-output-must-not-exist').exists()
    checks.append('Vendor output outside ignored private evidence refuses before creating a directory')
    result = {'software_checks_passed': True, 'checks': checks,
              'physical_firmware_write': False, 'recovery_qualified': False,
              'source_hashes': {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in
                                ['build/inspect-spi-boot.py', 'build/check-spi-boot.py']}}
    (base / 'qualification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inspection', type=Path)
    parser.add_argument('--image', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.inspection.resolve(), args.image.resolve()), indent=2))
