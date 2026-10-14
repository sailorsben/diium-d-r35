"""Publish evaluated return metadata only; preserve card/archive/core bytes."""
from pathlib import Path
from hashlib import sha256
import json,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 source=archive/'demand-spells-return-evaluation.json';r=json.loads(source.read_text())
 assert r['card_writes']==0 and r['FAT_clean'] and r['installed_payloads_verified']==82
 for n,h in r['inputs'].items():assert digest(ROOT/n)==h,n
 mpath=ROOT/'evidence/manifest.json';m=json.loads(mpath.read_text())
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 for n,h in json.loads((ROOT/'build/demand-visible-private-v3/frozen.json').read_text()).items():assert digest(ROOT/n)==h,n
 ready=json.loads((ROOT/'build/demand-spells-private-v1/ready.json').read_text())
 for n,h in ready['additional_sources'].items():assert digest(ROOT/n)==h,n
 for group in ('source_hashes','payload_hashes','proof_hashes'):
  for n,h in ready['qualification'][group].items():assert digest(ROOT/n if group=='source_hashes' else ROOT/'build/demand-spells-private-v1'/n)==h,n
 target=ROOT/'evidence/2026-10-14/demand-spells-return/analysis.json';assert not target.exists();target.parent.mkdir()
 # Preserve count and first occurrence; full lists remain in immutable archive.
 public=json.loads(json.dumps(r))
 for epoch in public['epochs']:
  seq=epoch.pop('invalid_running_sync_sequences',[])
  epoch['invalid_running_sync_count']=len(seq);epoch['first_invalid_running_sync_sequence']=seq[0] if seq else None
 target.write_text(json.dumps(public,indent=2)+'\n')
 m['entries'].append({'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
 'source_sha256':digest(source),'published_sha256':digest(target),'bytes':target.stat().st_size,'normalized':True})
 mpath.write_text(json.dumps(m,indent=2)+'\n')
 print('Published evaluated40-epoch physical return; frozen emulator/runtime/test and prior evidence exact; no card writes')
if __name__=='__main__':main(Path(sys.argv[1]))
