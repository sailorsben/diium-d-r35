"""Install only the user's authorized three files, with verified rollback copies."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, zipfile
from datetime import datetime

work = Path(__file__).resolve().parent.parent
sd = Path(r'H:\DIIUM D-R35').resolve()
assert sd == Path(r'H:\DIIUM D-R35').resolve() and (sd / 'retro/vrtemu').is_file()
destination = work / 'SNES-Plus-v1'
assert not destination.exists(), 'Use a fresh package destination; never overwrite a rollback.'
destination.mkdir()
rollback = destination / 'rollback'
rollback.mkdir()

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

baseline = json.loads((work / 'sd-inspection.json').read_text(encoding='utf-8'))
for binary in baseline['binaries']:
    assert sha(sd / binary['path']) == binary['sha256'], binary['path'] + ' changed since inspection'
assert (sd / 'retro/init').read_bytes() == (work / 'boot-cleanup/init.original').read_bytes()
assert not (sd / 'retro/libs/emu_sfc_plus.so').exists()
assert b'showlogo' not in (work / 'boot-cleanup/init').read_bytes()
before = {str(p.relative_to(sd)).replace('\\', '/'): sha(p) for p in sd.rglob('*') if p.is_file()}
(destination / 'before-hashes.json').write_text(json.dumps(before, indent=2), encoding='utf-8')

changes = {
    'retro/init': work / 'boot-cleanup/init',
    'retro/libs/emu_sfc.so': work / 'build/emu_sfc.so',
    'retro/libs/emu_sfc_plus.so': work / 'build/emu_sfc_plus.so',
}
for rel in ['retro/init', 'retro/libs/emu_sfc.so']:
    target = rollback / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(sd / rel, target)
    assert sha(target) == before[rel]

commit = (work / 'build/core-source-commit.txt').read_text().strip()
readme = f'''DIIUM D-R35 - SNES Plus v1 update
Prepared {datetime.now().isoformat(timespec='seconds')} (Windows local time)

Installed into the supplied COPY at H:\\DIIUM D-R35, not onto a live handheld.

CHANGES
1. retro/libs/emu_sfc.so: D-R35 adapter, version 1.
2. retro/libs/emu_sfc_plus.so: upstream Snes9x 2005 Plus, commit {commit}.
3. retro/init: removed only the delayed showlogo screen-size experiment.
The original emulator core, Snes9x 2010 core, ROMs, menu, driver, settings,
saves, and all other files remain unchanged.

COPY TO THE REAL CARD
Power the handheld off and put its SD card in the PC. Extract the update ZIP.
Merge the ZIP's retro folder into the existing retro folder at the SD root.
Replace init and emu_sfc.so and add emu_sfc_plus.so. Do not replace the whole
retro folder or delete its existing contents. Safely eject the SD card.
Alternatively, copy those same three files from the updated H copy.
No firmware flash, internal-storage update, or Android APK installation is used.

CHECK ON THE HANDHELD
Boot once and check whether the delayed menu flash is gone.
Open FF3/VI fresh, test its opening music for 1-2 minutes, then test controls
and menu return. Note whether music wobbles, crackles, slows, or sounds clean.
Use fresh Plus save states. States from the previous cores are incompatible;
the adapter rejects them. In-game battery saves use the normal save-RAM API.
Battery-save persistence, button mappings, frame pacing, and sound through
the physical driver still need the handheld test.
The adapter writes retro/emu_sfc_plus_v1.log on the real card. If loading fails
or audio is still bad, preserve that log after exiting/powering off normally.
Each fresh core session replaces that diagnostic log; it does not grow forever.

ROLLBACK
Power off, reinsert the card into the PC, and merge the rollback ZIP's retro
folder onto the SD root, replacing retro/init and retro/libs/emu_sfc.so.
This restores the exact pre-update boot script and emulator adapter. The
extra emu_sfc_plus.so file is harmless when the old adapter is restored.
Do not load Plus save states in the previous core.

IMPLEMENTATION AND VERIFICATION
The Plus core uses Blargg's more accurate SNES APU and native 32040 Hz audio.
The adapter continuously resamples stereo output to the launcher's 44100 Hz,
preserves fractional phase across batches, normalizes RGB565 row pitch, loads
raw/ZIP ROMs, provides safe input callbacks, and intercepts unsafe geometry
and AV requests rather than invoking the vendor's broken geometry callback.
No host geometry callback or binary patch is used.

ARM Cortex-A7 execution was tested under QEMU with the device's exported
glibc 2.30 and libraries. FF3 ran for 1800 frames through each of ZIP path,
ZIP memory, and raw-ROM memory loading. All three produced identical PCM,
valid video, and working serialize/unserialize in one process. Incompatible
state rejection was tested. A 1000 Hz stereo tone remained 1000.023 Hz within
FFT bin resolution; whole/chunked processing was byte-identical. Geometry
sentinels and the absence of vendor geometry/AV calls were checked directly.
These tests do not measure handheld CPU speed, memory use, speaker sound,
SD performance, or the launcher's actual audio-driver scheduling.
The supplied core needs only GLIBC_2.4/2.7 symbols; the shim GLIBC_2.4.
Core static text/data/BSS totals ~1.17 MiB; adapter ~0.52 MiB, excluding heap
and shared dependencies. QEMU process RSS is not handheld RSS.

CREDITS AND SOURCE
Snes9x, libretro contributors, and Shay Green (Blargg).
Upstream: https://github.com/libretro/snes9x2005
Documentation: https://docs.libretro.com/library/snes9x_2005_plus/
Full upstream tracked source, adapter source, build scripts, tests and original
license notices are supplied in SNES-Plus-v1-source.zip, alongside this update.
The upstream core source was not modified. Existing device libraries are
external runtime/build dependencies and are not distributed in this package.
Build requires ARM GCC, make, zlib headers, and the exported device libraries
in build/sysroot/lib; see the build scripts for flags and symlink setup.
The private game ROM and captured game audio are not bundled in these ZIPs.
'''
(destination / 'README.txt').write_text(readme, encoding='utf-8')
manifest = {'source_commit': commit, 'changes': {}, 'rollback': {}}
for rel, source in changes.items():
    manifest['changes'][rel] = {'sha256': sha(source), 'bytes': source.stat().st_size,
        'previous_sha256': before.get(rel)}
for rel in ['retro/init', 'retro/libs/emu_sfc.so']:
    manifest['rollback'][rel] = {'sha256': sha(rollback / rel), 'bytes': (rollback / rel).stat().st_size}
(destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

source_zip = destination / 'SNES-Plus-v1-source.zip'
source_root = work / 'build/snes9x2005'
tracked = subprocess.check_output(['git', '-C', str(source_root), 'ls-files'], text=True).splitlines()
with zipfile.ZipFile(source_zip, 'w', zipfile.ZIP_DEFLATED) as z:
    for rel in tracked:
        z.write(source_root / rel, 'build/snes9x2005/' + rel)
    for rel in ['emu_sfc_plus.c', 'harness.c', 'adapter-check.c', 'build-plus.sh', 'build-adapter.sh',
                'run-harness.sh', 'run-more-checks.sh', 'core-source-commit.txt', 'abi-versions.txt',
                'verification-path.log', 'verification-more.log', 'install-and-package.py']:
        z.write(work / 'build' / rel, 'build/' + rel)
    z.write(work / 'boot-cleanup/init.diff', 'boot-cleanup/init.diff')
    z.writestr('README.txt', readme)
    for name in ['GPL-2', 'LGPL-2.1']:
        license_path = Path(r'\\wsl.localhost\Ubuntu\usr\share\common-licenses') / name
        z.write(license_path, 'licenses/' + name + '.txt')

with zipfile.ZipFile(destination / 'SNES-Plus-v1-update.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for rel, source in changes.items():
        info = zipfile.ZipInfo(rel)
        info.create_system = 3; info.external_attr = 0o100755 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, source.read_bytes())
    z.write(destination / 'README.txt', 'README.txt')
    z.write(destination / 'manifest.json', 'manifest.json')
    z.write(source_root / 'copyright', 'licenses/snes9x-copyright.txt')
with zipfile.ZipFile(destination / 'SNES-Plus-v1-rollback.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for rel in manifest['rollback']:
        info = zipfile.ZipInfo(rel)
        info.create_system = 3; info.external_attr = 0o100755 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, (rollback / rel).read_bytes())
    z.write(destination / 'README.txt', 'README.txt')

for rel, source in changes.items():
    assert (sd / rel).resolve().is_relative_to(sd)
    shutil.copy2(source, sd / rel)
    assert sha(sd / rel) == manifest['changes'][rel]['sha256']

after = {str(p.relative_to(sd)).replace('\\', '/'): sha(p) for p in sd.rglob('*') if p.is_file()}
changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
assert changed == sorted(changes), changed
report = {'installed_to': str(sd), 'changed_files': changed, 'other_files_unchanged': len(before) - 2,
          'manifest': manifest, 'actual_handheld_test': 'pending'}
(destination / 'installation-verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'manifest'}, indent=2))
for p in sorted(destination.glob('*.zip')):
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
    print(f'{p.name}: {p.stat().st_size} bytes; SHA256 {sha(p)}')
