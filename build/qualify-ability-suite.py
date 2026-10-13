"""Preserve raw receipts; validate targets and normalize command-local identities."""
from pathlib import Path
from hashlib import sha256
import csv,json,shutil
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ability-suite-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(x for x in p.read_text().splitlines() if not x.startswith('#')))
def qualify():
    plan=json.loads((OUT/'plan-targeted.json').read_text());rom=(ROOT/'build/plus-a7-out/ff6.sfc').read_bytes()
    dest=OUT/'qualified-cases-v2';assert not dest.exists();dest.mkdir()
    for c in plan['cases']:
        path=f"{c['seq']:03d}";source=OUT/'targeted-cases'/path;target=dest/path;shutil.copytree(source,target)
        for name,key in [('scene.state','state_sha256'),('input.txt','input_sha256'),('expected.bin','expected_sha256')]:assert digest(source/name)==c[key]
        if c['family']=='tools' and c['possible_attack_ids']==[331]:
            c['possible_attack_ids'].append(336);c['random_or_conditional']=True
        ids=[i for i in c['possible_attack_ids'] if i<238 or c['family']=='tools'];raw=bytes([len(ids)])
        for i in ids:
            local=i-93 if c['family']=='blitz' else i-85 if c['family']=='bushido' else i-328 if c['family']=='tools' else i&255
            raw+=bytes([local])+rom[0x107fb2+i*14:0x107fb2+(i+1)*14]
        (target/'expected.bin').write_bytes(raw);c['expected_sha256']=digest(target/'expected.bin')
        (target/'case.json').write_text(json.dumps(c,indent=2)+'\n')
    (OUT/'plan-qualified-v2.json').write_text(json.dumps(plan,indent=2)+'\n')
    checks=[]
    for n in (48,49):
        r=rows(OUT/f'mock-revive/run-{n:03d}/animation.csv');assert int(r[0]['hp_wedge'])==0 and int(r[-1]['hp_wedge'])>0
        checks.append({'case':n,'ko_ally_revived':True})
    for n in range(121,137):
        r=rows(OUT/f'mock-families/run-{n:03d}/animation.csv');i=plan['cases'][n]['possible_attack_ids'][0]
        local=i-93 if n<129 else i-85
        prop=rom[0x107fb2+i*14:0x107fb2+(i+1)*14].hex()
        found=sum(x['attack']==f'{local:02x}' and x['properties']==prop for x in r)
        assert found>0,(n,local)
        checks.append({'case':n,'requested_properties_observed_samples':found,'command_local_attack':local})
    for n in (397,398,399):
        r=rows(OUT/f'mock-rage-tail-v3/run-{n:03d}/animation.csv');assert any(x['rage_terra']==f'{n-145:02x}' for x in r)
        checks.append({'case':n,'selected_rage_id':n-145})
    for n in range(113,121):
        r=rows(OUT/f'mock-middle-v3/run-{n:03d}/animation.csv');ids=plan['cases'][n]['possible_attack_ids']
        found=sum(any(x['attack']==f'{i-328:02x}' and x['properties']==rom[0x107fb2+i*14:0x107fb2+(i+1)*14].hex() for i in ids) for x in r)
        assert found>0,n
        checks.append({'case':n,'requested_tool_or_natural_branch_samples':found})
    (OUT/'target-checks-v2.json').write_text(json.dumps(checks,indent=2)+'\n')
    print('PASS:400 fixture hashes, KO target selection,16 Blitz/Bushido graphic identities,late Rage cursors')
if __name__=='__main__':qualify()
