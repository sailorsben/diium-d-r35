"""Publish this offline experiment's curated metadata only, never firmware files."""
from pathlib import Path
from hashlib import sha256
import json

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / 'device-evidence/snes-mvp-return-20261010T003708Z/spi-readback/firmware-qualified-candidate'
PREFIX = 'evidence/2026-10-09/firmware-offline-qualification/'


def publish():
    selected = ['loader-contract.json', 'preparation.json', 'qualification.json']
    qualification = json.loads((PRIVATE / 'qualification.json').read_text(encoding='utf-8'))
    assert qualification['all_checks_passed'] and len(qualification['checks']) == 9
    assert qualification['malformed_zip_fault_observed']
    assert not any(qualification[k] for k in ['device_access', 'staged_to_card', 'physical_flash_write', 'recovery_qualified'])
    for source, expected in qualification['source_sha256'].items():
        assert sha256((ROOT / source).read_bytes()).hexdigest() == expected
    manifest = ROOT / 'evidence/manifest.json'
    original = manifest.read_bytes()
    existing = json.loads(original)['entries']
    assert not any(e['published'].startswith(PREFIX) for e in existing)
    for entry in existing:
        assert sha256((ROOT / entry['published']).read_bytes()).hexdigest() == entry['published_sha256']
    additions = []
    for name in selected:
        source = PRIVATE / name
        raw = source.read_bytes()
        normalized = raw.decode('utf-8-sig').replace('\r\r\n', '\n').replace('\r\n', '\n').replace('\r', '\n').encode()
        for bad in [b'Bearer ', b'github_pat_', b'ghp_', b'C:\\Users', b'.codex/attachments']:
            assert bad not in normalized
        target = ROOT / PREFIX / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as output:
            output.write(normalized)
        additions.append({'source': source.relative_to(ROOT).as_posix(), 'published': target.relative_to(ROOT).as_posix(),
                          'source_sha256': sha256(raw).hexdigest(), 'published_sha256': sha256(normalized).hexdigest(),
                          'bytes': len(normalized), 'normalized': raw != normalized})
    closing = b'\r\n  ]\r\n}\r\n'
    assert original.endswith(closing)
    encoded = b',\r\n'.join(('\r\n'.join('    '+line for line in json.dumps(e, indent=2).splitlines())).encode() for e in additions)
    updated = original[:-len(closing)] + b',\r\n' + encoded + closing
    assert json.loads(updated)['entries'] == existing+additions
    manifest.write_bytes(updated)
    print(json.dumps({'published_metadata_files': len(additions), 'total_manifest_entries': len(existing)+len(additions),
                      'vendor_firmware_binaries_published': False}, indent=2))


if __name__ == '__main__':
    publish()
