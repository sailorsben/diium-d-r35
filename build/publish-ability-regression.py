"""Publish bounded qualification, cost sensitivity and protected staging metadata."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ability-regression-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def publish(archive):
    archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
    q=json.loads((OUT/'verification.json').read_text());installation=json.loads((archive/'ability2-installation.json').read_text())
    assert q['passed'] and installation['one_shot_armed'] and not q['production_gate_passed']
    for group in ('source_hashes','payload_hashes','proof_hashes'):
        for n,h in q[group].items():assert digest(ROOT/n)==h,n
    spec=importlib.util.spec_from_file_location('ability2_release',ROOT/'build/publish-snes-1.19.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
    manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)['entries']
    for e in old:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
    public=ROOT/'evidence/2026-10-13/ability-regression';assert not public.exists();public.mkdir(parents=True)
    summary={k:v for k,v in q.items() if k not in ('source_hashes','payload_hashes','proof_hashes')}
    summary['core_delta']='Counter-free Mode1 multi-background/irrelevant Window2 batching; other core code unchanged.'
    summary['hardware_result']='PENDING'
    (OUT/'public-qualification.json').write_text(json.dumps(summary,indent=2)+'\n')
    coverage={'version':q['version'],'cases':[{'seq':c['seq'],'original_case':c['original_case'],'name':c['name'],'family':c['family'],'observed_effect_id':c['observed_effect_id'],'calls':c['calls']} for c in json.loads((OUT/'plan.json').read_text())['cases']]}
    (OUT/'public-coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
    entries=[]
    for source,name in [(OUT/'public-qualification.json','qualification.json'),(OUT/'predictions.json','predictions.json'),(OUT/'public-coverage.json','coverage.json'),(archive/'ability2-installation.json','installation.json')]:
        published=public/name;published.write_bytes(release.public_text(source.read_bytes()))
        entries.append({'source':source.relative_to(ROOT).as_posix(),'published':published.relative_to(ROOT).as_posix(),'source_sha256':digest(source),'published_sha256':digest(published)})
    manifest.write_bytes(release.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(old)]==old
    print(f'Published4 bounded proofs; preserved{len(old)} historical entries')
if __name__=='__main__':publish(Path(sys.argv[1]))
