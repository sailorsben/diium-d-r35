"""Independent full card/payload/markers/normal-init/FAT check; no writes to I:."""
from pathlib import Path
import json,subprocess,sys
from attempt_archive import digest

ROOT=Path(__file__).resolve().parent.parent

def main(archive):
    archive=archive.resolve();assert archive.is_relative_to((ROOT/'device-evidence').resolve())
    i=json.loads((archive/'fivegame-replay-installation.json').read_text())
    a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text())
    card=Path('I:/');expected={e['path']:e['sha256'] for e in a['all_retro_files']+o['files']}
    expected['retro/snes-mvp/launch.sh']=i['dispatch_sha256']
    expected.update({i['target']+'/'+n:h for n,h in i['payload_hashes'].items()})
    markers=['retro/snes-mvp/armed',i['target']+'/armed']
    expected.update({n:i['marker_sha256'] for n in markers})
    assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}==set(expected)
    for n,h in expected.items():assert digest(card/n)==h,n
    assert sorted(p.relative_to(card).as_posix() for p in card.rglob('armed'))==sorted(markers)
    assert not list(card.rglob('Code.bkp'))
    assert digest(card/'retro/init')=='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
    r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True);(archive/'chkdsk-fivegame-replay-independent.txt').write_text(r.stdout+r.stderr)
    assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
    report={'passed':True,'protected_existing_files_verified':i['protected_existing_files'],'payload_files_verified':len(i['payload_hashes']),'exact_card_file_count':len(expected),'exact_two_markers':True,'normal_init_preserved':True,'kernel_UART_preserved':True,'no_firmware_update':True,'FAT_clean':True,'no_full_backup':True,'installation_sha256':digest(archive/'fivegame-replay-installation.json'),'checker_sha256':digest(Path(__file__)),'physical_result':'PENDING'}
    text=json.dumps(report,indent=2)+'\n';(archive/'fivegame-replay-live-verification.json').write_text(text)
    (ROOT/'evidence/2026-10-17/fivegame-replay/live-verification.json').write_text(text);print(text)

if __name__=='__main__':main(Path(sys.argv[1]))
