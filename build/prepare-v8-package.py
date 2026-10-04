from pathlib import Path
base=Path(__file__).resolve().parent
text=(base/'package-v7-audit.py').read_text().replace('v7','v8').replace('write-audit','display-test')
text=text.replace("'build':'v8 driver write audit'","'build':'v8 temporary display comparison'")
text=text.replace("prior=root/'device-evidence/card-D-v6-return/emu_sfc.so'",
                  "prior=root/'device-evidence/card-D-v7-return/emu_sfc.so'")
text=text.replace('d581788022c8d808a1b356144b76fe073645b21e6247a439cfe35c8616662f7e',
                  'cffdcf0f96706a8ca305a0949bf03190a51134cdcae2754bdeb2ed635542c11c')
text=text.replace("root/'SNES-Plus-v6-capture/SNES-Plus-v6-capture-source.zip','v6-full-source.zip'",
                  "root/'SNES-Plus-v7-write-audit/SNES-Plus-v7-write-audit-source.zip','v7-full-source.zip'")
text=text.replace("'audio_write_audit.h','audio-display-test-check.c'",
                  "'audio_write_audit_v8.h','audio-write-audit-check-v8.c','display_audio_test.h'")
text=text.replace("'prepare-v8-audit.py'","'prepare-v8-display.py','prepare-v8-package.py','restore-stable-v2.py'")
text=text.replace("'package-v8-audit.py','install-v8-audit.py'",
                  "'package-v8-display.py','install-v8-display.py'")
text=text.replace("pcm=(build/'verification/audio.s16le').read_bytes()",
                  "pcm=(build/'verification/audio.s16le').read_bytes()\n"
                  "assert pcm==(build/'verification/display-enabled/audio.s16le').read_bytes()\n"
                  "phase_report=(build/'verification/display-enabled/emu_sfc_plus_v8_display_test.txt').read_text()\n"
                  "assert 'normal_callbacks=720' in phase_report and 'hold_callbacks=720' in phase_report and 'black_callbacks=360' in phase_report")
text=text.replace("'PASS recovered chunk ioctl ABI',", "'PASS display comparison: unchanged held buffer, black packed pixels, two cycles, automatic permanent normal-video return', 'PASS recovered chunk ioctl ABI',")
text=text.replace("'hardware_clicking':'unresolved'", "'hardware_clicking':'unresolved','display_test_audio_unchanged':True,'test_end_run':4320,'cleanup_on_return':'restore proven v2 and archive/delete v8 diagnostic outputs'")
readme='''DIIUM D-R35 -- SNES Plus v8 TEMPORARY display/audio comparison

V7 still clicked. Its driver accepted all 2,975,744 bytes across 1,011 calls,
without errors, partial writes or fallback. The physical v6 PCM sounded clean
on the PC. Investigation remains downstream of generated game samples.

V8 retains v7's audio path and adds a bounded display comparison:
  12 seconds normal display
  12 seconds held picture (no new scaler submissions)
  12 seconds black picture (normal scaler submission frequency)
This repeats twice; after 4320 emulated frames (about 72 seconds), normal video
permanently resumes for the rest of that game load. Pause menus pause this clock.
The game, controller polling and audio keep running throughout. Do not walk
into a fight during held/black intervals; remain at the clicking location.

Test: listen through both cycles. Does clicking change during held or black
phases? Once normal video has resumed, ESC -> Save state, wait for the save to
finish, Exit, and reconnect D:. Report the sound comparison. The latest PCM,
write audit, timing and display-phase counts are saved under retro with v8 names.

Only retro/libs/emu_sfc.so is replaced. Core, interpolation, chunk-memory video
allocation and tagged states remain compatible. This is an experiment, not a
claimed fix, and no audio hardware or kernel configuration is changed.

Cleanup: the preceding twenty emulator diagnostic files have been archived and
hash-verified on the PC, then removed from D:. On this test's return, archive
the v8 outputs and restore the proven v2 adapter, removing the capture worker,
write audit and display experiment from the active emulator. Keep games, saves,
the required Plus core, and the original emulator backup. restore-stable-v2.py
implements the checked restoration; remove v8 diagnostic outputs only after
their evidence is preserved. No claim that restoring v2 fixes clicking.

Verification: ARM/QEMU with device glibc 2.30; FF3 PCM with the display test
enabled and disabled is byte-identical to v2. A driver mock verifies unchanged
held buffers, black pixels, both cycles and permanent normal-video resumption.
Capture, Save-state reports with delayed worker, video allocation, resampling,
state compatibility, and write-result accounting checks pass. Hardware test pending.
'''
start=text.index("(out/'README.txt').write_text(")
end=text.index('with zipfile.ZipFile',start)
text=text[:start]+"(out/'README.txt').write_text("+repr(readme)+")\n"+text[end:]
(base/'package-v8-display.py').write_text(text,newline='\n')
text=(base/'install-v7-audit.py').read_text().replace('v7','v8').replace('write-audit','display-test')
(base/'install-v8-display.py').write_text(text,newline='\n')
print('Prepared v8 package and installation with explicit restoration instructions.')
