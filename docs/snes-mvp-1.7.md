# MVP1.7: logging retry

2026-10-04, America/Chicago. Installed and one-shot armed on the tested card.
The user confirmed that stock boot still works after the 1.6 power-off and
requested logging and another test. This supersedes the earlier hold on
retesting; a controlled original/A7 comparison remains necessary before
claiming an A7 speedup.

## What this build changes

The exact A7 core, full-render policy, UI, display FIFO, audio service and
kernel-clock pacing remain the 1.6 implementation. This build repairs the
[missing crash evidence](snes-mvp-1.6-failure.md); it does not promise smoother
playback. If the failure reproduces, its progress and sampled waits can now
survive without reaching normal cleanup.

The runner publishes a complete checkpoint to an atomic RAM file outside core
callbacks, about once a second when frames advance. It also records loading,
pause-draining, failure and cleanup phases. Each record has build/core/ROM
identity, PID plus kernel session-start time, checkpoint time and cumulative
counters. Match these with the boot ID in `startup-platform.txt`.

Counters include completed core calls and wall/CPU histogram, submitted/held
drawings, display reservation/scaling/flip costs, PCM queue/acceptance/retry
accounting, live audio-worker CPU, audio-space/lead waits and pacing lateness.
RAM checkpoint duration and errors are recorded. A blocked runner cannot
publish another checkpoint; its last record and independent thread snapshots
then matter together.

After READY, the wrapper waits two seconds for its first capture, then five
seconds between captures, at most 63 times. Capture time adds to those waits:
this is roughly a five-minute diagnostic window, not an emulation timeout.
It retains these bounded files under `retro/snes-mvp`:

| File | Evidence |
|---|---|
| `last-progress.txt`, `last-progress.previous` | Latest two copied RAM checkpoints; check build, session and phase |
| `runtime-platform.txt` | First three thread/IPC/platform snapshots |
| `runtime-platform-latest.txt` | Latest thread status, waits, syscall/stat, kernel CPU/memory/interrupt samples, watchdog/power helper state and bounded process inventory |
| `kernel-tail.txt` | Latest 16 KiB of readable kernel log |
| `diagnostic-flush.log` | Uptime before capture and after sync, exposing diagnostic duration |
| `last-run.log`, `startup.log` | Bounded stderr/stdout copy and existing durable lifecycle/input logs |

The wrapper copies checkpoints atomically, rotates the previous record and
syncs the capture. RAM work and SD capture can affect timing; their duration
is evidence, not zero-overhead instrumentation. Power loss can discard the
current interval; a noisy kernel ring can erase earlier messages. Neither
successful OSS writes nor sampled nonempty queues proves zero audio underruns.
Submission/flip counters are not optical panel measurements.

`saves/last-session.txt` remains the normal-exit report and can still be
historical after power-off. Do not substitute it for the current checkpoint.
The wrapper initializes a fresh `wrapper_start` marker before launching the
child; an older `last-progress.previous` is only usable after identity checks.

## Checks and preserved files

[Verification](../evidence/verification/snes-mvp-1.7/verification.json) binds
the runner and wrapper hashes to passing ARM/QEMU contracts. A real ARM runner
with the actual A7 core was killed before cleanup: fresh running counters and
live audio-worker CPU survived in RAM while the older final report remained
historical. A separate wrapper check proves card-style persistence while its
child is still alive, and verifies cancellation, splash handoff and startup
limits. QEMU checks do not establish handheld speed or shutdown diagnosis.

The pre-update card return was archived with source/copy/source hash checks.
The guarded installer archived the existing MVP and private progress, wrote
only the owned runner, wrapper and test notes, and armed last. All 19
pre-install private save/progress files, stock binaries, boot hook and the
exact core remain hash-identical. No new snapshot migration was performed.

The core remains CRC32 `90fbcc4e`, 660,912 bytes, SHA256
`2e88db49c18c9aa2c96f6806882e78acf9feb3da5e235109f13d1699a8e12766`.
The [owned release](../releases/snes-mvp-1.7/manifest.json) contains no ROM,
private snapshot/SRAM or vendor runtime dependencies. Historical releases and
their evidence remain available.

## Physical test

1. Boot the one-shot launcher and launch FF6, not Rev1.
2. MENU → Load snapshot → Resume; use the same map → party menu → map workload.
3. If sound/movement are badly degraded, about one minute is enough. Try
   MENU → Exit so normal final totals can also be written. If it runs normally,
   play for about five minutes.
4. Report when the lag/crackles start and whether the whole device powers off.
   Power down and reconnect D: for read-only collection before another update.

The marker is consumed at launch; the following reboot takes stock. The next
review will compare fresh frame progress, core/worker CPU, producer waits,
memory/helper/kernel samples and diagnostic duration. It will distinguish
observed costs from hypotheses before changing the failing pipeline.
