"""Publish bounded offline counts/qualification, never ROMs/states or raw returns."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/partial-selective-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 q=json.loads((OUT/'qualification.json').read_text());old=json.loads((ROOT/'build/partial-candidates-private-v1/qualification.json').read_text());model=json.loads((OUT/'workback.json').read_text());assert q['passed'] and old['passed'] and model['proofs']['total_original_output_calls']==18000
 for folder,receipt in ((OUT,q),(ROOT/'build/partial-candidates-private-v1',old)):
  for c in receipt['comparisons']:assert digest(folder/f"{c['variant']}/snes9x2005_plus_libretro.so")==c['core_sha256'] and digest(folder/f"exact/{c['case']:03d}-{c['variant']}.log")==c['log_sha256']
  assert json.loads((folder/'oracles.json').read_text())['passed']
 for folder,header in [('partial-merge-private-v1','partial-merge-census.h'),('partial-preflight-private-v1','partial-preflight-census.h')]:
  analysis=json.loads((ROOT/f'build/{folder}/analysis.json').read_text());assert analysis['passed']
  for c in analysis['cases']:assert digest(ROOT/f"build/{folder}/profile-core/snes9x2005_plus_libretro.so")==c['core_sha256'] and digest(ROOT/f"build/{folder}/exact/{c['case']:03d}.log")==c['log_sha256']
  assert digest(ROOT/'build'/header)==digest(ROOT/f'build/{folder}/profile-core/source/a7_partial_merge.h')
 for name,folder in [('local','partial-candidates-private-v1'),('sparse','partial-candidates-private-v1'),('selective','partial-selective-private-v1')]:
  assert digest(ROOT/f'build/partial-merge-{name}.h')==digest(ROOT/f'build/{folder}/{name}/source/a7_common_batch.h')
  assert digest(ROOT/'build/partial-merge-kernels.h')==digest(ROOT/f'build/{folder}/{name}/source/a7_partial_kernels.h')
 staged=json.loads((ROOT/'build/combined-test-private-v1/verification.json').read_text())
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for n,h in staged[group].items():assert digest(ROOT/n)==h,n
 source=[ROOT/'build'/n for n in ('analyze-partial-merge.py','build-partial-candidates.sh','build-partial-merge.sh','build-partial-preflight.sh','build-partial-selective.sh','check-partial-candidates.py','inspect-partial-merge.sh','partial-merge-census.h','partial-merge-kernel-check.c','partial-merge-kernels.h','partial-merge-local.h','partial-merge-selective.h','partial-merge-sparse.h','partial-preflight-census.h','prepare-partial-candidates.py','prepare-partial-merge.py','prepare-partial-preflight.py','prepare-partial-selective.py','qualify-partial-candidates.py','report-partial-workback.py','summarize-partial-assembly.py','publish-partial-workback.py')]+[ROOT/'docs/snes-meteor-quasar-partial-workback.md']
 for p in source:
  assert b'\r' not in p.read_bytes(),p
  if p.suffix=='.py':compile(p.read_text(),str(p),'exec')
 spec=importlib.util.spec_from_file_location('partial_public',ROOT/'build/publish-snes-1.19.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();prior=json.loads(raw)['entries']
 for e in prior:assert digest(ROOT/e['published'])==e['published_sha256']
 identity={'source_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in source},'prior_staged_local_source_payload_proofs_unchanged':True,'staged_identity_sha256':digest(ROOT/'build/combined-test-private-v1/verification.json'),'card_access':False,'installed':False,'A7_savings_measured':False,'QEMU_timings_used':False,'production_gate_passed':False}
 (OUT/'workback-identity.json').write_text(json.dumps(identity,indent=2)+'\n')
 public=ROOT/'evidence/2026-10-13/partial-merge';assert not public.exists();public.mkdir()
 pairs=((ROOT/'build/partial-merge-private-v1/analysis.json','mask-census.json'),(ROOT/'build/partial-preflight-private-v1/analysis.json','depth-probe-census.json'),(ROOT/'build/partial-candidates-private-v1/qualification.json','prototypes-qualified.json'),(ROOT/'build/partial-candidates-private-v1/oracles.json','prototypes-oracles.json'),(OUT/'qualification.json','selective-qualified.json'),(OUT/'oracles.json','selective-oracles.json'),(OUT/'workback.json','workback.json'),(OUT/'workback-identity.json','identity.json'),(ROOT/'build/partial-candidates-private-v1/kernel-check.log','mask-kernel-check.txt'))
 entries=[]
 for src,name in pairs:
  dest=public/name;dest.write_bytes(pub.public_text(src.read_bytes()));entries.append({'source':src.relative_to(ROOT).as_posix(),'published':dest.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(dest)})
 manifest.write_bytes(pub.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(prior)]==prior
 print('Published',len(entries),'bounded offline receipts; preserved',len(prior),'old entries; current card test unchanged')
if __name__=='__main__':main()
