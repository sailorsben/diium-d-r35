"""Publish source-bound return metrics and input hashes, never card payloads."""
from pathlib import Path
from hashlib import sha256
import json

ROOT = Path(__file__).resolve().parent.parent
def digest(p): return sha256(p.read_bytes()).hexdigest()

def main():
    src = ROOT / 'build/render-pressure-return-private/return.json'
    report = json.loads(src.read_text())
    assert report['physical'] and report['source_sha256'] == digest(ROOT/'build/evaluate-render-pressure-return.py')
    archive = ROOT/'device-evidence'/report['archive']
    assert report['archive_sha256'] == digest(archive/'archive.json')
    for name,h in report['inputs'].items(): assert digest(archive/name) == h, name
    assert report['end_to_end_accepted'] == 50 and report['completed_production_shutdown_failures'] == 5 and report['production_failures'] == 15
    manifest = ROOT/'evidence/manifest.json'; raw = manifest.read_bytes(); data = json.loads(raw)
    for entry in data['entries']: assert digest(ROOT/entry['published']) == entry['published_sha256'], entry['published']
    dst = ROOT/'evidence/2026-10-15/render-pressure1/return.json'; assert not dst.exists()
    dst.write_bytes(src.read_bytes())
    data['entries'].append(dict(source=src.relative_to(ROOT).as_posix(), published=dst.relative_to(ROOT).as_posix(),
                              source_sha256=digest(src), published_sha256=digest(dst), bytes=dst.stat().st_size, normalized=False))
    encoded = (json.dumps(data,indent=2)+'\n').encode()
    manifest.write_bytes(encoded.replace(b'\n',b'\r\n') if b'\r\n' in raw else encoded)
    print(json.dumps(dict(all_proofs_verified=len(data['entries']), return_inputs_verified=len(report['inputs']), private_payloads_published=False)))

if __name__ == '__main__': main()
