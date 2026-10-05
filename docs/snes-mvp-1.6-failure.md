# MVP1.6 physical failure

2026-10-04, America/Chicago. This supersedes the expected smoother/full-speed
behavior described before the first physical run. The expectation was wrong.

## Physical observation

The user reports: "Sound was VERY choppy, movement was slow, graphics were
actually great, then the whole device shut off."

That establishes a failed performance/stability test. Clean-looking graphics
is useful physical evidence about that run's appearance, not all-path renderer
qualification. Slow movement with choppy sound is consistent with production
missing deadlines; it does not isolate renderer CPU, waits or scheduling.
Whole-device power-off needs its own explanation. No shutdown cause is proven.

## What survived and what did not

[Selected return](../evidence/2026-10-04/snes-mvp-1.6-failure/analysis.json):
33 files were copied with source/copy/source hash verification and zero card
writes. Returned runner, A7 core and wrapper match the installed release.
Stock binaries and all 18 pre-existing private progress files remain unchanged.
The armed marker is absent; the following boot takes the stock path.

Splash completes, GPIO initialization succeeds, first display completes and
READY is reached at kernel uptime 8.459 seconds. Game launch is requested at
9.592 seconds. Later pause/input events survive through 23.542 seconds.
The startup log has no child-exit, main-exit or teardown-completion record.
The copied stderr log is empty; there is no retained final kernel ring or
power-helper output that identifies a panic, watchdog event or power-off request.

Early snapshots at uptime 11.29, 17.43 and 29.55 seconds show the main thread
running. The display worker is in a condition wait, then scanout waits; the audio
worker is in futex waits. Thread switch counts advance and its ID changes after
the pause/resume transition. These are sampled states, not a CPU profile or a
complete deadlock/queue diagnosis. RSS is 11,988–12,492 KiB, high-water 14,520 KiB,
and process swap is zero in those samples. Later memory exhaustion is not ruled
out, but these samples supply no evidence for swap thrashing.

`last-session.txt` is byte-identical to the earlier 1.5 return: its original
core identity is `5ba71d2a`/656,816 bytes, whereas this run's returned A7 core is
`90fbcc4e`/660,912 bytes. The old 23,872 calls and 11.838% holds do not belong to
1.6. Its new core/worker/queue totals were only written on normal session exit;
power-off lost them. This is a concrete observability defect.

The report analyzer's new `--core` guard rejects this file against the returned
A7 core, while preserving analysis against its original core. Both API and CLI
were checked using the actual stale return. Matching core identity alone cannot
prove freshness after two runs of the same binary; the next session still needs
an explicit identity and in-progress marker.

## What changes before another test

1. Keep this release unarmed. Preserve the failing release and local evidence;
   do not silently replace it or its private state while diagnosing.
2. Give each session an explicit build/core identity and in-progress record.
   Publish bounded phase counters to RAM, with occasional diagnostic persistence
   outside frame callbacks, so abrupt shutdown cannot leave an old report posing
   as the current result. Capture kernel/helper state in that bounded diagnostic.
3. Compare original and A7 core on the same device, ROM, snapshot, inputs and
   callback sinks before claiming a rendering speedup. Measure thread CPU and
   kernel wall time; correctness checks and NEON instruction names cannot price
   execution on this A7.
4. Isolate host changes against that result: audio service, display queue and
   full-render policy changed together in 1.6. The three early snapshots cannot
   decide which change caused the severe slowdown or whether shutdown shares
   its cause. Keep the proven splash/input/clock contracts.

No replacement runtime or new one-shot is installed by this failure review.
The original full-speed goal stands. This run establishes that the first bundle
did not meet it, rather than proving full rendering impossible on the device.
