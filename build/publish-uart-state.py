"""Publish source-bound offline metadata; never vendor bytes or private packages."""
from pathlib import Path
from hashlib import sha256
import json

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/uart-kernel-private'


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main():
    module = json.loads((OUT / 'qualification.json').read_text())
    package = json.loads((OUT / 'package-qualification.json').read_text())
    assert len(module['checks']) == 15 and len(package['owner_checks']) == 12
    assert not module['installed'] and not package['card_access'] and not package['production_gate']
    assert digest(OUT / 'qualification.json') == package['compiled_module_qualification_sha256']
    for report in [module, package]:
        for name, expected in report['sources'].items():
            assert digest(ROOT / name) == expected, name
    for name, expected in package['payloads'].items():
        assert digest(OUT / 'package' / name) == expected, name
    manifest = ROOT / 'evidence/manifest.json'
    data = json.loads(manifest.read_text())
    prior = len(data['entries'])
    for entry in data['entries']:
        assert digest(ROOT / entry['published']) == entry['published_sha256'], entry['published']
    for name in ['prepared.json', 'qualification.json', 'package-qualification.json']:
        source = OUT / name
        target = ROOT / 'evidence/2026-10-14/uart-state' / name
        assert not target.exists()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        data['entries'].append({'source': source.relative_to(ROOT).as_posix(), 'published': target.relative_to(ROOT).as_posix(),
            'source_sha256': digest(source), 'published_sha256': digest(target), 'bytes': target.stat().st_size, 'normalized': False})
    manifest.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'prior_published_hashes_verified': prior, 'published_metadata': 3, 'card_access': False}))


if __name__ == '__main__':
    main()
