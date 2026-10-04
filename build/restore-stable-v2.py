"""Run only after retrieving v8 evidence from the returned card."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import shutil
import json
root=Path(__file__).resolve().parent.parent
retro=Path('D:/retro').resolve()
manifest=json.loads((root/'SNES-Plus-v8-display-test/manifest.json').read_text())
stable=root/'device-evidence/card-D-v2-return/emu_sfc.so'
def digest(p): return sha256(p.read_bytes()).hexdigest()
assert (retro/'vrtemu').is_file()
assert digest(stable)==manifest['rollback_v2_sha256']
assert digest(retro/'libs/emu_sfc.so')==manifest['adapter_sha256']
assert digest(retro/'libs/emu_sfc_plus.so')==manifest['core_sha256']
before={str(p.relative_to(retro)):digest(p) for p in retro.rglob('*') if p.is_file()}
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out=root/'device-evidence'/('v8-restoration-'+stamp)
out.mkdir(parents=True,exist_ok=False)
shutil.copy2(retro/'libs/emu_sfc.so',out/'emu_sfc_v8.so')
archived=[]
for p in retro.glob('emu_sfc_plus_v8*'):
    assert p.resolve().parent==retro and p.is_file()
    dest=out/p.name; shutil.copy2(p,dest)
    assert digest(dest)==digest(p)
    archived.append({'name':p.name,'sha256':digest(dest)})
    p.unlink()
shutil.copy2(stable,retro/'libs/emu_sfc.so')
assert digest(retro/'libs/emu_sfc.so')==manifest['rollback_v2_sha256']
assert digest(retro/'libs/emu_sfc_plus.so')==manifest['core_sha256']
after={str(p.relative_to(retro)):digest(p) for p in retro.rglob('*') if p.is_file()}
changed=[n for n in before if n in after and before[n]!=after[n]]
removed=sorted(set(before)-set(after))
assert changed==[str(Path('libs/emu_sfc.so'))],changed
assert removed==sorted(item['name'] for item in archived),removed
assert not set(after)-set(before)
report={'active_adapter':'proven v2; no capture/reporting worker/display experiment',
        'adapter_sha256':digest(retro/'libs/emu_sfc.so'),'archived_and_removed':archived,
        'clicking':'not claimed fixed','archive':str(out),
        'other_retro_files_unchanged':True,'changed_files':changed,
        'user_observation':'No clicking difference during display comparison; Ninja Gaiden NES sounded clean.',
        'v8_report':'One complete 720-frame hold and black phase; 2372 full driver writes, no errors. Returned WAV and timing report are empty.'}
(out/'restoration.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
