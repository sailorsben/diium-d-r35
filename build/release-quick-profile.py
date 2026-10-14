"""Freeze and publish bounded quick-profile receipts; private fixtures stay local."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/quick-profile-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def freeze(archive):
 a=json.loads((archive/'archive.json').read_text());q=json.loads((OUT/'qualification.json').read_text());p=json.loads((OUT/'plan.json').read_text())
 assert a['fat_clean'] and a['card_writes']==0 and q['passed'] and q['native_client_qualified'] and q['wrapper_qualified']
 assert len(q['actual_controller_runs'])==4 and sum(r['phase_samples'] for r in q['actual_controller_runs'])==200
 assert not (OUT/'verification.json').exists() and not p['frameskip']
 assert q['runner_sha256']==digest(OUT/'ability-suite') and q['wrapper_sha256']==digest(OUT/'launch.sh')
 for n,h in q['reused_proofs'].items():assert digest(ROOT/n)==h
 for n,c in p['cores'].items():assert digest(OUT/f'cores/{n}.so')==c['sha256']
 assert p['cores']['control']['sha256']==p['cores']['profile']['sha256']=='e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129'
 source=[ROOT/'build'/n for n in ('prepare-quick-profile.py','build-quick-profile.sh','quick-profile.h','qualify-quick-profile.py','release-quick-profile.py','install-quick-profile.py','report-quick-profile.py')]
 source += [ROOT/'docs'/n for n in ('snes-quick-profile.md','snes-quick-profile-test.txt')]
 source += [x for folder in (OUT,OUT/'runner') for x in folder.glob('*') if x.suffix in ('.c','.h') and x.is_file()]
 payload=[OUT/n for n in ('ability-suite','launch.sh','dispatch.sh','ROM-PATH.txt','plan.json')]+list((OUT/'cores').glob('*.so'))+[x for x in (OUT/'cases').rglob('*') if x.is_file()]
 proof=[OUT/'qualification.json',OUT/'abi.txt']+[ROOT/n for n in q['reused_proofs']]
 for key,items in (('source_hashes',source),('payload_hashes',payload),('proof_hashes',proof)):q[key]={x.relative_to(ROOT).as_posix():digest(x) for x in items}
 q.update(archive=archive.name,authorization=p['authorization'])
 (OUT/'verification.json').write_text(json.dumps(q,indent=2)+'\n')
 print('Frozen four-epoch profiling diagnostic; native result pending')
def publish(archive):
 spec=importlib.util.spec_from_file_location('release',ROOT/'build/publish-snes-1.19.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)['entries']
 for e in old:assert digest(ROOT/e['published'])==e['published_sha256']
 dest=ROOT/'evidence/2026-10-13/quick-profile';dest.mkdir(exist_ok=True);entries=[]
 pairs=[(OUT/'qualification.json','qualification.json'),(OUT/'verification.json','identity.json')]
 p=json.loads((OUT/'plan.json').read_text());p.pop('authorization');p['cases']=[{'fixture':c['seq'],'name':c['name']} for c in p['cases']]
 (OUT/'public-plan.json').write_text(json.dumps(p,indent=2)+'\n');pairs.append((OUT/'public-plan.json','plan.json'))
 if (archive/'profile-installation.json').exists():pairs.append((archive/'profile-installation.json','installation.json'))
 for src,name in pairs:
  d=dest/name;data=pub.public_text(src.read_bytes())
  if d.exists():assert d.read_bytes()==data
  else:d.write_bytes(data)
  if not any(e['published']==d.relative_to(ROOT).as_posix() for e in old):entries.append({'source':src.relative_to(ROOT).as_posix(),'published':d.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(d)})
 if entries:manifest.write_bytes(pub.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(old)]==old
 print('Published',len(entries),'bounded receipts; preserved',len(old),'old manifest entries')
if __name__=='__main__':
 archive=Path(sys.argv[2]).resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 {'freeze':freeze,'publish':publish}[sys.argv[1]](archive)
