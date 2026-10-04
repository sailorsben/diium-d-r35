from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json, os, re, shutil, zipfile

root = Path(__file__).resolve().parent.parent
card = Path('D:/')
retro = card / 'retro'
build = root / 'build/production'
package = root / 'SNES-Plus-v11-production'
old_hash = 'a9f7b96a6c285645a9ab51b8d9929427e51fff46fecea92cbf430efbf0ac6bf4'
core_hash = '1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657'
pcm_hash = '66a890a9303fb63fd5758f0d310f46000f8b1fc810042a7c9d33d555eb9a87be'
callbacks_hash = '1fcec31f3738023192683ba78d9a08cb1a991fe21a18198411725229889cdb3c'

def digest(p):
    h = sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()

assert (retro / 'vrtemu').is_file()
assert digest(retro / 'libs/emu_sfc.so') == old_hash
assert digest(retro / 'libs/emu_sfc_plus.so') == core_hash
control, test = build / 'verification/control', build / 'verification/test'
assert digest(control / 'native.s16le') == digest(test / 'native.s16le') == pcm_hash
assert digest(control / 'batches.csv') == digest(test / 'batches.csv') == callbacks_hash
assert 'Drawn=4200 Held=0' in (control / 'checks.log').read_text()
assert 'Drawn=2100 Held=2100' in (test / 'checks.log').read_text()
assert all(not (build / 'verification' / name / 'should-not-exist.txt').exists()
           for name in ('control', 'test', 'state'))
assert max(tuple(map(int, v.split('.'))) for v in re.findall(r'GLIBC_([0-9]+\.[0-9]+)', (build / 'abi-versions.txt').read_text())) <= (2, 30)
assert (build / 'verification/completed.json').is_file(), 'Run checks to successful completion first'
completed = json.loads((build / 'verification/completed.json').read_text())
assert completed['exit_code'] == 0
source = (root / 'build/emu_sfc_plus_production.c').read_text()
header = (root / 'build/render_budget_production.h').read_text()
assert all(x not in source + header for x in ('rt9_save', 'SNDCTL_DSP_GETODELAY', 'RT9_BINS', 'D35_V10_REPORT'))
original = (root / 'build/render_budget_v10.h').read_text()
algorithm = original[original.index('static uint32_t rb10_draw_us'):original.index('static void rt9_max')]
assert algorithm in header, 'Adaptive algorithm must match proven v10'

def inventory():
    return {str(p.relative_to(card)).replace('\\', '/'): digest(p)
            for folder in (retro, card / '002') for p in folder.rglob('*') if p.is_file()}

before = inventory()
backup = root / 'device-evidence' / ('production-install-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
backup.mkdir()
(backup / 'before-sha256.json').write_text(json.dumps(before, indent=2) + '\n')
shutil.copy2(retro / 'libs/emu_sfc.so', backup / 'emu_sfc.so')
for name in ('states/SFC', 'saves/SFC'):
    if (retro / name).is_dir(): shutil.copytree(retro / name, backup / name)
for p in backup.rglob('*'):
    if p.is_file() and str(p.relative_to(backup)).replace('\\', '/').startswith(('states/', 'saves/')):
        assert digest(p) == digest(retro / p.relative_to(backup))

package.mkdir(exist_ok=True)
shutil.copy2(build / 'emu_sfc.so', package / 'emu_sfc.so')
instructions = '''D-R35 SNES Plus production v11

This adapter retains the adaptive rendering used in the successful v10 test.
It keeps audio and emulated game processing enabled on every core step and
omits some drawing when measured work exceeds the budget, capped at half.
No automatic reports, OSS queue queries, audio captures, worker threads or
timed picture freezes. The continuous 44100 Hz resampler and chunk-backed
video buffers are unchanged. Compatible Plus save states retain their format.

Install only retro/libs/emu_sfc.so. Keep emu_sfc_plus.so under its own name.
rollback-to-v10.zip restores the exact adapter tested successfully on hardware.
rollback-to-clean.zip restores the older adapter without adaptive rendering.
The production cleanup passed ARM emulation checks; its next handheld run
still needs confirmation. No ROMs or saves are included in these packages.
'''
(package / 'instructions.txt').write_text(instructions)
with zipfile.ZipFile(package / 'update.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(build / 'emu_sfc.so', 'retro/libs/emu_sfc.so')
    z.write(package / 'instructions.txt', 'instructions.txt')
with zipfile.ZipFile(package / 'rollback-to-v10.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(backup / 'emu_sfc.so', 'retro/libs/emu_sfc.so')
with zipfile.ZipFile(package / 'rollback-to-clean.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(root / 'build/clean/emu_sfc.so', 'retro/libs/emu_sfc.so')

dest, temporary = retro / 'libs/emu_sfc.so', retro / 'libs/emu_sfc.so.productiontmp'
assert not temporary.exists()
try:
    shutil.copy2(build / 'emu_sfc.so', temporary)
    assert digest(temporary) == digest(build / 'emu_sfc.so')
    os.replace(temporary, dest)
    after = inventory()
    changed = [n for n in sorted(set(before) | set(after)) if before.get(n) != after.get(n)]
    assert changed == ['retro/libs/emu_sfc.so'], changed
except Exception:
    shutil.copy2(backup / 'emu_sfc.so', dest)
    raise
proof = {'frame_comparison': 4200, 'stereo_audio_frames': 3090874,
         'pcm_equal_to_v10_and_full_rendering': pcm_hash,
         'callback_history_equal_to_v10': callbacks_hash,
         'test_video_draws': 2100, 'test_video_holds': 2100,
         'adaptive_math_exactly_preserved': True, 'state_roundtrip': completed,
         'automatic_report_absent': True, 'raw_test_pcm_cleanup': 'pending'}
(package / 'verification.json').write_text(json.dumps(proof, indent=2) + '\n')
result = {'card': 'D:/', 'build': 'v11 production adaptive rendering', 'backup': str(backup),
          'changed_contents': changed, 'adapter_sha256': digest(dest), 'core_sha256': core_hash,
          'states_saves_roms_other_retro_files_unchanged': True,
          'hardware_test': 'v10 successful; production cleanup pending handheld confirmation'}
(package / 'card-D-installation-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
