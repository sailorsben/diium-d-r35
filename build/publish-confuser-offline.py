"""Publish bounded work counts/proofs; never ROM, saves, screenshots or cores."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/confuser-private-v1'
a=json.loads((OUT/'analysis.json').read_text())
assert not a['hardware_prices_measured'] and not a['qemu_timings_used'] and not a['card_access']
assert a['production_cores_unchanged'] and a['output_comparison_frames']==10800
dest=ROOT/'evidence/2026-10-11/confuser-offline'
assert not dest.exists()
manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)
for entry in old['entries']:
    assert sha256((ROOT/entry['published']).read_bytes()).hexdigest()==entry['published_sha256']
dest.mkdir(parents=True)
files={OUT/'analysis.json':'analysis.json',OUT/'effect-counts.csv':'effect-counts.csv'}
for rel,h in a['proofs'].items():
    p=ROOT/rel;assert sha256(p.read_bytes()).hexdigest()==h
    label=p.parent.name+'-'+p.name if p.parent!=OUT else p.name
    assert label not in files.values();files[p]=label
assert len(files)==13
entries=[]
for p,name in files.items():
    source=p.read_bytes();published=source.replace(b'\r\n',b'\n')
    (dest/name).write_bytes(published)
    entries.append({'source':p.relative_to(ROOT).as_posix(),'published':(dest/name).relative_to(ROOT).as_posix(),
      'source_sha256':sha256(source).hexdigest(),'published_sha256':sha256(published).hexdigest(),
      'bytes':len(published),'normalized':published!=source})
spec=importlib.util.spec_from_file_location('confuser_publisher',ROOT/'build/publish-snes-1.19.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
manifest.write_bytes(m.append_manifest(raw,entries))
assert json.loads(manifest.read_bytes())['entries'][:len(old['entries'])]==old['entries']
print(f'Published {len(entries)} bounded files; preserved {len(old["entries"])} earlier entries')
