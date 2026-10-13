"""Freeze reviewable predictions, exact source and authorized experimental payload."""
from pathlib import Path
from hashlib import sha256
import json,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ability3-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def freeze(archive):
    archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
    a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
    assert not (OUT/'verification.json').exists()
    q=json.loads((OUT/'qualification.json').read_text());plan=json.loads((OUT/'plan.json').read_text())
    assert q['passed'] and len(plan['cases'])==q['case_count']==18
    for c in plan['cases']:
        folder=OUT/f"cases/{c['seq']:03d}"
        for n,key in [('scene.state','state_sha256'),('input.txt','input_sha256'),('expected.bin','expected_sha256')]:assert digest(folder/n)==c[key]
    source=[ROOT/'build'/n for n in ('prepare-ability3.py','build-ability3.sh','qualify-ability3.py','report-ability3.py','finalize-ability3.py','install-ability3.py','ability-suite-main.c','ability-observer.h','plus-a7-multi-window.h','plus-a7-math-palette.h','plus-a7-math-check.c','check-ability3-math.sh','prepare-ability3-release.py','glibc230-stat-compat.c')]
    source+=[ROOT/'docs'/n for n in ('snes-ability3.md','snes-ability3-test.txt')]
    source+=[p for d in ('runner','core','counted-core') for p in (OUT/d).rglob('*') if p.is_file() and p.suffix in ('.c','.h')]
    source+=[OUT/'main.c',OUT/'compare.c',OUT/'core/link.T']
    payload=[OUT/n for n in ('ability-suite','plus-a7.so','launch.sh','dispatch.sh','ROM-PATH.txt','plan.json')]+[p for p in (OUT/'cases').rglob('*') if p.is_file()]
    proof=[OUT/n for n in ('qualification.json','predictions.json','abi.txt','mock.log','native.log','wrapper.log')]
    proof+=[OUT/'math-check.log',OUT/'qualify.py']
    proof+=list((OUT/'exact').glob('*.log'))+list((OUT/'census').glob('*.log'))
    q={**q,'archive':archive.name,'authorization':plan['authorization'],'renderer_changed':True,'hardware_result':'PENDING',
       'source_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in source},
       'payload_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in payload},
       'proof_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in proof}}
    (OUT/'verification.json').write_text(json.dumps(q,indent=2)+'\n')
    print('Frozen18-case experimental renderer regression; exact-output qualified, A7 saving pending')
if __name__=='__main__':freeze(Path(sys.argv[1]))
