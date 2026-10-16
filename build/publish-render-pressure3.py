"""Publish only source-bound preparation/qualification/audit metadata."""
from pathlib import Path
from hashlib import sha256
import json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/render-pressure3-private'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 q=json.loads((OUT/'qualification.json').read_text());assert q['passed'] and q['controller_mock_phases']==77 and not q['card_access'] and not q['installed']
 for group in ['sources','local_compile_dependencies']:
  for n,h in q[group].items():assert digest(ROOT/n)==h,n
 for n,h in q['payloads'].items():assert digest(OUT/n)==h,n
 assert digest(OUT/'preparation.json')==q['preparation_sha256']
 fault=json.loads((OUT/'fault-qualification.json').read_text());assert fault['passed'] and fault['wrapper_sha256']==q['payloads']['launch.sh'] and fault['qualification_sha256']==digest(OUT/'qualification.json')
 assert fault['source_sha256']==digest(ROOT/'build/check-render-pressure3-faults.py')
 audit=json.loads((OUT/'device-path-audit.json').read_text());assert audit['source_sha256']==digest(ROOT/'build/audit-device-render-path.py') and len(audit['functions'])==11
 assert digest(OUT/'controller-qualification.json')==q['controller_qualification_sha256']
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();m=json.loads(raw)
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 for n in ['preparation.json','qualification.json','fault-qualification.json','device-path-audit.json','controller-qualification.json']:
  src=OUT/n;dst=ROOT/'evidence/2026-10-15/render-pressure3'/n;assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
  m['entries'].append({'source':src.relative_to(ROOT).as_posix(),'published':dst.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(dst),'bytes':dst.stat().st_size,'normalized':False})
 encoded=(json.dumps(m,indent=2)+'\n').encode();manifest.write_bytes(encoded.replace(b'\n',b'\r\n') if b'\r\n' in raw else encoded)
 print(json.dumps({'all_proofs_verified':len(m['entries']),'vendor_binary_or_ROM_publication':False,'card_access':False}))
if __name__=='__main__':main()
