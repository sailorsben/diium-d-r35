"""Independent complete card readback after the matched five-game installation."""
from pathlib import Path
from hashlib import sha256
import json,sys,subprocess
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 receipt=json.loads((archive/'fivegame-installation.json').read_text());assert receipt['one_shot_armed']
 card=Path('I:/');target=card/'retro/snes-fivegame1'
 a=json.loads((archive/'archive.json').read_text());outside=json.loads((archive/'outside-retro.json').read_text())
 protected=[e for e in a['all_retro_files']+outside['files'] if e['path']!='retro/snes-mvp/launch.sh']
 for e in protected:assert digest(card/e['path'])==e['sha256'],e['path']
 for n,h in receipt['payload_hashes'].items():assert digest(target/n)==h,n
 assert digest(card/'retro/snes-mvp/launch.sh')==receipt['dispatch_sha256']
 for p in (target/'armed',card/'retro/snes-mvp/armed'):assert digest(p)==receipt['marker_sha256']
 assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==sorted(['retro/snes-mvp/armed','retro/snes-fivegame1/armed'])
 assert {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}==set(receipt['payload_hashes'])|{'armed'}
 assert not list(card.rglob('Code.bkp')) and not (card/'retro/uart-fix1/disabled').exists()
 r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True);(archive/'chkdsk-fivegame-independent.txt').write_text(r.stdout+r.stderr)
 assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
 report={'version':'fivegame1','passed':True,'protected_files_verified':len(protected),'payload_files_verified':len(receipt['payload_hashes']),
         'only_expected_markers':True,'persistent_UART_and_patched_init_exact':True,'FAT_clean':True,'physical_result':'PENDING',
         'installation_sha256':digest(archive/'fivegame-installation.json'),'checker_sha256':digest(Path(__file__))}
 (archive/'fivegame-live-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
