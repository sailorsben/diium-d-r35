"""Independent installed-byte, protected-progress and FAT readback; no writes."""
from pathlib import Path
from hashlib import sha256
import json, subprocess, sys
ROOT=Path(__file__).resolve().parent.parent;archive=ROOT/'device-evidence'/sys.argv[1]
card=Path('D:/');proof=json.loads((archive/'cost-installation.json').read_text())
def digest(p):return sha256(p.read_bytes()).hexdigest()
for name,wanted in proof['payload_hashes'].items():assert digest(card/'retro/snes-cost1'/name)==wanted,name
assert digest(card/'retro/snes-mvp/launch.sh')==proof['dispatch_sha256']
records=json.loads((archive/'collection.json').read_text())['copied_and_hash_verified']
protected={e['card_path']:e['sha256'] for e in records if e['card_path']!='retro/snes-mvp/launch.sh'}
lab=json.loads((archive/'lab-collection.json').read_text())
protected.update({'retro/platform-lab/'+e['relative_path']:e['sha256'] for e in lab['copied']})
previous=json.loads((ROOT/'device-evidence/snes-mvp-1.19-install-20261010T064616Z/protected.json').read_text())
protected.update({p:h for p,h in previous.items() if p.startswith('retro/spi-readback')})
for name,wanted in protected.items():assert digest(card/name)==wanted,name
assert (card/'retro/snes-mvp/armed').read_bytes()==b'SNES-cost1 diagnostic measurement suite; baseline renderer only; no production candidate\n'
assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/snes-mvp/armed']
assert not (card/'retro/update/Code.bkp').exists()
r=subprocess.run(['chkdsk','D:'],capture_output=True,text=True)
(archive/'chkdsk-independent-cost.txt').write_text(r.stdout,encoding='utf-8')
assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
result={'passed':True,'card_writes':0,'payloads_exact':True,'protected_files_reread':len(protected),
        'fat_clean':True,'only_measurement_marker_armed':True,'candidate_installed':False}
(archive/'independent-cost-readback.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
