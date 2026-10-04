from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import csv, io, json, os, re, shutil, zipfile

root = Path(__file__).resolve().parent.parent
card = Path('D:/')
retro = card / 'retro'
package = root / 'SNES-Plus-v9-core-render-test'
build = root / 'build/v9-render'
clean_hash = '16aa482408689d4a2ff5ee622ae90b2123471bb64c397127a4d7e0e738ed1ea4'
core_hash = '1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657'
def digest(p):
    h = sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
assert (retro / 'vrtemu').is_file(), 'Test card must be mounted as D:'
assert digest(retro/'libs/emu_sfc.so') == clean_hash, 'Expected the clean Plus adapter'
assert digest(retro/'libs/emu_sfc_plus.so') == core_hash
control, test = build/'verification/control', build/'verification/test'
assert digest(control/'native.s16le') == digest(test/'native.s16le')
assert digest(control/'batches.csv') == digest(test/'batches.csv')
rows = list(csv.DictReader(io.StringIO('bin,render_off,' + (test/'report.txt').read_text().split('bin,render_off,',1)[1])))
assert sum(int(r['draws']) for r in rows) == 3000
assert sum(int(r['duplicates']) for r in rows) == 1200
assert all(int(r['draws']) == 0 for r in rows if r['render_off'] == '1')
assert max(tuple(map(int,v.split('.'))) for v in re.findall(r'GLIBC_([0-9]+\.[0-9]+)', (build/'abi-versions.txt').read_text())) <= (2,30)
package.mkdir(exist_ok=True)
proof = {'emulated_frames':4200, 'stereo_output_frames':3090874,
         'identical_pcm_sha256':digest(test/'native.s16le'),
         'identical_callback_history_sha256':digest(test/'batches.csv'),
         'actual_core_video_frames':3000, 'duplicate_video_callbacks':1200,
         'state_roundtrip':'ARM harness passed 1800 frames, real serialization and restoration',
         'hardware_result':'pending', 'raw_test_pcm_cleanup':'pending'}
(package/'verification.json').write_text(json.dumps(proof,indent=2)+'\n')
shutil.copy2(build/'emu_sfc.so', package/'emu_sfc.so')
(package/'instructions.txt').write_text('''D-R35 v9: disable core rendering, preserve audio/game processing

Load FF6's save state in the clicking mine, then stand still.
About 30 seconds of normal video -> about 20 seconds holding the picture ->
normal video again. Listen for whether clicking stops during the held picture
and returns afterward. Do not move during the held picture; gameplay continues.
This is a one-time sequence after each game load, successful state load or reset.
Times can be longer if gameplay is running slowly; opening ESC pauses the count.

After the picture resumes, wait another 20 seconds, then use ESC and Save state
(an unused slot if available) to flush the timing report. Exit the game normally.
The report is retro/emu_sfc_plus_v9_render_test.txt on the card. Reconnect D:.
No disk logging occurs during gameplay. The ordinary Plus state format remains.

The rollback ZIP restores the exact clean adapter. emu_sfc_plus.so is unchanged.
Hardware behavior remains unverified until you test it.
''')
with zipfile.ZipFile(package/'rollback-to-clean.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(retro/'libs/emu_sfc.so', 'retro/libs/emu_sfc.so')
with zipfile.ZipFile(package/'update.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(build/'emu_sfc.so','retro/libs/emu_sfc.so')
    z.write(package/'instructions.txt','instructions.txt')

def inventory():
    return {str(p.relative_to(card)).replace('\\','/'):digest(p)
            for folder in [retro, card/'002'] for p in folder.rglob('*') if p.is_file()}
before = inventory()
backup = root/'device-evidence'/('v9-render-install-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
backup.mkdir(exist_ok=False)
(backup/'before-sha256.json').write_text(json.dumps(before,indent=2)+'\n')
shutil.copy2(retro/'libs/emu_sfc.so',backup/'emu_sfc.so')
for name in ['states/SFC','saves/SFC']:
    if (retro/name).is_dir(): shutil.copytree(retro/name, backup/name)
assert digest(backup/'emu_sfc.so') == clean_hash
for p in backup.rglob('*'):
    if p.is_file() and str(p.relative_to(backup)).replace('\\','/').startswith(('states/','saves/')):
        assert digest(p) == digest(retro/p.relative_to(backup))
dest = retro/'libs/emu_sfc.so'
temporary = retro/'libs/emu_sfc.so.v9tmp'
assert not temporary.exists()
try:
    shutil.copy2(build/'emu_sfc.so',temporary)
    assert digest(temporary) == digest(build/'emu_sfc.so')
    os.replace(temporary,dest)
    after = inventory()
    changed = [n for n in sorted(set(before)|set(after)) if before.get(n)!=after.get(n)]
    assert changed == ['retro/libs/emu_sfc.so'], changed
except Exception:
    shutil.copy2(backup/'emu_sfc.so',dest)
    raise
result = {'card':'D:/','build':'v9 core-render A/B','backup':str(backup),
          'changed_contents':changed,'adapter_sha256':digest(dest),'core_sha256':core_hash,
          'states_saves_snes_roms_other_retro_files_unchanged':True,'hardware_test':'pending'}
(package/'card-D-installation-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
