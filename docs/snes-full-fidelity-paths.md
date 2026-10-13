# Full-frame optimization paths and the headroom requirement — 2026-10-13

Every frame is required. Ben explicitly rejects adaptive frame skipping unless
there is proof that full-frame execution is physically impossible on this
hardware. No such proof exists. Failed implementations, another core's speed,
QEMU duration, nominal MHz, or a finite spell sweep cannot establish it.
No frame skipping, sample removal, ROM patch, changed guest clocks, installation
or rearm is introduced here. The measured ability3 cache remains rejected;
ability2 is the source baseline. All new executables are separately owned offline
experiments. The card and qualified historical artifacts are untouched.

## Three isolated mechanisms

**Capture fixed color per scanline, then batch rendering.** Genuine `$2132`
changes currently force repeated renderer setup and tile preambles. Capture
the effective RGB565 operand at `RenderLine`, alongside the existing line state.
Ordered prefix validity makes deferral constant-time. Full NEON tiles, scalar
full/clipped tiles, subscreen clearing and backdrop processing select the captured
operand for the destination row. Other register changes retain their original
flushes. This does not cache composed output or ignore color changes.

The first guarded envelope is Mode 1, ordinary width/height, no mosaic, and the
known 256/512-pixel strides. Unsupported modes retain original flushes. Mode 7,
hires and mosaic receive no invented saving. The helper uses 512 bytes of color
rows and 1,028 bytes of prefix data plus a few scalar fields; memory size does not
price cache traffic or CPU work. Capturing colors, checking eligibility, querying
prefixes and selecting row operands all have added costs.

**Simplify true-subscreen composition.** When every active lane has depth above 1,
full add/subtract and half subtract can operate directly on subscreen pixels.
They need no fixed-color selection, duplicate enabled/fixed classification or
final enable-mask selection. Mixed/fixed/disabled lanes retain the original
compositor. The already-qualified half-add shortcut stays intact. Offline tails
expose 4,166 eligible full-add rows in Holy, 4,410 in Meltdown, 4,395 in Quasar and
3,262.5 in Bahamut. Meteor exposes only 274.8125; this is not its dominant path.
The new subtract shortcuts have zero eligible rows in these eighteen contexts,
so their extra predicates have no counted benefit here. Do not ship them merely
because their output is correct.

**Remove provably unused DSP interpolation.** The pinned interpolation function
only reads sample history and the Gaussian table. With envelope zero its result
is multiplied by zero; with noise enabled it is replaced by noise before scaling.
Skip those calculations while retaining every voice clock, BRR decode, envelope,
pitch, timer, KON/KOFF, echo and visible register/state update. Generate exactly
the original samples. This is not disabling voices or making the APU less accurate.

Primary-source review found the comparable zero-envelope optimization in
[Snes9x-Z's DSP](https://github.com/andrezaiats/snes9x-Z/blob/c3c6710f9efcfec4c2c513baeb602cf17dd7d909/apu/bapu/dsp/SPC_DSP.cpp).
Its [README](https://github.com/andrezaiats/snes9x-Z#reproducing-this-yourself)
reports separate single-thread gains on x86-64/arm64 and warns that its threaded
renderer needs a spare core. Those are that project's claims against modern
Snes9x, not D-R35 measurements. A secondary PPU thread cannot supply another CPU
on this single-core A7. Its interpolation-mode dispatch, timer batching and ring
buffer changes do not automatically apply to our older Blargg C implementation.
We adapted the dead-calculation mechanism and independently qualify our outputs.

## Corrections and independent coverage

The fixed-row integration initially selected the scalar clipped row from the
tile's base offset. A tile can begin at X=-1..-7, preceding pixel 0 or the current
row. Source review found that counterexample despite eighteen exact battle
replays and 406 bounded animation screens passing. The corrected caller selects
`Offset + StartPixel`, its first visible destination. At row 0 the old unsigned
base could index far beyond the color-row array. No affected build was installed.

The new oracle executes the actual original scalar tile functions, one original
flush per row, against the candidate's eight-row batches. All 16,128 fixtures
compare pixel/depth/canary receipts, including negative X, row 0, the right edge,
eight distinct colors, every flip, all seven math modes, 2/4bpp and both strides.
It rejects the preserved old integration with an ARM signal 11. This is a local
candidate counterexample, not a reclassification of the device's PCM failures.
The helper also passes 22,118,400 independent packing/row/offset checks and
unsupported-mode, gap, repeat, invalid-prefix, reset and non-math cleanup guards.

An earlier construction expected seven color-math row loops; source contains six.
The separate helper fixture initially omitted the brightness-table allocation,
then incorrectly assumed `BUILD_PIXEL` replicates green into bit 5. Pinned source
leaves that bit clear. The failed construction/oracle logs remain private; both
fixture errors were corrected before the final independent checks. Upstream
large-pixel switch fallthrough warnings are acknowledged in the standalone
tile fixture, rather than changing unrelated production code.

Each of the three final isolated cores passes eighteen original-ROM command
contexts for 1,200 calls, both counter-free and counted: 129,600 new candidate
comparison calls in total. Visible-pixel and PCM CRC/count/geometry agree each
call; normalized logical serialized state agrees every 30 calls. Counted command
hooks additionally verify animation initialization, table access and deinitialization.
Shared unchanged baseline census results are reused where available.
The final fixed-row core additionally passes 406 animation records for 600 calls
each, with initialization/table identity checks: 243,600 comparisons. These
screens apply a 14-byte animation overlay in both cores to one Bio Blast battle
context. They are not 406 natural commands or a guarantee of animation completion.
All new correctness evidence is offline; none supplies A7 timing.

The [receipts](../evidence/2026-10-13/full-fidelity-paths/prediction.json)
retain exact core/proof hashes, per-case populations and physical-baseline frame
indices. ROM, states, SRAM, PCM, vendor dependencies and full traces stay private.

## Calculated targets, not invented prices

Use the 16 calls immediately before the final archived ability2 record in every
case. Failed cases exclude the terminal call; completed controls also omit their
final ordinary call to retain the same sampling rule. Work populations are aligned
to those exact frame indices. Main CPU and total step are direct physical clocks;
observer and admission costs stay included. Frequency was unexposed. The old
ability3 measurements cannot price these different paths.

<!-- BEGIN MATCHED TARGETS -->
Representative aligned ability2 tails; milliseconds are physical baseline
measurements, counts are exact offline observations of those same frames.

| Context | Baseline step ms | Removed full/clipped calls | Saving to deadline ms | Saving to 20% margin ms | Equal dispatch floor us, deadline/margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| Holy | 17.661 | 1,612 / 0 | 0.972 | 4.310 | 0.603 / 2.674 |
| Meteor | 18.466 | 1,612 / 0 | 1.778 | 5.116 | 1.103 / 3.173 |
| Meltdown | 17.559 | 1,612 / 0 | 0.871 | 4.208 | 0.540 / 2.611 |
| Siren | 18.523 | 8,350.375 / 207 | 1.835 | 5.173 | 0.214 / 0.604 |
| Bahamut | 17.089 | 1,612 / 0 | 0.401 | 3.739 | 0.249 / 2.319 |
| Carbunkl | 17.573 | 12,292 / 240 | 0.885 | 4.222 | 0.071 / 0.337 |
| Quasar | 17.549 | 1,612 / 0 | 0.861 | 4.198 | 0.534 / 2.605 |
| Lullaby Rage | 18.705 | 10,651.0625 / 109.375 | 2.017 | 5.354 | 0.187 / 0.498 |
| Bio Blast | 16.610 | 1,612 / 0 | 0 | 3.259 | 0 / 2.022 |
| Confuser | 16.476 | 1,612 / 0 | 0 | 3.126 | 0 / 1.939 |
<!-- END MATCHED TARGETS -->

Rank the mechanisms by actual exposure. Fixed-color fragmentation is the
strongest setup-removal target in Siren, Carbunkl and Lullaby. Full-add subscreen
composition is a substantial separate target in Holy, Meltdown, Quasar and
Bahamut. Meteor has only 275 eligible new full-add rows and the ordinary 1,612
removable tile calls: the visible work left inside those tiles remains the
harder target. At the hypothetical 0.5 us dispatch price, e=b=0, fixed batching
saves only 0.806 ms there against its 1.778 ms deficit. This assumption cannot
declare either a pass or a hardware limit.

DSP zero-envelope calls per aligned tail average 750 in Meteor, 1,372 in Holy,
1,544 in Siren, 1,716 in Carbunkl and 2,593 in Bio Blast. Noise-replacement
opportunities are zero in these tails. These counts support a shared mechanism,
but its new branch also touches voices whose interpolation is still needed;
the net saving must include that cost.

Let d_full/d_clip be removable tile dispatch/preamble prices excluding pixel
work, e removable entry setup excluding work inside its entries, and b all added
capture/query/row-selection/cache/register/traversal costs, in aligned A7 us.
Do not count the same preamble in both d and e.

`S_fixed = delta_full*d_full + delta_clip*d_clip + delta_entries*e - b`

`S_sub = N_add*k_add + N_sub*k_sub + N_half_sub*k_half_sub - extra_predicate_cost - other_added_costs`

`S_dsp = N_zero*g_zero + N_noise*g_noise - extra_branch_cost - other_added_costs`

All prices remain unmeasured. The floor assuming equal tile prices and e=b=0
is a break-even threshold, not a unit-cost estimate. Counts cannot be divided
into inclusive PPU/APU time to manufacture these prices. The receipt's 0.1/0.25/
0.5 us sensitivities are explicitly hypothetical. Meteor/Holy need additional
pixel or DSP savings if fixed-row batching does not cross their measured floor.
There is no reason to sum isolated savings without qualifying interactions in
the eventual combined core.

The proposed 20% capacity margin targets13.350524 ms of active service per nominal
16.6881545 ms call, leaving3.337631 ms free. Current expensive-step thresholds are
conservative because all observed admission cost remains included. Healthy
intentional pacing waits must be identified separately: a paced16.688 ms step is
not proof of zero spare capacity. Headroom must be demonstrated over the actual
heavy workload and live peripheral service, not inferred from pooled FPS or
cheap control frames. The tail-mean target is not a worst-case certificate.

For measured net saving S, the conditional local production proxy is
`735.947520*1e6/(T_before_us-S)` against 44,100 output frames/sec. It is not a
physical DAC measurement. Demand full effect/recovery coverage, correct cumulative
reserve accounting and repayment, every frame, and repeated casts with margin.

## Missing evidence and the next decision

Directly price the removed blank/visible, plain/math, full/clipped preamble
populations; the added fixed-color capture, prefix and row-selection paths;
the existing/new compositor shapes; and silent/noise/ordinary DSP branches.
Use kernel scheduling/thread CPU clocks, warm caches and live audio/display
workers. Record frequency availability per run; never assume 666MHz. Timer/loop/
instrumentation costs stay included. Sparse sampling or owned batches must avoid
the prior dense observer's millisecond-scale perturbation. Then measure net
combined behavior and tail distributions; instrumentation itself cannot be
subtracted into a passing verdict.

Separately resolve native SETUP/errno77 and the 384-frame terminal pointer excess.
[ALSA's recovery contract](https://www.alsa-project.org/alsa-doc/alsa-lib/group___p_c_m.html)
handles EINTR/EPIPE/ESTRPIPE, not arbitrary EBADFD. Generic underrun recovery is
not a demonstrated repair for this vendor transition. No recovery, mute or larger
buffer is added as a substitute for throughput and valid pointer accounting.

Remaining coverage includes the complete 400 normal-command contexts on the new
cores, previously unobserved Rage spells, multi-target/reflection and enemy/party
variations, repeated casting/recovery, field/event states, and unsupported PPU
modes. Adversarial raster/visibility fixtures and a measured worst-work envelope
are necessary before saying no plausible spell can fail. Visibility-first
composition or CPU/SPC/DSP specialization remain architectural options if the
priced paths leave a deficit; their benefit is not claimed here.

The production gate is **NOT MET**. The physical saving and spare-capacity verdict
are unknown. No measured lower bound proves that every correct implementation
must exceed this A7's capacity. Full frames remain the requirement; failure of
these candidates would call for another mechanism, not permission to skip frames.

A hardware-impossibility claim would need a defensible lower bound on the work
every correct implementation must perform, compared with measured sustainable
hardware capacity under the actual audio/display load. Profiling one function,
exhausting a list of attempted optimizations or failing another finite test is
not that proof. This investigation has not established such a lower bound.
