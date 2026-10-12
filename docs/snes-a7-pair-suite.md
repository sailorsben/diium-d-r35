# A7 pair1: complete renderer cost, 2026-10-11

The user authorized staging a new physical measurement after the offline Bio
Blast experiments. The test card is now **I:**, FAT32 DIIUM D-R35, serial
11EB-1465. D: is the previous system disk; historical D:-specific installers
must not be run against it. This suite measures the whole-path net effect of
window batching, small palette tables and prefix validity. It is not a production
replacement and does not claim isolated e/r/b unit costs.

## Experiment

Use the exact shipping1.19 baseline binary and an isolated combined core with
no census counters. The runner disables all core phase profiling. Audio and
display workers run through the existing native client, owned chunk buffers
and joined lifetimes. Every emulator frame is rendered and submitted; no audio
quota, frameskip, error recovery or vendor PCM policy is changed.

For each of three start states, run baseline / combined / combined / baseline:

| Start before replay call | Bound | Warmup excluded from later-state cost comparison | Useful range |
|---|---:|---:|---|
|0|500 calls|naturally runs through earlier scene|entire effect277..438 and recovery, if PCM survives|
|261|80 calls|first16 calls|277..340|
|384|96 calls|first16 calls|400..479, including effect400..438|

Starts261 and384 are produced by executing the baseline with the original
Bio Blast input sequence, without game-memory edits. After call36, replay input
is zero. Each snapshot payload is unchanged between the two cores; only its
separate core identity header changes after output qualification. The baseline
and candidate both reload their state on each independent pass. Cache warmup
is deliberately visible in the records;16 calls is an initial exclusion, not
proof of steady state. On return, inspect its convergence before pricing.

Each pass begins a new audio epoch. Later starts avoid accumulated pre-effect
audio debt, but cannot prove uninterrupted playback or recovery of the original
full effect. A PCM fault ends its pass without reprime; the next pass is another
experiment. MENU or a termination signal aborts the suite. The one-shot marker
is consumed before startup, so the next boot goes to stock.

## Observer

Existing frame-boundary kernel thread CPU and wall clocks remain. New records
add frequency reads and copies of worker/service statistics outside the timed
core call, with their wall duration separately reported as `observer_ns`.
`step_ns` includes admission, callbacks, bookkeeping and the new observer.
There are no entry/tile/row clocks, microbenchmark repetitions, per-pixel CRCs
or core counters during the physical run. Costs are never calibrated away.

Frequency discovery uses exposed policy0 or cpu0 sysfs, pins the minimum to
the existing maximum only when possible on the single online CPU, and restores
it after the pass. Before/after frequency is recorded per call. Missing sysfs
is explicitly unavailable, not an assumed666MHz. Compare known frequencies
separately; ABBA mitigates order drift but cannot prove unknown-frequency parity.

At most500 bounded frame records and32,768 native PCM history entries are kept
in RAM. Frame CSV and PCM history flush after both workers stop; sync occurs
between independent passes. The wrapper performs platform discovery outside
the child's lifetime and keeps live progress in /tmp. It shares the previously
qualified splash handoff and refuses to race an active showlogo display owner.

## Falsifiable predictions and return analysis

The offline change removes8,340.864 plain tile calls/effect frame and reduces
RGB-cache storage/traffic. Its net saving is unknown: added gathers, table
queries, changed batching and cache interactions can still lose. Match replay
call numbers across both variants and both order positions; report CPU, wall,
admission, observer and complete-step mean/median/p95/p99, distributions of
paired saving, frequency conditions and surviving sample coverage. Do not
compare unmatched surviving prefixes or manufacture a complete-effect result
from short later epochs. Do not divide inclusive rendering time by tile counts.

The prior late-call deficit is1,514.283us; the separate sustained PCM proxy
requires2,436.981us/call. A measured saving above the former is promising for
the late-call deadline but is not sufficient proof of sustained audio closure.
Measure actual cadence against16.6881545ms/call and44,100 accepted sink frames/s;
include observer/worker contention and full cumulative PCM reserve, valid
RUNNING epochs, fault pointers and subsequent recovery. Short snapshots cannot
supply the full reserve history required for production acceptance.

If combined improves CPU/wall but PCM still stops with adequate measured reserve,
investigate the vendor PCM pointer/stop lifecycle separately. If net saving is
insufficient, inspect the paired changes and don't re-arm this build unchanged.
No production installation verdict precedes the physical return.

## Qualification, staging and preservation

The core passes6,000 exact visible-pixel/native-PCM/geometry/normalized-state
comparisons:1,200 complete Bio Blast,2,400 general, and1,200 each from the two
cold-reloaded later states using zero input. The real runner passes12 mock
experiments (2,704 calls), all drawings submitted, correct PCM accounting and
no progress save writes. Both cores also pass injected EBADFD, independent clean
retry/drain and sustained deficit rejection through an independently consuming
native provider. These are contract checks; all QEMU durations are excluded
from A7 performance evidence. Wrapper fixtures cover splash exit/stall/zombie,
startup error/timeout, consumed one-shot, and zero live-child diagnostic card
writes/global sync. The runner requires no glibc newer than2.30.

`archive-a7-pair-card.py` privately copies/hash-verifies every retro file before
read-only CHKDSK. The installer pins card serial, stock/adapter/runner/core/init
and old cost1 dispatch, verifies the complete archive and qualified source,
payload and proof hashes, and refuses an existing pair1 target or any armed
marker. Only `retro/snes-pair1`, `retro/snes-mvp/launch.sh` and its one-shot
marker are written. Payload/arm readback and subsequent FAT checks precede
completion. Every earlier retro file except that owned dispatch remains hashed
unchanged; ROM content is also protected. Rollback restores only owned paths
after a fresh clean health report. ROMs, snapshots, vendor cores, native
dependencies and all raw archives remain ignored/private.

Build: `sh build/build-a7-pair.sh`, then `python3 build/check-a7-pair-native.py`
and `python3 build/check-a7-pair-wrapper.py` in the pinned ARM WSL environment.
Preparation refuses an existing tree. Explicit resume is only for a build
that failed before qualification. Windows staging takes the exact successful
archive path: `python build/install-a7-pair.py <private archive>`.

Physical instructions: [test card](snes-a7-pair-test.txt).
