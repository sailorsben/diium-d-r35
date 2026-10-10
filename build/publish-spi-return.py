"""Publish measured SPI metadata and readback-install checks, never flash contents."""
from pathlib import Path
from hashlib import sha256
import json

ROOT = Path(__file__).resolve().parent.parent
RETURN = ROOT / 'device-evidence/snes-mvp-return-20261010T000105Z'
RESTORE = ROOT / 'device-evidence/snes-mvp-return-20261010T000150Z'
INSTALL = ROOT / 'device-evidence/snes-mvp-return-20261010T001625Z'
PREFIX = 'evidence/2026-10-09/spi-identify-return/'
INSTALL_PREFIX = 'evidence/2026-10-09/spi-readback-install/'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def publish():
    found = read(RETURN / 'spi-analysis.json')
    assert found['complete'] and found['marker_matches']
    assert found['result']['ids'] == ['c84017c84017'] * 3
    assert found['result']['operations'] == 5 and found['result']['errno'] == 0
    assert found['result']['flash_writes'] is False and found['result']['global_config_writes'] is False
    assert read(RESTORE / 'spi-restoration.json')['init_sha256'] == 'b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
    assert read(INSTALL / 'readback-verification.json')['only_spi_readback_armed']
    assert read(INSTALL / 'readback-installation.json')['run_id'] == '5250ec9cd87740ff9fba5ec82ae3a707'
    for path in [RETURN / 'chkdsk-spi-return.txt', RESTORE / 'chkdsk-prerestore.txt', INSTALL / 'chkdsk-postreadback.txt']:
        assert 'found no problems' in path.read_text()
    qualification = read(ROOT / 'releases/spi-readback-1/qualification.json')
    assert qualification['software_checks_passed'] and len(qualification['checks']) == 9
    contract = {'measured_triplet': 'c84017', 'measured_six_byte_response': 'c84017c84017',
        'matched_family': 'GigaDevice 64-Mbit SPI NOR; exact suffix/package not identified',
        'nominal_capacity_bytes': 8388608, 'capacity_provenance': 'Matched primary manufacturer ID/density and Linux flash table; full physical readback pending',
        'read_opcode': '03', 'address_bits': 24, 'last_nominal_address': '0x7fffff',
        'manufacturer_reference': {'url': 'https://download.gigadevice.com/Datasheet/DS-00484-GD25Q64E-Rev1.6.pdf',
            'id_printed_page': 19, 'ordinary_read_printed_page': 22},
        'kernel_reference': 'https://raw.githubusercontent.com/torvalds/linux/v4.19/drivers/mtd/spi-nor/spi-nor.c',
        'kernel_table': 'gd25q64, ID0xc84017, 128 * 64KiB',
        'vendor_read_path': 'Exact privately preserved vrtemu uses03 + 24-bit address, command then receive transfer',
        'flash_writes': False, 'global_configuration_writes': False, 'recovery_qualified': False,
        'full_readback_physical_execution': 'pending', 'raw_flash_contents_published': False}
    contract_source = RETURN / 'chip-contract.json'
    contract_source.write_text(json.dumps(contract, indent=2) + '\n', encoding='utf-8', newline='\n')
    selected = {
        PREFIX + 'analysis.json': RETURN / 'spi-analysis.json',
        PREFIX + 'preservation.json': RETURN / 'spi-preservation.json',
        PREFIX + 'restoration.json': RESTORE / 'spi-restoration.json',
        PREFIX + 'chkdsk-return.txt': RETURN / 'chkdsk-spi-return.txt',
        PREFIX + 'chip-contract.json': contract_source,
        INSTALL_PREFIX + 'installation.json': INSTALL / 'readback-installation.json',
        INSTALL_PREFIX + 'verification.json': INSTALL / 'readback-verification.json',
        INSTALL_PREFIX + 'chkdsk-postinstall.txt': INSTALL / 'chkdsk-postreadback.txt',
    }
    manifest = ROOT / 'evidence/manifest.json'
    original = manifest.read_bytes()
    existing = json.loads(original)['entries']
    assert not any(e['published'].startswith((PREFIX, INSTALL_PREFIX)) for e in existing)
    for entry in existing:
        assert digest(ROOT / entry['published']) == entry['published_sha256'], entry['published']
    additions = []
    for published, path in selected.items():
        raw = path.read_bytes()
        normalized = raw.decode('utf-8-sig').replace('\r\r\n', '\n').replace('\r\n', '\n').replace('\r', '\n').encode()
        for bad in [b'Bearer ', b'github_pat_', b'ghp_', b'C:\\Users', b'.codex/attachments']:
            assert bad not in normalized
        target = ROOT / published
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(normalized)
        additions.append({'source': path.relative_to(ROOT).as_posix(), 'published': published,
            'source_sha256': sha256(raw).hexdigest(), 'published_sha256': digest(target),
            'bytes': len(normalized), 'normalized': raw != normalized})
    closing = b'\r\n  ]\r\n}\r\n'
    assert original.endswith(closing)
    encoded = b',\r\n'.join(('\r\n'.join('    ' + line for line in json.dumps(e, indent=2).splitlines())).encode() for e in additions)
    updated = original[:-len(closing)] + b',\r\n' + encoded + closing
    assert json.loads(updated)['entries'] == existing + additions
    manifest.write_bytes(updated)
    print(json.dumps({'published_metadata_files': len(additions), 'raw_flash_or_vendor_contents_published': False}, indent=2))


if __name__ == '__main__':
    publish()
