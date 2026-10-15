"""Publish verified interpreted metadata; preserve every prior proof byte."""
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
    source = archive / 'uart-pair-return.json'
    record = json.loads(source.read_text())
    assert record['physical_archive'] == archive.name and record['mock'] is False
    assert record['handler_restored'] and record['module_loaded_unloaded']
    assert record['same_handler_enable_and_GIC_correlation_observed']
    assert record['hook_count_matches_bracketed_irq_growth'] and record['complete_histogram']
    assert record['frozen']['gic_errors'] == record['frozen']['bypass'] == 0
    for name, expected in record['input_sha256'].items():
        assert digest(archive / name) == expected, name
    install = ROOT / 'evidence/2026-10-15/uart-pair/installation.json'
    assert digest(install) == record['installation_receipt_sha256']
    manifest = ROOT / 'evidence/manifest.json'
    original = manifest.read_bytes()
    data = json.loads(original)
    prior = len(data['entries'])
    for entry in data['entries']:
        assert digest(ROOT / entry['published']) == entry['published_sha256'], entry['published']
    target = ROOT / 'evidence/2026-10-15/uart-pair/return.json'
    assert not target.exists()
    target.write_bytes(source.read_bytes())
    data['entries'].append({'source': source.relative_to(ROOT).as_posix(),
        'published': target.relative_to(ROOT).as_posix(), 'source_sha256': digest(source),
        'published_sha256': digest(target), 'bytes': target.stat().st_size, 'normalized': False})
    encoded = (json.dumps(data, indent=2) + '\n').encode()
    if b'\r\n' in original:
        encoded = encoded.replace(b'\n', b'\r\n')
    manifest.write_bytes(encoded)
    print(json.dumps({'prior_proofs_verified': prior, 'published': target.relative_to(ROOT).as_posix()}))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
