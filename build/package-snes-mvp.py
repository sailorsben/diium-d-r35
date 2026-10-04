"""Prepare/install one-shot SNES MVP without replacing any production binary."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import os
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / 'SNES-MVP-v1'
BUILD = ROOT / 'build/snes-mvp'
EXPECTED = {
    'retro/init': '6d65bf756183f37c19a542703c8d50193d5c137e7d0d45be4ac980fcdcb8efbd',
    'retro/vrtemu': '8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72',
    'retro/driver.so': '2c0134b3fc425f5b65c271c014e291824590c773190014f4e50c3ed33c2f13f9',
    'retro/main': 'ace334d88d013240e2b93eb8cb691f1f09e4109d6d509648a5518cbae0b25873',
    'retro/showlogo': '436d8018808b150c926274575a195f664e61db646f44713371019e9ae10caf3b',
    'retro/libs/emu_sfc.so': '3a0ceb3cfde5148cecec0fb7cf5cf4c57229f9c6040626f79de3a520ae38c00e',
    'retro/libs/emu_sfc_plus.so': '1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657',
}

def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()

def prepare():
    binary = BUILD / 'out/snes-mvp'
    assert binary.is_file(), 'Build the runner first'
    checks = json.loads((BUILD / 'out/verification.json').read_text())
    assert checks['passed'] and checks['binary_sha256'] == digest(binary), 'Verify this exact build first'
    versions = re.findall(r'GLIBC_(\d+)\.(\d+)', (BUILD / 'out/abi-versions.txt').read_text())
    assert max((int(a), int(b)) for a,b in versions) <= (2,30)
    payload = PACKAGE / 'retro/snes-mvp'
    payload.mkdir(parents=True, exist_ok=True)
    shutil.copy2(binary, payload / 'snes-mvp')
    before = (ROOT / 'Hardware-Console-v3/init.before').read_bytes()
    assert sha256(before).hexdigest() == EXPECTED['retro/init']
    (payload / 'init.stock').write_bytes(before)
    (PACKAGE / 'init.stock').write_bytes(before)
    shutil.copy2(BUILD / 'launch.sh', payload / 'launch.sh')
    (payload / 'armed').write_text('SNES-MVP-v1.5 one-shot\n', newline='\n')
    old = b'  /usr/retro/main &'
    assert before.count(old) == 1
    new = b'''  # D35 SNES MVP: own hardware before the stock supervisor starts.
  if [ -f /usr/retro/snes-mvp/armed ]; then
    /bin/sh /usr/retro/snes-mvp/launch.sh
  fi
  /usr/retro/main &'''
    (PACKAGE / 'init.mvp').write_bytes(before.replace(old,new))
    instructions = '''D-R35 SNES MVP 1.5 -- physical D-pad correction

The next boot opens the SNES game library. D-pad selects; A or Start launches.
B in the library returns to the stock launcher. In-game, use MENU (or the
documented Start+Select fallback) for Resume / Save snapshot / Load snapshot / Exit.
Snapshots and in-game saves stay in retro/snes-mvp/saves. Existing saves are untouched.
The MVP scans existing card folder 002 and ROMs/SNES; supports .zip/.sfc/.smc.

This is a one-shot boot. After a restart, the production launcher returns automatically.
v1.4 worked: the launcher responded, FF6 started, and the save state loaded.
The D-pad labels were wrong because native vendor masks had been interpreted
without tracing the final stock libretro callback table. v1.5 corrects the
shared input path: GPIO 0x200 Up, 0x201 Down, 0x202 Left, 0x203 Right.
The GPIO regression now extracts the reference mask table from the pinned stock
executable. Both launcher and game use the corrected mapping.
The working direct kernel clock and relative wait repair are retained.
Menu repeats, gameplay deadlines, heartbeat and logs share that clock.
Boot-helper copies and three bounded process/IPC snapshots are still collected.
The working splash handoff still completes before opening the MVP display.
Held buttons no longer block the first library frame. Startup has a 20-second
watchdog and persistent breadcrumbs in retro/snes-mvp/startup.log. If startup
fails, it attempts to return to stock; the following reboot always skips the MVP.
If the screen stays on the loading animation, power off normally if possible,
then reconnect the card. startup.log, startup-processes.txt, runtime-platform.txt
and startup-stall.txt if present identify the last stage and process state.
To re-arm: create an empty file named armed in retro/snes-mvp on the card.
To remove the boot change: restore this package's init.stock as card retro/init.
Do not overwrite any emulator library, driver, ROM or original save.

Test: first press Down, Up, then A or Start and check selection/launch behavior.
Launch Final Fantasy VI (not Rev 1). MENU -> Load snapshot opens your copied
FF6 cave/map save point. Resume, check controls/music, play map -> party menu -> map,
open MENU, save a snapshot, move, reload, then Exit game and B to stock launcher.
Report whether pictures, controls and sound work, and where anything fails.
Return the SD card after shutdown; retro/snes-mvp/last-run.log and
retro/snes-mvp/saves/last-session.txt provide evidence.

Status: boot/library, game start and save-state load are hardware-confirmed.
The physical D-pad correction remains pending the next handheld test.
Clock-skew, launcher navigation, stock-table input and real-core ARM checks pass.
ARM/QEMU checks do not prove physical audio/display/input or a speed increase.
The current Plus core/resampler/adaptive policy are retained. This MVP uses one
binary with separate menu/runtime modules and releases menu allocations in-game.
'''
    (PACKAGE / 'TEST-ME.txt').write_text(instructions, newline='\n')
    shutil.copy2(PACKAGE / 'TEST-ME.txt', payload / 'TEST-ME.txt')
    manifest = {'name':'SNES-MVP-v1.5','built_utc':datetime.now(timezone.utc).isoformat(),
                'binary_sha256':digest(binary),'core_sha256':EXPECTED['retro/libs/emu_sfc_plus.so'],
                'verification':checks,'hardware_test':'pending','scope':'SNES-only; one-shot; isolated saves',
                'sources':{p.name:digest(p) for p in BUILD.glob('*') if p.suffix in ('.c','.h')},
                'payload':{str(p.relative_to(PACKAGE)).replace('\\','/'):digest(p)
                           for p in payload.rglob('*') if p.is_file()}}
    (PACKAGE / 'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(PACKAGE / 'SNES-MVP-v1.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in payload.rglob('*'):
            if p.is_file(): z.write(p,str(p.relative_to(PACKAGE)))
        for name in ('init.mvp','init.stock','TEST-ME.txt','manifest.json'): z.write(PACKAGE/name,name)
    return manifest

def install(card):
    card = card.resolve()
    assert str(card).lower() in ('d:\\','d:/'), 'This installer targets the verified D: card only'
    for relative,wanted in EXPECTED.items():
        assert digest(card/relative)==wanted, f'Unexpected card file: {relative}'
    target=card/'retro/snes-mvp'
    assert not target.exists(), 'MVP folder already exists; preserve it and inspect before updating'
    archive=ROOT/'device-evidence'/('snes-mvp-install-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    archive.mkdir()
    shutil.copy2(card/'retro/init',archive/'init.before')
    saves={str(p.relative_to(card)).replace('\\','/'):digest(p) for folder in ('retro/states','retro/saves')
           for p in (card/folder).rglob('*') if p.is_file()}
    (archive/'original-save-hashes.json').write_text(json.dumps(saves,indent=2)+'\n')
    shutil.copytree(PACKAGE/'retro/snes-mvp',target)
    for p in (PACKAGE/'retro/snes-mvp').rglob('*'):
        if p.is_file(): assert digest(p)==digest(target/p.relative_to(PACKAGE/'retro/snes-mvp'))
    tmp=card/'retro/init.snes-mvp-tmp'
    assert not tmp.exists()
    try:
        with tmp.open('xb') as f:
            f.write((PACKAGE/'init.mvp').read_bytes()); f.flush(); os.fsync(f.fileno())
        assert digest(tmp)==digest(PACKAGE/'init.mvp')
        os.replace(tmp,card/'retro/init')
        for relative,wanted in EXPECTED.items():
            if relative!='retro/init': assert digest(card/relative)==wanted
        for relative,wanted in saves.items(): assert digest(card/relative)==wanted
    except Exception:
        shutil.copy2(archive/'init.before',card/'retro/init')
        raise
    result={'card':str(card),'installed_utc':datetime.now(timezone.utc).isoformat(),
            'archive':str(archive),'one_shot_armed':True,'original_saves_unchanged':True,
            'production_binaries_unchanged':True,'init_sha256':digest(card/'retro/init'),
            'binary_sha256':digest(target/'snes-mvp'),'hardware_test':'pending'}
    (PACKAGE/'installation.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def update(card):
    """Update only the owned launcher files; preserve all private game progress."""
    card=card.resolve()
    assert str(card).lower() in ('d:\\','d:/'), 'This updater targets the verified D: card only'
    target=card/'retro/snes-mvp'
    assert target.is_dir() and not (target/'armed').exists(), 'Inspect/collect an armed test before updating'
    assert digest(card/'retro/init')==digest(PACKAGE/'init.mvp'), 'Unexpected boot hook'
    assert digest(target/'init.stock')==EXPECTED['retro/init'], 'Unexpected original init backup'
    for relative,wanted in EXPECTED.items():
        if relative!='retro/init': assert digest(card/relative)==wanted, f'Unexpected production file: {relative}'
    assert shutil.disk_usage(card).free>4*1024*1024, 'Insufficient card space'
    archive=ROOT/'device-evidence'/('snes-mvp-update-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    archive.mkdir()
    shutil.copy2(card/'retro/init',archive/'init.before')
    shutil.copytree(target,archive/'snes-mvp.before')
    protected={str(p.relative_to(card)).replace('\\','/'):digest(p)
               for folder in ('retro/states','retro/saves','retro/snes-mvp/saves')
               for p in (card/folder).rglob('*') if p.is_file()}
    (archive/'save-hashes.before.json').write_text(json.dumps(protected,indent=2)+'\n')
    changed=('snes-mvp','launch.sh','TEST-ME.txt')
    try:
        for name in changed:
            source=PACKAGE/'retro/snes-mvp'/name
            temporary=target/(name+'.update-tmp')
            assert not temporary.exists(), f'Unexpected staging file: {temporary}'
            with temporary.open('xb') as f:
                f.write(source.read_bytes()); f.flush(); os.fsync(f.fileno())
            assert digest(temporary)==digest(source)
            os.replace(temporary,target/name)
        for name in changed: assert digest(target/name)==digest(PACKAGE/'retro/snes-mvp'/name)
        for relative,wanted in protected.items(): assert digest(card/relative)==wanted, f'Save changed: {relative}'
        for relative,wanted in EXPECTED.items():
            if relative!='retro/init': assert digest(card/relative)==wanted
        assert digest(card/'retro/init')==digest(archive/'init.before')
        marker=target/'armed.update-tmp'
        assert not marker.exists(), 'Unexpected pending arm marker'
        with marker.open('xb') as f:
            f.write(b'SNES-MVP-v1.5 physical D-pad correction one-shot\n'); f.flush(); os.fsync(f.fileno())
        os.replace(marker,target/'armed')
    except Exception:
        for name in changed:
            old=archive/'snes-mvp.before'/name
            if old.exists(): shutil.copy2(old,target/name)
        raise
    result={'card':str(card),'updated_utc':datetime.now(timezone.utc).isoformat(),
            'archive':str(archive),'one_shot_armed':True,'all_saves_unchanged':True,
            'protected_save_count':len(protected),'production_binaries_unchanged':True,
            'init_unchanged':True,'binary_sha256':digest(target/'snes-mvp'),
            'launch_sha256':digest(target/'launch.sh'),'hardware_test':'physical D-pad correction pending',
            'previous_test':'Launcher worked, FF6 started and state loaded; D-pad directions incorrect; 2465 real core frames with no write errors'}
    (PACKAGE/'update-installation.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--install',action='store_true'); parser.add_argument('--update',action='store_true'); parser.add_argument('--card',default='D:/')
    args=parser.parse_args(); manifest=prepare()
    assert not (args.install and args.update)
    result=update(Path(args.card)) if args.update else install(Path(args.card)) if args.install else manifest
    print(json.dumps(result,indent=2))
