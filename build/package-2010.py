from pathlib import Path
from hashlib import sha256
import json
import shutil
import zipfile

root = Path(__file__).resolve().parent.parent
build = root / 'build/comparison-2010'
package = root / 'SNES-2010-comparison'
package.mkdir(exist_ok=True)
for name in ['emu_sfc.so', 'emu_sfc_2010.so']:
    shutil.copy2(build / name, package / name)
restore = package / 'restore'
restore.mkdir(exist_ok=True)
shutil.copy2(root / 'build/clean/emu_sfc.so', restore / 'emu_sfc.so')
digest = lambda p: sha256(p.read_bytes()).hexdigest()
manifest = {
    'core': 'Snes9x 2010',
    'upstream_commit': (build / 'core-source-commit.txt').read_text().strip(),
    'core_sha256': digest(package / 'emu_sfc_2010.so'),
    'adapter_sha256': digest(package / 'emu_sfc.so'),
    'plus_adapter_sha256': digest(restore / 'emu_sfc.so'),
    'plus_core_sha256': '1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657',
    'state_folder': 'retro/states/SFC',
    'preserved_plus_state_folder': 'retro/states/SFC-Plus-preserved',
    'state_tag': 'D3520101/fe69',
    'default_logging': False,
    'audio_video_transport': 'Same as clean Plus adapter; native core/rate/state identity changed',
    'verification': {
        'arm_qemu_device_glibc': '2.30',
        'ff3_frames': 1800,
        'video_audio_save_load': True,
        'chunk_buffer_contract': True,
        'continuous_resampler': True,
        'stat_compatibility': True,
        'maximum_required_glibc': '2.17',
        'harness_max_rss_kib': 29284,
        'rom_sha256': '0f51b4fca41b7fd509e4b8f9d543151f68efa5e97b08493e4b2a0c06f5d8d5e2',
        'handheld_performance_and_clicking': 'Not tested yet'
    }
}
assert manifest['plus_adapter_sha256'] == '16aa482408689d4a2ff5ee622ae90b2123471bb64c397127a4d7e0e738ed1ea4'
(package / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
(package / 'README.txt').write_text('''DIIUM D-R35: Snes9x 2010 comparison

The installed SNES adapter loads emu_sfc_2010.so. Keep both files in retro/libs.
All SNES games use 2010 while this comparison is installed. The unchanged Plus
core remains alongside it and the clean Plus adapter is backed up on the PC.

The audio transport and display handling match the clean Plus adapter:
continuous conversion to 44100 Hz, original frontend audio callback, packed
RGB565 copied to two alternating chunk-memory buffers, unsafe geometry callback
intercepted. No display experiment, audio capture, timing worker or automatic
diagnostic log is included. New toolchain stat names are bridged to the device
glibc 2.30 ARM32 entry points; no device runtime library is replaced.

Save states from Plus cannot be loaded by 2010. Installation preserves the whole
existing SNES state folder as retro/states/SFC-Plus-preserved and makes a fresh
SFC folder for 2010. Original states are also backed up on the PC. Games, ROMs,
menus and battery-save files are unchanged. For this test launch Final Fantasy
VI and start a new game. Compare the opening, outdoor walking, and combat with
your previous Plus run. Report clicks, music pitch/warbling, speed and graphics.

To restore the clean Plus adapter and original states after reconnecting D:,
run restore-plus.py with the same Windows Python used to install this package.
The script verifies identities, archives new 2010 states on the PC, returns the
original Plus state folder, and removes only the comparison core it installed.
Do not copy a Plus save state into the 2010 state folder.

Verification: ARM/QEMU with the handheld glibc 2.30, exact card FF3 ROM, 1800
frames, rendered title image checked, input/audio callbacks, state save/load,
SRAM exposure, chunk-memory contract, continuous resampling, stat ABI checks.
No GLIBC version later than 2.17 is required. Test harness peak RSS was 29284
KiB; this excludes the real launcher/driver. Handheld speed, memory pressure,
sound quality and resolution of clicking remain unproven until the device run.
''', encoding='utf-8')
with zipfile.ZipFile(package / 'SNES-2010-comparison-update.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for name in ['emu_sfc.so', 'emu_sfc_2010.so']:
        z.write(package / name, 'retro/libs/' + name)
    z.write(package / 'README.txt', 'README.txt')
print(json.dumps(manifest, indent=2))
