# ROM-free pressure test return — 2026-10-15

The device completed all 70 phases without forced termination. Fifty non-audio
cells pass end to end. Five audio cells complete all production with valid
running pointers and substantial reserve, then fail because the new controller
finishes an already-drained stream. Fifteen heavy audio cells fail during
production. This is useful cost evidence, not a demonstrated hardware ceiling.

Strict archive `device-evidence/a7-pair-before-20261016T034259Z` is FAT-clean.
All archived input bytes and the installed executable/wrapper/qualification/
dispatcher match their receipts. Against the pre-install archive, 8,272 prior
files remain exact; the only changes are the authorized dispatcher, consumed
`last-launch-lab` marker and stock swapfile. ROM and patched normal init also
verify directly on I:. Both one-shots are consumed, no firmware trigger remains,
and the next boot selects stock with the UART correction. No card writes or
rearm occurred during collection.

The [source-bound report](../evidence/2026-10-15/render-pressure1/return.json)
records all 70 cells and hashes all 376 raw run files. The original reporter
independently returns 50 accepted cells. Full PCM histories are retained from
entry zero. Wrapper `lab_exit=1` reflects the 20 issues; supervisor `forced=0`,
`reaped=1`, `raw_status=256` establishes a normal child exit with status 1.

## Rendering costs

Warm median main-thread CPU milliseconds per generated frame, first eight and
final validation-copy frame excluded:

| Synthetic scene | Scalar control | Project NEON | Cached colors |
| --- | ---: | ---: | ---: |
| Static, 256×224, two layers | 5.678 | 3.786 | 3.814 |
| Dense math, 256×224, eight layers | 32.522 | 20.317 | 20.478 |
| Occluded, 256×224, eight layers | 19.008 | 16.785 | 16.787 |
| Window/palette churn, 256×224 | 11.156 | 7.330 | 8.356 |
| High resolution, 512×448 | 45.005 | 30.944 | 32.801 |
| Native output, 640×480 | 32.513 | 21.822 | 21.939 |

The project NEON route is 11.7–37.5% cheaper than this deliberately scalar
correctness control. Those kernels already exist in the core; this is **not**
a newly obtained emulator speedup. Costs include shared deterministic command
preparation, depth/subscreen setup and row work. They do not price the entire
PPU or CPU/APU. The dense workload alone exceeds the 16.688153 ms production
quantum; it needs about 17.9% lower main CPU cost before other costs are paid.

Cached colors do not win any of the six CPU-only cells. They are effectively
equal for occluded rows, about 0.5–0.8% more expensive in three repeated cases,
6.0% more expensive at high resolution and 14.0% more expensive with churn.
This rejects the tested cached-color implementation as a general improvement
for these streams. It does not reject every possible tile/line cache.

All 50 non-audio phases finish without a recorded oracle/guard/accounting
failure. This includes final pixel/depth equivalence for the rendering cells.
It does not establish optical panel delivery or DAC fidelity.

## Display, memory and overlap

Prebuilt display completes 180 frames in about 2.99–3.02 seconds at each of
256×224, 512×448 and 640×480: approximately 60 fps. Ordinary output size alone
does not explain the heavy renderer's deficit in this test.

Dense NEON, audio off, 180 complete frames:

| Output route | Queued display | Serial display |
| --- | ---: | ---: |
| Heap render plus copy | 44.17 fps | 30.06 fps |
| Direct chunk render | 45.65 fps | 30.04 fps |

Serial joins leave the expensive producer and display poorly overlapped; the
roughly 33.3 ms serial cadence is consistent with missing alternate display
opportunities, not independent proof of an exact vblank mechanism. Queuing is
already in the runtime. Do not add scale/flip wall durations to producer CPU:
the operations overlap and the flip includes waiting.

Direct output reduces queued dense phase-average main CPU from 21.480 to
20.799 ms/frame (0.681 ms), and total wall service from 22.640 to 21.904
ms/frame. This is a measured synthetic opportunity, insufficient by itself to
reach 16.688 ms and not yet a full-core installation candidate. Direct chunk
render also changes memory mappings; it must retain source ownership and
full-core correctness. Memory-only copy medians are 0.408/0.375 ms at 256×224,
1.948/1.925 ms at 512×448 and 2.609/2.582 ms at 640×480 for heap/chunk targets.
These are payload-copy times, not total DRAM bandwidth or a cache-policy proof.

## Audio: distinguish production from test cleanup

Audio-only produces all 180 quanta at negotiated 44,100 Hz. Every observed
running pointer identity remains valid, with minimum production reserve 2,718
frames (61.63 ms). Four light static-render controls also complete 180 quanta,
180 submitted/scaled/flipped frames and valid production pointers; minimum
reserve is 2,590 frames (58.73 ms). All 135,293 enqueued samples per channel
are accepted in each of those five cells, with no software remainder/clear or
worker audio error. These are bounded production successes, not end-to-end
audio passes or proof of audible output.

The new test controller has a concrete double-finish bug:

1. `audio_pipe_stop(1)` joins `audio-owner.c`, whose worker calls
   `board_audio_finish()` and completes `pcm_finish()`.
2. The controller then calls `board_audio_finish()` again.
3. The second finish attempts `SYNC_AVAIL_MIN` on the already SETUP stream and
   fails with errno 77. In phase 042 the first `DRAIN_REQUEST` is at
   44.098500 s, after production ends at 44.097414 s; the subsequent
   `SYNC_AVAIL_MIN` failure is at 44.181163 s.

That bug is ours and must be corrected and qualified before any repeat. It
does not invalidate earlier CPU-only costs, and it must not be attributed to
the vendor driver. Preserve the frozen controller and support sources that
produced this run; no runtime correction has been installed during this review.

All eight dense render+audio cells fail during production after 3–9 completed
quanta. Four steady-load cells fail after 6/4/3/2 quanta as requested extra CPU
increases from 4 to 16 ms/frame. The three nominal 24/48/80 ms burst cells all
fail after 12 quanta, **before their first frame-29 burst**. There is no burst
tolerance result. Failed prefixes include the known application-pointer/count
divergence and SETUP/errno77 transition; reserve minima are reported only before
the first invalid running pointer. Zero reported XRUNs does not mean continuous
playback. Submitted drawings can exceed `completed` by one when audio fails
after submission; those cells remain failed, rather than calling that a lost
or duplicated drawing without further evidence.

The detailed/aggregate light-render controls consume respectively 4.109/4.085
and 4.052/4.079 phase-average main CPU ms/frame in forward/reverse pairs.
The roughly 24–27 microsecond differences do not explain a multi-millisecond
renderer deficit. This is one short ordered run, with inherited board/PCM
instrumentation present in both modes; no general tracing-cost or significance
claim is justified.

## Device context and next work

Across first/last phase snapshots, IRQ19 advances 6,747 in 93.206 seconds:
72.39/sec. The permanent correction remains attached with fault/bypass/full
counters zero. Wrapper totals reconcile 6,865 intercepted calls as 6,316 added
services plus 549 fallbacks, including 6,314 writes and two empty stops.
RX/break rises by 25; frame/parity/overrun remain zero. The clock source is
`arch_sys_counter`; the requested cpufreq sysfs file is absent. This run does
not establish CPU frequency, thermal limits or complete driver efficiency.

The next diagnostic change should remove the extra finish and move load sweeps
onto the known light workload, so steady and burst capacity can actually be
measured. General optimization work should price the heavy row/depth/math
path in the real core, with direct-output reuse as a smaller measured lead.
The tested color cache has no case for installation. No new core candidate,
driver change, firmware update or card rearm follows from this review.
