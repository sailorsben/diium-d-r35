from pathlib import Path
import hashlib, json, shutil, zipfile

work = Path(__file__).resolve().parent.parent
copy = Path(r'H:\DIIUM D-R35')
package = work / 'SNES-Plus-v2'
assert not package.exists(), 'Never overwrite a rollback/package.'
old = json.loads((work / 'SNES-Plus-v1/manifest.json').read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for rel, entry in old['changes'].items():
    assert sha(copy / rel) == entry['sha256'], rel
package.mkdir()
shutil.copy2(copy / 'retro/libs/emu_sfc.so', package / 'emu_sfc-v1-backup.so')
before = {str(p.relative_to(copy)).replace('\\','/'): sha(p) for p in copy.rglob('*') if p.is_file()}
files = {'retro/libs/emu_sfc.so': work / 'build/v2/emu_sfc.so',
         'retro/libs/emu_sfc_plus.so': work / 'build/v2/emu_sfc_plus.so'}
assert sha(files['retro/libs/emu_sfc_plus.so']) == old['changes']['retro/libs/emu_sfc_plus.so']['sha256']
manifest = {'version': 2, 'files': {rel: {'bytes': p.stat().st_size, 'sha256': sha(p)} for rel,p in files.items()},
    'previous_adapter_sha256': sha(package / 'emu_sfc-v1-backup.so'),
    'hardware_test': 'pending; ARM/mock-ioctl tests passed', 'physical_card_D_modified': False}
readme = f'''DIIUM D-R35 - SNES Plus v2: hardware video-buffer test
Prepared October 3, 2026 America/Chicago

USE BOTH FILES WITH THESE EXACT NAMES
  retro/libs/emu_sfc.so       = ADAPTER v2 ({files['retro/libs/emu_sfc.so'].stat().st_size} bytes)
  retro/libs/emu_sfc_plus.so  = PLUS CORE ({files['retro/libs/emu_sfc_plus.so'].stat().st_size} bytes)
The launcher opens emu_sfc.so. That adapter opens emu_sfc_plus.so.
Renaming the Plus core to emu_sfc.so bypasses the adapter and its audio/video
handling. Extract this ZIP and merge its retro folder into the SD root D:\\,
replacing these two files. Keep the existing folder and all other files.
The original core and Snes9x 2010 files are retained. No firmware flash is used.

CHANGED IN V2
The adapter now copies every video frame into vendor chunk memory allocated
through /dev/chunkmem, including native images that already have compact rows.
Two alternating buffers preserve the previous image while the display worker
reads it. Row pitch remains compact RGB565. The adapter waits for the worker
before freeing the video allocation. A chunk allocation error produces a
diagnostic instead of falling back to an ordinary RAM buffer on the handheld.
The unchanged Plus core and continuous 32040-to-44100 Hz audio conversion are
retained. Plus v1 and v2 save-state formats are the same.
The earlier boot-screen-test removal remains installed; this update does not
replace init or change the menu, driver, settings, ROMs, or saves.

WHY THIS CHANGE
The original core's S9xInitDisplay calls ChunkMemAlloc for its screen buffers.
Recovered ChunkMemAlloc uses /dev/chunkmem and ioctl 0xc00c4301 with three
32-bit fields: physical address, mapped virtual address, and allocation bytes.
ChunkMemFree uses ioctl 0x400c4303. The display driver's worker passes the
frame address into its PScale hardware-scaler request. V1 instead handed it
ordinary BSS memory. This is a concrete mismatch and a leading explanation
for corruption; the actual corrected display still needs a handheld test.

CARD EVIDENCE
The D: card was READ only. Both installed files matched the v1 package hashes.
Its v1 log recorded successful FF3 loading and 9600 completed emulator frames.
The user reports substantially improved sound with v1 but intermittent proper
graphics in the top half and corrupt graphics below. Earlier testing renamed
the raw Plus core to emu_sfc.so, bypassing the adapter. The later D: snapshot
has the intended two-file arrangement. The two runs must not be conflated.
The pause-menu image differs from the existing game cover PNG, consistent
with a captured game preview rather than that cover art.

CHECK THIS BUILD
Safely eject the card, boot the handheld and run FF3 fresh.
Check the whole screen through the intro, then press ESC and Resume a few times.
Note whether sound remains improved and whether clicking persists.
Afterward, reconnect the card. The diagnostic is:
  D:\\retro\\emu_sfc_plus_v2.log
It should contain a VIDEO chunk pool line with mapped/physical addresses,
allocation size, wait=1, and the first video dimensions/pitches.
There should be no TEST ONLY heap-mode line on the handheld.

VALIDATION LIMITS
QEMU ARM Cortex-A7 execution with the device's exported glibc 2.30 passed
1800 FF3 frames, image output, save-state roundtrip, incompatible-state rejection
and the continuous audio resampling tests. The chunk-ioctl contract, alternating
buffer retention, row copying and wait-before-free were checked using mocked
kernel calls. QEMU game tests explicitly use ordinary RAM because the PC has
no /dev/chunkmem device. These checks do not prove physical DMA, cache behavior,
driver timing, or clean sound on the handheld.

ROLLBACK
Power off and merge SNES-Plus-v2-rollback-to-v1.zip onto the SD root. It restores
only the exact v1 adapter at retro/libs/emu_sfc.so; keep emu_sfc_plus.so.
The earlier SNES-Plus-v1 rollback ZIP restores the pre-Plus experiment instead.

SOURCE AND CREDITS
The Plus core is unchanged upstream commit a79dfe9047e7fec58808aefe48ad2bf499c7af11.
https://github.com/libretro/snes9x2005
Snes9x/libretro contributors and Shay Green (Blargg).
SNES-Plus-v2-source.zip contains the full previous source archive plus v2 source,
build scripts, tests, ABI report, and disassembly evidence. No game ROM or
captured game audio is included. To rebuild: unpack the included v1 source ZIP
first, overlay the build files from this archive, prepare the exported device
libraries, run build-plus.sh, build-adapter.sh, then build-v2.sh. See v1 README
and build scripts for the original setup details.
'''
(package / 'README.txt').write_text(readme, encoding='utf-8')
(package / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

def zip_file(z, p, rel, executable=False):
    info = zipfile.ZipInfo(rel); info.create_system = 3
    info.external_attr = (0o100755 if executable else 0o100644) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(info, p.read_bytes())
with zipfile.ZipFile(package / 'SNES-Plus-v2-update.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for rel,p in files.items(): zip_file(z, p, rel, True)
    z.write(package / 'README.txt', 'README.txt')
    z.write(package / 'manifest.json', 'manifest.json')
    z.write(work / 'build/snes9x2005/copyright', 'licenses/snes9x-copyright.txt')
with zipfile.ZipFile(package / 'SNES-Plus-v2-rollback-to-v1.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    zip_file(z, package / 'emu_sfc-v1-backup.so', 'retro/libs/emu_sfc.so', True)
    z.write(package / 'README.txt', 'README.txt')
with zipfile.ZipFile(package / 'SNES-Plus-v2-source.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(work / 'SNES-Plus-v1/SNES-Plus-v1-source.zip', 'SNES-Plus-v1-source.zip')
    for rel in ['emu_sfc_plus_v2.c','adapter-check-v2.c','video-contract-check.c','build-v2.sh',
                'run-v2-checks.sh','package-v2.py','v2/abi-versions.txt','v2-tests.log',
                'trace-hardware.py','hardware-disassembly.txt']:
        z.write(work / 'build' / rel, 'build/' + rel)
    z.write(package / 'README.txt', 'README.txt')

shutil.copy2(files['retro/libs/emu_sfc.so'], copy / 'retro/libs/emu_sfc.so')
after = {str(p.relative_to(copy)).replace('\\','/'): sha(p) for p in copy.rglob('*') if p.is_file()}
changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
assert changed == ['retro/libs/emu_sfc.so']
assert sha(copy / 'retro/libs/emu_sfc.so') == manifest['files']['retro/libs/emu_sfc.so']['sha256']
for p in package.glob('*.zip'):
    with zipfile.ZipFile(p) as z: assert z.testzip() is None
    print(p.name, p.stat().st_size, sha(p))
print('H: copy updated: only retro/libs/emu_sfc.so changed. D: card read only.')
