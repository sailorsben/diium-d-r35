from pathlib import Path
from hashlib import sha256
import json
import wave
import zipfile

root=Path(__file__).resolve().parent.parent
build=root/'build/v7-capture'
out=root/'SNES-Plus-v7-write-audit'
out.mkdir(exist_ok=True)
def digest(p): return sha256(p.read_bytes()).hexdigest()
pcm=(build/'verification/audio.s16le').read_bytes()
assert pcm==(root/'build/v2/verification/audio.s16le').read_bytes()
meta=dict(line.split('=',1) for line in (build/'verification/emu_sfc_plus_v7_capture.txt').read_text().splitlines() if '=' in line)
with wave.open(str(build/'verification/emu_sfc_plus_v7_audio.wav'),'rb') as w:
    assert (w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getnframes())==(44100,2,2,264600)
    start=int(meta['first_output_frame'])
    assert w.readframes(w.getnframes())==pcm[start*4:(start+264600)*4]
checks=(build/'checks.log').read_text()
for expected in ['PASS latest six-second WAV saved explicitly by Save state before unload',
                 'PASS Save state saves timing and audio while background reporter has not run',
                 'PASS rolling capture preserves exact latest samples across wrap; partial save and write errors verified',
                 'PASS recovered chunk ioctl ABI', 'PASS resampler:', 'PASS frames=1800',
                 'PASS periodic report before exit/save; no gameplay wait; worker joins promptly',
                 'PASS driver write audit: exact pointer/bytes, one submission, short/error/zero accounting and fallback']:
    assert expected in checks,expected
verification={'audio_unchanged_from_v2_in_FF3_harness':True,'capture_matches_exact_output_segment':True,
              'driver_branch_verified_by_mock':True,'real_driver_write_results':'pending',
              'driver_call_count_in_FF3_QEMU':0,'hardware_clicking':'unresolved'}
(build/'verification/capture-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
prior=root/'device-evidence/card-D-v6-return/emu_sfc.so'
rollback=root/'device-evidence/card-D-v2-return/emu_sfc.so'
core=build/'emu_sfc_plus.so'
assert digest(prior)=='d581788022c8d808a1b356144b76fe073645b21e6247a439cfe35c8616662f7e'
assert digest(core)=='1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657'
assert digest(rollback)=='4a805d19446fad487cf3c43a6b74bbed7027d6af037df1c9f393426a403cabb5'
(out/'README.txt').write_text('''DIIUM D-R35 -- SNES Plus v7 driver-write diagnostic

The physical v6 six-second capture succeeded. The user heard it as clean on
the PC despite clicks on the handheld. This moves investigation downstream
of the captured emulator PCM; it does not prove a hardware-only fault.

V7 resolves sound_driver_playframe and DSP from the already-open driver.so.
The recovered driver function tailcalls Linux write(DSP,pcm,byte_count).
PlaySound calls that function with frames*4; PlayFrame passes the same samples
but discards the write result and returns zero. V7 uses the same driver call
with the same pointer and byte count and records its actual return value.
The wrapper's silence tracking and timing printf are bypassed in this test.
If the driver/function/descriptor is unavailable, playback uses the original
frontend callback and the report explicitly records fallback calls.

Diagnostic only. There are no retries, inserted silence, sample edits, new
audio buffers, rate/fragment configuration changes or double submissions.
Successful byte counts still do not prove correct kernel/DMA/analog output.

Test: stay at the outdoor location where clicks occur for at least ten seconds.
Note whether clicking changes. ESC -> Save state, wait for it to finish, Exit,
and reconnect the card as D:. A save in another scene replaces the recording.

Files under retro:
  emu_sfc_plus_v7_write_audit.txt  Actual write counts, bytes, errors and fallback.
  emu_sfc_plus_v7_audio.wav        Latest six seconds of submitted PCM.
  emu_sfc_plus_v7_capture.txt      Recording sample offset and final run.
  emu_sfc_plus_v7_timing.log       Read-only queue and scheduling measurements.
  emu_sfc_plus_v7.log              Startup and explicit-save status.

Only retro/libs/emu_sfc.so is updated; keep emu_sfc_plus.so alongside it.
Core, interpolation, chunk-memory video and tagged states remain compatible.
The update is reversible with the included proven-v2 rollback package.

Verification: ARM/QEMU with device glibc 2.30; FF3 harness PCM is byte-identical
to v2 (the harness exercises fallback because it lacks the physical driver).
A separate mock exercises direct driver delivery: exact original pointer and
byte count, one call per callback, no PCM mutation, short/zero/error accounting,
unavailable-descriptor fallback, and saved reports. Capture ring, explicit Save
with inactive worker, video, resampler and state checks pass. Physical test pending.
''')
with zipfile.ZipFile(out/'SNES-Plus-v7-write-audit-update.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(build/'emu_sfc.so','retro/libs/emu_sfc.so')
with zipfile.ZipFile(out/'SNES-Plus-v7-write-audit-rollback-to-v2.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(rollback,'retro/libs/emu_sfc.so')
with zipfile.ZipFile(out/'SNES-Plus-v7-write-audit-source.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(root/'SNES-Plus-v6-capture/SNES-Plus-v6-capture-source.zip','v6-full-source.zip')
    for name in ['emu_sfc_plus_v7_capture.c','device_audio_capture_v7.h','audio_diagnostics_v7_capture.h',
                 'audio_write_audit.h','audio-write-audit-check.c','audio-diagnostics-check-v7.c',
                 'adapter-check-v7-capture.c','video-contract-check-v7-capture.c','harness-v7-capture.c',
                 'build-v7-capture.sh','run-v7-capture-checks.sh','prepare-v7-audit.py',
                 'package-v7-audit.py','install-v7-audit.py']:
        z.write(root/'build'/name,'build/'+name)
manifest={'build':'v7 driver write audit','adapter_sha256':digest(build/'emu_sfc.so'),
          'core_sha256':digest(core),'expected_before_sha256':digest(prior),
          'rollback_v2_sha256':digest(rollback),'verification':verification,
          'packages':{p.name:digest(p) for p in out.glob('*.zip')}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
