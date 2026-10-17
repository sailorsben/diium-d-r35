"""Independent complete I: hash/ZIP/FAT verification; card read-only."""
from pathlib import Path
from hashlib import sha256
import io,json,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');i=json.loads((archive/'uart-kernel-installation.json').read_text());assert i['armed_vendor_update'];card=Path('I:/')
 entries=json.loads((archive/'archive.json').read_text())['all_retro_files']+json.loads((archive/'outside-retro.json').read_text())['files']
 expected={e['path']:e['sha256'] for e in entries};expected['retro/init']=i['normal_init_sha256'];expected['retro/update/Code.bkp']=i['package_sha256']
 for n,h in expected.items():assert digest(card/n)==h,n
 assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}==set(expected)
 assert not list((card/'retro').rglob('armed'))
 b=(card/'retro/update/Code.bkp').read_bytes();assert b[:3]==b'WQW'
 with zipfile.ZipFile(io.BytesIO(b[3:])) as z:assert z.testzip() is None and z.namelist()==['SPI_ROM.bin'] and sha256(z.read('SPI_ROM.bin')).hexdigest()==i['candidate_sha256']
 r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True);(archive/'chkdsk-kernel-independent.txt').write_text(r.stdout+r.stderr);assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
 protected=sum(e['path'] not in {'retro/init','retro/update/Code.bkp'} for e in entries)
 result={'version':'uart-kernel1','passed':True,'all_existing_paths_present':True,'protected_existing_files_verified':protected,'all_existing_files':len(entries),'verified_final_file_count':len(expected),'only_expected_two_files_changed':True,'full_ZIP_CRC_and_candidate_image_verified':True,'original_normal_init_exact_no_UART_module_hook':True,'saves_evidence_stock_and_old_UART_payloads_preserved':True,'FAT_clean':True,'no_emulator_test_armed':True,'installation_sha256':digest(archive/'uart-kernel-installation.json'),'checker_sha256':digest(Path(__file__)),'physical_boot':'PENDING'}
 (archive/'uart-kernel-live-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
