"""Publish bounded correctness/count/prediction receipts, never private inputs."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json
ROOT=Path(__file__).resolve().parent.parent

def digest(p):return sha256(p.read_bytes()).hexdigest()

if __name__=='__main__':
    fixed=ROOT/'build/fixed-rows-private-v3'
    prediction=json.loads((fixed/'prediction.json').read_text())
    assert prediction['card_writes']==0 and not prediction['production_gate_passed']
    assert not prediction['frameskip_authorized'] and prediction['full_fidelity_required']
    spec=importlib.util.spec_from_file_location('release',ROOT/'build/publish-snes-1.19.py')
    release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
    manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();prior=json.loads(raw)['entries']
    for e in prior:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
    public=ROOT/'evidence/2026-10-13/full-fidelity-paths';assert not public.exists();public.mkdir()
    pairs=(('build/fixed-rows-private-v3/qualification.json','fixed-rows.json'),
        ('build/subscreen-rows-private-v1/qualification.json','subscreen-rows.json'),
        ('build/dsp-dead-work-private-v1/qualification.json','DSP-dead-work.json'),
        ('build/fixed-rows-private-v3/screen.json','animation-screen.json'),
        ('build/fixed-rows-private-v3/prediction.json','prediction.json'),
        ('build/fixed-rows-private-v3/row-check.log','row-oracle.txt'),
        ('build/subscreen-rows-private-v1/check.log','subscreen-oracle.txt'),
        ('build/fixed-rows-private-v3/clipping-candidate.log','clipping-oracle.txt'),
        ('build/fixed-rows-private-v3/clipping-exact.log','clipping-exact.txt'),
        ('build/fixed-rows-private-v3/clipping-old-counterexample.log','old-integration-counterexample.txt'))
    entries=[]
    for original,name in pairs:
        src=ROOT/original;dst=public/name;dst.write_bytes(release.public_text(src.read_bytes()))
        entries.append({'source':original,'published':dst.relative_to(ROOT).as_posix(),
                        'source_sha256':digest(src),'published_sha256':digest(dst)})
    manifest.write_bytes(release.append_manifest(raw,entries))
    assert json.loads(manifest.read_bytes())['entries'][:len(prior)]==prior
    print('Published10 bounded receipts; preserved',len(prior),'historical entries;no ROM/state/PCM/card exports')
