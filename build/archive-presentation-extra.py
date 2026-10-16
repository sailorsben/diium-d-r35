"""Hash outside-retro files; retain only changed progress and logs."""
from pathlib import Path
from hashlib import sha256
import json,shutil,sys
from attempt_archive import inventory, write_manifest
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
 assert not (archive/'outside-retro.json').exists()
 card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\')
 entries=inventory(card,archive,outside=True)
 write_manifest(archive/'outside-retro.json',entries,card_writes=0,files=entries)
 print('Supplemental hashes:',len(entries),'files;',sum(e['new_content_bytes'] for e in entries),'new saved bytes; zero card writes')
if __name__=='__main__':main(Path(sys.argv[1]))
