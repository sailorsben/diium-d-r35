"""Independent read-only installed-card verification; writes only local receipt."""
from pathlib import Path
from hashlib import sha256
import json,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to((ROOT/'device-evidence').resolve())
 a=json.loads((archive/'archive.json').read_text());i=json.loads((archive/'uart-spells-installation.json').read_text())
 f=json.loads((archive/'uart-fix-installation.json').read_text());q=json.loads((ROOT/'build/uart-fix-private/qualification.json').read_text())
 card=Path('I:/');base=card/i['target'];assert i['one_shot_armed'] and i['persistent_UART_enabled'] and i['FAT_clean']
 assert f['source_commit']==i['source_commit'] and f['init_sha256']==i['init_sha256']==q['payloads']['init']
 unchanged=0
 for e in a['all_retro_files']:
  if e['path'] in ('retro/init','retro/snes-mvp/launch.sh'):continue
  assert digest(card/e['path'])==e['sha256'],e['path'];unchanged+=1
 for n,h in i['payload_hashes'].items():assert digest(base/n)==h,n
 for n,h in q['payloads'].items():assert digest(card/'retro/init' if n=='init' else card/'retro/uart-fix1'/n)==h,n
 assert digest(card/'retro/uart-fix1/qualification.json')==f['qualification_sha256']
 assert digest(card/'retro/uart-fix1/original-init')=='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
 assert not (card/'retro/uart-fix1/disabled').exists() and not (card/'retro/update/Code.bkp').exists()
 assert digest(card/'retro/snes-mvp/launch.sh')==i['dispatch_sha256']
 assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/snes-mvp/armed']
 assert digest(card/'retro/snes-mvp/armed')==i['marker_sha256']
 assert digest(card/'002/Final Fantasy VI.zip')=='f61af2bd9e3f9b6a2bd543fb176af0b81fd9e5ba4ea0fa0f453371ccb45d3911'
 r={'verified':True,'source_commit':i['source_commit'],'card_writes':0,'protected_prior_files_exact':unchanged,'test_payloads_exact':len(i['payload_hashes']),
 'persistent_UART_payloads_exact':True,'sole_marker_and_dispatcher_exact':True,'ROM_progress_exact':True,'no_firmware_trigger':True,'physical_result':'PENDING'}
 (archive/'uart-spells-live-verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
