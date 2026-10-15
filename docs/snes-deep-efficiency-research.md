# Deeper efficiency research: compiler cause and strongest verified mechanism

2026-10-14. No I: access, install or rearm. New work is local compiler controls,
observer/prototype comparisons and a prepared unchanged-core diagnostic. All
previous qualified trees, raw returns and published evidence remain intact.

Subsequent explicit "Arm I" authorization installed and armed the unchanged-core
diagnostic from pushed6123047 after a fresh strict archive and guarded checks.
Physical attribution remains pending; the research preparation below is retained
as recorded. [Current installation](snes-pc-profile-installation.md).

## Compiler interaction pinned to SPC loop unswitching and LTO partitioning

GCC13.3 reports reproduce demand-v3 **byte for byte**. They reproduce the
combined candidate's **.text byte for byte**; its pinned library-version string
differs, so the full ELF hash differs. This rules out studying a merely similar
compiler output. Reports show the exact change:

- Baseline: APU initialization and the SPC interpreter reside in one LTRANS
  optimization unit. GCC hoists `allow_time_overflow` and unswitches the opcode
  loop into two versions. Named interpreter size21260 bytes.
- Combined: initialization resides in LTRANS11, interpreter in LTRANS12.
  The flag remains loaded/tested in the opcode loop; no SPC unswitch report.
  Named interpreter size10212 bytes. The nearly halved static call sites describe
  one loop instead of two, not half the emulated execution.
- Counterfactual combined with `-flto-partition=one`: the same invariant is
  unswitched again, named interpreter21388 bytes. Thus PPU source growth can
  change the optimizer's treatment of unchanged APU code through partitioning.
- Selectively compile only apu_blargg.c with `-fno-lto`: the SPC loop is again
  unswitched. Its object is **byte-identical across baseline and combined PPU
  source trees**, SHA256
  `a3baec4aabbbb539858fb7fc59b5b96bddf7e7e6bb7a51c6e6fa394f8b542097`.
  This supplies a reproducible experimental boundary while retaining LTO
  elsewhere. It does not prove that boundary faster than v3.
- Negative control: snapshot the flag into a call-local const. It removes the
  need to reread that global but **does not restore unswitching** under the
  original partition layout. Do not present it as a proven fix.

GCC documents the default balanced LTO partitioning, its one/source-file modes,
and loop unswitching's duplicated loops.
[GCC13.3 optimization reference](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html).
Compiler reports establish the transformation and partition dependence; they do
not measure its A7 cost or prove how much of the physical regression it caused.
DSP helper sizes differ by only a few bytes in the original comparison; the
substantial demonstrated structural change is the SPC loop, not a halving of DSP.

Four compiler controls pass14400 raw graphics/PCM/geometry comparisons on
Meteor, Quasar and Confuser, normalized state every30 calls. These are semantic
checks, not speed rankings. Full one-partition compilation is a research control,
not the recommended blanket build flag. A stable object still moves in the
linked image: address/layout/cache interactions remain. Future measurements need
raw v3, a boundary-only control, and the priority change using that same boundary;
price both the boundary cost and total net result. Do not silently redefine v3.

## What the current A7 logs actually time

The latest returned **v3 controls**, not old inclusive phase totals, give this
range across their heaviest valid16-call windows:

| Timed owner | Meteor | Quasar |
| --- | ---: | ---: |
| Core call, including callbacks/observer |15.448–15.515ms|14.629–14.689ms|
| Other timed main-thread work |0.225–0.244ms|0.211–0.254ms|
| Disjoint audio-worker increments |0.456–0.478ms|0.452–0.500ms|
| Disjoint display-worker increments |0.780–0.852ms|0.703–0.784ms|
| Total timed CPU in each actual window |16.975–17.048ms|16.056–16.190ms|

Range endpoints need not come from the same run; the JSON retains each actual
window and its components. About91 percent of recorded Meteor CPU is inside the
core call. Main pacing/worker optimization cannot receive credit for that pool.
The nominal recorded deficit is0.287–0.360ms to16.688153ms, excluding uncounted
OS/kernel and reserve/recovery costs. Frequency remains unavailable.

**The returned logs do not split this current core into PPU versus65C816 versus
SPC/DSP time.** Neither source counts, GCC dumps nor QEMU can manufacture those
A7 milliseconds. The earlier~87 percent PPU share of effect growth predates v3.
It is supporting history, not a current measurement. This part of the requested
attribution remains pending the prepared physical diagnostic below.

## Refreshed current-core work: exact outputs, no time inference

A fresh v3 observer passes7200 raw graphics/PCM/geometry calls on Holy, Meteor,
Quasar, Rage032, Bio Blast and Confuser, with normalized state every30 calls.
Every supported foreground-depth pixel has store provenance; every call obeys
math writes minus overwritten math equals surviving math owners. It changes no
rendering decisions. All selected layouts are supported and all outputs match.

| Mean work per call | Meteor120–239 | Meteor496–535 | Quasar496–541 |
| --- | ---: | ---: | ---: |
|65C816 opcode dispatches|14249.6|14183.3|14258.5|
|SPC opcode attempts, includes time-boundary retry|4311.7|4412.4|4438.9|
|Gaussian interpolations|2039.6|2777.6|3765.8|
|Decoded tiles|20.0|19.5|22.5|
|NEON palette preparations|—|16|15.9|
|Main RGB pixel writes|57521.9|85687.0|63241.9|
|RGB writes later overwritten|3350.9|28599.0|6153.9|
|Math writes later overwritten|2365.2|2250|2807.3|

CPU/SPC counts are comparatively stable while RGB work grows; DSP interpolation
also grows and cannot be dismissed. These are mechanisms, not a CPU-time split.
The chosen late Meteor/Quasar intervals have no observed CPU-to-SPC port reads
or writes; scanline SPC entries average~261 and end-frame calls262 per call.
That narrows the old port-driven residual ambiguity for these intervals, not
for all games. Decoding and palette rebuilding populations are too small to
receive speculative multi-millisecond credits.

## Strongest verified general mechanism: draw unique top-priority BG3 first

In Meteor, BG3 (source index2) later overwrites27600 already-colored pixels per
late call. Existing depth rejection cannot reject a winner that has not yet
been drawn. The top priority in mode1 with BG3Priority is unique: high BG3 is
D+17, above the other BG/OBJ priorities. Draw that tile class first, retain
original ordering for the rest, and use existing depth tests to reject covered
work earlier. Transparent holes still expose the original lower layers.

The local **observer-backed counterfactual** does this for mode1 with BG3 enabled,
BG3Priority set, ordinary256-pitch/non-hires output, no pseudo-hires or active
BG3 mosaic. It retains original windows, main/sub distinction, raster lifetime,
sprite evaluation/order/limits, math and unsupported-mode fallback. Original
low BG3 tiles still draw at their original position. This is rendering-state
eligibility, with no spell/game ID, prediction, completed-frame reuse or omission.

It passes **21600 raw graphics/PCM/geometry comparisons across all18 contexts**,
state every30 calls, with positive-path visits. It is a research prototype with
large observation arrays, not a release candidate or installation payload.

| Meteor496–535 work | v3 | Priority counterfactual |
| --- | ---: | ---: |
|Main RGB writes|85687.0|57865.3|
|Overwritten RGB writes|28599.0|777.3|
|Batch RGB vector expansions|10922.5|7515.3|
|Plain batch row visits|25504|19316|
|Math pixel writes|40528|38278|
|Overwritten math writes|2250|0|
|BG invocation count|7|9|
|Palette preparations|16|15|
|Tile decodes|19.5|19.5|

That removes97.3 percent of wasted RGB writes, **32.5 percent of this RGB-write
population**, and3407.2 vector expansions per call. It is not32.5 percent of
whole core time. Rage032 shows the same direction. Quasar removes3132.8 RGB
writes and182.2 vector expansions; its opportunity is smaller. A mere
deferred-math pass would target only the~5–6 percent discarded math and add
metadata/readback costs, so it ranks below this traversal/order change.

The prototype pays two extra BG invocations and~2906 filtered tile attempts per
Meteor call (~5409 Quasar), plus priority guards, code footprint and all retained
traversal/depth work. Net A7 saving remains **unknown**. An illustrative price
gate using only3407 removed vector expansions is0.3ms/3407 =0.088 microseconds
net per expansion, before added costs. Pixel/row/expansion populations overlap;
do not sum them or multiply their percentage by15.5ms.

Before a performance candidate: remove observer arrays, keep compiler controls,
add independent original-renderer tests for mixed priority/transparency, equal
depth, clipping, flipped16x16 tiles, OBJ limit/order and state transitions, then
qualify every frame/sample. Physical acceptance still needs full valid effect/
recovery, cumulative reserve and pointers, not only cheaper early calls.

## Concrete next measurement: same core, sampled PCs

`build/current-pc-profile-private-v1` is prepared and qualified locally, **not
installed or armed**. Both variants contain the exact unchanged demand-v3 ELF
SHA1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8.
Four automatic epochs run Meteor control/sample and Quasar sample/control.
The ordinary owned-output/native runner remains responsible for all frames,
PCM, full histories and joined cleanup. No core phase hooks are enabled.

A main-thread CLOCK_THREAD_CPUTIME_ID timer targets that thread and records
frame/ELF-relative PC in bounded RAM only during retro_run. It makes no clock,
file, allocation or lock call in the handler; teardown blocks/drains pending
signals before restoring the old handler, then flushes after workers join.
Exact ELF symbols classify PPU, CPU ops/memory, DSP, SPC/APU, DMA, mixed scheduler,
other core and outside-core host/library samples. Inlined scheduler work remains
explicitly mixed. It cannot independently price palette expansion versus stores
inside one fused producer.

Linux CPU timers and targeted delivery are documented in
[timer_create](https://man7.org/linux/man-pages/man2/timer_create.2.html).
Only one pending notification is queued per timer, so elapsed intervals can
coalesce; see [timer overruns](https://man7.org/linux/man-pages/man2/timer_getoverrun.2.html).
Our local1ms-request smoke checks delivered roughly one sample per10ms and
reported overruns. No assertion of1ms resolution, invented samples or overrun
weighting follows. Short intervals may remain too sparse; sample counts and
disturbance versus the control must decide whether attribution is usable.

Host and actual ARM/glibc2.30 sampler tests pass capture/frame/disarm/drain/restart.
The actual controller passes4800 calls; native consuming PCM/direct output,
fault/retry/state paths, wrapper, ABI and physical-mock rejection pass. Mock
frames intentionally lack physical pointer validity and are explicitly labeled
nonphysical rather than relaxing physical filtering. A7 timer support and
delivered sampling quality remain unverified. Unsupported timer/signal/mapping
fails clearly. The future guarded installer requires fresh archive/FAT/hash/
clean-pushed-source checks and explicit rearm authorization.

Research setup failures preserved privately: wrong mosaic field before build,
initial sampler workload too short for host delivery, non-PIE executable map
handling, and mock-prefix qualification. All corrected before the corresponding
final qualification. No failed performance result is replaced by a host-time claim.

**Decision:** compiler interaction is identified and a control boundary exists;
priority scheduling is the strongest verified work-removal lead. Current A7
inner-owner time remains the specific missing measurement. Run the unchanged
core diagnostic before putting any optimized candidate on I:.

[Evidence packet](../evidence/2026-10-14/deep-efficiency-research/decision.json).
