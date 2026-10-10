"""Publish this return's curated metadata only; keep all firmware contents private."""
from pathlib import Path
from hashlib import sha256
import json

ROOT = Path(__file__).resolve().parent.parent
RETURN = ROOT / 'device-evidence/snes-mvp-return-20261010T003708Z'
RESTORE = ROOT / 'device-evidence/snes-mvp-return-20261010T003804Z'
INSPECTION = RETURN / 'spi-readback/boot-inspection'
PREFIX = 'evidence/2026-10-09/spi-readback-return/'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def publish():
    found = read(RETURN / 'readback-analysis.json')
    assert found['complete'] and found['marker_matches'] and not found['errors']
    assert found['pass_sha256'] == ['5c4ea86ca5c497a26136ee9a59d8a31085e15c8d1dc5f063b874a20c400d9e2b'] * 2
    assert read(RESTORE / 'readback-postrestore.json')['armed_profiles'] == []
    assert read(INSPECTION / 'qualification.json')['software_checks_passed']
    assert read(INSPECTION / 'inspection.json')['candidate']['full_flash_image_created'] is False
    for path in [RETURN / 'chkdsk-readback-return.txt', RESTORE / 'chkdsk-postrestore.txt']:
        assert 'found no problems' in path.read_text(encoding='utf-8-sig')
    selected = {
        'analysis.json': RETURN / 'readback-analysis.json',
        'preservation.json': RETURN / 'readback-preservation.json',
        'restoration.json': RESTORE / 'readback-restoration.json',
        'postrestore.json': RESTORE / 'readback-postrestore.json',
        'chkdsk-return.txt': RETURN / 'chkdsk-readback-return.txt',
        'chkdsk-postrestore.txt': RESTORE / 'chkdsk-postrestore.txt',
        'boot-inspection.json': INSPECTION / 'inspection.json',
        'boot-inspection-qualification.json': INSPECTION / 'qualification.json',
    }
    manifest = ROOT / 'evidence/manifest.json'
    original = manifest.read_bytes()
    existing = json.loads(original)['entries']
    assert not any(e['published'].startswith(PREFIX) for e in existing)
    for entry in existing:
        assert digest(ROOT / entry['published']) == entry['published_sha256'], entry['published']
    additions = []
    for name, path in selected.items():
        raw = path.read_bytes()
        normalized = raw.decode('utf-8-sig').replace('\r\r\n', '\n').replace('\r\n', '\n').replace('\r', '\n').encode()
        for bad in [b'Bearer ', b'github_pat_', b'ghp_', b'C:\\Users', b'.codex/attachments']:
            assert bad not in normalized
        target = ROOT / PREFIX / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as output:
            output.write(normalized)
        additions.append({'source': path.relative_to(ROOT).as_posix(),
            'published': target.relative_to(ROOT).as_posix(),
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
