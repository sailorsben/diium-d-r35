from pathlib import Path
from hashlib import sha256
import json
import wave
import zipfile

root=Path(__file__).resolve().parent.parent
build=root/'build/v8-capture'
out=root/'SNES-Plus-v8-display-test'
out.mkdir(exist_ok=True)
def digest(p): return sha256(p.read_bytes()).hexdigest()
pcm=(build/'verification/audio.s16le').read_bytes()
assert pcm==(build/'verification/display-enabled/audio.s16le').read_bytes()
phase_report=(build/'verification/display-enabled/emu_sfc_plus_v8_display_test.txt').read_text()
assert 'normal_callbacks=720' in phase_report and 'hold_callbacks=720' in phase_report and 'black_callbacks=360' in phase_report
assert pcm==(root/'build/v2/verification/audio.s16le').read_bytes()
meta=dict(line.split('=',1) for line in (build/'verification/emu_sfc_plus_v8_capture.txt').read_text().splitlines() if '=' in line)
with wave.open(str(build/'verification/emu_sfc_plus_v8_audio.wav'),'rb') as w:
    assert (w.getframerate(),w.getnchannels(),w.getsampwidth(),w.getnframes())==(44100,2,2,264600)
    start=int(meta['first_output_frame'])
    assert w.readframes(w.getnframes())==pcm[start*4:(start+264600)*4]
checks=(build/'checks.log').read_text()
for expected in ['PASS latest six-second WAV saved explicitly by Save state before unload',
                 'PASS Save state saves timing and audio while background reporter has not run',
                 'PASS rolling capture preserves exact latest samples across wrap; partial save and write errors verified',
                 'PASS display comparison: unchanged held buffer, black packed pixels, two cycles, automatic permanent normal-video return', 'PASS recovered chunk ioctl ABI', 'PASS resampler:', 'PASS frames=1800',
                 'PASS periodic report before exit/save; no gameplay wait; worker joins promptly',
                 'PASS driver write audit: exact pointer/bytes, one submission, short/error/zero accounting and fallback']:
    assert expected in checks,expected
verification={'audio_unchanged_from_v2_in_FF3_harness':True,'capture_matches_exact_output_segment':True,
              'driver_branch_verified_by_mock':True,'real_driver_write_results':'pending',
              'driver_call_count_in_FF3_QEMU':0,'hardware_clicking':'unresolved','display_test_audio_unchanged':True,'test_end_run':4320,'cleanup_on_return':'restore proven v2 and archive/delete v8 diagnostic outputs'}
(build/'verification/capture-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
prior=root/'device-evidence/card-D-v7-return/emu_sfc.so'
rollback=root/'device-evidence/card-D-v2-return/emu_sfc.so'
core=build/'emu_sfc_plus.so'
assert digest(prior)=='cffdcf0f96706a8ca305a0949bf03190a51134cdcae2754bdeb2ed635542c11c'
assert digest(core)=='1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657'
assert digest(rollback)=='4a805d19446fad487cf3c43a6b74bbed7027d6af037df1c9f393426a403cabb5'
(out/'README.txt').write_text("DIIUM D-R35 -- SNES Plus v8 TEMPORARY display/audio comparison\n\nV7 still clicked. Its driver accepted all 2,975,744 bytes across 1,011 calls,\nwithout errors, partial writes or fallback. The physical v6 PCM sounded clean\non the PC. Investigation remains downstream of generated game samples.\n\nV8 retains v7's audio path and adds a bounded display comparison:\n  12 seconds normal display\n  12 seconds held picture (no new scaler submissions)\n  12 seconds black picture (normal scaler submission frequency)\nThis repeats twice; after 4320 emulated frames (about 72 seconds), normal video\npermanently resumes for the rest of that game load. Pause menus pause this clock.\nThe game, controller polling and audio keep running throughout. Do not walk\ninto a fight during held/black intervals; remain at the clicking location.\n\nTest: listen through both cycles. Does clicking change during held or black\nphases? Once normal video has resumed, ESC -> Save state, wait for the save to\nfinish, Exit, and reconnect D:. Report the sound comparison. The latest PCM,\nwrite audit, timing and display-phase counts are saved under retro with v8 names.\n\nOnly retro/libs/emu_sfc.so is replaced. Core, interpolation, chunk-memory video\nallocation and tagged states remain compatible. This is an experiment, not a\nclaimed fix, and no audio hardware or kernel configuration is changed.\n\nCleanup: the preceding twenty emulator diagnostic files have been archived and\nhash-verified on the PC, then removed from D:. On this test's return, archive\nthe v8 outputs and restore the proven v2 adapter, removing the capture worker,\nwrite audit and display experiment from the active emulator. Keep games, saves,\nthe required Plus core, and the original emulator backup. restore-stable-v2.py\nimplements the checked restoration; remove v8 diagnostic outputs only after\ntheir evidence is preserved. No claim that restoring v2 fixes clicking.\n\nVerification: ARM/QEMU with device glibc 2.30; FF3 PCM with the display test\nenabled and disabled is byte-identical to v2. A driver mock verifies unchanged\nheld buffers, black pixels, both cycles and permanent normal-video resumption.\nCapture, Save-state reports with delayed worker, video allocation, resampling,\nstate compatibility, and write-result accounting checks pass. Hardware test pending.\n")
with zipfile.ZipFile(out/'SNES-Plus-v8-display-test-update.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(build/'emu_sfc.so','retro/libs/emu_sfc.so')
with zipfile.ZipFile(out/'SNES-Plus-v8-display-test-rollback-to-v2.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(rollback,'retro/libs/emu_sfc.so')
with zipfile.ZipFile(out/'SNES-Plus-v8-display-test-source.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(root/'SNES-Plus-v7-write-audit/SNES-Plus-v7-write-audit-source.zip','v7-full-source.zip')
    for name in ['emu_sfc_plus_v8_capture.c','device_audio_capture_v8.h','audio_diagnostics_v8_capture.h',
                 'audio_write_audit_v8.h','audio-write-audit-check-v8.c','display_audio_test.h','audio-diagnostics-check-v8.c',
                 'adapter-check-v8-capture.c','video-contract-check-v8-capture.c','harness-v8-capture.c',
                 'build-v8-capture.sh','run-v8-capture-checks.sh','prepare-v8-display.py','prepare-v8-package.py','restore-stable-v2.py',
                 'package-v8-display.py','install-v8-display.py']:
        z.write(root/'build'/name,'build/'+name)
manifest={'build':'v8 temporary display comparison','adapter_sha256':digest(build/'emu_sfc.so'),
          'core_sha256':digest(core),'expected_before_sha256':digest(prior),
          'rollback_v2_sha256':digest(rollback),'verification':verification,
          'packages':{p.name:digest(p) for p in out.glob('*.zip')}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
