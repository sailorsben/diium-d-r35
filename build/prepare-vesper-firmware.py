"""Prepare a hash-bound PRIVATE offline image and updater fixtures; no device I/O.

Vendor-containing images/packages stay under ignored device-evidence. This is
preparation for verification, not an installer or permission to stage an update.
"""
from pathlib import Path
from hashlib import sha256
import argparse, io, json, struct, zipfile, zlib

ROOT = Path(__file__).resolve().parent.parent
FLASH = '5c4ea86ca5c497a26136ee9a59d8a31085e15c8d1dc5f063b874a20c400d9e2b'
GZIP = 'c21e859f68d04a600ad168b30d28d145c75139ac66580608a4a401e2f163ba94'
CPIO = '0be2ef40010501966e4729abe13ae5341b78802f8055d6b9b87afe4b52b1b9ea'


def digest(data):
    return sha256(data).hexdigest()


def package(data):
    stream = io.BytesIO()
    info = zipfile.ZipInfo('SPI_ROM.bin', (2026, 10, 9, 12, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(info, data)
    # The exact decoder's handling of prefix/relative ZIP offsets is checked by
    # the QEMU updater harness; it is not assumed from Python's ZIP implementation.
    return b'WQW' + stream.getvalue()


def prepare(image, rootfs, output):
    private = (ROOT / 'device-evidence').resolve()
    output = output.resolve()
    if not output.is_relative_to(private) or output == private or output.exists():
        raise ValueError('Fresh output inside ignored device-evidence required')
    original, compressed = image.read_bytes(), rootfs.read_bytes()
    assert len(original) == 8388608 and digest(original) == FLASH
    assert len(compressed) == 3297826 and digest(compressed) == GZIP
    decoder = zlib.decompressobj(31)
    cpio = decoder.decompress(compressed, 8455681)
    assert decoder.eof and not decoder.unused_data and len(cpio) == 8455680 and digest(cpio) == CPIO
    start, old_size, length_field = 0x301d10, 3406558, 0xc0040
    assert struct.unpack_from('<I', original, length_field)[0] == old_size
    assert original[start:start+10] == compressed[:10]
    data = bytearray(original)
    struct.pack_into('<I', data, length_field, len(compressed))
    data[start:start+old_size] = compressed + b'\xff' * (old_size-len(compressed))
    assert len(data) == len(original)
    assert data[:length_field] == original[:length_field]
    assert data[length_field+4:start] == original[length_field+4:start]
    assert data[start+old_size:] == original[start+old_size:]
    blocks = [offset for offset in range(0, len(data), 65536)
              if data[offset:offset+65536] != original[offset:offset+65536]]
    assert blocks == [0xc0000] + list(range(0x300000, 0x650000, 65536))
    normal = package(data)
    mismatch = bytearray(data)
    struct.pack_into('<I', mismatch, 0x108, struct.unpack_from('<I', data, 0x108)[0]+10)
    wrong_crc = bytearray(normal)
    central = wrong_crc.index(b'PK\x01\x02')
    wrong_crc[central+16] ^= 1
    consistent_bad_crc = bytearray(wrong_crc)
    consistent_bad_crc[3+14] ^= 1
    repeat_baseline = bytearray(original)
    struct.pack_into('<I', repeat_baseline, 0x100, zlib.crc32(data))
    files = {'spi-vesper-offline.bin': data, 'fixture-compatible.bkp': normal,
             'fixture-incompatible.bkp': package(mismatch),
             'fixture-bad-crc.bkp': wrong_crc, 'fixture-missing-prefix.bkp': normal[3:],
             'fixture-consistent-bad-crc.bkp': consistent_bad_crc,
             'fixture-already-recorded-baseline.bin': repeat_baseline}
    output.mkdir(parents=True)
    for name, contents in files.items():
        (output / name).write_bytes(contents)
        assert (output / name).read_bytes() == contents
    report = {'version': 1, 'baseline_sha256': FLASH, 'candidate_sha256': digest(data),
        'candidate_bytes': len(data), 'rootfs_gzip_sha256': GZIP,
        'rootfs_compressed_bytes': len(compressed), 'rootfs_slot_bytes': old_size,
        'changed_ranges': [{'offset': length_field, 'bytes': 4, 'purpose': 'initrd table length'},
                           {'offset': start, 'bytes': old_size, 'purpose': 'gzip rootfs plus FF tail'}],
        'all_other_flash_bytes_exact': True, 'changed_64k_blocks': [hex(b) for b in blocks],
        'shared_blocks': {'0xc0000': 'table plus initial kernel bytes; preserved kernel bytes must be rewritten together',
                          '0x300000': 'kernel tail plus rootfs start; preserved kernel tail must be rewritten together'},
        'bootloader_static_splash_kernel_dt_gpda_unchanged': True,
        'compatibility_word_offset': '0x108',
        'compatibility_word': hex(struct.unpack_from('<I', data, 0x108)[0]),
        'first_item_crc32': hex(zlib.crc32(data)),
        'files': {name: {'bytes': len(value), 'sha256': digest(value)} for name, value in files.items()},
        'device_access': False, 'staged_to_card': False, 'physical_flash_write': False,
        'recovery_qualified': False,
        'limits': 'Private candidate and rejection fixtures only. Actual loader/updater checks run separately. No physical-write or recovery qualification.'}
    (output / 'preparation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('image', type=Path)
    p.add_argument('rootfs', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(prepare(args.image, args.rootfs, args.output), indent=2))
