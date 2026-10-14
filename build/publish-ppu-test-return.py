"""Publish bounded physical return metadata only, preserving all frozen proofs."""
from pathlib import Path
from hashlib import sha256
import json,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 src=archive/'ppu-test-return-evaluation.json';r=json.loads(src.read_text())
 assert r['FAT_clean'] and r['card_writes']==0 and r['installed_payloads_verified']==91 and r['marker_consumed']
 assert r['ROM_live_sha256']=='f61af2bd9e3f9b6a2bd543fb176af0b81fd9e5ba4ea0fa0f453371ccb45d3911'
 for n,h in r['inputs'].items():assert digest(ROOT/n)==h,n
 ready=json.loads((ROOT/'build/ppu-test-private-v1/ready.json').read_text())
 for n,h in ready['additional_sources'].items():assert digest(ROOT/n)==h,n
 q=json.loads((ROOT/'build/ppu-test-private-v1/verification.json').read_text())
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for n,h in q[group].items():assert digest(ROOT/n if group=='source_hashes' else ROOT/'build/ppu-test-private-v1'/n)==h,n
 for n,h in json.loads((ROOT/'evidence/2026-10-14/ppu-refinements/inputs.json').read_text()).items():assert digest(ROOT/n)==h,n
 mpath=ROOT/'evidence/manifest.json';m=json.loads(mpath.read_text())
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 public=json.loads(json.dumps(r))
 for epoch in public['epochs']:
  bad=epoch.pop('invalid_running_sync_sequences',[]);epoch['invalid_running_sync_count']=len(bad);epoch['first_invalid_running_sync_sequence']=bad[0] if bad else None
 target=ROOT/'evidence/2026-10-14/ppu-test-return/analysis.json';assert not target.exists();target.parent.mkdir(parents=True)
 target.write_text(json.dumps(public,indent=2)+'\n')
 m['entries'].append({'source':src.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(target),'bytes':target.stat().st_size,'normalized':True})
 mpath.write_text(json.dumps(m,indent=2)+'\n')
 print('Published56-epoch physical evaluation; prior proofs exact; no emulator/card writes')
if __name__=='__main__':main(Path(sys.argv[1]))
