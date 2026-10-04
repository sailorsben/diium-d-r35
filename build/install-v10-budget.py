from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import csv, io, json, os, re, shutil, zipfile

root = Path(__file__).resolve().parent.parent
card = Path('D:/')
retro = card / 'retro'
package = root / 'SNES-Plus-v10-audio-priority'
build = root / 'build/v10-budget'
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
rows = list(csv.DictReader(io.StringIO('bin,adaptive_enabled,' + (test/'report.txt').read_text().split('bin,adaptive_enabled,',1)[1])))
rows = [r for r in rows if r.get('calls') is not None]
assert sum(int(r['calls']) for r in rows) == 4200
assert sum(int(r['draws']) for r in rows) == 2100
assert sum(int(r['duplicates']) for r in rows) == 2100
assert all(int(r['draws']) + int(r['duplicates']) == int(r['calls']) for r in rows)
assert max(tuple(map(int,v.split('.'))) for v in re.findall(r'GLIBC_([0-9]+\.[0-9]+)', (build/'abi-versions.txt').read_text())) <= (2,30)
package.mkdir(exist_ok=True)
proof = {'emulated_frames':4200, 'stereo_output_frames':3090874,
         'identical_pcm_sha256':digest(test/'native.s16le'),
         'identical_callback_history_sha256':digest(test/'batches.csv'),
         'actual_core_video_frames':2100, 'duplicate_video_callbacks':2100,
         'state_roundtrip':'ARM harness passed 1800 frames, real serialization and restoration',
         'hardware_result':'pending', 'adaptive_budget_check':'697/2000 skips for measured mine costs; average 15355 us; light workload returns to full drawing', 'raw_test_pcm_cleanup':'pending'}
(package/'verification.json').write_text(json.dumps(proof,indent=2)+'\n')
shutil.copy2(build/'emu_sfc.so', package/'emu_sfc.so')
(package/'instructions.txt').write_text("""D-R35 v10: adaptive audio priority

Load the FF6 mine save and listen while standing still, then walk around.
Open and close FF6's party menu for comparison, then try a battle.
There is no timed picture hold. When frame work is too expensive, some frames
are not drawn; game CPU and audio keep running every frame. At most half of
drawing is skipped. Video can be less smooth in heavy scenes.

After about a minute on the map, ESC -> Save state to an unused slot if available
to write the report, then exit the game normally. Reconnect D: for collection.
Report: retro/emu_sfc_plus_v10_audio_priority.txt. No gameplay disk logging.
Existing Plus save states remain compatible; estimates restart on state load.
The rollback ZIP restores the exact clean adapter. The Plus core is unchanged.
Hardware results remain pending until you test this build.
""")
with zipfile.ZipFile(package/'rollback-to-clean.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(retro/'libs/emu_sfc.so', 'retro/libs/emu_sfc.so')
with zipfile.ZipFile(package/'update.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(build/'emu_sfc.so','retro/libs/emu_sfc.so')
    z.write(package/'instructions.txt','instructions.txt')

def inventory():
    return {str(p.relative_to(card)).replace('\\','/'):digest(p)
            for folder in [retro, card/'002'] for p in folder.rglob('*') if p.is_file()}
before = inventory()
backup = root/'device-evidence'/('v10-budget-install-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
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
temporary = retro/'libs/emu_sfc.so.v10tmp'
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
result = {'card':'D:/','build':'v10 adaptive audio priority','backup':str(backup),
          'changed_contents':changed,'adapter_sha256':digest(dest),'core_sha256':core_hash,
          'states_saves_snes_roms_other_retro_files_unchanged':True,'hardware_test':'pending'}
(package/'card-D-installation-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
