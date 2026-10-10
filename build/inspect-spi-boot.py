"""Inspect the exact private SPI readback and prepare a rootfs-only candidate.

No device access, execution of vendor code, full flash-image generation or update
staging. All extracted/candidate vendor contents are restricted to device-evidence.
"""
from pathlib import Path
from hashlib import sha256
import argparse, io, json, stat, struct, zipfile, zlib

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = '5c4ea86ca5c497a26136ee9a59d8a31085e15c8d1dc5f063b874a20c400d9e2b'
STOCK = '436d8018808b150c926274575a195f664e61db646f44713371019e9ae10caf3b'
PATCHED = 'ab56a67ae629e816a5752b1ad7cec2c335b46c82df84856f8a41376d2f919ebe'
MAX_OUTPUT = 32 * 1024 * 1024


def digest(data):
    return sha256(data).hexdigest()


def gunzip(data):
    decoder = zlib.decompressobj(31)
    result = decoder.decompress(data, MAX_OUTPUT + 1)
    if len(result) > MAX_OUTPUT or not decoder.eof or decoder.unconsumed_tail:
        raise ValueError('Truncated or oversized gzip stream')
    return result, len(data) - len(decoder.unused_data)


def newc(data):
    """Parse bounded newc metadata only; never extract paths or create nodes."""
    if len(data) > MAX_OUTPUT:
        raise ValueError('Oversized archive')
    offset, entries, seen = 0, [], {}
    for _ in range(4096):
        if offset + 110 > len(data) or data[offset:offset + 6] != b'070701':
            raise ValueError('Missing/truncated newc header')
        fields = [int(data[offset + 6 + i * 8:offset + 14 + i * 8], 16) for i in range(13)]
        mode, size, namesize = fields[1], fields[6], fields[11]
        if not 1 <= namesize <= 4096 or offset + 110 + namesize > len(data):
            raise ValueError('Invalid name length')
        name = data[offset + 110:offset + 110 + namesize]
        if name[-1:] != b'\0' or b'\0' in name[:-1]:
            raise ValueError('Invalid archive name')
        name = name[:-1].decode('utf-8')
        if name.startswith('/') or '..' in name.split('/'):
            raise ValueError('Duplicate or unsafe archive name')
        # The vendor archive repeats directory records. Preserve their order;
        # refuse repeated file bodies that could hide an overwritten splash.
        if name in seen and not (stat.S_ISDIR(mode) and stat.S_ISDIR(seen[name])):
            raise ValueError('Duplicate non-directory archive name')
        seen[name] = mode
        body = (offset + 110 + namesize + 3) & ~3
        end = body + size
        if end > len(data):
            raise ValueError('Truncated body')
        if fields[12] != 0:
            raise ValueError('Unexpected newc checksum')
        entries.append({'name': name, 'mode': mode, 'bytes': size,
                        'header_offset': offset, 'data_offset': body,
                        'sha256': digest(data[body:end])})
        offset = (end + 3) & ~3
        if name == 'TRAILER!!!':
            if size or offset > len(data) or any(data[offset:]):
                raise ValueError('Invalid trailer/padding')
            return entries
    raise ValueError('Entry budget exceeded')


def inspect(image, output):
    private = ROOT / 'device-evidence'
    output = Path(output).resolve()
    if not output.is_relative_to(private.resolve()) or output == private.resolve():
        raise ValueError('Vendor contents must stay inside ignored device-evidence')
    if output.exists():
        raise ValueError('Use a fresh private output directory')
    data = Path(image).read_bytes()
    assert len(data) == 8388608 and digest(data) == EXPECTED, 'Exact returned image required'
    assert data[:8] == b'PGpssiip'
    base = 0xc0000
    sections = []
    expected = [('kernel', 0x78, 0x241c98, 0x8000),
                ('initrd', 0x241d10, 0x33fade, 0xa00000),
                ('cmdline', 0x5817ee, 0x28fa, 0x100)]
    for i, (label, relative, size, address) in enumerate(expected):
        off = base + 36 * i
        kind, header_length = struct.unpack_from('<II', data, off)
        name = data[off + 8:off + 24].rstrip(b'\0').decode('ascii')
        start, length, load = struct.unpack_from('<III', data, off + 24)
        assert (kind, header_length, name, start, length, load) == (1, 28, label, relative, size, address)
        payload = data[base + start:base + start + length]
        sections.append({'name': name, 'offset': base + start, 'bytes': length,
                         'load_address': load, 'sha256': digest(payload)})
    assert struct.unpack_from('<III', data, base + 108) == (2, 4, 0x8000)
    assert struct.unpack_from('<I', data, base + 0x78 + 0x24)[0] == 0x016f2818
    dt = sections[2]
    assert struct.unpack_from('>II', data, dt['offset']) == (0xd00dfeed, dt['bytes'])
    root_section = sections[1]
    compressed = data[root_section['offset']:root_section['offset'] + root_section['bytes']]
    rootfs, consumed = gunzip(compressed)
    assert consumed == len(compressed) and len(rootfs) == 8455680
    entries = newc(rootfs)
    assert len(entries) == 559
    selected = {e['name']: e for e in entries if e['name'] in
                ['showlogo', 'init.project.rc', 'init', 'power_key', 'wdt', 'sysinit']}
    logo = selected['showlogo']
    assert stat.S_ISREG(logo['mode']) and logo['bytes'] == 198408 and logo['sha256'] == STOCK
    script = selected['init.project.rc']
    script_data = rootfs[script['data_offset']:script['data_offset'] + script['bytes']]
    assert b'/showlogo &' in script_data and script_data.index(b'/showlogo &') < script_data.index(b'/usr/retro/init &')
    assert selected['power_key']['sha256'] == 'a754c50d9843eb94e163424988b86a313a642899441a7847aa3e60b393ac12eb'
    assert selected['wdt']['sha256'] == '6a8d50aae684876074b54dc1b43acdc456a964d913aae6997b2f54fa5d97094a'
    release = ROOT / 'releases/vesper-boot-1'
    art = json.loads((release / 'manifest.json').read_text())
    encoded = (release / 'logo.zip').read_bytes()
    assert digest(encoded) == art['logo_zip_sha256'] and len(encoded) == 0x29bf4 - 0x7180
    with zipfile.ZipFile(io.BytesIO(encoded)) as archive:
        assert archive.testzip() is None and digest(archive.read('ui.raw')) == art['ui_raw_sha256']
    original_logo = rootfs[logo['data_offset']:logo['data_offset'] + logo['bytes']]
    replacement = original_logo[:0x7180] + encoded + original_logo[0x29bf4:]
    assert digest(replacement) == PATCHED and len(replacement) == len(original_logo)
    start = logo['data_offset'] + 0x7180
    end = logo['data_offset'] + 0x29bf4
    candidate = rootfs[:start] + encoded + rootfs[end:]
    changed = [e['name'] for e, updated in zip(entries, newc(candidate)) if e != updated]
    assert changed == ['showlogo'] and candidate[:start] == rootfs[:start] and candidate[end:] == rootfs[end:]
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
    gzip_candidate = compressed[:10] + compressor.compress(candidate) + compressor.flush()
    gzip_candidate += struct.pack('<II', zlib.crc32(candidate), len(candidate))
    decoded, used = gunzip(gzip_candidate)
    assert decoded == candidate and used == len(gzip_candidate)
    assert len(gzip_candidate) <= len(compressed), 'Candidate exceeds current initrd allocation'
    report = {'version': 1, 'flash_sha256': EXPECTED, 'flash_bytes': len(data),
        'section_table_offset': base, 'sections': sections,
        'rootfs': {'compression': 'gzip', 'format': 'cpio newc', 'bytes': len(rootfs),
                   'sha256': digest(rootfs), 'records_including_trailer': len(entries),
                   'selected_entries': selected},
        'candidate': {'stage': 'offline rootfs only; not an installable firmware package',
                      'changed_files': changed, 'all_other_cpio_bytes_unchanged': True,
                      'showlogo_sha256': PATCHED, 'rootfs_sha256': digest(candidate),
                      'compressed_sha256': digest(gzip_candidate),
                      'compressed_bytes': len(gzip_candidate), 'current_slot_bytes': len(compressed),
                      'fits_current_slot': True, 'full_flash_image_created': False,
                      'staged_to_card': False, 'boot_image_validation_qualified': False,
                      'recovery_qualified': False},
        'flash_writes': False, 'vendor_code_executed': False,
        'limits': 'Exact table/payload extraction and offline rootfs replacement; bootloader checks, updater container, physical writes and recovery remain unqualified.'}
    output.mkdir(parents=True)
    for name, payload in [('rootfs-stock.cpio', rootfs), ('rootfs-vesper.cpio', candidate),
                          ('rootfs-vesper.cpio.gz', gzip_candidate),
                          ('showlogo-stock', original_logo), ('showlogo-vesper', replacement),
                          ('init.project.rc', script_data)]:
        (output / name).write_bytes(payload)
        assert digest((output / name).read_bytes()) == digest(payload)
    (output / 'rootfs-index.json').write_text(json.dumps(entries, indent=2) + '\n', encoding='utf-8', newline='\n')
    (output / 'inspection.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.image, args.output), indent=2))
