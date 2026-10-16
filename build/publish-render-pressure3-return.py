"""Publish measured pressure3 metrics and source/input hashes only."""
from pathlib import Path
from hashlib import sha256
import json
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
    src=ROOT/'build/render-pressure3-return-private/return.json';r=json.loads(src.read_text())
    assert r['physical'] and r['source_sha256']==digest(ROOT/'build/evaluate-render-pressure3-return.py')
    archive=ROOT/'device-evidence'/r['archive']
    assert digest(archive/'archive.json')==r['archive_sha256']
    for name,h in r['inputs'].items():assert digest(archive/name)==h,name
    assert r['accepted']==62 and r['failed']==15
    manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();data=json.loads(raw)
    for e in data['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
    dst=ROOT/'evidence/2026-10-15/render-pressure3/return.json';assert not dst.exists();dst.write_bytes(src.read_bytes())
    data['entries'].append(dict(source=src.relative_to(ROOT).as_posix(),published=dst.relative_to(ROOT).as_posix(),source_sha256=digest(src),published_sha256=digest(dst),bytes=dst.stat().st_size,normalized=False))
    encoded=(json.dumps(data,indent=2)+'\n').encode();manifest.write_bytes(encoded.replace(b'\n',b'\r\n') if b'\r\n' in raw else encoded)
    print(json.dumps(dict(all_proofs_verified=len(data['entries']),input_files_verified=len(r['inputs']),private_payloads_published=False)))
if __name__=='__main__':main()
