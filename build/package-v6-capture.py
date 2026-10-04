from pathlib import Path
from hashlib import sha256
import json
import wave
import zipfile

root=Path(__file__).resolve().parent.parent
build=root/'build/v6-capture'
out=root/'SNES-Plus-v6-capture'
out.mkdir(exist_ok=True)
def digest(p): return sha256(p.read_bytes()).hexdigest()

pcm=(build/'verification/audio.s16le').read_bytes()
original=(root/'build/v2/verification/audio.s16le').read_bytes()
assert pcm==original, 'Playback changed'
meta=dict(line.split('=',1) for line in
          (build/'verification/emu_sfc_plus_v6_capture.txt').read_text().splitlines() if '=' in line)
with wave.open(str(build/'verification/emu_sfc_plus_v6_audio.wav'),'rb') as w:
    assert (w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getnframes())==(44100,2,2,264600)
    start=int(meta['first_output_frame'])
    assert w.readframes(w.getnframes())==pcm[start*4:(start+264600)*4]
checks=(build/'checks.log').read_text()
for expected in ['PASS latest six-second WAV saved explicitly by Save state before unload',
                 'PASS Save state saves timing and audio while background reporter has not run',
                 'PASS rolling capture preserves exact latest samples across wrap; partial save and write errors verified',
                 'PASS recovered chunk ioctl ABI', 'PASS resampler:', 'PASS frames=1800',
                 'PASS periodic report before exit/save; no gameplay wait; worker joins promptly']:
    assert expected in checks,expected
verification={'audio_unchanged_from_v2': True, 'capture_matches_exact_output_segment':True,
              'captured_stereo_frames':264600,'first_output_frame':start,
              'save_works_without_worker':True, 'hardware_capture':'pending'}
(build/'verification/capture-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
prior=root/'device-evidence/card-D-v5-return/emu_sfc.so'
rollback=root/'device-evidence/card-D-v2-return/emu_sfc.so'
core=build/'emu_sfc_plus.so'
assert digest(prior)=='6e8b114eb11387d7f20221da3c7769ffec90801aceea878ed4a9eefe08ee8116'
assert digest(core)=='1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657'
assert digest(rollback)=='4a805d19446fad487cf3c43a6b74bbed7027d6af037df1c9f393426a403cabb5'
(out/'README.txt').write_text('''DIIUM D-R35 -- SNES Plus v6 explicit rolling audio capture

Diagnostic only; no clicking fix is claimed. The physical v5 return contained
its correct startup log and adapter, but no WAV or periodic timing report.
The cause of the missing background output remains unproven.

V6 keeps the exact latest six seconds of submitted PCM in a bounded RAM ring.
Save state writes it to the SD card synchronously while gameplay is paused.
The worker never accesses the ring. Saving another state replaces the capture
with the six seconds immediately preceding that save. Exit does not replace it.
Captures made in the first six seconds contain only the available audio.

Test: launch FF3, get to the location where clicks are audible, and leave it
there for ten seconds. ESC -> Save state. Wait for the save to finish, then
ESC -> Exit and reconnect D:. Avoid a second save in a different scene.

Files under retro:
  emu_sfc_plus_v6_audio.wav     Latest six seconds of submitted stereo PCM.
  emu_sfc_plus_v6_capture.txt   Frame count, final run, exact output offset.
  emu_sfc_plus_v6.log           Includes saved=1/error=0 or capture error.
  emu_sfc_plus_v6_timing.log    Timing measurements, also saved by Save state.

This captures emulator output before the vendor frontend/driver, not sound
recorded from the speakers. A clean recording does not prove kernel acceptance
or analog output. Outdoors versus indoors/combat is a clue, not a diagnosis;
the user reports clicks without wind and through both headphones and speaker.

Only retro/libs/emu_sfc.so is replaced. Keep emu_sfc_plus.so alongside it.
Chunk-memory video, core, interpolation, playback samples and tagged save-state
format are retained. Capture RAM is 1058400 bytes plus small ring counters.
No capture disk I/O, waiting or locking happens in gameplay callbacks.

Verified with ARM/QEMU and device glibc 2.30: exact last-six-seconds data across
ring wrap, partial capture, file-write errors, Save-state audio/timing output
with the worker deliberately delayed, unchanged FF3 PCM versus proven v2,
video buffer contract, resampler and state compatibility. Hardware test pending.
''')
with zipfile.ZipFile(out/'SNES-Plus-v6-capture-update.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(build/'emu_sfc.so','retro/libs/emu_sfc.so')
with zipfile.ZipFile(out/'SNES-Plus-v6-capture-rollback-to-v2.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(rollback,'retro/libs/emu_sfc.so')
with zipfile.ZipFile(out/'SNES-Plus-v6-capture-source.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(root/'SNES-Plus-v5-capture/SNES-Plus-v5-capture-source.zip','v5-full-source.zip')
    for name in ['emu_sfc_plus_v6_capture.c','device_audio_capture_v6.h','audio_diagnostics_v6_capture.h',
                 'audio-diagnostics-check-v6.c','adapter-check-v6-capture.c',
                 'video-contract-check-v6-capture.c','harness-v6-capture.c',
                 'build-v6-capture.sh','run-v6-capture-checks.sh','prepare-v6-capture.py',
                 'package-v6-capture.py','install-v6-capture.py']:
        z.write(root/'build'/name,'build/'+name)
manifest={'build':'v6 explicit rolling audio capture','adapter_sha256':digest(build/'emu_sfc.so'),
          'core_sha256':digest(core),'expected_before_sha256':digest(prior),
          'rollback_v2_sha256':digest(rollback),'capture_pcm_ram_bytes':1058400,
          'verification':verification,'packages':{p.name:digest(p) for p in out.glob('*.zip')}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
