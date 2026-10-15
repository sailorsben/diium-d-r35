"""Publish verified returned-device metadata, keeping prior proofs byte-exact."""
from pathlib import Path
from hashlib import sha256
import json,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to((ROOT/'device-evidence').resolve())
 result=archive/'uart-spells-return.json';r=json.loads(result.read_text())
 assert r['mock'] is False and r['card_writes']==0 and r['fat_clean'] and r['marker_consumed']
 assert r['archive']==archive.name and len(r['epochs'])==48
 for n,h in r['inputs'].items():assert digest(ROOT/n)==h,n
 qpath=ROOT/'build/uart-spells-private/return-reporter-qualification.json';q=json.loads(qpath.read_text());assert q['passed']
 for n,h in q['sources'].items():assert digest(ROOT/n)==h,n
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();m=json.loads(raw)
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 for source,name in [(result,'return.json'),(qpath,'return-reporter-qualification.json')]:
  target=ROOT/'evidence/2026-10-15/uart-spells1'/name;assert not target.exists()
  target.write_bytes(source.read_bytes())
  m['entries'].append({'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),'source_sha256':digest(source),'published_sha256':digest(target),'bytes':target.stat().st_size,'normalized':False})
 encoded=(json.dumps(m,indent=2)+'\n').encode();manifest.write_bytes(encoded.replace(b'\n',b'\r\n') if b'\r\n' in raw else encoded)
 print(json.dumps({'all_proofs_verified':len(m['entries']),'metadata_only':True}))
if __name__=='__main__':main(Path(sys.argv[1]))
