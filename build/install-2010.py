from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import os
import shutil

root = Path(__file__).resolve().parent.parent
package = root / 'SNES-2010-comparison'
card = Path('D:/').resolve()
retro = card / 'retro'
manifest = json.loads((package / 'manifest.json').read_text())

def digest(p):
    h = sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(4*1024**2), b''): h.update(block)
    return h.hexdigest()

def inventory():
    return {p.relative_to(card).as_posix(): digest(p) for p in card.rglob('*')
            if p.is_file() and 'System Volume Information' not in p.relative_to(card).parts}

assert digest(retro / 'libs/emu_sfc.so') == manifest['plus_adapter_sha256'], 'Not the expected modified card'
assert digest(retro / 'libs/emu_sfc_plus.so') == manifest['plus_core_sha256']
assert digest(package / 'emu_sfc.so') == manifest['adapter_sha256']
assert digest(package / 'emu_sfc_2010.so') == manifest['core_sha256']
states = card / manifest['state_folder']
parked = card / manifest['preserved_plus_state_folder']
# Both directory rename endpoints are checked against the intended card folder.
assert states.resolve().parent == (retro / 'states').resolve()
assert parked.resolve().parent == (retro / 'states').resolve()
assert states.is_dir() and not parked.exists()
assert not (retro / 'libs/emu_sfc_2010.so').exists()
before = inventory()
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup = root / 'device-evidence' / ('2010-install-' + stamp)
backup.mkdir(parents=True, exist_ok=False)
shutil.copy2(retro / 'libs/emu_sfc.so', backup / 'emu_sfc_plus_clean.so')
shutil.copytree(states, backup / 'SFC-Plus-states')
assert digest(backup / 'emu_sfc_plus_clean.so') == manifest['plus_adapter_sha256']
for p in states.rglob('*'):
    if p.is_file(): assert digest(p) == digest(backup / 'SFC-Plus-states' / p.relative_to(states))
(backup / 'card-before-sha256.json').write_text(json.dumps(before, indent=2)+'\n')
for name in ['emu_sfc_2010.so', 'emu_sfc.so']:
    dst = retro / 'libs' / (name + '.install-2010')
    assert not dst.exists()
    with (package / name).open('rb') as src, dst.open('xb') as f:
        shutil.copyfileobj(src, f); f.flush(); os.fsync(f.fileno())
    assert digest(dst) == digest(package / name)
try:
    (retro / 'libs/emu_sfc_2010.so.install-2010').replace(retro / 'libs/emu_sfc_2010.so')
    states.rename(parked)
    states.mkdir()
    (retro / 'libs/emu_sfc.so.install-2010').replace(retro / 'libs/emu_sfc.so')
except Exception:
    shutil.copy2(backup / 'emu_sfc_plus_clean.so', retro / 'libs/emu_sfc.so')
    if parked.exists() and states.exists() and not any(states.iterdir()):
        states.rmdir(); parked.rename(states)
    raise
expected = dict(before)
expected['retro/libs/emu_sfc.so'] = manifest['adapter_sha256']
expected['retro/libs/emu_sfc_2010.so'] = manifest['core_sha256']
for name in list(expected):
    if name.startswith('retro/states/SFC/'):
        expected[name.replace('retro/states/SFC/', 'retro/states/SFC-Plus-preserved/', 1)] = expected.pop(name)
after = inventory()
assert after == expected, 'Unexpected card content change'
assert not list(retro.rglob('*.install-2010'))
report = {
    'card': str(card), 'installed_utc': datetime.now(timezone.utc).isoformat(),
    'active_core': 'Snes9x 2010', 'adapter_sha256': manifest['adapter_sha256'],
    'core_sha256': manifest['core_sha256'], 'backup': str(backup),
    'preserved_plus_states': str(parked),
    'all_other_card_files_unchanged': True, 'fresh_2010_state_folder': True,
    'automatic_diagnostic_logs': False, 'handheld_result': 'Awaiting user test'
}
(package / 'card-D-installation-verification.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
