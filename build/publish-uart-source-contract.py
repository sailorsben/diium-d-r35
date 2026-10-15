"""Publish interpreted source-contract research, never vendor bodies."""
from pathlib import Path
from hashlib import sha256
import json
import sys

ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main(board=False):
    source = ROOT / 'device-evidence/uart-source-research' / ('board-contract.json' if board else 'contract-research.json')
    record = json.loads(source.read_text())
    assert not record['card_access'] and not record['production_gate'] and len(record['checks']) == 6
    for name, expected in record['sources'].items():
        assert digest(ROOT / name) == expected, name
    for entry in record.get('external_sources', []):
        assert len(entry['commit']) == 40 and entry['commit'] in entry['url']
    manifest = ROOT / 'evidence/manifest.json'
    data = json.loads(manifest.read_text())
    for entry in data['entries']:
        assert digest(ROOT / entry['published']) == entry['published_sha256'], entry['published']
    prior = len(data['entries'])
    target = ROOT / 'evidence/2026-10-15/uart-source-contract' / ('board.json' if board else 'research.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists()
    target.write_bytes(source.read_bytes())
    data['entries'].append({'source': source.relative_to(ROOT).as_posix(), 'published': target.relative_to(ROOT).as_posix(),
        'source_sha256': digest(source), 'published_sha256': digest(target), 'bytes': target.stat().st_size, 'normalized': False})
    manifest.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'prior_hashes_verified': prior, 'published': target.relative_to(ROOT).as_posix()}))


if __name__ == '__main__':
    main('--board' in sys.argv[1:])
