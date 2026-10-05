# MVP1.7 return: full rendering, incomplete speed

2026-10-04, America/Chicago. The user reached a Save Point, saved and exited
normally without a crash. Play remained laggy; **FF6's party menu** helped
partially. That menu changes the game workload without resetting the host
audio pipeline. It supports scene-dependent deadline pressure, not a proven
launcher-pause reset fix.

## Fresh evidence and preserved progress

Read-only collection archived and source/copy/source hash-verified 38 files
before any update. The marker is consumed; the card remains unarmed and
unchanged by this review. Runner/wrapper/core match the exact 1.7 release and
stock binary hashes match the preceding return.

The final report and latest checkpoint share build 1.7, core `90fbcc4e`,
session `492-10687444000`, phase `finished` and 7,068 calls. This is fresh
evidence, unlike the stale final report after the 1.6 power-off. The startup
log records main exit rc=0, display join and completed FreeVFB/board cleanup.
The wrapper's final child-exit line is absent; do not invent why it is missing.

The new SRAM and its backup changed, as did the final report and its backup.
The other 15 of 19 pre-install private files are unchanged, including private
states. All current progress and previous generations are retained in the
local archive. No SRAM/state contents or private progress hashes are published.
The user's in-game save was not overwritten or rolled back by collection.

[Selected raw return](../evidence/2026-10-04/snes-mvp-1.7/last-session.txt) and
[analysis](../evidence/2026-10-04/snes-mvp-1.7/analysis.json) preserve the numbers.

## What accounts for the lag

All 7,068 calls submitted video, with zero internal holds or duplicate frames.
They consumed 129.381 seconds of measured active-loop time, approximately
**54.629 emulation calls/sec, 91.17% of native speed**. The loop clock excludes
launcher pause/load/cleanup and omits some loop bookkeeping. This is not
optical panel FPS; no physical presentation counter is available.

| Producer phase | Mean per completed core call |
|---|---:|
| Core call, including its callbacks/preemption | 15.384 ms wall / 13.986 ms thread CPU |
| Wait for display publication/source credit | 0.736 ms wall |
| Audio-lead check/wait | 1.876 ms wall |
| Kernel-clock pacing wait | 0.204 ms wall |
| Software audio-space check/wait | 0.0036 ms wall |
| RAM checkpoint work | 0.0107 ms wall |
| Entire measured active loop | 18.305 ms wall |

The native budget is 16.688 ms. At least 2,197 calls (31.084%) exceed it;
another 70 lie in the ambiguous [16,17) ms histogram bin. Median is [13,14)
ms, p95 [21,22), p99 [35,36), maximum 64.332 ms. There is a substantial
20–22 ms cluster; the mean hides recurring expensive work.

Video callback mean is 0.947 ms, audio callback mean 0.439 ms; both are already
inside core-call wall time. Display and audio workers consume 0.717 and
0.176 ms CPU per core call respectively. Their CPU shares the single A7.
Scaler wall averages 2.318 ms and flip 12.327 ms per display job; these overlap
the producer and are **not** an extra 14.645 ms of serial frame time or CPU.
There are 7,076 display jobs, including pause UI. Display queue high-water is
two; measured producer blocking is the 0.736 ms above.

The audio-lead wait totals 13.263 seconds, a useful target for reviewing the
production controller. It can also be legitimate throttling in lighter
scenes. Removing its total from this run and calling that a speed gain would
be an unsupported counterfactual. Likewise, ordinary flip waits are not proof
that the CPU is wasted. Display lifecycle cleanup alone is unlikely to solve
the heavier core-call deadline violations.

## Sound, memory and instrumentation

All 5,201,571 resampled frames plus 4,096 priming frames were accepted. There
are zero write errors, zero ending software frames and zero software clears.
Partial/EAGAIN handling worked at the logical transport boundary. The device
queue was sampled at zero; maximum accepted-write gap is 71.280 ms. These
support starvation risk but do not identify the exact underrun count, prove
continuous DAC playback, or time-localize each gap. Pause transitions and
device resets are separate events/counters.

Early RSS is 11,736–12,424 KiB, high-water 14,472 KiB. Returned-to-library RSS
is 3,216 KiB. Process swap is zero in retained samples. There is no measured
swap-thrashing explanation here; unsampled system pressure remains unknown.

RAM checkpoints took 75.614 ms total, at most 2.240 ms each, with zero reported
errors. The 27 wrapper capture/sync windows took 6.330 seconds elapsed in total,
mean 234.4 ms, maximum 260 ms. That is observer wall time, not proven main-thread
stall time or observer CPU. It is sufficiently intrusive that the next
performance test should keep RAM counters while reducing live SD/process work.

The returned firmware reports `head: not found`. Thus system-wide CPU/memory/IRQ
samples and the bounded process inventory were **not** captured. Kernel tail
and stderr/stdout copies are empty; that is a collection gap, not evidence of
silence or absence of kernel problems. Three early and one latest platform
snapshots also cannot reconstruct the entire scene timeline.

The source now uses the already-qualified `sed` command for bounded line
capture. A regression runs the actual wrapper with a restricted PATH lacking
`head` and checks CPU/memory contents, along with the existing startup/splash/
live-progress/cancellation contracts. This source correction is **not installed
on the card**; the shipped 1.7 release remains byte-identical. Its exporter now
refuses to overwrite that historical release with different checked bytes.

## Next engineering decision

**Subsequent user direction:** Ben rejects the paired device comparison below
and requests a smarter forward A7 build. [MVP1.8](snes-mvp-1.8.md) is the active
implementation/test sequence; the following proposal remains historical.

The full-render path works functionally, but it has not met full-speed audio/
video acceptance. The 1.6 power-off cause remains unexplained; one clean exit
does not settle it. Party-menu relief and the expensive-call distribution
justify concentrating on scene-dependent emulation/render cost and the
production controller, while retaining the working display ownership.

Before another claim or large core rewrite, compare original and A7 code on
the same saved workload and callback sinks using kernel wall/thread CPU time.
Price PPU, APU and host work separately, sampling in RAM at low frequency;
correctness equivalence and NEON instructions cannot establish a speedup.
Review lead-throttle behavior with simultaneous software/device queue records
and account for diagnostic interference. A single production controller must
maintain sound headroom without adding avoidable frame delay. Do not restore
held drawings as an unannounced fallback.

No new build or one-shot is installed by this return review. The next test
must preserve the user's newly earned in-game save as well as the old private
snapshot; loading an old snapshot is not a substitute for retaining new SRAM.
