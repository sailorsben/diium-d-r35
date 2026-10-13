"""Append bounded return evidence while retaining all prior manifest entries."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def publish(archive,suite):
    archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
    assert suite=='ability3'
    source=archive/'ability-analysis';s=json.loads((source/'summary.json').read_text())
    assert s['version']==f'1.19-{suite}' and s['card_writes']==0 and s['fat_clean'] and s['marker_consumed']
    assert s['exact_installed_payload_verified']==79
    spec=importlib.util.spec_from_file_location('release',ROOT/'build/publish-snes-1.19.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
    manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();prior=json.loads(raw)['entries']
    for e in prior:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
    public=ROOT/f'evidence/2026-10-13/{suite}-return';assert not public.exists();public.mkdir()
    entries=[]
    for n in ('summary.json','cases.json','aligned-comparison.json','verdict.json'):
        src=source/n;dst=public/n;dst.write_bytes(release.public_text(src.read_bytes()))
        entries.append({'source':src.relative_to(ROOT).as_posix(),'published':dst.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(dst)})
    manifest.write_bytes(release.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(prior)]==prior
    print('Published4 bounded return receipts; preserved',len(prior),'historical entries')
if __name__=='__main__':publish(Path(sys.argv[1]),sys.argv[2])
