from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import shutil
import json
root=Path(__file__).resolve().parent.parent
retro=Path('D:/retro')
shim=root/'build/v8-capture/emu_sfc.so'
def digest(p): return sha256(p.read_bytes()).hexdigest()
manifest=json.loads((root/'SNES-Plus-v8-display-test/manifest.json').read_text())
assert (retro/'vrtemu').is_file(),'Reconnect tested SD card as D:'
assert digest(shim)==manifest['adapter_sha256']
assert digest(retro/'libs/emu_sfc.so')==manifest['expected_before_sha256']
assert digest(retro/'libs/emu_sfc_plus.so')==manifest['core_sha256']
before={str(p.relative_to(retro)).replace('\\','/'):digest(p) for p in retro.rglob('*') if p.is_file()}
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup=root/'device-evidence'/('card-D-before-v8-audit-'+stamp)
backup.mkdir(parents=True,exist_ok=False)
shutil.copy2(retro/'libs/emu_sfc.so',backup/'emu_sfc.so')
assert digest(backup/'emu_sfc.so')==manifest['expected_before_sha256']
(backup/'retro-before-sha256.json').write_text(json.dumps(before,indent=2)+'\n')
shutil.copy2(shim,retro/'libs/emu_sfc.so')
after={str(p.relative_to(retro)).replace('\\','/'):digest(p) for p in retro.rglob('*') if p.is_file()}
changed=[n for n in sorted(set(before)|set(after)) if before.get(n)!=after.get(n)]
assert changed==['libs/emu_sfc.so'],changed
assert after['libs/emu_sfc.so']==manifest['adapter_sha256']
report={'card':'D:/','build':manifest['build'],'backup':str(backup),
        'changed_contents':changed,'adapter_sha256':after['libs/emu_sfc.so'],
        'core_sha256':after['libs/emu_sfc_plus.so'],
        'other_retro_files_unchanged':True,'hardware_test':'pending'}
(root/'SNES-Plus-v8-display-test/card-D-installation-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
