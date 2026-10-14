"""Publish bounded offline fusion evidence and verify the running test is untouched."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fused-toolbox-private-v2'

def digest(p):return sha256(p.read_bytes()).hexdigest()

def main():
 for folder in ('fused-toolbox-private-v1','fused-toolbox-private-v2','fused-count-private-v2'):
  base=ROOT/'build'/folder;q=json.loads((base/'qualification.json').read_text());assert q['passed']
  for c in q['comparisons']:
   core=base/('core/snes9x2005_plus_libretro.so' if folder=='fused-count-private-v2' else ('plus-a7.so' if c['label']=='ordinary' else 'counted-core/snes9x2005_plus_libretro.so'))
   assert digest(core)==c['core_sha256']
   assert digest(base/f"exact/{c['case']:03d}-{c['label']}.log")==c['log_sha256']
  if folder!='fused-count-private-v2':
   assert q['calls']==43200 and json.loads((base/'oracles.json').read_text())['passed']
   assert json.loads((base/'composition.json').read_text())['passed']
  else:assert q['calls']==3600 and q['prior_observer_fields_unchanged_every_call']
 staged=json.loads((ROOT/'build/combined-test-private-v1/verification.json').read_text())
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for name,h in staged[group].items():assert digest(ROOT/name)==h,name
 prior=json.loads((ROOT/'build/partial-selective-private-v1/workback-identity.json').read_text())
 for name,h in prior['source_hashes'].items():assert digest(ROOT/name)==h,name
 sources=sorted([*ROOT.glob('build/*fused*.py'),*ROOT.glob('build/*fused*.sh'),*ROOT.glob('build/fused*.h'),ROOT/'docs/snes-fused-toolbox.md'])
 for p in sources:
  assert b'\r' not in p.read_bytes(),p
  if p.suffix=='.py':compile(p.read_text(encoding='utf-8'),str(p),'exec')
 base=(ROOT/'build/partial-merge-selective.h').read_text();a=base.index('static inline __attribute__((always_inline)) unsigned d35_batch_tile_mode_base(');b=base.index('static inline __attribute__((always_inline)) unsigned d35_batch_tile_mode_plain(',a)
 for suffix,folder in (('','fused-toolbox-private-v1'),('-v2','fused-toolbox-private-v2')):
  for core in ('core','counted-core'):
   dest=ROOT/f'build/{folder}/{core}/source'
   assert (dest/'a7_common_batch.h').read_text()==(ROOT/f'build/fused-toolbox{suffix}.h').read_text().replace('/* FUSED_BASE */',base[a:b])
   assert digest(dest/'a7_common_band.h')==digest(ROOT/f'build/fused-toolbox-band{suffix}.h')
   assert digest(dest/'a7_partial_kernels.h')==digest(ROOT/'build/partial-merge-kernels.h')
   assert digest(dest/'a7_window.h')==digest(ROOT/'build/ability-regression-private-v1/core/source/a7_window.h')
 identity={'source_hashes':{p.relative_to(ROOT).as_posix():digest(p) for p in sources},'prior_staged_sources_payloads_proofs_unchanged':True,'prior_partial_workback_sources_unchanged':True,'staged_verification_sha256':digest(ROOT/'build/combined-test-private-v1/verification.json'),'window_header_sha256':digest(ROOT/'build/ability-regression-private-v1/core/source/a7_window.h'),'card_access':False,'installed':False,'A7_savings_measured':False,'QEMU_timings_used':False,'production_gate_passed':False}
 (OUT/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
 spec=importlib.util.spec_from_file_location('fusion_public',ROOT/'build/publish-snes-1.19.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)['entries']
 for e in old:assert digest(ROOT/e['published'])==e['published_sha256']
 public=ROOT/'evidence/2026-10-13/fused-toolbox';assert not public.exists();public.mkdir()
 pairs=[]
 for folder,label in (('fused-toolbox-private-v1','prototype'),('fused-toolbox-private-v2','veto')):
  pairs.extend((ROOT/f'build/{folder}/{kind}.json',f'{label}-{kind}.json') for kind in ('qualification','oracles','composition'))
 pairs.extend(((ROOT/'build/fused-count-private-v2/qualification.json','observer-refinement.json'),(OUT/'identity.json','identity.json')))
 entries=[]
 for src,name in pairs:
  dest=public/name;dest.write_bytes(pub.public_text(src.read_bytes()));entries.append({'source':src.relative_to(ROOT).as_posix(),'published':dest.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(dest)})
 manifest.write_bytes(pub.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(old)]==old
 print('Published',len(entries),'bounded fusion receipts; preserved',len(old),'prior entries; no card access')
if __name__=='__main__':main()
