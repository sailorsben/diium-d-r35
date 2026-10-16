# Corrected ROM-free pressure test

`render-pressure2` fixes the first lab's controller double-drain and moves the
seven load sweeps onto the light static workload. It is qualified offline and
installed/armed once on I: from pushed `fa3005d`; physical results are pending.
The original pressure1 sources,
payloads, return logs and published evidence remain intact.

The joined audio worker owns the only normal `board_audio_finish()` call.
The controller calls `audio_pipe_stop(1)`, reads the joined worker's error and
accounting, flushes history and closes the stream. It no longer calls finish
again. Injected worker-finish failure still makes the cell fail.

Phases 59–65 now use static 256×224, two layers, cached colors, direct chunk
output, queued display and native audio—the same route that completed production
in pressure1's light instrumentation controls. The four steady CPU targets
remain 4/8/12/16 ms per frame; the three burst targets remain 24/48/80 ms every
30th frame. All other cells, frame counts and order remain unchanged (70 cells).
`load_events` records completed burn calls, so a failed cell cannot be described
as a burst test unless it actually reached a burst. Full runs should record six
bursts per burst cell; failed prefixes report their actual count.

This is a diagnostic correction, not a production emulator performance candidate.
There is no claimed new A7 saving or reduced FFVI deficit. Compared with pressure1,
ARM text grows 512 bytes, data/BSS stay unchanged; added event counting is one
increment per executed load, with result persistence outside the timed loop.
Its physical CPU cost is unmeasured. Intentional load burns remain measured
CPU-clock targets; no MHz assumption or kernel configuration change is added.

Qualification includes:

- 60 full-frame scalar/NEON/cache oracle and guard cases.
- All 70 short ARM mock cells, with exact light sweep parameters checked and
  mock performance rejected by the reporter.
- The actual controller linked to the unchanged threaded audio owner against
  a deterministic fake device: single finish for audio-only and rendering,
  worker-finish failure propagation, owner join/close and six executed bursts
  across two 24/48/80 ms events each. Reintroducing the original controller
  finish fails this fixture. This qualifies the failed seam; it does not
  simulate real PCM/DMA timing or prove physical capacity.
- Exact firmware-shell syntax, normal marker consumption, replay skip,
  forced-child hold, absent/faulty UART and combined/unknown-child faults.
- ABI ≤ firmware glibc 2.30, local header pins, NEON instruction presence and
  byte-identical board/audio support from the physically used suite.

[Qualification](../evidence/2026-10-15/render-pressure2/qualification.json),
[controller seam](../evidence/2026-10-15/render-pressure2/controller-qualification.json),
[wrapper faults](../evidence/2026-10-15/render-pressure2/fault-qualification.json).
The matching-kernel audit is reused byte-for-byte; it is not a new driver change.
An initial focused-fixture link exposed the host time64 default; aligning its
flags with the production time32 build fixed that fixture build. Production
already used time32; no deployed ABI or audio-owner source was changed.

Build with `prepare-render-pressure2.py`, `build-render-pressure2.sh`,
`check-render-pressure2-controller.py`, `qualify-render-pressure2.py` and
`check-render-pressure2-faults.py`. Preparation requires a fresh private directory.
The installer requires clean pushed source, a fresh strict archive, healthy FAT,
stock/init/ROM and qualified payload checks, then uses separate
`retro/render-pressure2` and two owned one-shots. The verifier independently
reads back all protected prior files, payloads, dispatcher and exact markers.

Safely eject I:, cold boot and allow about 5–6 minutes. Expect generated patterns,
quiet audio and deliberate overload failures. Select+Start aborts. If stock has
not returned after about six minutes, power off and return the card. Forced or
uncertain child termination deliberately holds stock until reboot; the following
boot is stock with permanent UART correction. Results land under
`retro/render-pressure2/results/run-<boot_id>-<pid>`. Archive before any further
update/rearm. Native production/finish acceptance, executed physical bursts and
load thresholds remain to be measured.

Installation uses fresh strict archive
`device-evidence/a7-pair-before-20261016T034959Z`. FAT checks pass before payload
staging, after payload verification and after arming. The sole changed prior
file is the owned SNES dispatcher; all 8,654 protected prior files match exactly.
Pressure1, all prior logs/private progress,
stock/ROM/core, normal init and permanent UART correction are preserved. Both
owned marker bytes and payloads are independently read back after arming.
[Installation receipt](../evidence/2026-10-15/render-pressure2/installation.json),
[independent readback](../evidence/2026-10-15/render-pressure2/live-verification.json).
No firmware update payload or production performance change is installed.
