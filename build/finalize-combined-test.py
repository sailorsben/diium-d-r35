"""Freeze the separately authorized measurement payload after all seam checks."""
from pathlib import Path
from hashlib import sha256
import json,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/combined-test-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def freeze(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
 q=json.loads((OUT/'qualification.json').read_text());plan=json.loads((OUT/'plan.json').read_text())
 assert q['passed'] and q['native_client_qualified'] and q['wrapper_qualified']
 assert len(plan['runs'])==48 and not plan['frameskip'] and plan['measurement_only']
 assert not (OUT/'verification.json').exists()
 assert len(q['actual_controller_runs'])==48 and len(plan['snapshot_migrations'])==24
 assert 'PASS:14' in (OUT/'headroom-check.log').read_text() and 'PASS synthetic-only model' in (OUT/'model-check.log').read_text()
 for r in q['reused_unchanged_core_proof']:assert digest(ROOT/r['proof'])==r['proof_sha256']
 for name,h in plan['cores'].items():assert digest(OUT/f'cores/{name}.so')==h['sha256']
 for m in plan['snapshot_migrations']:assert digest(OUT/f"cases/{m['fixture']:03d}/{m['variant']}.state")==m['state_sha256'] and m['payload_unchanged']
 source=[ROOT/'build'/n for n in ('prepare-combined-test.py','build-combined-test.sh','combined-test-main.c','combined-headroom.h','combined-headroom-check.c','check-combined-headroom.sh','check-combined-model.py','qualify-combined-test.py','finalize-combined-test.py','install-combined-test.py','report-combined-return.py','publish-combined-test.py')]
 source+=[ROOT/'docs'/n for n in ('snes-combined-measurement.md','snes-combined-test.txt')]
 source+=[p for folder in ('runner',) for p in (OUT/folder).rglob('*') if p.is_file() and p.suffix in ('.c','.h')]
 source+=[OUT/'main.c',OUT/'combined-identity.h']
 payload=[OUT/n for n in ('ability-suite','launch.sh','dispatch.sh','ROM-PATH.txt','plan.json')]+list((OUT/'cores').glob('*.so'))+[p for p in (OUT/'cases').rglob('*') if p.is_file()]
 proof=[OUT/n for n in ('qualification.json','abi.txt','mock.log','native.log','wrapper.log','headroom-check.log','model-check.log')]+[ROOT/r['proof'] for r in q['reused_unchanged_core_proof']]
 q={**q,'archive':archive.name,'authorization':plan['authorization'],'source_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in source},'payload_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in payload},'proof_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in proof}}
 (OUT/'verification.json').write_text(json.dumps(q,indent=2)+'\n');print('Frozen measurement-only 48-run payload; A7 result pending')
if __name__=='__main__':freeze(Path(sys.argv[1]))
