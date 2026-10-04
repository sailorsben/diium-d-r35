from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import json
import shutil
import zipfile

root=Path(__file__).resolve().parent.parent
package=root/'SNES-comparison-Chrono-Trigger'
card=Path('D:/')
retro=card/'retro'
assert (retro/'vrtemu').is_file() and (card/'002/Final Fantasy VI.zip').is_file()
def digest(p): return sha256(p.read_bytes()).hexdigest()
expected_adapter='16aa482408689d4a2ff5ee622ae90b2123471bb64c397127a4d7e0e738ed1ea4'
assert digest(retro/'libs/emu_sfc.so')==expected_adapter
check=(package/'verification/checks.log').read_text()
assert 'PASS frames=1800' in check and 'core=Snes9x 2005 Plus' in check
prepared=json.loads((package/'prepared.json').read_text())
assert digest(package/'Chrono Trigger.zip')==prepared['game_zip_sha256']
rom_destination=card/'002/Chrono Trigger.zip'
image_destination=card/'002/images/Chrono Trigger.png'
assert not rom_destination.exists() and not image_destination.exists(), 'Inspect existing game before replacing'
tracked=[p for folder in [retro,card/'002'] for p in folder.rglob('*') if p.is_file()]
before={str(p.relative_to(card)):digest(p) for p in tracked}
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup=root/'device-evidence'/('chrono-install-'+stamp)
backup.mkdir(parents=True,exist_ok=False)
for p in [card/'002/filelist.txt',retro/'fileinfo.txt',retro/'fileinfo.dat']:
    dest=backup/p.relative_to(card)
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p,dest)
    assert digest(dest)==digest(p)
shutil.copy2(package/'Chrono Trigger.zip',rom_destination)
shutil.copy2(package/'Chrono Trigger.png',image_destination)
def append_entry(path,line):
    old=path.read_bytes()
    key=line.split(';',1)[0].encode('utf-8')
    assert not any(row.split(b';',1)[0]==key for row in old.splitlines())
    new=old+(b'' if not old or old.endswith(b'\n') else b'\n')+line.encode('utf-8')+b'\n'
    path.write_bytes(new)
    assert path.read_bytes()==new
append_entry(card/'002/filelist.txt','Chrono Trigger.zip;Chrono Trigger;CHRONOTRIGGER;Chrono Trigger')
append_entry(retro/'fileinfo.txt','002/Chrono Trigger.zip;Chrono Trigger;CHRONO TRIGGER;CHRONOTRIGGER;Chrono Trigger')
with zipfile.ZipFile(rom_destination) as z:
    assert z.testzip() is None
    assert sha256(z.read('Chrono Trigger.sfc')).hexdigest()==prepared['rom_sha256']
after={str(p.relative_to(card)):digest(p) for folder in [retro,card/'002'] for p in folder.rglob('*') if p.is_file()}
changed={n for n in set(before)|set(after) if before.get(n)!=after.get(n)}
allowed={str(Path(n)) for n in ['002/Chrono Trigger.zip','002/images/Chrono Trigger.png',
                               '002/filelist.txt','retro/fileinfo.txt']}
assert changed==allowed,changed
assert digest(retro/'libs/emu_sfc.so')==expected_adapter
assert not list(retro.glob('emu_sfc_plus_v[1-8]*'))
report={'installed_game':'Chrono Trigger (USA)','card':'D:/','rom_path':str(rom_destination),
        'source':prepared['source'],'requested_archive_empty':True,'launcher_category':'SFC/SNES (002)',
        'changes':sorted(changed),'rom_sha256':prepared['rom_sha256'],
        'zip_sha256':digest(rom_destination),'backup':str(backup),
        'emulator_unchanged':True,'existing_roms_and_saves_unchanged':True,
        'hardware_game_launch':'pending','arm_emulator_boot_audio_video_state_checks':'passed'}
(package/'card-D-installation-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
