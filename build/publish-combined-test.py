"""Publish bounded measurement qualification/install identity, no private inputs."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/combined-test-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def publish(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 installation=archive/'combined-installation.json';install=json.loads(installation.read_text()) if installation.exists() else None;q=json.loads((OUT/'verification.json').read_text());plan=json.loads((OUT/'plan.json').read_text())
 assert q['passed'] and q['measurement_only'] and not q['production_gate_passed'] and not q['frameskip']
 if install:assert install['one_shot_armed'] and not install['frameskip']
 spec=importlib.util.spec_from_file_location('combined_public',ROOT/'build/publish-snes-1.19.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();prior=json.loads(raw)['entries']
 for e in prior:assert digest(ROOT/e['published'])==e['published_sha256']
 public=ROOT/'evidence/2026-10-13/combined-measurement';public.mkdir(exist_ok=True)
 entries=[]
 pairs=((archive/'fullpaths-analysis/analysis.json','prior-return-analysis.json'),(archive/'fullpaths-return-integrity.json','prior-return-integrity.json'),(OUT/'qualification.json','qualification.json'),(OUT/'verification.json','identity.json'),(OUT/'headroom-check.log','headroom-check.txt'),(OUT/'model-check.log','model-check.txt'),(OUT/'native.log','native-check.txt'),(OUT/'wrapper.log','wrapper-check.txt'))
 if install:pairs+=((installation,'installation.json'),)
 for src,name in pairs:
  dest=public/name
  if dest.exists():assert dest.read_bytes()==release.public_text(src.read_bytes());continue
  dest.write_bytes(release.public_text(src.read_bytes()));entries.append({'source':src.relative_to(ROOT).as_posix(),'published':dest.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(dest)})
 summary={'version':plan['version'],'runs':plan['runs'],'contexts':[{'fixture':c['seq'],'name':c['name'],'family':c['family']} for c in plan['cases']],'cores':plan['cores'],'nominal_minutes':plan['nominal_minutes'],'every_frame':True,'measurement_only':True,'production_gate_passed':False,'A7_result':'PENDING','unchanged_core_proofs_reused_by_hash':True,'actual_offline_controller_calls':48*1200,'warmup_calls':120,'headroom_fraction':0.2,'period_ns':plan['period_ns'],'target_ns':plan['target_ns'],'logging':'RAM; diagnostic flush after audio join and display idle; included observer costs'}
 src=OUT/'public-plan.json';src.write_text(json.dumps(summary,indent=2)+'\n');dest=public/'plan.json';dest.write_bytes(release.public_text(src.read_bytes()));
 if not any(e['published']==dest.relative_to(ROOT).as_posix() for e in prior):entries.append({'source':src.relative_to(ROOT).as_posix(),'published':dest.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(dest)})
 if entries:manifest.write_bytes(release.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(prior)]==prior
 print('Published bounded measurement receipts; preserved',len(prior),'old entries; A7 result PENDING')
if __name__=='__main__':publish(Path(sys.argv[1]))
