"""Publish metadata only; verify and preserve all existing evidence hashes."""
from pathlib import Path
from hashlib import sha256
import argparse,importlib.util,json
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive=None):
 q=json.loads((ROOT/'build/uart-fix-private/qualification.json').read_text());assert q['all_checks_passed']
 iq=json.loads((ROOT/'build/uart-fix-private/installation-qualification.json').read_text());assert iq['all_checks_passed'] and iq['qualification_sha256']==digest(ROOT/'build/uart-fix-private/qualification.json')
 for p in [q,iq]:
  for n,h in p['sources'].items():assert digest(ROOT/n)==h,n
 sources=[('build/uart-fix-private/'+n,'uart-fix1/'+dest) for n,dest in [('preparation.json','preparation.json'),('prepared.json','kernel-guards.json'),('qualification.json','qualification.json'),('installation-qualification.json','installation-qualification.json')]]
 sources.append(('build/uart-spells-private/qualification.json','uart-spells1/qualification.json'))
 if archive:
  archive=archive.resolve();assert archive.is_relative_to((ROOT/'device-evidence').resolve())
  for n,dest in [('uart-fix-installation.json','uart-fix1/installation.json'),('uart-spells-installation.json','uart-spells1/installation.json')]:
   r=json.loads((archive/n).read_text());assert r['physical_boot' if n.startswith('uart-fix-') else 'physical_result']=='PENDING'
   sources.append(((archive/n).relative_to(ROOT).as_posix(),dest))
  verified=archive/'uart-spells-live-verification.json'
  if verified.exists():
   v=json.loads(verified.read_text());assert v['verified'] and v['card_writes']==0
   sources.append((verified.relative_to(ROOT).as_posix(),'uart-spells1/live-verification.json'))
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();m=json.loads(raw)
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 for source,destination in sources:
  src=ROOT/source;dst=ROOT/'evidence/2026-10-15'/destination
  if dst.exists():assert dst.read_bytes()==src.read_bytes();continue
  dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
  m['entries'].append({'source':source,'published':dst.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(dst),'bytes':dst.stat().st_size,'normalized':False})
 encoded=(json.dumps(m,indent=2)+'\n').encode();manifest.write_bytes(encoded.replace(b'\n',b'\r\n') if b'\r\n' in raw else encoded)
 print(json.dumps({'proofs_verified':len(m['entries']),'metadata_only':True}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',type=Path);a=p.parse_args();main(a.archive)
