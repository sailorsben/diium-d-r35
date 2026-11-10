# One-shot native Star Fox playback

Armed and independently verified on I: from `b4aa130`. Readback matches
both markers, all 11 profile files and 1,935 protected existing files.
CHKDSK and an explicit dirty-flag query pass before staging, after payload
copy, after activation and after independent readback. Physical playback
is pending.
[Installation receipt](../evidence/2026-11-10/snes-throughput/superfx-native-installation.json).

This test runs the measured full-tile plus Super FX core in the native LCD
and ALSA runner. It reuses the single-window controller from the
[cold replay qualification](../evidence/2026-11-10/snes-throughput/cold-raster-runner.json)
and the same Star Fox ROM, inputs and expected-output fixture as the
[core-only measurement](snes-superfx-device-test.md). It silently advances
8,656 emulated ticks while displaying a progress screen. It then runs 1,200
ticks with full raster, native PCM and blocking presentation (policy 0).
The script drives the game. Test output and any generated progress stay
inside the isolated test directory.

Both supervised QEMU rehearsals completed the 8,656-tick warmup and all
1,200 gameplay calls, with exact final software audio accounting and
normal child reaping. One checked pixels, PCM and sample counts against
the frozen reference, and one disabled that oracle. Five firmware BusyBox
cases exercised normal completion, an unarmed reboot, active splash,
observer refusal and a crashing child. These qualify the controller and
boot seam. Physical output and timing await the card return.
[Qualification receipt](../evidence/2026-11-10/snes-throughput/superfx-native-qualification.json).

## Timing and audio budget before installation

The handheld measured 15.283 ms mean core CPU for this exact ELF, down
0.622 ms (3.91%) against full-tile. Its p95 was 24.147 ms and 396 of the
1,200 calls exceeded one NTSC tick. At 16.688155 ms/tick, average incremental
critical-path work must be at most **1.405509 ms/tick** for average real-time
throughput. The added work includes native PCM resampling, queue publication,
driver service, and LCD transfer or blocking, net of overlap. Its actual
cost and publication cadence on this combined build are unmeasured. The
real-time run omits the callback CRC oracle, which cost 1.743 ms/tick in
the combined core timing test. The oracle remains active in the exact-output
rehearsal and previously passed on the same ELF on the handheld.
[A7 timing receipt](../evidence/2026-11-10/snes-raster-batches/superfx-device-return.json).

The console-clock quota is about 534.688 source frames per tick at 32,040 Hz,
or 735.948 frames per tick when resampled to the previously negotiated
44.1 kHz. The combined core timings give the following serial backlog
sensitivity, with constant critical-path overhead and 44.1 kHz conversion
rounded to whole frames. It assumes continuous publication and no driver
cost beyond the extra time shown.

| Extra time per tick | Peak reserve drawdown | Deficit at tick 1,200 |
| --- | ---: | ---: |
| 0 ms | 19.399 ms / 855 frames | 0 |
| 0.5 ms | 48.753 ms / 2,150 frames | 0 |
| 1.0 ms | 157.901 ms / 6,963 frames | 2.514 ms / 111 frames |

The actual opening deficit and full cumulative reserve are unknown. The
previous native test used a 2,823-frame prime and a 3,712-frame ring and
lost PCM after four calls with the older core. This test keeps the native
audio policy and measures whether the improvement alone gets through the
opening and completes the scene. A result can fail at startup, later in
the scene, or at final reserve recovery even with a viable average.
[Clock quota](snes-focus-1-return.md) ·
[Native PCM failure and opening reserve](snes-throughput-architecture.md).

## Acceptance and boot

- Check the complete 8,656-call warmup, all 1,200 measured calls and
  presentations, zero presentation skips, correct generated and accepted
  PCM, clean worker teardown and normal child reaping. Use the PCM
  transaction trace to reconstruct accepted audio versus hardware demand,
  check for driver-added periods or DROP, and require full reserve recovery.
  A truncated trace bounds the failed prefix. The offline rehearsal proves
  all 1,200 pixel/PCM/sample-count checks with the exact boot binaries.
- Safely eject I:, insert it with the handheld off, connect charging power,
  and boot once. Watch for **STAR FOX - COLD REPLAY**, then gameplay with
  sound. Let the scripted input run. Note any audible dropout or visible
  freeze. At full speed the gameplay window lasts about 20 seconds.
- When stock appears, shut down normally and reconnect I:. If the progress
  screen stalls or stock fails to return, the supervisor detects 60 seconds
  without warmup progress and caps the suite at 35 minutes. A forced stop
  holds the display seam until reboot. Reconnect the card for partial logs.
  Both one-shot markers are consumed before native hardware is opened, so
  the next boot is stock.

Results go to `retro/snes-superfx-native1/results/run-*`. Archive the card
before changing it and retain `wrapper.log`, `supervisor.txt`, and the
run's `warmup.txt`, `frames.csv`, `headroom.txt`, `last-session.txt` and
`pcm-full.txt`. This measurement leaves the production gate closed.
