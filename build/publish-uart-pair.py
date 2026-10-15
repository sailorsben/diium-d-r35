"""Publish interpreted status-probe proofs or its verified install receipt."""
from pathlib import Path
from hashlib import sha256
import json
import sys

ROOT = Path(__file__).resolve().parent.parent


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main(archive=None):
    manifest = ROOT / 'evidence/manifest.json'
    data = json.loads(manifest.read_text())
    for entry in data['entries']:
        assert digest(ROOT / entry['published']) == entry['published_sha256'], entry['published']
    prior = len(data['entries'])
    out = ROOT / 'evidence/2026-10-15/uart-pair'
    out.mkdir(exist_ok=True)
    if archive:
        archive = archive.resolve()
        assert archive.is_relative_to(ROOT / 'device-evidence')
        source = archive / 'uart-pair-installation.json'
        record = json.loads(source.read_text())
        assert record['original_status_capture'] and record['one_shot_armed'] and record['clean_FAT']
        assert record['ROM_unchanged'] and record['original_progress_unchanged']
        for name in ['chkdsk-before-uart-pair.txt', 'chkdsk-after-uart-pair-payload.txt', 'chkdsk-after-uart-pair-arm.txt']:
            health = (archive / name).read_text()
            assert '11EB-1465' in health and 'Windows has scanned the file system and found no problems.' in health
        pairs = [(source, out / 'installation.json')]
    else:
        private = ROOT / 'build/uart-pair-private'
        proof = json.loads((private / 'qualification.json').read_text())
        package = json.loads((private / 'package-qualification.json').read_text())
        assert len(proof['checks']) == 14 and len(package['owner_checks']) == 18
        assert digest(private / 'qualification.json') == package['compiled_module_qualification_sha256']
        for record in [proof, package]:
            for name, expected in record['sources'].items():
                assert digest(ROOT / name) == expected, name
        for name, expected in package['payloads'].items():
            assert digest(private / 'package' / name) == expected, name
        pairs = [(private / name, out / name) for name in ['prepared.json', 'qualification.json', 'package-qualification.json']]
    for source, target in pairs:
        assert not target.exists()
        target.write_bytes(source.read_bytes())
        data['entries'].append({'source': source.relative_to(ROOT).as_posix(), 'published': target.relative_to(ROOT).as_posix(),
            'source_sha256': digest(source), 'published_sha256': digest(target), 'bytes': target.stat().st_size, 'normalized': False})
    manifest.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'prior_hashes_verified': prior, 'published': len(pairs)}))


if __name__ == '__main__':
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
