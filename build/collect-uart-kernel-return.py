"""Strict read-only sparse return collection; accept only known firmware trigger."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess
from attempt_archive import inventory,write_manifest,digest
ROOT=Path(__file__).resolve().parent.parent
def main():
 card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\')
 i=json.loads((ROOT/'evidence/2026-10-16/uart-kernel1/installation.json').read_text());trigger=card/'retro/update/Code.bkp'
 if trigger.exists():assert digest(trigger)==i['package_sha256']
 assert not list((card/'retro').rglob('armed'))
 out=ROOT/'device-evidence'/('uart-kernel-return-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
 entries=inventory(card,out);outside=inventory(card,out,outside=True)
 r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True);(out/'chkdsk-return.txt').write_text(r.stdout+r.stderr)
 assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
 write_manifest(out/'archive.json',entries,all_retro_files=entries,fat_clean=True,card_writes=0,known_update_sha256=i['package_sha256'],update_trigger_present=trigger.exists())
 write_manifest(out/'outside-retro.json',outside,files=outside,card_writes=0)
 print(out)
if __name__=='__main__':main()
