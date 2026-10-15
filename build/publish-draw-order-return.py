"""Publish bounded verified physical metadata, retaining every preparation proof."""
from pathlib import Path
from hashlib import sha256
import json,sys
ROOT=Path(__file__).resolve().parent.parent

def digest(p):return sha256(p.read_bytes()).hexdigest()

def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 src=archive/'draw-order-return-evaluation.json';r=json.loads(src.read_text())
 assert r['FAT_clean'] and r['card_writes']==0 and r['installed_payloads_verified']==85 and r['marker_consumed']
 assert r['ROM_live_sha256']=='f61af2bd9e3f9b6a2bd543fb176af0b81fd9e5ba4ea0fa0f453371ccb45d3911'
 assert len(r['epochs'])==48 and r['APU_compiler_output_stable'] and not r['production_gate_passed']
 for n,h in r['inputs'].items():assert digest(ROOT/n)==h,n
 out=ROOT/'build/draw-order-test-private-v1';ready=json.loads((out/'ready.json').read_text());q=json.loads((out/'verification.json').read_text())
 for n,h in ready['additional_sources'].items():assert digest(ROOT/n)==h,n
 assert ready['verification_sha256']==digest(out/'verification.json')
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for n,h in q[group].items():assert digest(ROOT/n if group=='source_hashes' else out/n)==h,n
 for n,h in json.loads((ROOT/'build/draw-order-private-v1/frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 manifest=ROOT/'evidence/manifest.json';m=json.loads(manifest.read_text())
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 public=json.loads(json.dumps(r))
 for epoch in public['epochs']:
  bad=epoch.pop('invalid_running_sync_sequences',[]);epoch['invalid_running_sync_count']=len(bad);epoch['first_invalid_running_sync_sequence']=bad[0] if bad else None
 target=ROOT/'evidence/2026-10-14/draw-order-return/analysis.json';assert not target.exists();target.parent.mkdir(parents=True)
 target.write_text(json.dumps(public,indent=2)+'\n')
 m['entries'].append({'source':src.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
  'source_sha256':digest(src),'published_sha256':digest(target),'bytes':target.stat().st_size,'normalized':True})
 manifest.write_text(json.dumps(m,indent=2)+'\n')
 print(json.dumps({'published':str(target),'prior_published_hashes_verified':len(m['entries'])-1,'frozen_preparation_exact':True,'card_writes':0}))

if __name__=='__main__':main(Path(sys.argv[1]))
