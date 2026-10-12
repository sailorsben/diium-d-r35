"""Publish bounded contract proofs and staging identity, never private cores/state."""
from pathlib import Path
from hashlib import sha256
import importlib.util, json, sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/a7-pair-private-v1'
q=json.loads((OUT/'verification.json').read_text())
assert q['passed'] and q['native_client_qualified'] and q['wrapper_qualified']
installation=json.loads((Path(sys.argv[1])/'pair-installation.json').read_text())
assert installation['one_shot_armed'] and installation['all_fat_checks_clean'] and not installation['production_replacement']
manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)
for e in old['entries']:assert sha256((ROOT/e['published']).read_bytes()).hexdigest()==e['published_sha256']
dest=ROOT/'evidence/2026-10-11/a7-pair1-qualification';assert not dest.exists();dest.mkdir(parents=True)
entries=[]
for name in q['proof_hashes']:
    p=OUT/name;data=p.read_bytes();assert sha256(data).hexdigest()==q['proof_hashes'][name]
    (dest/name).write_bytes(data)
    entries.append({'source':p.relative_to(ROOT).as_posix(),'published':(dest/name).relative_to(ROOT).as_posix(),
        'source_sha256':sha256(data).hexdigest(),'published_sha256':sha256(data).hexdigest(),'bytes':len(data),'normalized':False})
release=ROOT/'releases/snes-a7-pair-1';assert not release.exists();release.mkdir()
published={'version':q['version'],'output_comparisons':q['output_comparisons'],'checks':q['checks'],'hardware_measured':False,
    'production_replacement':False,'limits':q['limits'],'card':'I:','protected_retro_files':installation['protected_retro_files'],
    'all_fat_checks_clean':True,'one_shot_armed':True,'physical_result':'PENDING',
    'artifact_sha256':{n:h for n,h in q['payload_hashes'].items() if not n.endswith('.state')},
    'owned_source_sha256':{n:h for n,h in q['source_hashes'].items() if not n.startswith('build/a7-pair-private-v1/')},
    'qualification_manifest_sha256':sha256((OUT/'verification.json').read_bytes()).hexdigest(),
    'staging_proof_sha256':sha256((Path(sys.argv[1])/'pair-installation.json').read_bytes()).hexdigest(),
    'private_archive':installation['archive'],'proofs':q['proof_hashes']}
for p in (ROOT/'build/install-a7-pair.py',Path(__file__)):
    published['owned_source_sha256'][p.relative_to(ROOT).as_posix()]=sha256(p.read_bytes()).hexdigest()
(release/'manifest.json').write_text(json.dumps(published,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('pair_publisher',ROOT/'build/publish-snes-1.19.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
manifest.write_bytes(m.append_manifest(raw,entries))
assert json.loads(manifest.read_bytes())['entries'][:len(old['entries'])]==old['entries']
print(f'Preserved {len(old["entries"])} prior evidence entries; published {len(entries)} contract logs and separate release identity')
