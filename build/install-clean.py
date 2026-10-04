from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import json
import shutil
root=Path(__file__).resolve().parent.parent
retro=Path('D:/retro')
manifest=json.loads((root/'SNES-Plus-clean/manifest.json').read_text())
def digest(p): return sha256(p.read_bytes()).hexdigest()
assert (retro/'vrtemu').is_file()
assert digest(retro/'libs/emu_sfc.so')==manifest['expected_before_sha256']
assert digest(retro/'libs/emu_sfc_plus.so')==manifest['core_sha256']
shim=root/'build/clean/emu_sfc.so'
assert digest(shim)==manifest['adapter_sha256']
before={str(p.relative_to(retro)):digest(p) for p in retro.rglob('*') if p.is_file()}
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup=root/'device-evidence'/('clean-install-'+stamp)
backup.mkdir(parents=True,exist_ok=False)
shutil.copy2(retro/'libs/emu_sfc.so',backup/'emu_sfc_v2.so')
assert digest(backup/'emu_sfc_v2.so')==manifest['expected_before_sha256']
shutil.copy2(shim,retro/'libs/emu_sfc.so')
after={str(p.relative_to(retro)):digest(p) for p in retro.rglob('*') if p.is_file()}
changed=[n for n in sorted(set(before)|set(after)) if before.get(n)!=after.get(n)]
assert changed==[str(Path('libs/emu_sfc.so'))],changed
assert digest(retro/'init')=='6d65bf756183f37c19a542703c8d50193d5c137e7d0d45be4ac980fcdcb8efbd'
assert not list(retro.glob('emu_sfc_plus_v[1-8]*'))
report={'card':'D:/','active_build':manifest['build'],'changed_contents':changed,
        'adapter_sha256':after[str(Path('libs/emu_sfc.so'))],
        'other_retro_files_unchanged':True,'screen_flash_test_removed':True,
        'old_plus_diagnostic_outputs_removed':True,'clicking':'unresolved','backup':str(backup)}
(root/'SNES-Plus-clean/card-D-installation-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
