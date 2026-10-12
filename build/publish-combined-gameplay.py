"""Publish manual-test identity and bounded proofs; all progress/core bytes private."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/combined-gameplay-private-v1'
archive=Path(sys.argv[1]).resolve();assert archive.is_relative_to(ROOT/'device-evidence')
q=json.loads((OUT/'verification.json').read_text())
installed=json.loads((archive/'manual-gameplay-installation.json').read_text())
assert q['passed'] and installed['one_shot_armed'] and installed['fat_checks_clean']
manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)
for e in old['entries']:assert sha256((ROOT/e['published']).read_bytes()).hexdigest()==e['published_sha256']
dest=ROOT/'evidence/2026-10-11/combined-gameplay1-qualification';assert not dest.exists();dest.mkdir(parents=True)
entries=[]
for name,h in q['proof_hashes'].items():
    p=OUT/name;data=p.read_bytes();assert sha256(data).hexdigest()==h
    public=data.replace(b'\r\n',b'\n');(dest/name).write_bytes(public)
    entries.append({'source':p.relative_to(ROOT).as_posix(),'published':(dest/name).relative_to(ROOT).as_posix(),
        'source_sha256':h,'published_sha256':sha256(public).hexdigest(),'bytes':len(public),'normalized':public!=data})
release=ROOT/'releases/snes-combined-gameplay-1';assert not release.exists();release.mkdir()
public={'version':q['version'],'core_sha256':q['core_sha256'],'core_crc32':q['core_crc32'],'core_bytes':q['core_bytes'],
    'regular_runner_sha256':q['regular_runner_sha256'],'manual_controls':True,'forced_replay':False,
    'qualification_checks':q['checks'],'long_gameplay_result':'PENDING','new_test_saves_separate':True,
    'original_progress_unchanged':True,'original_retro_files_protected':installed['original_retro_files_protected'],
    'one_shot_armed':True,'fat_checks_clean':True,'card':'I:','archive_before_writes':archive.name,
    'artifact_sha256':{n:h for n,h in q['payload_hashes'].items() if not n.startswith('saves/')},
    'source_hashes':q['source_hashes'],'proof_hashes':q['proof_hashes'],'timing_evidence':q['timing_evidence'],'telemetry':q['telemetry'],
    'qualification_sha256':sha256((OUT/'verification.json').read_bytes()).hexdigest(),
    'staging_sha256':sha256((archive/'manual-gameplay-installation.json').read_bytes()).hexdigest()}
for p in (ROOT/'build/install-combined-gameplay.py',Path(__file__)):
    public['source_hashes'][p.relative_to(ROOT).as_posix()]=sha256(p.read_bytes()).hexdigest()
(release/'manifest.json').write_bytes((json.dumps(public,indent=2)+'\n').encode())
spec=importlib.util.spec_from_file_location('manual_publisher',ROOT/'build/publish-snes-1.19.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
manifest.write_bytes(m.append_manifest(raw,entries))
assert json.loads(manifest.read_bytes())['entries'][:len(old['entries'])]==old['entries']
print(f'Preserved {len(old["entries"])} prior entries; published{len(entries)} manual-setup qualification proofs')
