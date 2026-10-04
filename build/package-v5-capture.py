from pathlib import Path
from hashlib import sha256
import json
import zipfile

root=Path(__file__).resolve().parent.parent
out=root/'SNES-Plus-v5-capture'
out.mkdir(exist_ok=True)
def digest(p): return sha256(p.read_bytes()).hexdigest()
shim=root/'build/v5-capture/emu_sfc.so'
core=root/'build/v5-capture/emu_sfc_plus.so'
rollback=root/'device-evidence/card-D-v2-return/emu_sfc.so'
prior=root/'device-evidence/card-D-v4-return/emu_sfc.so'
assert digest(prior)=='808c7b7e82396dbc6ffca37c672565c39a4eaca3ae17971d71b5f0cba196e457'
assert digest(rollback)=='4a805d19446fad487cf3c43a6b74bbed7027d6af037df1c9f393426a403cabb5'
assert digest(core)=='1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657'
verification=json.loads((root/'build/v5-capture/verification/capture-verification.json').read_text())
assert verification['capture_matches_exact_output_segment'] and verification['audio_unchanged_from_v2']
checks=(root/'build/v5-capture/checks.log').read_text()
for required in ['PASS complete six-second WAV saved during play before unload',
                 'PASS periodic report before exit/save; no gameplay wait; worker joins promptly',
                 'PASS bounded capture starts at target run, completes exactly, and cannot overwrite completed PCM',
                 'PASS frames=1800', 'PASS diagnostic:', 'PASS resampler:',
                 'PASS recovered chunk ioctl ABI']:
    assert required in checks,required
readme='''DIIUM D-R35 -- SNES Plus v5 ON-DEVICE AUDIO CAPTURE

This is a diagnostic, not a claimed clicking fix. V4 measured the configured
44.1 kHz/stereo/16-bit format and reported nonempty queues during the later wind
section, despite persistent clicks. The user reports clicks with and without
the BESIGN isolator and with headphones or the built-in speaker.

V5 adds an exact six-second recording of the post-conversion PCM sent to the
vendor frontend. Capture begins at core run 8400, about 140 seconds of emulated
game time after a fresh load. These samples come from the actual handheld CPU.
PlayFrame was inspected: it passes the same pointer and stereo-frame count to
PlaySound, which converts the count to bytes and calls sound_driver_playframe.
This capture does not include analog speaker/headphone output or prove that the
kernel accepted every submitted byte.

Test: launch FF3/FFVI from the beginning and let the opening run without
skipping it for about three minutes, through the canyon/wind scene. Leave it
playing another 20 seconds. Note whether clicks are heard in that scene.
Then ESC -> Exit and reconnect the card as D:.
If a state was automatically restored or the opening was skipped, report that;
the capture will contain whichever scene was running at the specified time.

Files written under retro:
  emu_sfc_plus_v5_audio.wav       Six seconds, 44.1 kHz stereo signed 16-bit.
  emu_sfc_plus_v5_capture.txt     Exact output offset and first/last run.
  emu_sfc_plus_v5.log             Startup and periodic-reporter status.
  emu_sfc_plus_v5_timing.log      V4-style timing/queue measurements.

Gameplay copies submitted PCM into one bounded RAM allocation (1058400 bytes).
There are no capture file writes, waits or locks in the gameplay callback.
After completion, the existing background reporter saves the WAV; partial WAV
files use a .tmp name until completion. The capture cannot drop callbacks or
overwrite completed PCM. Existing diagnostic storage is 172088 bytes, worker
stack allocation 128 KiB, plus runtime overhead. Playback samples and their
counts, core options, resampling, video buffers and save-state format are kept.

Only retro/libs/emu_sfc.so is updated. Keep emu_sfc_plus.so alongside it.
The rollback ZIP restores the proven v2 adapter.

Checks: ARM/QEMU with device glibc 2.30; FF3 capture saved during play before
unload; WAV data equals the exact corresponding slice of submitted PCM;
1800-frame output remains byte-for-byte identical to v2; resampling, video
buffers, tagged states, read-only OSS queries, unsupported-query fallback,
nonblocking measurement locks, periodic output and worker shutdown pass.
The test harness starts capture earlier using an environment override; the
installed production default remains run 8400. Physical audio capture pending.
'''
(out/'README.txt').write_text(readme)
with zipfile.ZipFile(out/'SNES-Plus-v5-capture-update.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(shim,'retro/libs/emu_sfc.so')
with zipfile.ZipFile(out/'SNES-Plus-v5-capture-rollback-to-v2.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(rollback,'retro/libs/emu_sfc.so')
with zipfile.ZipFile(out/'SNES-Plus-v5-capture-source.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(root/'SNES-Plus-v4-diagnostic/SNES-Plus-v4-diagnostic-source.zip','v4-full-source.zip')
    for name in ['emu_sfc_plus_v5_capture.c','device_audio_capture.h','audio_diagnostics_v5_capture.h',
                 'audio-diagnostics-check-v5.c','adapter-check-v5-capture.c',
                 'video-contract-check-v5-capture.c','harness-v5-capture.c',
                 'build-v5-capture.sh','run-v5-capture-checks.sh','prepare-v5-capture.py',
                 'package-v5-capture.py','install-v5-capture.py']:
        z.write(root/'build'/name,'build/'+name)
manifest={'build':'v5 on-device audio capture','adapter_sha256':digest(shim),
          'core_sha256':digest(core),'rollback_v2_sha256':digest(rollback),
          'expected_before_sha256':digest(prior),'capture_start_run':8400,
          'capture_frames':264600,'capture_pcm_ram_bytes':1058400,
          'diagnostic_storage_bytes':172088,'worker_stack_bytes':131072,
          'capture_matches_output_verified':True,'audio_unchanged_from_v2':True,
          'hardware_test':'pending','packages':{p.name:digest(p) for p in out.glob('*.zip')}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
