# Hardware lab1 physical return — 2026-10-04

The lab completed, returned to the regular launcher and exited0. Ben reports
clicks between tests, hard-to-read text and otherwise a successful run. The
exact lab binary/wrapper match the installed release. Display join, FreeVFB
and wrapper exit records all survive; no timeout or forced termination fired.

Archive41 MVP files plus17 lab files with source/copy/source SHA256 checks and
zero card writes. All20 protected private progress/report entries, stock
hashes, boot hook, game runner/core and original game-wrapper bytes are intact.
Both one-shot markers are consumed. No replacement build or re-arm occurred.
Selected [raw results](../evidence/2026-10-04/platform-lab-1-return/results.log),
[analysis](../evidence/2026-10-04/platform-lab-1-return/lab-analysis.json) and
[verification](../evidence/2026-10-04/platform-lab-1-return/lab-verification.json)
are published with provenance. Full private archives remain local.

## What the platform sustained

| Phase | Submissions / vendor flips | Producer calls/sec | Producer CPU/call | Display-worker CPU/call | Audio-worker CPU/call |
|---|---:|---:|---:|---:|---:|
| Display only |240 /240|59.797|0.590ms|0.619ms|—|
| Audio only |0 /0|59.891|0.053ms|—|0.155ms|
| Audio + display |240 /240|59.912|0.616ms|0.627ms|0.284ms|
| +12ms CPU burst |240 /240|59.913|12.609ms|0.627ms|0.289ms|
| +12ms CPU slices |240 /240|59.836|12.618ms|0.636ms|0.278ms|

The burst phase has about13.525ms of timed producer/worker CPU per call and
nearly native submission throughput. Scaler wall averages2.24–2.26ms; flip
wall10.30–14.20ms. Worker wall overlaps producer CPU and must not be added to
its frame budget. Reserve waits total only1.34–1.46ms across each240-job phase;
FIFO high-water is1. Every submitted job completes in order by phase drain.

This is evidence that the working audio/display platform can service a
substantial CPU load without becoming the sustained bottleneck in this run.
It is not proof that FF6 fits: the workload is register arithmetic, not the
emulator's cache/memory/APU/PPU access pattern or worst-case frame distribution.
Nor are vendor flip returns a measurement of optical panel cadence. The short
successful run does not resolve the earlier whole-device power-off cause.

## Audio observations

All four requested rates32000/32040/44100/48000 are accepted through OSS, with
2048-byte fragments and8192-byte reported hardware capacity. This qualifies
negotiation, not exact DAC rate or low-cost native32040 playback.

In all four timed sound phases:

- Query/write errors and short writes are0. EAGAIN is expected full-buffer
  flow control, not discarded PCM.
- After initial empty startup, successful GETODELAY samples remain6144–8192
  bytes:1536–2048 stereo frames, about34.83–46.44ms at the negotiated44100Hz.
- Maximum accepted-write gaps are22.903–22.930ms. These are not xruns; the
  sampled queue retains more headroom than that interval.
- GETOPTR is supported and raw bytes progress without a backward sample in
  these short phases. Samples requested every5ms arrive about every9.7–10.0ms.
  Sampling can miss events; there is no qualified hardware underrun counter.

An important ABI correction: GETOSPACE frequently reports negative free bytes,
including-2048 and-4. Upstream4.19 subtracts the OSS staging buffer from hardware
space. Its non-mmap GETOPTR.blocks represents queued periods, not a reliable
count of periods played since the previous query; its byte count is masked by
INT_MAX. These formulas are consistent with the observations, but vendor
modifications are not ruled out ([Linux4.19 OSS implementation](https://raw.githubusercontent.com/torvalds/linux/v4.19/sound/core/oss/pcm_oss.c)).
The analyzer now retains negative space and raw first/last counter values and
refuses to manufacture a modulo-2^32 played-byte delta after a backward sample.
Do not promote this cursor into a scheduling clock without a qualified wrap,
reset, staging and consumption contract.

The user's transition clicks are consistent with opening/resetting/closing OSS
and abruptly starting/stopping a nonzero waveform. Those boundaries are explicit
in this lab; they are not evidence of FF6's steady-playback clicking. Their exact
physical mechanism is not established. Future audible probes should ramp/drain
their tone at transitions.

## Renderer experiment: NEON wins, this color cache loses

| Synthetic4bpp workload | Scalar CPU/draw | NEON CPU/draw | Color-cache CPU/draw | Cache hits |
|---|---:|---:|---:|---:|
| Reuse |1.676µs|0.666µs|0.954µs|62.48%|
| Thrashing |1.680µs|0.682µs|1.548µs|0%|
| Palette churn |1.682µs|0.675µs|1.111µs|46.86%|

NEON is about2.5x faster than the scalar fixture. The27152-byte direct-mapped
color cache is about43%,127% and65% slower than NEON in these cases. Even its
reuse case has collisions; this does not prove every possible color cache
loses. It does rule out adopting this implementation as the performance fix.
Do not quote2.5x as an additional whole-core speedup: the installed1.8 already
uses NEON, and the fixture is ordinary plain4bpp rather than all rendering.
Next renderer work should first address the actual core's palette spills,
empty-row scheduling and hot-code footprint, retaining exact output.

Voluntary1ms yields with the same12ms CPU budget do not demonstrate better
audio service or throughput. Demote blanket CPU slicing as the next fix.

## The strongest new timing clue

Across200 advancing nominal5ms deadlines, mean lateness is5.482ms and maximum
9.568ms. This measures lateness from scheduled deadlines; expired waits return
immediately, so it is **not** a measurement that every5ms sleep lasts10.482ms.
Pipeline start lateness reaches10.0–11.73ms even though steady throughput is
near native and display queue pressure is small.

Coarse/tick-bound wakeups or inherited timer slack are credible explanations.
High-resolution timer enablement, timer slack, kernel getres and individual
short-wait durations were not captured, so CONFIG_HZ=100 or a guaranteed10ms
sleep quantum is not established. Kernel4.19 distinguishes coarse/high-res
timer operation ([hrtimer source](https://raw.githubusercontent.com/torvalds/linux/v4.19/kernel/time/hrtimer.c)).

The current game producer polls its audio lead with an intended1ms sleep, and
the audio transport/space path also has1ms backoff calls. Those waits can
consume scarce wall-time headroom if wakeups are coarse. This is a concrete
next target, not a proven complete explanation of the prior lag or a free
5.48ms CPU saving.

Before choosing a timer workaround, qualify kernel-clock resolution, inherited
PR_GET_TIMERSLACK and independent1/2/5ms waits alongside interrupt-driven OSS
wakes. Prefer one consumer-owned, bounded audio-headroom controller and wake
the producer on meaningful consumption/space changes. Avoid stacking unrelated
lead polling and frame-timer gates. Publish already-emulated PCM during core
execution, preserving synchronous CPU/APU timing and the exact stream. Do not
replace sleeping with a broad busy spin or blindly assign real-time priorities.

Clock/cache sysfs, clk_summary and both probed trace_clock paths returnENOENT.
That is path availability evidence, not proof of absent caches, fixed clocks
or a kernel without tracing support. Libc monotonic still disagrees with the
kernel:447.391s versus8.409s. Retain direct kernel scheduling reads.

## Readability and next physical test

The lab rendered the640×480 notice font, then decimated it into the256×224
test frame. This is a code-grounded explanation for the user's readability
complaint. Future lab labels should be drawn with a large font directly at
their test-frame resolution, or on a separate native-resolution transition
screen. It does not invalidate the timing/counter data, and should still be fixed.

The next physical probe should resolve the timer/audio-consumption seam with
readable labels and smooth tone transitions. The next game build should use
that result to repair coherent lead control/in-frame PCM publication and the
emitted renderer, then retain every drawing for the actual FF6 acceptance run.
