"""Publish bounded numeric evidence; never ROMs, states, SRAM or core binaries."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ff6-effect-screen-private-v1'
archive=Path(sys.argv[1]).resolve();assert archive.is_relative_to(ROOT/'device-evidence')
analysis=json.loads((OUT/'analysis.json').read_text())
assert analysis['general_exact_records']==analysis['current_exact_records']==406
assert analysis['total_exact_comparison_calls']==567000 and not analysis['QEMU_timings_used']
for path,h in analysis['raw_proof_sha256'].items():assert sha256((ROOT/path).read_bytes()).hexdigest()==h
returned=json.loads((archive/'confuser-gameplay-return-analysis.json').read_text())
assert not returned['write_errors'] and returned['calls']==7119 and returned['marker_consumed']
raw=(ROOT/'evidence/manifest.json').read_bytes();old=json.loads(raw)
for e in old['entries']:assert sha256((ROOT/e['published']).read_bytes()).hexdigest()==e['published_sha256']
dest=ROOT/'evidence/2026-10-12/effect-safety-screen';assert not dest.exists();dest.mkdir(parents=True)
natural='\n'.join(line for p in sorted((OUT/'natural').glob('*.log'))
    for line in p.read_text().splitlines() if line.startswith(('CASE ','PASS: ','IDENTITY ')))+'\n'
assert natural.count('IDENTITY init_hits=')==8
(OUT/'natural-proof-summary.log').write_text(natural)
sources=[archive/'confuser-gameplay-return-analysis.json']+[OUT/name for name in
    ('analysis.json','catalog.json','coverage.csv','window-pairs.csv','multi-window-oracle.log','natural-proof-summary.log')]
entries=[]
for source in sources:
    data=source.read_bytes();public=data.replace(b'\r\n',b'\n');target=dest/source.name;target.write_bytes(public)
    entries.append({'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
        'source_sha256':sha256(data).hexdigest(),'published_sha256':sha256(public).hexdigest(),
        'bytes':len(public),'normalized':data!=public})
spec=importlib.util.spec_from_file_location('screen_publisher',ROOT/'build/publish-snes-1.19.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
(ROOT/'evidence/manifest.json').write_bytes(module.append_manifest(raw,entries))
assert json.loads((ROOT/'evidence/manifest.json').read_bytes())['entries'][:len(old['entries'])]==old['entries']
print(f'Published{len(entries)} bounded files; preserved{len(old["entries"])} prior entries')
