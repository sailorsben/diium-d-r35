# Physical frame budget and burst recovery — 2026-10-15

The corrected test completes all 70 phases, with **58 accepted and 12 failed**.
The light static renderer plus **8 ms extra CPU work per frame** completes all
180 quanta with valid PCM pointers and accounting. Adding 12 ms fails. Six
24 ms extra-CPU bursts pass; 48 and 80 ms burst sequences fail. The frame
budget is now bounded by actual measurements, without claiming an exact
device ceiling or long-duration stability from three-second cells.

The double-drain correction is physically accepted in audio-only, the two
passing steady-load cells, the passing burst cell and all four unloaded light
controls. Each finishes production, drains once and closes without an audio
error. This is eight passing audio cells plus 50 non-audio cells. Eight dense
render/audio cells, two steady-load cells and two burst cells fail production.
Wrapper exit1 reflects those expected diagnostic issues; supervisor forced0,
reaped1/raw_status256 records a normal child exit, not a crash or timeout.

## What fits within 16.688153 ms

The production quantum generates about 736 samples/channel at negotiated
44,100 Hz. It is a wall-clock budget shared by main emulation/render work,
audio/display workers, kernel work and scheduling. Blocking time is not CPU
consumption, and display work can overlap the producer. A per-frame median
or one occasionally long frame cannot alone decide sustainable throughput.

All sweep cells use static 256×224, two layers, cached rows, direct chunk
output, queued display and native audio. Main CPU below is warm median of
completed valid iterations, excluding first8/final validation-copy iteration:

| Extra CPU each frame | Main CPU per frame | Result | Lowest observed valid PCM reserve |
| --- | ---: | --- | ---: |
| None, unloaded light control | 4.026 ms | 180/180, pass | 58.73 ms |
| 4 ms | 8.054 ms | 180/180, pass | 52.93 ms |
| 8 ms | 12.036 ms | 180/180, pass | 50.02 ms |
| 12 ms | 16.302 ms before pointer fault | 57 completed, failure on next iteration | 3.02 ms before pointer fault |
| 16 ms | 20.435 ms, short valid warm prefix | 11 completed, failure on next iteration | 3.06 ms before pointer fault |

These are ~3-second full cells or shorter failed prefixes. The 8 ms cell runs
180 executed loads and accepts all135,293 queued frames (2,823 priming plus
132,470 generated), with zero cleared/remaining, valid running pointers and
180 submitted/scaled/flipped drawings. Its phase-average main CPU is12.123 ms;
display worker CPU averages0.767 ms/drawing. Audio worker CPU is60.571 ms for
the whole cell including final drain, roughly0.337 ms/quantum but with a different
time boundary. Do not sum these into an exact synchronous per-frame charge.

A useful current operating point is **about12 ms main-thread CPU**, leaving
about4.6 ms of the16.688 ms quantum for other work and scheduling. That remainder
is not all free CPU. About16.3 ms main CPU leaves only0.39 ms, insufficient for
the other observed work in this path. The tested extra-load transition lies
between8 and12 ms; it is not an exact universal12 ms main-thread limit.

The 8 ms cell's phase wall is3,017.414 ms for180 quanta. Phase wall includes
pipeline drain/validation-copy and start/end transients; it is not a precise
long-run rate estimate. Production histories retain substantial reserve and
valid counts throughout this bounded cell. Repeat duration and intermediate
loads would be required to qualify a tighter sustainable threshold.

## What bursts it absorbs

Bursts add CPU-clock work every30th frame (about every0.5 seconds), while the
baseline still renders. `load_events` confirms each burn actually executed.

| Added burst | Executed events | Outcome |
| --- | ---: | --- |
| 24 ms | 6 | All180 quanta, valid pointers, drawings, accounting and drain; pass |
| 48 ms | 3 | Stops during third burst,89 complete quanta; pointer accounting already invalid around second burst |
| 80 ms | 1 | Stops during first burst,29 complete quanta; incomplete burst iteration has no frame timing row |

For24 ms, the six complete burst iterations consume28.13–28.67 ms main CPU.
Render-plus-burn wall time is27.89–29.19 ms; full iteration wall is41.41–42.11 ms
because it includes normal admission waits. Calling that entire41–42 ms a CPU
stall would be wrong. Minimum valid observed native reserve is1,438 frames,
32.61 ms. The first five bursts regain at least the2,823-frame primed lead
(64.01 ms) within5.33–10.94 ms **after their observed reserve minima**. The
sixth burst is the final produced frame: it passes through drain, but has no
subsequent production recovery window. These are sampled recovery intervals,
not an exact minimum-to-maximum or optical/audio-latency measurement.

The 48 ms run is particularly informative. After the first burst, valid native
reserve falls to486 frames (11.02 ms). It never regains the2,823-frame prime
threshold before the next burst. The first pointer mismatch is seq312 at
99.008946 s, around the second burst, where application pointer46,627 differs
from accepted count46,243 by384 frames. Thereafter the report censors reserve
and recovery claims; continuing to a third burn is not proof that the second
was safely absorbed. Final stop is SETUP/errno77. In the80 ms run, the worker
has no valid low-reserve observation during the long burn before the fault;
its sampled minimum must not be called the actual minimum or evidence against
starvation. Zero explicit XRUN counters do not establish continuity.

Thus **24 ms additional CPU bursts are demonstrated at this spacing;48 ms
is not reliable in this path**. Nothing establishes a safe threshold between
them, arbitrary burst frequency, or arbitrary real-game workloads.

## Recovery is constrained by presentation too

Before the first48 ms burst, frames8–28 have median display-reservation wait
0.006 ms, main CPU4.012 ms and audio-admission wait12.652 ms. After it,
frames30–58 remain pointer-valid but change to:

| Per-frame median, frames30–58 | Measured |
| --- | ---: |
| Main CPU | 4.385 ms |
| Render wall | 4.651 ms |
| Display-slot reservation wait | 11.452 ms |
| Audio admission wait | 0.094 ms |
| Full iteration wall | 16.589 ms |

Native lead stays below the priming target. The producer has spare CPU but
waits for presentation credit instead of using that room to regenerate its
audio lead quickly. The state change supports **display backpressure as a
recovery constraint** in this all-drawings-retained controller. It does not
prove a particular scaler/flip driver fault, nor yet qualify another queue
mode or an audio-aware frame policy. Observations after the second burst's
pointer corruption are excluded from this comparison.

## Where to focus next

1. **Price an audio-reserve-aware production/presentation policy.** The clean
   first48 ms burst exposes a path where CPU is available but a display slot
   gates audio recovery. A controlled experiment should allow emulated audio
   to catch up without requiring every produced frame to wait for presentation.
   That requires an explicit rendering/presentation policy, retained buffer
   ownership, game-state/audio continuity and a bounded visual-correctness test.
   Do not replace READY jobs or free DMA sources still owned by the worker.
   The falsifier is that valid lead still fails to recover despite removing
   this wait, or that a supposedly saved wait costs equivalent extra CPU/work.
2. **Reduce sustained core work in the expensive cases.** Dense synthetic
   NEON rows still cost20.341 ms main CPU, and real rendering plus direct
   output21-ish ms; they exceed even the bare quantum and cannot be rescued
   indefinitely by buffering. Profile real-core row/depth/color work plus
   CPU/APU against the measured operating point. The synthetic stream does
   not price65816/SPC/DSP or full PPU decoding/register behavior. An approximate
   12 ms main CPU target is a useful tested goal for this frontend, not a claim
   that every real FFVI frame must reproduce these synthetic costs.
3. **Keep smaller leads proportionate.** Cached rows again fail to beat NEON
   in every CPU-only scene; direct output saves around0.7 ms in the dense
   pipeline but leaves it far over budget. Prebuilt display still reaches
   roughly60fps at all three sizes. Another color cache or speculative scaler
   ioctl change has weaker evidence than the two issues above.

No change is installed or armed as part of this analysis. A next candidate
still needs the measured A7 saving/cost/break-even gate and matched physical
comparison; these results are measurements and prioritized leads.

## Evidence and card state

Strict archive `device-evidence/a7-pair-before-20261016T040248Z` retains9,035
files/2,031,287,802 bytes and clean FAT. All original archive hashes verify;
executable/wrapper/qualification/dispatcher and pinned sources match the
installation. Of8,655 pre-install files,8,651 stay exact. Changed files are the
authorized dispatcher, consumed `last-launch-lab`, stock swapfile and the
UART helper's fresh boot log (same healthy attachment with new counters).
The ROM and patched init also verify directly on I:. No firmware trigger or
armed marker remains, and collection made zero card writes. The next boot is
stock with permanent UART correction.

IRQ19 advances7,540 in104.302 s:72.29/sec, attached with fault/bypass/full0.
Module7,656 calls reconcile as7,059 added services (7,057 writes/two empty stops)
plus597 fallbacks. RX/break rises25; frame/parity/overrun remain0. CPU frequency
sysfs is unavailable; the clock source remains `arch_sys_counter`. No clock,
temperature or whole-device optimum claim is inferred.

[Source-bound report and376 input hashes](../evidence/2026-10-15/render-pressure2/return.json).
The frozen original reporter independently accepts58 cells. Full PCM histories
are retained from entry0; failed-pointer tails are censored for reserve/recovery.
No ROM, private saves, vendor binaries or full card payloads are published.
