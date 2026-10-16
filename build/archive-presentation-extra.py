"""Read-only supplemental archive: protect every file outside retro as well."""
from pathlib import Path
from hashlib import sha256
import json,shutil,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
 assert not (archive/'outside-retro.json').exists()
 card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\')
 entries=[]
 for p in sorted(card.rglob('*')):
  if not p.is_file() or p.relative_to(card).parts[0].lower()=='retro':continue
  assert not p.is_symlink();rel=p.relative_to(card);target=archive/rel
  target.parent.mkdir(parents=True,exist_ok=True);h=digest(p);shutil.copy2(p,target)
  assert digest(p)==digest(target)==h
  entries.append({'path':rel.as_posix(),'sha256':h,'bytes':p.stat().st_size})
 (archive/'outside-retro.json').write_text(json.dumps({'card_writes':0,'files':entries},indent=2)+'\n')
 print('Supplemental archive verified:',len(entries),'files,',sum(e['bytes'] for e in entries),'bytes; zero card writes')
if __name__=='__main__':main(Path(sys.argv[1]))
