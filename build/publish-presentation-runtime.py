"""Publish only verified integration metadata; preserve every old evidence hash."""
from pathlib import Path
from hashlib import sha256
import json, os, subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/presentation-runtime-private-v1'
DEST=ROOT/'evidence/2026-10-15/presentation-runtime'
def digest(p): return sha256(p.read_bytes()).hexdigest()
def main():
    q=json.loads((OUT/'qualification.json').read_text())
    c=json.loads((OUT/'controls-qualification.json').read_text())
    prep=json.loads((OUT/'preparation.json').read_text())
    assert q['passed'] and c['passed'] and not q['production_gate'] and not q['card_access']
    assert digest(OUT/'qualification.json')==c['qualification_sha256']
    assert digest(ROOT/'build/check-presentation-controls.py')==c['checker_sha256']
    assert digest(OUT/'runner/presentation-controls-check.c')==c['generated_fixture_sha256']
    assert digest(OUT/'controls.log')==c['log_sha256']
    assert digest(OUT/'preparation.json')==q['preparation_sha256']
    assert digest(OUT/'snes-mvp')==q['runner_sha256']
    assert digest(OUT/'plus-a7.so')==q['core_sha256']
    for group,base in [(q['sources'],ROOT),(q['generated_sources'],OUT),
                       (q['log_hashes'],OUT),(prep['frozen_sources'],ROOT),(prep['sources'],OUT)]:
        for n,h in group.items(): assert digest(base/n)==h,n
    # Production PCM is intentionally distinct from the pressure diagnostic.
    for n in ('audio-owner.c','audio-pipe.h','native-pcm.c','native-pcm.h'):
        assert digest(OUT/'runner'/n)==digest(ROOT/'build/demand-private-v1/runtime-v1'/n),n
    manifest=ROOT/'evidence/manifest.json'
    newline='\r\n' if b'\r\n' in manifest.read_bytes() else '\n'
    m=json.loads(manifest.read_text())
    for e in m['entries']: assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
    prior=len(m['entries'])
    size_cmd=(['wsl','--exec'] if os.name=='nt' else [])+[
        'arm-linux-gnueabihf-size','build/presentation-runtime-private-v1/snes-mvp',
        'build/demand-private-v1/owned-output-runner']
    size=subprocess.run(size_cmd,cwd=ROOT,capture_output=True,text=True,check=True).stdout
    # Metadata only, no arbitrary logs/private payloads copied into publication.
    public={**q,'executable_size':size,'production_audio_unchanged':True,
            'publisher_sha256':digest(Path(__file__)),'prior_published_hashes_verified':prior,
            'performance_gate':{'actual_runner_A7_saving':'UNMEASURED','added_A7_cost':'UNMEASURED',
                'remaining_FFVI_deficit':'UNMEASURED','scratch_heap_bytes':123008,
                'physical_cadence_input_audio':'PENDING','hardware_package':'NOT_PREPARED'}}
    DEST.mkdir(parents=True,exist_ok=True)
    for name,value,source in [('qualification.json',public,OUT/'qualification.json'),
                              ('controls-qualification.json',c,OUT/'controls-qualification.json')]:
        target=DEST/name;assert not target.exists(),target
        target.write_text(json.dumps(value,indent=2)+'\n')
        m['entries'].append({'source':source.relative_to(ROOT).as_posix(),
            'published':target.relative_to(ROOT).as_posix(),'source_sha256':digest(source),
            'published_sha256':digest(target),'bytes':target.stat().st_size,'normalized':value!=json.loads(source.read_text())})
    manifest.write_bytes((json.dumps(m,indent=2)+'\n').replace('\n',newline).encode('utf-8'))
    print(f'Published two metadata proofs; all {prior} prior published hashes verified; no card access')
if __name__=='__main__': main()
