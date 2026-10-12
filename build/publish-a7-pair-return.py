"""Publish bounded A7 measurements only; preserve full return privately."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
archive=Path(sys.argv[1]).resolve();assert archive.is_relative_to(ROOT/'device-evidence')
analysis=json.loads((archive/'pair-analysis.json').read_text())
assert analysis['hardware_measured'] and analysis['card_writes']==0 and analysis['all_staged_payload_hashes_match']
manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)
for e in old['entries']:assert sha256((ROOT/e['published']).read_bytes()).hexdigest()==e['published_sha256']
dest=ROOT/'evidence/2026-10-11/a7-pair1-return';assert not dest.exists();dest.mkdir(parents=True)
files={archive/'pair-analysis.json':'analysis.json'}
for p in sorted((archive/'retro/snes-pair1').glob('pass-*/pair.csv')):files[p]=p.parent.name+'.csv'
assert len(files)==13
entries=[]
for p,name in files.items():
    source=p.read_bytes();published=source.replace(b'\r\n',b'\n');(dest/name).write_bytes(published)
    entries.append({'source':p.relative_to(ROOT).as_posix(),'published':(dest/name).relative_to(ROOT).as_posix(),
        'source_sha256':sha256(source).hexdigest(),'published_sha256':sha256(published).hexdigest(),
        'bytes':len(published),'normalized':published!=source})
spec=importlib.util.spec_from_file_location('pair_return_publisher',ROOT/'build/publish-snes-1.19.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
manifest.write_bytes(m.append_manifest(raw,entries))
assert json.loads(manifest.read_bytes())['entries'][:len(old['entries'])]==old['entries']
print(f'Preserved {len(old["entries"])} earlier entries; published analysis and12 bounded frame captures')
