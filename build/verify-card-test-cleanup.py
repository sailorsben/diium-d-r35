"""Independent remaining-file hashes, armed rollback ZIP and FAT after cleanup."""
from pathlib import Path
import json,sys,io,zipfile,subprocess
from hashlib import sha256
from attempt_archive import digest
ROOT=Path(__file__).resolve().parent.parent
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');p=json.loads((archive/'cleanup-plan.json').read_text());r=json.loads((archive/'cleanup-result.json').read_text());assert r['plan_sha256']==digest(archive/'cleanup-plan.json');card=Path('I:/');expected={**p['protected'],p['restore_dispatcher']['path']:p['restore_dispatcher']['sha256']}
 for n,h in expected.items():assert digest(card/n)==h,n
 assert {x.relative_to(card).as_posix() for x in card.rglob('*') if x.is_file()}==set(expected)
 assert not list(card.rglob('armed')) and list(card.rglob('Code.bkp'))==[card/'retro/update/Code.bkp']
 i=json.loads((ROOT/'evidence/2026-10-16/battery-rollback/installation.json').read_text());assert digest(card/'retro/update/Code.bkp')==i['package_sha256']
 for n,h in i['card_UART_payloads'].items():assert digest(card/'retro/init' if n=='init' else card/'retro/uart-fix1'/n)==h,n
 assert not (card/'retro/uart-fix1/disabled').exists();b=(card/'retro/update/Code.bkp').read_bytes();assert b[:3]==b'WQW'
 with zipfile.ZipFile(io.BytesIO(b[3:])) as z:assert z.testzip() is None and z.namelist()==['SPI_ROM.bin'] and sha256(z.read('SPI_ROM.bin')).hexdigest()==i['candidate_sha256']
 health=subprocess.run(['chkdsk','I:'],capture_output=True,text=True);(archive/'chkdsk-cleanup-independent.txt').write_text(health.stdout+health.stderr);assert health.returncode==0 and '11EB-1465' in health.stdout and 'Windows has scanned the file system and found no problems.' in health.stdout
 v={'passed':True,'remaining_files_verified':len(expected),'all_save_paths_unchanged':True,'rollback_exact_full_ZIP_CRC_and_image_verified':True,'proven_UART_boot_payloads_exact':True,'no_game_markers':True,'FAT_clean':True,'cleanup_receipt_sha256':digest(archive/'cleanup-result.json'),'checker_sha256':digest(Path(__file__))};(archive/'cleanup-independent.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
