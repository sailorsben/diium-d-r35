"""Bounded numeric proofs only; no ROM, states, SRAM or vendor/core binaries."""
from pathlib import Path
from hashlib import sha256
import csv,importlib.util,io,json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ability-suite-private-v1'
PUBLIC=ROOT/'evidence/2026-10-12/ability-suite'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def publish():
    q=json.loads((OUT/'verification.json').read_text());assert q['passed'] and not q['hardware_measured']
    for group in ('source_hashes','payload_hashes','proof_hashes'):
        for n,h in q[group].items():assert digest(ROOT/n)==h,n
    install=ROOT/'device-evidence'/q['archive']/'ability-installation.json';i=json.loads(install.read_text())
    assert i['one_shot_armed'] and i['fat_checks_clean'] and i['original_progress_unchanged']
    plan=json.loads((OUT/'plan-qualified-v2.json').read_text())
    for n,h in i['payload_hashes'].items():
        source=OUT/'qualified-cases-v2'/n[6:] if n.startswith('cases/') else {'ability-suite':OUT/'ability-suite-v4',
            'plan.json':OUT/'plan-qualified-v2.json','suite-identity.json':OUT/'verification.json',
            'TEST-ME.txt':ROOT/'docs/snes-ability-suite-test.txt'}.get(n,OUT/n)
        assert digest(source)==h,n
    assert not PUBLIC.exists();PUBLIC.mkdir(parents=True)
    compact={k:v for k,v in q.items() if k not in ('source_hashes','payload_hashes','proof_hashes')}
    compact['core_and_stock_progress_preserved']=True
    compact['animation_matches_are_not_completion_proof']=True
    (OUT/'public-summary.json').write_text(json.dumps(compact,indent=2)+'\n')
    (OUT/'public-installation.json').write_text(json.dumps({k:v for k,v in i.items() if k!='payload_hashes'},indent=2)+'\n')
    table=io.StringIO(newline='');writer=csv.writer(table);writer.writerow(['case','family','name','possible_graphic_ids','calls','random_or_conditional','conditions'])
    for c in plan['cases']:writer.writerow([c['seq'],c['family'],c['name'],';'.join(map(str,c['possible_attack_ids'])),c['calls'],c['random_or_conditional'],';'.join(c['conditions'])])
    (OUT/'public-coverage.csv').write_text(table.getvalue(),newline='\n')
    proof='Offline contract checks; not A7 performance evidence.\n'+(OUT/'native-v3.log').read_text().split('PASS:')[-1].strip()+'\n'+(OUT/'wrapper-check.log').read_text()
    (OUT/'public-proof.log').write_text(proof,newline='\n')
    spec=importlib.util.spec_from_file_location('ability_release',ROOT/'build/publish-snes-1.19.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
    manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)['entries']
    for e in old:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
    entries=[]
    for source,name in [(OUT/'public-summary.json','summary.json'),(OUT/'public-installation.json','installation.json'),
        (OUT/'public-coverage.csv','coverage.csv'),(OUT/'public-proof.log','contract-proof.log'),(OUT/'target-checks-v2.json','target-checks.json')]:
        published=PUBLIC/name;published.write_bytes(release.public_text(source.read_bytes()))
        entries.append({'source':source.relative_to(ROOT).as_posix(),'published':published.relative_to(ROOT).as_posix(),
            'source_sha256':digest(source),'published_sha256':digest(published)})
    manifest.write_bytes(release.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(old)]==old
    print(f'Published5 bounded proofs; preserved{len(old)} historical manifest entries')
if __name__=='__main__':publish()
