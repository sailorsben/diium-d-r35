"""Replace only the first-screen pixels in the verified installed Vesper image.

Images/packages remain private; this helper never accesses the physical device.
The bitmap uses the exact RGB565 background already accepted in the animation.
"""
from pathlib import Path
from hashlib import sha256
import argparse, importlib.util, io, json, struct, zipfile, zlib

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / 'device-evidence'
BASELINE_PATH = PRIVATE / 'snes-mvp-return-20261010T044231Z/expected-after-vendor.bin'
BASELINE_SHA = 'd20301be923288e6ace49b43dd8cce306855ded8cd961643e5ee14854d9e6f03'
BITMAP_SHA = '88a6f47f3e29e4bb1da2d854ea840272897f24fa3b90efebf5a72bd97921b975'
UI_SHA = 'a4b4a573f9120cc91a113a692489f6ad7a51f8f6c36831535cbb2428b4dfb874'
START, SIZE = 0x8854, 640 * 480 * 2
ZIP_DATE = (2026, 10, 10, 12, 0, 0)


def digest(data):
    return sha256(data).hexdigest()


def package(data):
    stream = io.BytesIO()
    info = zipfile.ZipInfo('SPI_ROM.bin', ZIP_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(info, data)
    return b'WQW' + stream.getvalue()


def save(path, record):
    path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')


def prepare(output):
    output = output.resolve()
    if not output.is_relative_to(PRIVATE.resolve()) or output == PRIVATE.resolve() or output.exists():
        raise ValueError('Fresh private output required')
    baseline = BASELINE_PATH.read_bytes()
    assert len(baseline) == 8388608 and digest(baseline) == BASELINE_SHA
    assert digest(baseline[START:START+SIZE]) == BITMAP_SHA
    # Existing independent loader extraction verifies the stock pointer and size
    # instructions. They must still be exact in the installed Vesper baseline.
    spec = importlib.util.spec_from_file_location('loader', ROOT / 'build/extract-spi-loader.py')
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)
    original = PRIVATE / 'snes-mvp-return-20261010T003708Z/spi-readback/offline-review/spi-nor.bin'
    loader.extract(original)
    assert baseline[:0x100] == original.read_bytes()[:0x100]
    assert baseline[0x200:START] == original.read_bytes()[0x200:START]
    ui = (ROOT / 'releases/vesper-boot-1/ui.raw').read_bytes()
    assert digest(ui) == UI_SHA
    assert struct.unpack_from('<IIHHHH', ui) == (304, 31457920, 0, 0, 640, 480)
    bitmap = ui[304:304+SIZE]
    assert len(bitmap) == SIZE
    candidate = baseline[:START] + bitmap + baseline[START+SIZE:]
    assert len(candidate) == len(baseline)
    assert candidate[:START] == baseline[:START] and candidate[START+SIZE:] == baseline[START+SIZE:]
    blocks = [i for i in range(0, len(candidate), 65536) if candidate[i:i+65536] != baseline[i:i+65536]]
    assert blocks == list(range(0, 0xa0000, 65536))
    normal = package(candidate)
    crc = zlib.crc32(candidate)
    dos_time = ((ZIP_DATE[0]-1980)<<25) | (ZIP_DATE[1]<<21) | (ZIP_DATE[2]<<16) | (ZIP_DATE[3]<<11)
    expected = bytearray(candidate)
    struct.pack_into('<II', expected, 0x100, crc, dos_time)
    incompatible = bytearray(candidate)
    struct.pack_into('<I', incompatible, 0x108, struct.unpack_from('<I', candidate, 0x108)[0]+10)
    bad_crc = bytearray(normal)
    central = bad_crc.index(b'PK\x01\x02')
    bad_crc[central+16] ^= 1
    bad_crc[3+14] ^= 1
    already = bytearray(baseline)
    struct.pack_into('<I', already, 0x100, crc)
    files = {'baseline-installed.bin': baseline, 'spi-vesper-static.bin': candidate,
             'expected-after-vendor.bin': expected, 'fixture-compatible.bkp': normal,
             'fixture-incompatible.bkp': package(incompatible),
             'fixture-consistent-bad-crc.bkp': bad_crc, 'fixture-missing-prefix.bkp': normal[3:],
             'fixture-already-recorded-baseline.bin': already, 'vesper-static.rgb565': bitmap}
    output.mkdir()
    for name, raw in files.items():
        (output / name).write_bytes(raw)
        assert (output / name).read_bytes() == raw
    # Preview is a lossless interpretation of existing accepted pixels, not new art.
    from PIL import Image
    pixels = []
    for (v,) in struct.iter_unpack('<H', bitmap):
        r, g, b = (v>>11)&31, (v>>5)&63, v&31
        pixels.append(((r<<3)|(r>>2), (g<<2)|(g>>4), (b<<3)|(b>>2)))
    preview = Image.new('RGB', (640, 480))
    preview.putdata(pixels)
    preview.save(output / 'preview.png')
    result = {'version': 1, 'baseline_sha256': BASELINE_SHA,
              'candidate_sha256': digest(candidate), 'expected_after_vendor_sha256': digest(expected),
              'package_sha256': digest(normal), 'package_bytes': len(normal),
              'bitmap_offset': hex(START), 'bitmap_bytes': SIZE, 'dimensions': [640, 480],
              'pixel_format': 'little-endian RGB565', 'original_bitmap_sha256': BITMAP_SHA,
              'replacement_bitmap_sha256': digest(bitmap), 'accepted_ui_sha256': UI_SHA,
              'candidate_changes_only_bitmap': True, 'second_animation_rootfs_kernel_tables_unchanged': True,
              'boot_header_and_code_unchanged': True, 'changed_64k_blocks': [hex(i) for i in blocks],
              'vendor_metadata': {'crc_offset': '0x100', 'date_offset': '0x104',
                                  'crc32': f'{crc:08x}', 'zip_dos_time': f'{dos_time:08x}'},
              'files': {name: {'bytes': len(raw), 'sha256': digest(raw)} for name, raw in files.items()},
              'device_access': False, 'staged_to_card': False, 'physical_update': 'pending',
              'limits': 'Candidate only; loader/updater and bitmap-reference execution qualify separately. Boot ROM and physical display acceptance remain untested.'}
    save(output / 'preparation.json', result)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    print(json.dumps(prepare(p.parse_args().output), indent=2))
