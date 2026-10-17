"""Independent full card/ZIP/kernel/module and FAT verification; read only."""
from pathlib import Path
from hashlib import sha256
import io,json,sys,subprocess,zipfile,zlib
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');i=json.loads((archive/'battery-rollback-installation.json').read_text());assert i['armed_vendor_update'];a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());card=Path('I:/');expected={e['path']:e['sha256'] for e in a['all_retro_files']+o['files']}
 expected['retro/init']=i['card_UART_payloads']['init'];expected['retro/uart-fix1/launch.sh']=i['card_UART_payloads']['launch.sh'];expected['retro/update/Code.bkp']=i['package_sha256']
 for n,h in expected.items():assert digest(card/n)==h,n
 assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}==set(expected)
 assert not list(card.rglob('armed')) and list(card.rglob('Code.bkp'))==[card/'retro/update/Code.bkp']
 for n,h in i['card_UART_payloads'].items():assert digest(card/'retro/init' if n=='init' else card/'retro/uart-fix1'/n)==h,n
 assert not (card/'retro/uart-fix1/disabled').exists();b=(card/'retro/update/Code.bkp').read_bytes();assert b[:3]==b'WQW'
 with zipfile.ZipFile(io.BytesIO(b[3:])) as z:
  assert z.testzip() is None and z.namelist()==['SPI_ROM.bin'];image=z.read('SPI_ROM.bin');assert sha256(image).hexdigest()==i['candidate_sha256'];assert sha256(zlib.decompress(image[0xc0078+0x48b8:0x301d10],31)).hexdigest()==i['restored_kernel_sha256']
 r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True);(archive/'chkdsk-battery-rollback-independent.txt').write_text(r.stdout+r.stderr);assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
 v={'passed':True,'protected_existing_files_verified':i['protected_existing_files'],'exact_file_set_count':len(expected),'full_ZIP_CRC_image_original_kernel_verified':True,'proven_card_UART_payloads_verified':True,'no_game_tests_armed':True,'only_expected_firmware_trigger':True,'FAT_clean':True,'no_full_backup':True,'installation_sha256':digest(archive/'battery-rollback-installation.json'),'checker_sha256':digest(Path(__file__)),'physical_rollback':'PENDING','battery_result':'UNPROVEN'};(archive/'battery-rollback-live-verification.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
