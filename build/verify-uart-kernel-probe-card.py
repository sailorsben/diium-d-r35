"""Independent complete card readback for one-shot measurement, not firmware."""
from pathlib import Path
from hashlib import sha256
import json,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');i=json.loads((archive/'verification-installation.json').read_text());a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());card=Path('I:/');expected={e['path']:e['sha256'] for e in a['all_retro_files']+o['files'] if e['path']!='retro/update/Code.bkp'}
 expected['retro/init']=i['init_sha256'];expected.update({'retro/uart-kernel-verify1/'+n:h for n,h in i['payload_hashes'].items()});expected['retro/uart-kernel-verify1/armed']=i['marker_sha256']
 for n,h in expected.items():assert digest(card/n)==h,n
 assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}==set(expected)
 assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/uart-kernel-verify1/armed'] and not list(card.rglob('Code.bkp'))
 r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True);(archive/'chkdsk-verification-independent.txt').write_text(r.stdout+r.stderr);assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
 v={'passed':True,'protected_existing_files_verified':i['protected_existing_files'],'payload_and_marker_verified':True,'only_read_only_verification_armed':True,'no_update_trigger':True,'FAT_clean':True,'installation_sha256':digest(archive/'verification-installation.json'),'checker_sha256':digest(Path(__file__)),'physical_kernel_verification':'PENDING'};(archive/'verification-live-check.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
