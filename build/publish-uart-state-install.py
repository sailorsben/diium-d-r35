"""Publish the verified one-shot installation receipt, without private contents."""
from pathlib import Path
from hashlib import sha256
import json
import sys

ROOT = Path(__file__).resolve().parent.parent


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to(ROOT / 'device-evidence')
    source = archive / 'uart-state-installation.json'
    record = json.loads(source.read_text())
    assert record['snapshot_only'] and record['one_shot_armed'] and record['clean_FAT']
    assert record['ROM_unchanged'] and record['original_progress_unchanged']
    assert record['protected_files'] == 7796 and record['source_commit'] == '3892f2a42da9950d6da81ec762fa8500d45b48b6'
    for name in ['chkdsk-before-uart-state.txt', 'chkdsk-after-uart-state-payload.txt', 'chkdsk-after-uart-state-arm.txt']:
        text = (archive / name).read_text()
        assert '11EB-1465' in text and 'Windows has scanned the file system and found no problems.' in text
    manifest = ROOT / 'evidence/manifest.json'
    data = json.loads(manifest.read_text())
    for entry in data['entries']:
        assert digest(ROOT / entry['published']) == entry['published_sha256'], entry['published']
    target = ROOT / 'evidence/2026-10-14/uart-state/installation.json'
    assert not target.exists()
    target.write_bytes(source.read_bytes())
    data['entries'].append({'source': source.relative_to(ROOT).as_posix(), 'published': target.relative_to(ROOT).as_posix(),
        'source_sha256': digest(source), 'published_sha256': digest(target), 'bytes': target.stat().st_size, 'normalized': False})
    manifest.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'prior_published_hashes_verified': len(data['entries']) - 1, 'published': target.relative_to(ROOT).as_posix()}))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
