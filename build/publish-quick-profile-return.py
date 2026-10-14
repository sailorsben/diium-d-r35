"""Publish bounded derived return measurements, never raw states/ROM/SRAM."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 assert archive.is_relative_to(ROOT/'device-evidence')
 spec=importlib.util.spec_from_file_location('profile_public',ROOT/'build/publish-snes-1.19.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
 folder=archive/'quick-profile-analysis';analysis=json.loads((folder/'analysis.json').read_text());assert analysis['integrity']['card_writes']==0 and analysis['integrity']['clean_FAT']
 inputs=json.loads((folder/'inputs.json').read_text())['inputs']
 for n,h in inputs.items():assert digest(ROOT/n)==h,n
 dest=ROOT/'evidence/2026-10-13/quick-profile-return';dest.mkdir(exist_ok=True)
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=json.loads(raw)['entries'];entries=[]
 for e in old:assert digest(ROOT/e['published'])==e['published_sha256']
 for name in ('analysis.json','integrity.json','inputs.json'):
  src=folder/name;d=dest/name;data=pub.public_text(src.read_bytes())
  if d.exists():assert d.read_bytes()==data
  else:d.write_bytes(data)
  if not any(e['published']==d.relative_to(ROOT).as_posix() for e in old):entries.append({'source':src.relative_to(ROOT).as_posix(),'published':d.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'published_sha256':digest(d)})
 if entries:manifest.write_bytes(pub.append_manifest(raw,entries));assert json.loads(manifest.read_bytes())['entries'][:len(old)]==old
 print('Published',len(entries),'return receipts; preserved',len(old),'historical manifest entries')
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
