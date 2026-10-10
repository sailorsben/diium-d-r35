"""Publish owned runner/source qualification; exclude core, ROM and snapshot."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent;out=ROOT/'build'/sys.argv[1]
archive=ROOT/'device-evidence'/sys.argv[2]
def digest(p):return sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('cost_publisher',ROOT/'build/publish-snes-1.19.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
q=json.loads((out/'verification.json').read_text());assert q['passed'] and not q['hardware_measured']
for group in ('source_hashes','artifacts'):
    for p,wanted in q[group].items():assert digest(ROOT/p)==wanted,p
assert digest(out/'unit-suite')==q['suite_sha256']
readback=json.loads((archive/'independent-cost-readback.json').read_text());assert readback['passed'] and readback['fat_clean']
public={k:v for k,v in q.items() if k!='state_sha256'}
public['release_kind']='measurement-only owned ARM runner; A7 values pending; separate baseline diagnostic core not published'
public['logging']='bounded RAM; audio joined/display queue drained before flush; synchronized between independent passes'
public['support_source_hashes']={p.relative_to(ROOT).as_posix():digest(p) for p in (ROOT/'build').glob('*a7-cost*.py')}
release=ROOT/'releases/snes-a7-cost1';release.mkdir(exist_ok=True)
payload={'unit-suite':(out/'unit-suite').read_bytes(),'manifest.json':(json.dumps(public,indent=2)+'\n').encode(),
         'TEST-ME.txt':(ROOT/'docs/snes-a7-cost-test.txt').read_bytes(),'launch.sh':(out/'launch.sh').read_bytes()}
for name,raw in payload.items():
    p=release/name;assert not p.exists() or p.read_bytes()==raw;p.write_bytes(raw)
manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)
for e in old['entries']:assert digest(ROOT/e['published'])==e['published_sha256']
prefix=ROOT/'evidence/verification/snes-a7-cost1';assert not prefix.exists();prefix.mkdir()
sources={out/'equivalence.log':'equivalence.log',out/'native-check.log':'native-check.log',out/'suite-check.log':'suite-check.log',
         out/'runner-abi.txt':'runner-abi.txt',archive/'independent-cost-readback.json':'independent-cost-readback.json',
         archive/'chkdsk-independent-cost.txt':'chkdsk-independent-cost.txt'}
add=[]
for source,name in sources.items():
    original=source.read_bytes();clean=base.public_text(original);target=prefix/name;target.write_bytes(clean)
    add.append({'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
        'source_sha256':sha256(original).hexdigest(),'published_sha256':sha256(clean).hexdigest(),
        'bytes':len(clean),'normalized':original!=clean})
manifest.write_bytes(base.append_manifest(raw,add))
print(json.dumps({'historical_entries_preserved':len(old['entries']),'new_evidence_files':len(add),
                  'private_rom_core_snapshot_or_progress_published':False},indent=2))
