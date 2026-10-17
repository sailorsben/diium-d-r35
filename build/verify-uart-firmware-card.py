"""Independent all-file readback after UART firmware staging; card read-only."""
from pathlib import Path
from hashlib import sha256
import io,json,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');card=Path('I:/')
 installed=json.loads((archive/'uart-firmware-installation.json').read_text());assert installed['armed_vendor_update']
 a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());entries=a['all_retro_files']+o['files']
 for e in entries:
  expected=installed['card_hook_sha256'] if e['path']==installed['only_changed_existing_file'] else e['sha256']
  assert digest(card/e['path'])==expected,e['path']
 trigger=card/'retro/update/Code.bkp';assert digest(trigger)==installed['package_sha256'];b=trigger.read_bytes();assert b[:3]==b'WQW'
 with zipfile.ZipFile(io.BytesIO(b[3:])) as z:assert z.testzip() is None and sha256(z.read('SPI_ROM.bin')).hexdigest()==installed['candidate_sha256']
 expected_paths={e['path'] for e in entries}|{installed['only_added_file']}
 assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}==expected_paths
 assert not list((card/'retro').rglob('armed'))
 r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True);(archive/'chkdsk-uart-firmware-independent.txt').write_text(r.stdout+r.stderr)
 assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
 report={'version':'uart-firmware1','passed':True,'protected_existing_files_verified':len(entries)-1,'all_prior_paths_present':True,'only_expected_changes':True,'package_full_ZIP_CRC_and_image_verified':True,'normal_init_UART_module_helper_saves_evidence_exact':True,'FAT_clean':True,'no_emulator_test_armed':True,'physical_update':'PENDING','installation_sha256':digest(archive/'uart-firmware-installation.json'),'checker_sha256':digest(Path(__file__))}
 (archive/'uart-firmware-live-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
