from pathlib import Path
from hashlib import sha256
import json
import zipfile

root = Path(__file__).resolve().parent.parent
out = root/'SNES-Plus-v3-diagnostic'
out.mkdir(exist_ok=True)
shim = root/'build/v3-diagnostic/emu_sfc.so'
core = root/'build/v3-diagnostic/emu_sfc_plus.so'
rollback = root/'device-evidence/card-D-v2-return/emu_sfc.so'
def digest(p):
    return sha256(p.read_bytes()).hexdigest()
assert digest(rollback) == '4a805d19446fad487cf3c43a6b74bbed7027d6af037df1c9f393426a403cabb5'
assert digest(core) == '1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657'
assert digest(root/'build/v3-diagnostic/verification/audio.s16le') == digest(root/'build/v2/verification/audio.s16le')
checks=(root/'build/v3-diagnostic/checks.log').read_text()
assert 'PASS diagnostic:' in checks and 'PASS frames=1800' in checks
assert 'PASS recovered chunk ioctl ABI' in checks and 'PASS resampler:' in checks
readme='''DIIUM D-R35 -- SNES Plus v3 DIAGNOSTIC

Purpose: investigate clicks heard only on handheld playback. This is a
measurement build, not a claimed audio fix.

The v2 chunk-backed video buffers, 32040-to-44100 Hz continuous conversion,
upstream Plus core, controls, ROM handling and save-state format are preserved.
The diagnostic observes the existing sound-driver DSP file descriptor using
read-only OSS queries. It does not open another audio device, reconfigure it,
write its own PCM or insert silence. Unsupported queries are reported, not
treated as evidence that audio underruns occurred.

Added RAM: 86016 bytes of bounded measurement storage. Measurements cover
audio-write duration, gaps between writes, queue depth (if supported), run
duration and video duration. The first anomalies and a rolling tail are kept.
Periodic SD log writes are removed from retro_run. Metrics are written on
save-state serialization, game unload or core deinitialization.

On the handheld: test the wind scene, a fight and victory music. Note roughly
when clicking occurs and whether it changes. Finish with ESC -> Exit to return
to the launcher before shutting down. Reconnect the SD card as D:.
If the frontend does not unload the core at Exit, saving to an unused save-state
slot also flushes measurements. Powering off during play can lose RAM metrics.

Logs in retro:
  emu_sfc_plus_v3.log          Startup and total samples at unload.
  emu_sfc_plus_v3_timing.log   Bins and timing/queue events from the last run.

Installation: the update archive replaces only retro/libs/emu_sfc.so.
emu_sfc_plus.so must remain alongside it under its existing name.
Rollback archive restores the exact working v2 shim. No core, ROM, save, boot
script or launcher changes are included.

Validation: ARM/QEMU with copied device glibc 2.30; 1800 FF3 frames with audio
identical to v2; tagged state save/load; resampler chunk-boundary equivalence;
recovered chunk-memory ABI, alternating buffer and retention checks; mock OSS
tests for read-only commands, unsupported queries, measurements and bounded
event retention. Physical audio timing still requires the handheld test.
'''
(out/'README.txt').write_text(readme)
with zipfile.ZipFile(out/'SNES-Plus-v3-diagnostic-update.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(shim, 'retro/libs/emu_sfc.so')
with zipfile.ZipFile(out/'SNES-Plus-v3-diagnostic-rollback-to-v2.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(rollback, 'retro/libs/emu_sfc.so')
with zipfile.ZipFile(out/'SNES-Plus-v3-diagnostic-source.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(root/'SNES-Plus-v2/SNES-Plus-v2-source.zip', 'v2-full-source.zip')
    for name in ['emu_sfc_plus_v3_diag.c','audio_diagnostics.h','audio-diagnostics-check.c',
                 'adapter-check-v3-diag.c','video-contract-check-v3-diag.c',
                 'build-v3-diag.sh','run-v3-diag-checks.sh','prepare-v3-diag.py',
                 'package-v3-diag.py','install-v3-diag.py','harness.c']:
        p=root/'build'/name
        if p.exists(): z.write(p, 'build/'+name)
manifest={
    'build':'v3 diagnostic','adapter_sha256':digest(shim),'core_sha256':digest(core),
    'rollback_v2_sha256':digest(rollback),'diagnostic_ram_bytes':86016,
    'test_pcm_sha256':digest(root/'build/v3-diagnostic/verification/audio.s16le'),
    'hardware_test':'pending',
    'packages':{p.name:digest(p) for p in out.glob('*.zip')}
}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
