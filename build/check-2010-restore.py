from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import os
import stat

root = Path(__file__).resolve().parent.parent
fixture = root / 'build/comparison-2010/restore-check'
fixture.mkdir(exist_ok=False)
package = fixture / 'package'
package.mkdir()
source = root / 'SNES-2010-comparison'
for name in ['manifest.json', 'restore-plus.py']:
    shutil.copy2(source / name, package / name)
shutil.copytree(source / 'restore', package / 'restore')
card = fixture / 'card'
libs = card / 'retro/libs'
libs.mkdir(parents=True)
for name in ['emu_sfc.so', 'emu_sfc_2010.so']:
    shutil.copy2(source / name, libs / name)
shutil.copy2(root / 'build/clean/emu_sfc_plus.so', libs / 'emu_sfc_plus.so')
states = card / 'retro/states/SFC'
states.mkdir(parents=True)
(states / 'Final Fantasy VI.sv0').write_bytes(b'new-2010-test-state')
parked = card / 'retro/states/SFC-Plus-preserved'
parked.mkdir()
(parked / 'Final Fantasy VI.sv0').write_bytes(b'original-plus-test-state')
roms = card / '002'
roms.mkdir()
(roms / 'unrelated.bin').write_bytes(b'protected-game-content')
subprocess.run([sys.executable, str(package / 'restore-plus.py'), '--card', str(card)], check=True)
assert (states / 'Final Fantasy VI.sv0').read_bytes() == b'original-plus-test-state'
assert not parked.exists() and not (libs / 'emu_sfc_2010.so').exists()
assert (roms / 'unrelated.bin').read_bytes() == b'protected-game-content'
manifest = json.loads((source / 'manifest.json').read_text())
assert hashlib.sha256((libs / 'emu_sfc.so').read_bytes()).hexdigest() == manifest['plus_adapter_sha256']
report = json.loads((package / 'restoration.json').read_text())
assert (Path(report['2010_states_archived']) / 'SFC-2010-states/Final Fantasy VI.sv0').read_bytes() == b'new-2010-test-state'
# Keep the small report, but remove only exact fixture-owned files after checks.
(root / 'build/comparison-2010/restore-check.json').write_text(json.dumps({'passed': True, 'original_states_restored': True, 'test_states_archived': True, 'unrelated_game_unchanged': True}, indent=2)+'\n')
assert fixture.resolve().parent == (root / 'build/comparison-2010').resolve()
for p in fixture.rglob('*'):
    assert p.resolve().is_relative_to(fixture.resolve())
for p in fixture.rglob('*'):
    if p.is_file(): p.unlink()
for p in sorted((p for p in fixture.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
    os.chmod(p, stat.S_IREAD | stat.S_IWRITE); p.rmdir()
fixture.rmdir()
print('PASS Plus restoration, original/test state isolation, core cleanup, unrelated game preservation; fixture removed')
