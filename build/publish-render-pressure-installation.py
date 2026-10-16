"""Publish installation metadata only; preserve all existing evidence bytes."""
from pathlib import Path
from hashlib import sha256
import json, sys

ROOT = Path(__file__).resolve().parent.parent

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to(ROOT / 'device-evidence')
    verification = json.loads((archive / 'render-pressure-live-verification.json').read_text())
    assert verification['all_protected_exact'] and verification['payloads_exact'] and verification['marker_bytes_exact']
    assert verification['source_sha256'] == digest(ROOT / 'build/verify-render-pressure-installation.py')
    assert verification['installation_sha256'] == digest(archive / 'render-pressure-installation.json')
    manifest = ROOT / 'evidence/manifest.json'
    raw = manifest.read_bytes()
    data = json.loads(raw)
    for entry in data['entries']:
        assert digest(ROOT / entry['published']) == entry['published_sha256'], entry['published']
    for source, name in [('render-pressure-installation.json', 'installation.json'),
                         ('render-pressure-live-verification.json', 'live-verification.json')]:
        src = archive / source
        dst = ROOT / 'evidence/2026-10-15/render-pressure1' / name
        assert not dst.exists()
        dst.write_bytes(src.read_bytes())
        data['entries'].append(dict(source=src.relative_to(ROOT).as_posix(),
                                    published=dst.relative_to(ROOT).as_posix(),
                                    source_sha256=digest(src), published_sha256=digest(dst),
                                    bytes=dst.stat().st_size, normalized=False))
    encoded = (json.dumps(data, indent=2) + '\n').encode()
    manifest.write_bytes(encoded.replace(b'\n', b'\r\n') if b'\r\n' in raw else encoded)
    print(json.dumps(dict(all_proofs_verified=len(data['entries']), private_payloads_published=False)))

if __name__ == '__main__':
    main(Path(sys.argv[1]))
