# Shared renderer fix and ability2 regression subset — 2026-10-13

Ability1 failed24 cases across11 observed effects. The recorded failure is
native audio publication entering SETUP/errno77, not a retained C fault. Holy and
Meteor's final ordinary calls exceed the16.688ms cycle-derived deadline even in
main-thread CPU alone. Correct native quota and complete software PCM accounting
rule out simply generating too little audio. The precise vendor transition from
deadline pressure/pointer bias to SETUP remains unresolved. See the
[returned measurements](snes-ability-suite-return.md).

The generic renderer correction batches Mode1 Window2 state for BG1/BG2/BG3
simultaneously, ignores absent BG4, and defers edge changes when no rendered layer
uses Window2. Each row retains its own inside/main/sub/target masks. Other PPU
changes still flush. Window1 combinations, OBJ/color windows, mosaic and other
unsupported modes retain the original path. This promotes the previously
offline-qualified generalized algorithm into a separate counter-free test core;
it is not a ROM patch or an effect-name switch.

The design rule is to remove repeated setup only when per-row state preserves
every output dependency. Pixel, depth, palette, fixed-color and timing semantics
still have to agree with the original renderer. A changed register does not
necessarily change any visible layer; conversely, varying fixed color cannot
simply be ignored to make an expensive animation cheap.

## Comparable upstream patterns

[RetroArch issue5453](https://github.com/libretro/RetroArch/issues/5453) reports
FF6 frame drops/audio stutter on Snes9x2005/Plus and a slower2010 core on another
ARM handheld. The retrievable issue body does not establish a transferable fix
or the D-R35's SETUP/errno77 cause. An emulator label and CPU MHz do not predict
the complete device deadline.

[Libretro's Plus documentation](https://docs.libretro.com/library/snes9x_2005_plus/)
identifies its Blargg APU and marks emulated slowdown/flicker options as unsafe.
Changing emulated CPU cycles addresses game-side slowdown and changes semantics;
it does not remove our demonstrated host rendering work.

The current [2010 compositor source](https://github.com/libretro/snes9x2010/blob/master/src/tile.c)
uses specialized NEON paths with scalar fallbacks and an exact-output requirement.
It also uses a different subscreen-depth representation (bit0x20 rather than
our pinned core's threshold above1) and separate fixed/full/half arithmetic.
The transferable pattern is dependency-aware specialization plus an independent
oracle; copying its kernels without reconciling those semantics is not a fix.
This comparison describes retrieved current source, not an assertion about every
historical2010 build.

## Matched failed-state work and prediction

Replay the actual returned snapshots, original ROM and input sequences. Compare
original1.19 against separate current/general inward-counter cores for1,200
calls each in11 contexts. Align to the16 recorded ordinary calls immediately
before each terminal A7 publication call. No substitute animation, different
state, QEMU timing or assumed frequency enters this calculation.

The four affected tails remove renderer/tile setup while retaining the same
NEON row attempts, tile decodes and palette builds. Holy changes112 renderer
entries to28; Meteor110 to28; Ultima113.5 to28; GrandTrain138.875 to28.
Their reduced tile calls do not mean skipped pixels: exact framebuffer/PCM/state
comparisons pass. The following table is populated from the aligned receipts.

| Effect | Required saving in matched tail (ms) | Removed full / clipped calls | Removed entries | Optimistic equal dispatch break-even (us) |
|---|---:|---:|---:|---:|
| HOLY | 2.877 | 4320.000 / 0.000 | 84.000 | 0.666 |
| METEOR | 2.992 | 2148.750 / 0.000 | 82.000 | 1.393 |
| ULTIMA | 1.457 | 1367.938 / 84.125 | 85.500 | 1.003 |
| MELTDOWN | 0.818 | 0 / 0 | 0 | No removed work |
| SLOW_2 | 0.284 | 0 / 0 | 0 | No removed work |
| SIREN | 2.001 | 0 / 0 | 0 | No removed work |
| BAHAMUT | 0.507 | 0 / 0 | 0 | No removed work |
| CARBUNKL | 0.978 | 0 / 0 | 0 | No removed work |
| QUASAR | 0.984 | 0 / 0 | 0 | No removed work |
| GRANDTRAIN | 2.965 | 2895.000 / 0.000 | 110.875 | 1.024 |
| LULLABY | 2.051 | 0 / 0 | 0 | No removed work |

Let d_full/d_clip be removable dispatch/preamble cost per corresponding tile
call, e removable cost per renderer entry, b added mask/cache/band work and u
other incremental work. All prices must ultimately be measured A7 microseconds.
For example, Holy requires `4320d_full +84e -b-u >=2876.596us`; Meteor requires
`2148.75d_full +82e -b-u >=2992.408us`. Do not divide inclusive PPU time by counts
to manufacture these prices.

As sensitivity only, set d_full=d_clip=0.4us, e=2.179us (an older partial warm
setup price), and b=u=0. Predicted savings are1.911ms Holy,1.038ms Meteor,
0.767ms Ultima and1.400ms GrandTrain. All remain below their measured tail
deficits. These optimistic assumptions therefore still fail the gate; they are
not measured candidate prices. The published prediction receipt computes
`P_new=735.94752*1e6/(T_tail_us-S_us)` and `44100-P_new` for each case.

Seven effects have zero removed work in these aligned counters: Meltdown,
Slow2, Siren, Bahamut, Carbunkl, Quasar and Lullaby. No deficit closure is predicted
from this mechanism. Siren/Carbunkl/Lullaby show approximately158/164/164 real
fixed-color flushes per call and162/168/168 renderer entries, versus23/28 in
ordinary-window cases. This supports a second fragmentation mechanism; it
does not price it. Most of their17,000–18,000 tile calls are not fresh tile
decodes. Meltdown/Slow2/Bahamut/Quasar already have28 entries but many row attempts:
their next useful target is row/depth/color composition, not more window deferral.

An intelligent next design for fixed-color fragmentation is captured per-row
fixed color with every tile/OBJ/backdrop consumer honoring it. It needs an exact
output oracle and prices for added lookup/materialization/cache work before it
can replace real flushes. A prior unused-fixed-color hypothesis saved zero work
in19 cases; it remains rejected. This test does not claim that larger change.
The work logger's $2126/$2127 fields are explicitly Window1; no new Window2
flush census is claimed from those zero columns.

## Qualification and physical test

The separate core is798,312 bytes, CRC4eef8dba, SHA256
`53c6d1f6c0253cb1c6e7b81ba22192f3739fa3f9605837c64691085918e1106b`.
The runtime reports1.19-ability2. All18 counter-free candidate contexts pass
21,600 exact graphics/PCM/periodic-state comparisons against original1.19.
The22 inward-census comparisons add26,400 calls. All18 actual new-runner cases
complete their full bounds offline, observe requested properties, select the
five correct Rage IDs and maintain lossless PCM accounting. Header-only state
identity migrations preserve all18 emulated payloads. Native consuming-provider
fault/retry/drain/deficit and actual one-shot/splash/wrapper checks pass.
Offline durations are not A7 performance evidence or physical acceptance.

The18 cases cover all11 observed failures, five of the255 Rage entries, their
normal-command equivalents, and Terrato/Bio Blast/Confuser controls. One fixture
per selected command retains the returned valid targeting and deterministic
inputs. This is about6.008 nominal minutes before reset/flush overhead; see
[boot instructions and order](snes-ability-regression-test.txt).

The physical run retains audio and display workers, uses the kernel scheduling
clock and thread CPU clock, warms through the actual pre-effect gameplay, checks
sysfs frequency and attempts the existing exposed-frequency control. Previous
device runs exposed no usable frequency; do not assume666MHz. The included RAM
observer/coarse-clock costs stay included. Logs accumulate in RAM during casts,
then flush after audio join/display idle. Native faults remain failures; the
next fixture opens a fresh independent epoch. No hidden recovery, reprime,
frameskip, reduced quota or live SD tracing is added.

Falsifiable acceptance: all18 cases reach1,200 full drawings with requested
animations, zero native faults and exact software PCM accounting. In each
matched expensive tail, measure net step/CPU savings against the archived
baseline; sustained steps must fit16.688ms with headroom. Require complete
effect/recovery cumulative reserve repayment where pointer accounting is valid.
Pointer divergence or a PCM stop rejects physical continuity even if average
FPS is60. If the seven unchanged-work effects improve, investigate actual path,
contention, frequency and run variance before attributing it to this algorithm.

The production installation gate remains **NOT MET**: aligned e/d/b/u prices,
candidate reserve curve and physical deficit closure are absent. The user's
request authorizes this isolated experimental subset for measurement and visual
qualification. It does not promote the candidate to production. Archive and
hash every returned file before staging; guard serial/FAT/boot hashes, preserve
production adapters/progress, and use a fresh folder/one-shot identity.

## Current installation receipt

The fresh pre-write archive is `a7-pair-before-20261013T071014Z`, containing4,605
hash-verified returned files with clean FAT/serial and no armed marker. The
separate target is `retro/snes-ability2`; only the existing one-shot dispatch and
its marker may change. The [installation receipt](../evidence/2026-10-13/ability-regression/installation.json)
records the final guarded staging outcome. The README and current handoff report
arming only after successful card readback. This is an experimental measurement
package, not a versioned production release.
