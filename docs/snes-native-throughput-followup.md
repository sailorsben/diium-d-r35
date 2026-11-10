# D-R35 Star Fox throughput and native audio

The combined core gets through 13 gameplay frames on the handheld before
the audio driver drops the stream. Those 13 steps average **20.798 ms**
against the **16.688 ms** NTSC deadline. The same tick IDs in the core-only
A7 replay average **18.332 ms** wall time after subtracting the callback
oracle. The **2.466 ms** difference includes all changes between the two
paths and the two boots. Across all 1,200 calls the core-only trace averages
**15.357 ms**, leaving just **1.331 ms** per tick for additional critical-path
work. The trace cannot price the entire device path from the short prefix.
[Physical return](snes-superfx-native-test.md#physical-return).

## Measured candidates

Train GCC on the actual Cortex-A7 build and relink the same source with
profile-guided optimization. The profile uses Mario, Metroid, and Star Fox
with cold replay. The resulting ARM code section drops from **651,556 to
472,148 bytes** (27.5%). F-Zero and Ranger are held out of training.
Each timing pair alternates call order on one host CPU lane.

| Game | Mean ARM replay CPU saved | Adjacent identical RGB565 frames out of 1,200 |
| --- | ---: | ---: |
| Mario, PAL | 7.20% | 338 |
| Metroid | 11.69% | 501 |
| F-Zero | 6.31% | 0 |
| Star Fox | 6.59–7.94% | 801 |
| Rendering Ranger R2 | 3.62% | 0 |

The output-checked Star Fox pair saves 6.59% after subtracting callback
verification CPU. The separate timing-only pair saves 7.94%. Its p95
improves 5.60%. All five 1,200-call exact pixel, PCM, sample-count and
callback-layout checks pass. Independent FFVI Meteor and Quasar and
Rendering Ranger cold-boot checks pass 4,800 calls with matched normalized
state. The identical-ELF timing control differs by 0.51%. The final core
imports GLIBC 2.4 and 2.7 symbols. These are ARM/QEMU measurements.
The handheld gain is pending.

Moving the Super FX instruction budget into a local variable, with and
without inlining five opcodes, saves at most 1% in the paired Star Fox
means. Packing the Gaussian coefficient table gives mixed results.
The NEON interpolation variant retains all four taps, signed shifts,
the intermediate 16-bit wrap and final saturation. It preserves the
exact audio and loses about 1.6% in both Star Fox pairs. The combined
interpreter and DSP experiment saves about 1% in Star Fox, with
larger gains in the other scenes. The profile-guided build ranks first.

## Stop sending identical pixels through the scaler

The returned Star Fox path copies 114,688 bytes per submitted frame
because it renders into a 1,024-byte pitch and the scaler consumes
packed 512-byte rows. The opening averages **0.863 ms** of copy wall
time and **0.767 ms** of display worker CPU per submitted picture.
These values bracket different work and clocks, with possible overlap.

The compact render guard protects a real ownership issue. Lifting the
guard appears exact for 1,200 calls when the renderer keeps receiving
the same address. With rotating targets and periodic fallback it corrupts
300 calls. With poisoned targets it corrupts 398 calls. In the first
three failing calls a byte-for-byte comparison finds **all 57,344 visible
pixels still contain the supplied poison** even though the PPU profiler
records work on those calls. The frame callback can return a target whose
visible pixels the renderer left untouched. A scratch surface with
last-frame contents concealed this defect. Retain the full-layout guard.

The working prototype pins the latest queued chunk surface and compares
visible RGB565 bytes. It leaves the previous picture on screen only after
full equality, with early rejection for obvious changes. A changed
picture is still copied if necessary, queued and flipped in order.
Emulation, rendering and PCM continue on every tick. The board worker
fixture proves 800 reuses and 400 ordered flips across 1,200 submissions
with both direct and pitched buffers. Its timing CSV records cumulative
comparison wall time and exact reuses separately from policy skips.
The five real replays give the
reuse counts in the table, with every output checked. Star Fox avoids
801 repacks and scaler/flip jobs in the replay, or 66.75% of the jobs.
Comparison cost averages 0.093 ms per Star Fox callback in QEMU.
The returned chunk-memory comparison cost and physical panel behavior
are still unmeasured.

## Audio reserve is a second deadline

The reserve model uses every A7 core-only tick and the exact generated
source sample counts. At 44.1 kHz, continuous 178/245 resampling of the
641,626 source frames yields 883,136 frames. Demand advances on the
sink clock. The model publishes each tick's quota at its end and tests
both initial deficit and refill-limited drawdown. It reserves two
128-frame periods as a margin for the observed vendor fill threshold.
This is a sensitivity model for the whole replay. Sub-tick arrivals,
PCM acceptance and physical scaler overlap remain to be measured.

| Assumed additional wall time per tick | Reuse assumption | Uniform core wall saving required to fit 2,823-frame prime |
| --- | --- | ---: |
| 1.0 ms | All frames submitted | 3.88% |
| 1.5 ms | All frames submitted | 6.87% |
| 1.5 ms | Save 1.0 ms on each repeated frame, compare in 0.1 ms | 3.50% |
| 2.466 ms | All frames submitted | 12.64% |
| 2.466 ms | Save 1.0 ms on each repeated frame, compare in 0.1 ms | 9.28% |
| 2.466 ms | Save 1.63 ms on each repeated frame, compare in 0.1 ms | 6.78% |

With 1.0 ms additional work and no optimization, the average fits at
16.357 ms and the initial deficit peaks at **9,410 frames**. A later
surplus repays it, but the current stream would run out well before
then. In the 2.466 ms scenario, an assumed 8% core saving and 1.0 ms
saved per repeated frame average 16.027 ms and still draw down about
3,656 frames. The 1.63 ms reuse scenario reduces that to 2,031 frames.
The larger reuse figure assumes the returned copy and worker costs
both clear the critical path, so measure it independently.

## Next handheld test

Measure the profile-guided core against the exact returned ELF in the
existing A7 core-only pair. Price the display change separately with
the same real LCD and the same core, accounting for CPU, copy, compared
frames and actual flips. The isolated controller's
`D35_MEASURE_DISPLAY=1` mode runs the normal 44.1 kHz conversion and
software audio owner with a discard sink. It keeps the physical display
path and can capture all 1,200 ticks through the PCM failure interval.
Set `D35_IDENTICAL_VIDEO_REUSE=0` and `1` for the display pair. This mode
is silent and records `native_pcm=0`. Its supervised ARM fixture passes
the frozen video and source PCM checks and accounts for all 883,136
converted frames.

Use real PCM for the subsequent bounded playback check with every
frame accounted for, exact sample counts, no vendor-added periods, no
DROP and full reserve recovery. Preserve the prior negotiation and prime
for this comparison.

Average break-even is `A7 core wall + native overhead − measured core
saving − measured repeat savings + comparison cost <= 16.688 ms`.
The same measured arrival schedule must fit the refill-limited reserve.
The prototypes are compiled and qualified off-card. Physical savings
and the final reserve are pending.

## Reproduce

Build isolated experiments with `build/build-snes-throughput.sh`, the
profile-guided core with `build/build-snes-core-pgo.sh`, and the timed
pairs with `build/run-snes-throughput-pair.py --core-hotpaths` and
`--core-pgo`. Run the strict held-out fixture with
`build/check-snes-scheduler-state.py`. The `cold-rotate` and `cold-poison`
modes of the replay qualify output ownership. Build the optional
`D35_DISPLAY_REUSE_PROBE` replay to price byte comparisons, and prepare
the isolated board candidate with `build/prepare-snes-native-reuse.py`
and `build/check-snes-native-reuse.sh`. Recompute the sensitivity analysis
from both physical CSVs and the frozen expected-output fixture using
`build/report-snes-native-reserve.py`.

[Timing and correctness evidence](../evidence/2026-11-10/snes-throughput/native-followup.json) ·
[Full reserve sensitivity](../evidence/2026-11-10/snes-throughput/native-reserve-sensitivity.json).
