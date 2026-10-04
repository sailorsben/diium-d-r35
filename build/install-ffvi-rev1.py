from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import shutil
import zipfile
import argparse

root = Path(__file__).resolve().parent.parent
package = root / 'SNES-comparison-FFVI-Rev1'
card = Path('D:/')
retro = card / 'retro'
stem = 'Final Fantasy VI (Rev 1)'
parser = argparse.ArgumentParser()
parser.add_argument('--verify-backup', type=Path, help='Verify an already copied comparison against its recorded pre-install inventory')
args = parser.parse_args()
def digest(path): return sha256(path.read_bytes()).hexdigest()
expected_adapter = '16aa482408689d4a2ff5ee622ae90b2123471bb64c397127a4d7e0e738ed1ea4'
expected_core = '1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657'
assert (retro / 'vrtemu').is_file()
assert digest(retro / 'libs/emu_sfc.so') == expected_adapter
assert digest(retro / 'libs/emu_sfc_plus.so') == expected_core
assert not (retro / 'libs/emu_sfc_2010.so').exists()
assert not (retro / 'states/SFC-Plus-preserved').exists()
# Check the actual PC state backup before any card mutation.
preserved = root / 'device-evidence/2010-install-20261004T073213Z/SFC-Plus-states'
assert preserved.is_dir()
for path in preserved.rglob('*'):
    if path.is_file():
        assert digest(path) == digest(retro / 'states/SFC' / path.relative_to(preserved))
check = (package / 'verification/checks.log').read_text()
assert 'PASS frames=1800' in check and 'core=Snes9x 2005 Plus' in check
prepared = json.loads((package / 'prepared.json').read_text())
assert digest(package / (stem + '.zip')) == prepared['game_zip_sha256']
assert digest(Path(prepared['source'])) == prepared['source_zip_sha256']
rom_dest = card / '002' / (stem + '.zip')
image_dest = card / '002/images' / (stem + '.png')
if not args.verify_backup:
    assert not rom_dest.exists() and not image_dest.exists()
def inventory():
    return {str(p.relative_to(card)): digest(p) for folder in [retro, card / '002']
            for p in folder.rglob('*') if p.is_file()}
if args.verify_backup:
    backup = args.verify_backup.resolve(strict=True)
    assert backup.parent == (root / 'device-evidence').resolve()
    assert backup.name.startswith('ffvi-rev1-install-')
    before = json.loads((backup / 'before-sha256.json').read_text())
else:
    before = inventory()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = root / 'device-evidence' / ('ffvi-rev1-install-' + stamp)
    backup.mkdir(parents=True, exist_ok=False)
    (backup / 'before-sha256.json').write_text(json.dumps(before, indent=2) + '\n')
    for path in [card / '002/filelist.txt', retro / 'fileinfo.txt', retro / 'fileinfo.dat']:
        dest = backup / path.relative_to(card)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        assert digest(path) == digest(dest)

def append_entry(path, line):
    old = path.read_bytes()
    key = line.split(';', 1)[0].encode('utf-8')
    assert not any(row.split(b';', 1)[0] == key for row in old.splitlines())
    new = old + (b'' if not old or old.endswith(b'\n') else b'\n') + line.encode('utf-8') + b'\n'
    path.write_bytes(new)
    assert path.read_bytes() == new

entries = [
    (card / '002/filelist.txt', stem + '.zip;' + stem + ';FINALFANTASYVIREV1;' + stem),
    (retro / 'fileinfo.txt', '002/' + stem + '.zip;' + stem + ';FINAL FANTASY VI REV 1;FINALFANTASYVIREV1;' + stem),
]
if not args.verify_backup:
    shutil.copy2(package / (stem + '.zip'), rom_dest)
    shutil.copy2(package / (stem + '.png'), image_dest)
    for path, entry in entries:
        append_entry(path, entry)
for path, entry in entries:
    assert path.read_bytes().splitlines().count(entry.encode('utf-8')) == 1
    assert path.read_bytes().startswith((backup / path.relative_to(card)).read_bytes())
assert digest(rom_dest) == prepared['game_zip_sha256']
assert digest(image_dest) == digest(package / (stem + '.png'))
with zipfile.ZipFile(rom_dest) as archive:
    assert archive.testzip() is None
    assert sha256(archive.read(stem + '.sfc')).hexdigest() == prepared['rom_sha256']
after = inventory()
changed = {n for n in set(before) | set(after) if before.get(n) != after.get(n)}
allowed = {str(Path(n)) for n in ['002/' + stem + '.zip', '002/images/' + stem + '.png',
                                  '002/filelist.txt', 'retro/fileinfo.txt']}
assert changed == allowed, changed
assert not list(retro.glob('emu_sfc_plus_v[1-8]*'))
report = {
    'card': str(card), 'installed_game': prepared['menu_label'], 'source': prepared['source'],
    'rom_sha256': prepared['rom_sha256'], 'changes': sorted(changed), 'backup': str(backup),
    'emulator': 'restored clean Snes9x 2005 Plus', 'emulator_unchanged': True,
    'existing_roms_and_saves_unchanged': True, 'plus_states_match_pre_2010_backup': True,
    'arm_qemu_boot_video_audio_state_checks': 'passed 1800 frames',
    'hardware_launch_and_clicking': 'pending user comparison',
    'installed_utc': datetime.now(timezone.utc).isoformat(),
}
(package / 'card-D-installation-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
