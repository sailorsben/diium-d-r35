"""Read-only I: attempt: changed progress/logs and complete hash inventory."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json, shutil, subprocess
from attempt_archive import inventory, write_manifest
ROOT=Path(__file__).resolve().parent.parent
def digest(p): return sha256(p.read_bytes()).hexdigest()
def archive(card):
    card=card.resolve()
    assert str(card).lower() in ('i:/','i:\\'), 'Explicitly reassigned test card only'
    assert (card/'retro/snes-cost1/suite-identity.json').is_file()
    out=ROOT/'device-evidence'/('a7-pair-before-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True,exist_ok=False)
    entries=inventory(card,out)
    r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True)
    (out/'chkdsk-before.txt').write_text(r.stdout+r.stderr,encoding='utf-8')
    assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
    assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
    write_manifest(out/'archive.json',entries,card='I:',all_retro_files=entries,card_writes=0,fat_clean=True)
    print(out)
    return out
if __name__=='__main__': archive(Path('I:/'))
