"""Publish interpreted return metadata only, preserving earlier proof bytes."""
from pathlib import Path
from hashlib import sha256
import json
import sys

ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to(ROOT / 'device-evidence')
    source = archive / 'uart-state-return.json'
    record = json.loads(source.read_text())
    assert record['physical_archive'] == archive.name and record['mock'] is False
    assert record['valid_snapshots'] == 100 and record['module_loaded_unloaded']
    for name, expected in record['input_sha256'].items():
        assert digest(archive / name) == expected, name
    manifest = ROOT / 'evidence/manifest.json'
    data = json.loads(manifest.read_text())
    for entry in data['entries']:
        assert digest(ROOT / entry['published']) == entry['published_sha256'], entry['published']
    target = ROOT / 'evidence/2026-10-14/uart-state/return.json'
    assert not target.exists()
    target.write_bytes(source.read_bytes())
    data['entries'].append({'source': source.relative_to(ROOT).as_posix(), 'published': target.relative_to(ROOT).as_posix(),
        'source_sha256': digest(source), 'published_sha256': digest(target), 'bytes': target.stat().st_size, 'normalized': False})
    manifest.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'prior_published_hashes_verified': len(data['entries']) - 1, 'published': target.relative_to(ROOT).as_posix()}))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
