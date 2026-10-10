# A7 cost1 measurement suite

The suite measures the known Bio Blast budget problem. It changes no guest
clock, audio quota or rendering decision. Its separate baseline renderer has
owned timing hooks and shadow window helpers. The deferred window renderer is
not a payload. Production `snes-mvp`, `plus-a7.so` and `emu_sfc.so` stay exact.
The installation gate remains **NOT MET / A7 results pending**.

Staged2026-10-10 after archive `snes-mvp-return-20261010T182533Z`:60 runtime/
progress and49 lab files preserved,141 protected hashes verified. Independent
readback checks all new payloads and135 archive/reader hashes; all four fresh
FAT checks pass. Only the measurement one-shot is armed. Its private state,
diagnostic core and runtime dependencies are not published. The owned runner
and six bounded qualification/readback files are published; all676 earlier
evidence hashes remain exact.

## Capture plan

The automatic driver runs modes `0,1,2,2,0,1,2,2,0,1,2,2,3`. Each independent
pass loads the same privately retained Magitek snapshot, confirms ability and
target at the existing replay input boundaries, then runs at most500 full calls.
The162-call census interval277..438 owns instrumentation. This is the aligned
replay used for the candidate work counts; it is not the exact physical battle
background from Focus1. A fault ends that pass and is retained. Subsequent
passes have new directories and native PCM epochs. They are not continuous
audio acceptance, implicit recovery or a hidden re-prime inside gameplay.

| Mode | What it records | Observer boundary |
|---|---|---|
|0, repeated3 times|Counters, full PCM timeline, normal main CPU/wall and workers|Clock regions/bench loops disabled; counter/shadow/frequency/record work remains|
|1, repeated3 times|Exclusive entry setup, window-mask/clip-bound work and PPU remainder; one sampled call per8|Color/cache clocks sample1/64 requests with a rotating offset; unselected color work stays in the pixel remainder|
|2, repeated6 times|Actual source setup blocks, row materialization payload, valid-bit test, mask capture/reset, deferral, fetch and row comparison|Four bounded batches/path/call:1,32,32,32 timed iterations, each preceded by16 warm iterations|
|3, once|Dense disjoint attribution at aligned frame320, including every color/cache request|Potentially large syscall interference; reported separately and never used as an ordinary cadence|

One timed observation gives an individual-call distribution;32-operation
batches give amortized unit distributions. The latter's p99 is a **batch-mean
p99**, not an individual-call tail. Keep both. Small warm kernels can be
dominated by timer overhead in the individual distribution. All timer, loop,
barrier, warmup and shadow work stays in the observed execution costs. Empty
batch and64-clock controls are reported; no calibration is subtracted.

The setup benchmarks repeat the actual generated source blocks in their live
calling state. Mode1/normal-resolution guards exclude stateful fallback
rendering from repeated setup. Object-list preparation is part of that setup
path; BG clip-bound selection and ComputeClipWindows are separately attributed.
Row miss timing covers palette/NEON materialization and validity update; the
valid-bit control does not represent the entire cache-hit lookup. Save/restore
around row benchmarks preserves the live cache. No pixel or PCM is replaced.

## Logging, clocks and memory

All performance clocks use direct kernel syscalls: thread CPU for attribution,
monotonic for scheduling/wall cost. No libc monotonic scheduling, QEMU timing,
assumed666MHz conversion or emulated-clock-to-host-cycle conversion is used.

The host reads policy0/cpu0 cpufreq, governor and CPU-online state before each
pass. On the observed single CPU, if min/max exist and are writable, it raises
minimum to the existing policy maximum and records readback. It restores the
original minimum at pass end. Current frequency is read through a retained FD
before and after every call; absent/error values remain `-1`. Those samples do
not prove a constant frequency between observations. Pin failure, restoration
readback and unavailable frequency remain explicit. Physical durations in
microseconds are still valid at the observed, possibly unknown frequency.

Records live in bounded RAM, never per-row text logging. Each pass keeps500
frame records and at most128 benchmark records/call. Native PCM keeps32,768
events with exact retained-start/total counts. Full timeline includes successful
passes, so onset and recovery survive if the stream completes and the ring
does not wrap. Fault-time kernel text is captured in RAM. Cost/PCM files flush
after the audio owner joins and the display queue drains; the display worker
remains idle until final board close. File fsync and a between-pass sync prevent
the previous pass's queued SD writeback from spilling into the next live pass.
Existing once-per-second RAM checkpoints remain timed and included.

The ARM link reports suite BSS4,289,528 bytes versus Focus1's63,200: an increase
of4,226,328 bytes (4.03MiB). Core BSS increases5,992 bytes. Returned pre-child
MemAvailable was25,712KiB; that is historical headroom, not a promised live
memory margin. No memory-growing event queue is used. Worker/storage/memory
effects stay observable; record overflow or incomplete history invalidates a
complete-effect claim.

## Qualification and boundaries

600 aligned actual ARM-core replay frames preserve every visible RGB565/native
PCM CRC, sample count, callback batching, geometry and normalized state across
the three ordinary measurement modes. Four500-call runner captures exercise
sparse, dense, benchmark and control modes. The automatic13-pass mock driver
retains13 separate500-call captures and zero failures. The consuming native
provider verifies injected EBADFD, deferred PCM flushing, clean120-frame retry
and drain, sustained-deficit rejection without hidden re-prime, and preservation
of previous evidence. These are software contracts, not A7 performance.

Core identity CRC`b5aa1b93`; SHA256
`ae2931386f40ce79f7a2c297d52e34dddadadb7c7d8da10a35f6039071db33ce`.
Suite SHA256
`0bdb238ffe20433fc20644b73189c60c7fbbc0f5c8aad3e3437acdcfbb712060`.
The replay payload is byte-identical to its private source; only its identity
header names this separately qualified diagnostic core. Original progress is
never rewritten with that header.

There are deliberate coverage limits. Shadow deferral on the baseline observes
shorter pending spans than the actual candidate can accumulate. Warm isolated
row/helper prices do not directly measure the whole candidate's changed cache
interactions. The analyzer leaves final e/r/b and the verdict unset where that
coverage is missing. This first capture should give usable component prices,
observer interference, actual phase ownership and the shape gaps to close;
it must not manufacture a complete candidate prediction from partial kernels.

## Scorecard interpretation

Retain `S=106.246914e-1423.919753r-b`. Exclusive setup time per observed entry is
descriptive; it is not inclusive PPU/entry time, and still needs weighting by
the candidate's removed entry/subpath population. Added-row payload and
bookkeeping/cache costs must be covered before filling final e/r/b.

The1,514.283us threshold reaches the late-call account before other loop work.
At the measured38,480.644/sec PCM production proxy, nominal quota735.947520
implies19.12444ms between output quotas. Reaching16.6881545ms there needs about
2,436.29us off that cadence. These are different accounting windows. A candidate
that saves1.514ms must not automatically be claimed to close the14.603%
throughput requirement. Apply measured saving only to its aligned cadence;
report remaining deficit, headroom and complete cumulative reserve separately.

2010's NEON compositor becomes a sensible target if pixel/depth/color-math work
owns the remaining CPU. Large entry/window work would instead favor reducing
dispatch/invalidation. Color materialization is already a NEON palette kernel
here. Sparse remainder includes unselected row work, so use the dense check and
warm path distributions before assigning the whole remainder to compositing.
No porting decision follows from the core's year label.

On D: return, run `python build/collect-a7-cost.py`, then analyze the archived
`snes-cost1` directory with `build/analyze-a7-cost.py`. Mock and synthetic native
provider timings are rejected unless explicitly using contracts-only mode,
which discards all timing distributions. Verify installation/collection hashes,
consumed marker, frequency/cache conditions and capture completeness first.
Physical instructions: [snes-a7-cost-test.txt](snes-a7-cost-test.txt).
