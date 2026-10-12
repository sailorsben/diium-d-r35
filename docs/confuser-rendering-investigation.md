# Confuser: BG3 clipping and half-add work — 2026-10-12

Investigation began2026-10-11 and completed2026-10-12. Evidence retains the
initial2026-10-11 experiment directory; the manual physical return is separate.

The strongest explanation is a rendering path the Bio Blast optimization does
not cover. Confuser uses a moving **BG3** circle, while the installed batching
guard requires **BG1**. Confuser also copies and waves the battle background on
BG1 and half-adds BG1/BG3 into affected BG2/sprite pixels. An actual ROM replay
confirms this path. A separate BG3 extension preserves output and removes
repeated tile setup; a separate half-add shortcut removes redundant selections.
These are offline hypotheses with exact-output proof, not measured A7 savings.
No card access, new device suite, staging or production-core change occurred.

## Physical failure and the cost to remove

The archived manual run is
`device-evidence/a7-pair-before-20261012T043106Z`. Between sparse samples13316
and13444, PPU CPU grows3.232 ->7.652ms, accounting for4.420 of5.257ms main-thread
CPU growth (84.1%). APU-inclusive grows4.048 ->4.261ms. These sampled costs
include observation; they are not per-function unit prices.

The23 completed calls before the abort average17.298ms core wall plus0.193ms
admission, against16.688ms nominal: **0.803ms minimum saving** before other loop
costs and headroom. Exclude the final failed call's13.057ms audio error path.

The retained native RUNNING trace provides a second local check:8,955 accepted
frames in215.472ms, or41,559.924/sec against44,100/sec. At unchanged quota, that
corresponds to **1.020ms/call** throughput-equivalent saving. This is a short
asynchronous endpoint window, different from the23-call timing tail; it is not
a whole-effect production rate. It supports aiming above1.020ms rather than
calling a0.803ms borderline model sufficient. Neither estimate includes new
candidate costs or safety headroom.

Application pointer bias grows0 ->128 ->256 ->384 frames before errno77/SETUP.
The final reported892-frame reserve exceeds accepted-minus-hardware accounting
by384. Keep that vendor edge unresolved; reported reserve is not independent
physical proof after bias appears. Underproduction remains a leading trigger.

## Game code -> renderer work

The local pinned disassembly and byte-matched ROM identify:

- C2/EEDE initialization: `$2124=cc`, enabling Window2 on BG3/BG4. Mode1 renders
  three backgrounds; BG4's window cannot affect a Mode1 BG4 drawing.
- C2/F973: half-add BG1/BG3 into affected BG2 and sprites.
- D0/3C89: BG3 circle expansion41 animation updates, hold65, contraction40,
  palette cycling and circle updates synchronized near scanline216.
- D0/3CC1: BG1 uses tilemap `$6100`, graphics `$1000` and the battle-background
  scroll base. Wave amplitudes1,3,5,7,9 then7,5,4,3,2,1, four updates per stage
  and97 additional updates at the large-wave plateau.

[Readable C loop model](../build/ff6-confuser.c) documents those semantics.
`frame(0)` yields to the game's animation scheduler. It does not consume a host
sleep budget or justify changing the core's nominal emulated-cycle quota.

In installed `a7_window.h`, `d35_window_eligible()` requires
`ClipWindow2Enable[0]` and rejects enabled Window2 on other layers. Confuser fails
that predicate, so `$2128/$2129` changes fall back to `FLUSH_REDRAW()` and
`S9xUpdateScreen()`. `DrawBackground()` then repeatedly invokes tile preambles
on short vertical ranges. BG1's actual varying scroll still needs separate row
work; capturing BG3's circle lets unaffected work remain batched.

The replay uses the preserved earlier private battle and **normal Down/A/A
inputs**, with no new RAM pokes. Visual selection and actual C2/EEDE execution
verify Confuser. Its Window2 interval is302 emulation calls, zero-based267..568.
This is a derived controlled encounter, not the13456-call physical input history.
The initial misselection executed Heal Force and produced no Confuser init;
it remains a private negative control and contributes no Confuser savings.

## Tested work populations

Means over the same302 calls; ordinary comparison is replay calls100..199.

| Work per call | Ordinary | Installed combined logic | BG3 batching |
|---|---:|---:|---:|
| Renderer entries |40.98|60.341|28.010|
| Full-tile calls |—|12,459.560|10,431.854|
| Clipped-tile calls |—|247.146|229.947|
| BG2 renderer entries |—|89.619|24.990|
| BG2 requested rows |—|358.911|358.911|
| Half-add full-tile rows |0|4,569.070|4,569.070|
| NEON row visits |8,642.960|17,792.169|17,792.169|
| Depth-rejected NEON rows |710.290|4,709.242|4,709.242|
| Tile decodes |20.090|19.586|19.586|
| Palette builds |—|12.887|12.887|
| Direct palette gathers |—|12,276.709|12,276.709|
| Palette-table queries |—|6,584.245|5,510.990|

BG3 batching removes32.331 renderer entries,1,772.066 plain full-tile calls,
255.639 half-add full-tile calls and17.199 clipped half-add calls per effect
call. It defers66.649 window-edge queries;2.013 retain fallback. Every frame's
requested row, decode and pixel-visibility census matches the baseline.
Palette builds and gathers also match. Fewer palette queries belong to the
removed tile-call population and must not be credited twice.

This ranks the hypotheses:

1. **Repeated traversal/tile setup from BG3 window fallback:** directly confirmed,
   with a tested way to remove it. The effect's real wave rows cannot all batch.
2. **Half-add and doubled row/depth work:** directly confirmed. About4,041.901
   visible half-add rows/call use true subscreen pixels on every active lane.
   Fixed-color selection and final enabled selection are redundant there.
3. **Single-CPU contention and vendor PCM stop semantics:** remain contributors
   to wall-time/termination; the offline replay cannot price or resolve them.
4. **Tile decode/palette rebuild churn:** weak explanations for the growth.
   Decode remains near20/call; the existing palette cache already limits table
   builds to about13. A second palette-cache rewrite has little evidence here.

## Exact-math shortcut and compiler control

The first shortcut checks `enabled_bits==active_bits && fixed_bits==0`, then
returns the existing exact `d35_add_half(color,subscreen)` result. It passes
output tests, but the counter-free ARM wrapper saves six general registers
versus the original's three. That extra pressure can consume the win.

The refined shortcut tests `active & ~(subdepth>1) == 0` before constructing the
general fixed/enabled masks. Its successful branch uses the existing half-add;
unsupported lane mixtures use the original general path. The counter-free ARM
wrapper retains the original three saved registers. This is compiler evidence
that the simplification exists, not a clock estimate. All4,041.901 observed
half-add rows meet the condition in this Confuser replay. The guard's cost on
other scenes and any memory/register effects must still be priced.

## Savings equation and predictions

All prices below are aligned **incremental A7 microseconds**, still unmeasured:

`S = 1772.066225 d_plain + 255.639073 d_half + 17.198675 d_clip_half
     + 32.331126 e + 4041.900662 f - b - u`

`d` prices removable tile-call preambles, excluding pixel rows. `e` prices the
removed renderer entry prefix. `f` is the shortcut's net credit per eligible
row, including its guards across the observed fast/fallback population. `b`
includes added target detection, row capture, prefix/band/clip and cache effects;
`u` covers other changed traversal/loop costs. Do not divide inclusive PPU CPU
by tile calls to manufacture `d`, or charge an entire row as removed work.

Sensitivity assumes one common `d`, zero entry credit and zero new costs:

| Assumed d,us | Assumed net f,us | Saving,ms | Remaining call,ms | Margin vs0.803ms /1.020ms requirements |
|---:|---:|---:|---:|---:|
|0.20|0|0.409|17.082|-0.394 /-0.611ms|
|0.30|0|0.613|16.878|-0.189 /-0.406ms|
|0.30|0.05|0.816|16.676|+0.013 /-0.204ms|
|0.40|0.05|1.020|16.471|+0.217 /~0ms|
|0.50|0.05|1.225|16.267|+0.422 /+0.205ms|

New costs subtract from every margin. Dispatch alone needs0.393us/removed call
for the basic timing floor, or0.499us for the native-rate proxy. Blend alone
needs0.199us/eligible row for the timing floor, or0.252us for the native proxy.
An0.05us blend saving yields0.202ms; it cannot be assumed from an instruction
count or an assumed666MHz clock.

An aligned Bio Blast transfer check offers a **heuristic**, not an independent
price: the actual A7 pair saves3.125..3.250ms across matching early effect calls
that remove6,443..6,589 tile calls. Scaling that whole-package net saving to
Confuser's2,028 removed calls suggests0.969..1.011ms. The Bio package also
changes palette caching and prefix logic that Confuser already has, and its
removed calls are plain rather than Confuser's mixed population. The transfer
can overpredict incremental savings. Using the whole-effect8,341 Bio average
against early-only A7 savings would also misalign the calculation.

At the observed0.803ms timing deficit, unchanged quota loses about35.4 reserve
frames/call. If that deficit persisted over302 calls, it would lose10,694 frames;
a2,823-frame starting reserve would last roughly80 calls (1.4s). This is a
falsifiable conditional prediction, not a reconstruction of Confuser's unknown
physical start time or actual complete reserve timeline. Buffers cannot sustain
that rate indefinitely.

## What is proved, and what remains before an A7 test

**10,800** actual ARM/QEMU pixel/native-PCM/geometry comparisons pass, with
normalized serialized state every30 calls: Confuser baseline/counting control
and each change, plus Bio Blast and intro/current-snapshot regressions.
The original clipping oracle passes1,048,576 states on both screens/every pixel.
Both blend forms pass the original scalar color/depth/flip/transparency/canary
oracle, including8,388,608 arithmetic comparisons per form. No QEMU timing or
cycle conversion is used. The shared old harness prints “Bio Blast” for its
A/A replay flag; verified snapshot/ROM init establish the actual Confuser case.

The leading candidate is **BG3 batching + the refined subscreen-only half-add
shortcut**. It is concrete and output-qualified offline, but fails the physical
installation gate on missing prices. Missing evidence is the incremental A7
dispatch mix, refined guard/math net cost, added BG3 capture/band/cache costs,
and complete effect/recovery cadence/reserve in the normal live-worker context.
The exact physical pre-Confuser state/input history and vendor stop semantics
remain missing. The derived replay now removes the earlier inability to execute
Confuser deterministically, without pretending it is that physical encounter.

If a future A7 comparison is authorized, predict saving above1.020ms plus
headroom, all drawings/native samples preserved, and stable cumulative reserve
across the complete302-call effect and recovery. A slower shortcut or continued
reserve erosion falsifies the proposed sufficiency. No automatic reprime,
frameskip, quota change or concealment of the PCM failure belongs to this claim.

## Reproduction and evidence

Existing private experiments remain under `build/confuser-private-v1/`; do not
rerun or overwrite them. Source preparations refuse existing destinations.
Analysis is reproducible with `python build/analyze-confuser-offline.py`.
Fresh preparation/control/count/equivalence/oracle modes are in
[preparation](../build/prepare-confuser-offline.py),
[runner](../build/run-confuser-offline.sh),
[checks](../build/check-confuser-offline.py),
[blend variants](../build/prepare-confuser-blend.py) and
[compiler inspection](../build/inspect-confuser-kernels.py).
Public counts/proofs are under `evidence/2026-10-11/confuser-offline/`.
ROM, screenshots, snapshots/SRAM, full traces and binaries stay private.
