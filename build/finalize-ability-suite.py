"""Freeze exact measurement payload after bounded offline qualifications."""
from pathlib import Path
from hashlib import sha256
import csv,json,re
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ability-suite-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def freeze():
    assert not (OUT/'verification.json').exists()
    plan=json.loads((OUT/'plan-qualified-v2.json').read_text());assert len(plan['cases'])==400
    for c in plan['cases']:
        folder=OUT/'qualified-cases-v2'/f"{c['seq']:03d}"
        for name,key in [('scene.state','state_sha256'),('input.txt','input_sha256'),('expected.bin','expected_sha256')]:assert digest(folder/name)==c[key]
    assert 'PASS: consuming native provider' in (OUT/'native-v3.log').read_text()
    assert 'zero diagnostic card writes or global sync during ready child' in (OUT/'wrapper-check.log').read_text()
    abi=set(re.findall(r'GLIBC_(\d+)\.(\d+)',(OUT/'ability-suite-v4-abi.txt').read_text()))
    assert max((int(a),int(b)) for a,b in abi)<=(2,30)
    completed=set();executions=0;partial=[]
    for folder in ['mock-final','mock-revive','mock-families','mock-rage-tail-v3','mock-middle-v3','mock-final-v4','mock-palidor-v4']:
        log=(OUT/(folder+'.log')).read_text();assert 'failures=0' in log
        for p in (OUT/folder).glob('run-*'):
            result=(p/'result.txt').read_text();assert 'runner_rc=0' in result
            rows=list(csv.DictReader(x for x in (p/'animation.csv').read_text().splitlines() if not x.startswith('#')))
            if len(rows)!=1200:
                assert folder=='mock-final' and p.name=='run-073' and len(rows)==225
                partial.append({'case':73,'calls':225,'reason':'owned SIGINT stopped long offline sweep'});continue
            completed.add(int(p.name[4:]));executions+=1
    assert len(completed)==149 and executions==153
    target_checks=json.loads((OUT/'target-checks-v2.json').read_text());assert len(target_checks)==29
    payload=['ability-suite-v4','plus-a7.so','launch.sh','dispatch.sh','ROM-PATH.txt','plan-qualified-v2.json']
    files=[OUT/n for n in payload]+[p for p in (OUT/'qualified-cases-v2').rglob('*') if p.is_file()]
    source=[ROOT/'build'/n for n in ['ability-suite-main.c','ability-observer.h','prepare-ability-suite.py','build-ability-suite.sh','check-ability-suite.py','qualify-ability-suite.py','finalize-ability-suite.py','install-ability-suite.py','glibc230-stat-compat.c']]
    source+=[ROOT/'docs'/n for n in ['snes-ability-suite.md','snes-ability-suite-test.txt']]
    source+=[p for p in (OUT/'runner').iterdir() if p.suffix in ('.c','.h')]
    proof=[OUT/n for n in ['native-v3.log','wrapper-check.log','target-checks-v2.json','ability-suite-v4-abi.txt']]
    q={'version':'1.19-ability1','archive':plan['archive'],'authorization':plan['authorization'],
       'passed':True,'native_client_qualified':True,'wrapper_qualified':True,'renderer_changed':False,
       'production_gate_passed':False,'hardware_measured':False,'hardware_result':'PENDING',
       'core_sha256':digest(OUT/'plus-a7.so'),'runner_sha256':digest(OUT/'ability-suite-v4'),
       'wrapper_sha256':digest(OUT/'launch.sh'),'case_count':400,'calls_per_case':1200,
       'nominal_minutes_before_reset_flush_overhead':133.505236,'offline_completed_case_contexts':149,
       'offline_full_bound_executions':153,'offline_animation_completion_not_proven':True,
       'preserved_partial_offline_cases':partial,
       'source_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in source},
       'payload_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in files},
       'proof_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in proof}}
    assert q['core_sha256']==plan['working_core_sha256']
    (OUT/'verification.json').write_text(json.dumps(q,indent=2)+'\n')
    print('PASS: exact runner/core/wrapper and400 fixture payload frozen;149 offline contexts;A7 result pending')
if __name__=='__main__':freeze()
