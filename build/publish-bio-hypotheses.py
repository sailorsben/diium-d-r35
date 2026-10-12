"""Publish bounded offline counts/proofs; never private ROM/state/core artifacts."""
from pathlib import Path
from hashlib import sha256
import json,importlib.util
ROOT=Path(__file__).resolve().parent.parent
source=ROOT/'build/bio-hypotheses-private'
analysis=json.loads((source/'analysis.json').read_text())
assert analysis['production_core_unchanged'] and not analysis['hardware_performance_measured']
manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)
for e in old['entries']:
    assert sha256((ROOT/e['published']).read_bytes()).hexdigest()==e['published_sha256']
dest=ROOT/'evidence/2026-10-11/bio-offline-hypotheses'
assert not dest.exists(),'Preserve published evidence'
dest.mkdir(parents=True)
files={source/'analysis.json':'analysis.json',source/'effect-counts.csv':'effect-counts.csv',
       source/'fast-window-check.log':'fast-window-check.log'}
for name in analysis['variants']:
    files[source/name/'equivalence-bio.log']=name+'-equivalence-bio.log'
    p=source/name/'equivalence-general.log'
    if p.exists():files[p]=name+'-equivalence-general.log'
entries=[]
for p,name in files.items():
    data=p.read_bytes();(dest/name).write_bytes(data)
    entries.append(dict(source=p.relative_to(ROOT).as_posix(),published=(dest/name).relative_to(ROOT).as_posix(),
        source_sha256=sha256(data).hexdigest(),published_sha256=sha256(data).hexdigest(),bytes=len(data),normalized=False))
spec=importlib.util.spec_from_file_location('publisher',ROOT/'build/publish-snes-1.19.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
manifest.write_bytes(module.append_manifest(raw,entries))
assert json.loads(manifest.read_bytes())['entries'][:len(old['entries'])]==old['entries']
print(f'Preserved {len(old["entries"])} historical entries; published {len(entries)} count/proof files.')
