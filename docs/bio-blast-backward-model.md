# Bio Blast: backward model from C paths and archived failures

**2026-10-11 follow-up:** [new isolated QEMU hypotheses](bio-blast-clever-renderer.md)
resolve the missing tile-call population:8,341 plain dispatches are removed per
effect frame. Palette/direct-NEON and fast validity variants pass output checks.
The ranking/unknowns below preserve the pre-experiment boundary; the new report
supersedes entry-only shelving and supplies a revised, still-unpriced cost gate.

2026-10-11. Analysis only: no device access, executable build, installation or
rearm. Reproduce with `python build/analyze-bio-backward.py`. The script reads
immutable work censuses and three archived A7 control CSVs, asserts alignment of
entry and total color-request counts, records input/source hashes, and writes
[the calculations](bio-backward-analysis.json). No QEMU timing is used.

The strongest explanation is increasing visible-row processing and associated
compositor/cache traffic, with raster fragmentation potentially increasing
dispatch/preamble work. Scalar clipping is real but smaller in population.
Tile decoding and palette materialization alone are weak explanations.
These are ranked mechanisms, not identified exclusive CPU shares.

## The actual C chain

Window writes force `S9xUpdateScreen` to finish pending rows. In `gfx.c`,
`DrawBackground` batches adjacent lines only while their scroll offsets agree,
within an eight-row tile boundary and the current flush range. Every tile
dispatch repeats `TILE_PREAMBLE_CODE` in `tile.h`: address calculation, indexed
cache lookup, blank-tile check and palette selection. Reducing renderer entries
does not necessarily reduce tile dispatches or row work.

In `tile.c:15`, eligible full tiles use `d35_render_tile`. Each row loads depth
and indices, tests visibility, and only surviving rows request `d35_color_row`
and composite. `a7_tile.h:91` selects fixed versus subscreen color math;
`a7_tile.h:123` performs direct stores for all-active rows or read/merge/write
for partial masks. These branch populations affect cost even at equal row counts.

Clipped functions (`tile.c:445`, `886`, `908` and related variants) instead use
`RENDER_CLIPPED_TILE_CODE`: masks and scalar four-pixel writers. They do not
enter the full-tile NEON helper. The color-row request counters therefore do
not measure these scalar clipped operations.

`a7_color_cache.h:31` is a 256-entry direct-mapped cache. Keys include absolute
tile pointer, palette pointer, palette epoch and bit depth, with row validity
bits. Palette changes can invalidate keys broadly; conflicting tile buckets
replace entries. Neither collision reason nor epoch-reset population is in
the current census. Absolute allocation placement can change across loads.

## What actually grows in the replay

Compare zero-based calls240..276 with277..290, the last complete control prefix.
The preceding interval is not certified effect-free. These are work counts
from the aligned replay, not Focus1's different physical encounter. The physical
CSV directly validates entries and total color requests; detailed path counts
are transferred from the deterministic census, not directly observed on A7.

| Mean per call | Preceding interval | Captured expensive prefix | Change |
|---|---:|---:|---:|
| Renderer entries |37.27|93.86|+56.59|
| Full tile requested rows, including blank/fallback cases |21,177.49|23,605.79|+2,428.30|
| Actual counted NEON row visits |10,125.22|14,039.36|+3,914.14 /38.66%|
| Empty NEON row visits |1,175.51|1,816.64|+641.13|
| All-active NEON row visits |7,630.24|10,421.00|+2,790.76|
| Clipped requested rows |17.08|122.79|+105.70|
| Full color-math requested rows |2,135.86|2,537.79|+401.92|
| Tile decodes |20.54|20.57|+0.03|
| Color materializations |3,728.81|3,892.36|+163.55 /4.39%|
| Color reuses |5,220.89|8,330.36|+3,109.47 /59.56%|
| Baseline Window2 pending flushes |9.19|65.86|+56.67|

The three physical controls increase main-thread CPU by3.725..3.824ms and
wall by4.110..4.125ms across these windows. CPU owns most of that increase.
This is distinct from Focus1's sampled PPU increase3.163ms and main CPU
increase4.427ms; do not equate the encounters or label main CPU pure PPU.
NEON visits include rejected rows; requested rows count before blank returns.
These overlapping counters must not be added as independent operations.

## Ranked mechanisms and numerical predictions

1. **Row visibility/compositing and full cache-access traffic: strongest target.**
   Surviving color requests grow3,273.01/call; most growth is cache reuse, not
   palette computation. A working model needs separate rejected, all-active,
   partial-mask, fixed/subscreen math and hit/miss prices. To explain Focus1's
   3.163ms growth solely through the replay's extra3,914 NEON visits requires
   an effective0.808us/extra visit. This is an inverse requirement across
   different windows, not a measured row price. Saving the late-call floor
   over the whole-effect15,368.96 NEON visits needs0.09853us saved/visit on
   average. A pure cache-access optimization over12,082.51 requests needs
   0.12533us/request. Measure those thresholds before choosing a kernel/cache
   rewrite. Branch costs and traffic could explain why requested rows alone
   fail to predict the growth.

2. **Raster fragmentation and repeated tile dispatch/preamble: plausible,
   unpriced beyond entry setup.** Window flushes closely track extra entries;
   per-call entry setup alone would predict only56.59*2.1785=123.28us growth,
   far below3.163ms. Explaining all that growth via extra entries would require
   55.90us/entry, contradicting the measured warm fixed-prefix explanation.
   However, short `Lines` batches repeat tile preambles and map/clip traversal.
   The census records row sums, not tile call counts or `LineCount` histograms:
   eight one-row calls and one eight-row call have the same count. For a dispatch
   optimization the falsifiable equation is `saving = removed_calls * dispatch_cost
   - added_cost`; both first terms are currently missing. The window candidate
   leaves all counted row/decode/NEON populations unchanged but adds1,423.92
   materializations. Its priced setup/rows/short helpers predict -32.918us.
   A verdict change requires at least1,547.20us additional measured saving in
   dispatch/locality or another omitted mechanism, plus headroom.

3. **Scalar clipped tiles and color math: real optimization opportunity,
   insufficient evidence for primary cause.** The prefix has122.79 requested
   clipped rows/call; closing1.514ms solely there requires12.33us saved/row.
   Whole-effect clipping averages234.64 rows, requiring6.454us saved/row.
   Explaining3.163ms growth solely through105.70 extra clipped rows requires
   29.923us/extra row. These are demanding thresholds, not proof of impossibility.
   Width, flip, blank/depth rejection and actual math branch prices are missing.
   Porting a masked NEON edge path is justified only if its measured aggregate
   saving meets a worthwhile target and preserves exact arithmetic.

4. **Color materialization/cache churn: modest priced payload; full lookup
   cost unknown.** At the measured0.10521us payload price, extra163.55 misses
   predict17.21us growth. Even removing all4,117.29 whole-effect materializations
   at that price credits433.17us, before replacement work:28.6% of the floor.
   The later-pass +19 misses predict only2.00us payload difference, not a
   multi-millisecond cause. This is a conditional warm payload accounting,
   not a bound on cache-key/collision/memory costs. Changing cache organization
   needs full hit/miss pricing and replacement reasons, not this payload alone.

5. **Tile decoding/APU or worker contention as the dominant growth source:
   lower priority.** Decode count is flat across the measured windows. An
   almost-constant20.6 decodes/call cannot explain growth through count alone;
   eliminating them would require73.61us saved/decode to meet the floor.
   Different bit depths/locality remain possible but unmeasured. Focus1's APU
   inclusive change is0.309ms versus PPU3.163ms. In the replay, increased
   wall-minus-main-CPU is roughly0.30..0.39ms, so external contention alone
   cannot explain the3.7..3.8ms CPU increase. Worker CPU can still consume
   headroom; callbacks/APU overlap and must not be double-counted.

## How accurately can the archive predict time?

Fit each count separately to physical CPU over calls240..283, then predict
the untouched seven calls284..290 independently in each control. Ordinary
least-squares slope/intercept; no calibration subtraction or terminal samples.
This tests prediction within one replay, not across all games or candidate code.

| Single predictor | Held-out mean absolute error across three runs |
|---|---:|
| NEON row visits |0.841..0.851ms|
| Color reuses |1.078..1.081ms|
| Renderer entries |1.165..1.218ms|
| Clipped requested rows |1.657..1.725ms|
| Full requested rows |2.497..2.544ms|
| Color materializations |3.112..3.174ms|
| Tile decodes |3.411..3.473ms|

The best maximum absolute error is1.107..1.188ms. Even its mean error is56%
of the late-call gate. It is not accurate enough to certify a1.514ms fix.
The apparent fitted entry slope82.7..85.0us is emphatically not entry cost:
entries correlate with other work. Counts co-vary as the effect evolves;
multi-feature fitting would not make these causal coefficients identifiable.
Held-out errors are empirical residuals, not confidence intervals. No full
effect recovery or independent-state prediction is available.

## What the audio failure predicts

The fixed quota gives `deficit_frames = 44.1 * (call_ms - 16.6881545)` while
production is quota-consistent and hardware runs at44.1k. At the late-call
floor, each call consumes about66.78 frames of reserve; the separate Focus1
PCM proxy consumes107.47 frames/call. A151..279-frame trusted low reserve
therefore covers only about3.4..6.3ms of zero-production blackout. Those minima
are observations, not necessarily the reserve immediately before any given call.

Three controls each lose1,568..1,647 nominal frames over just14 effect calls.
Reserve erosion preceding SETUP/77 is thus quantitatively expected. An exact
stop frame is not predictable from the cadence average: within-call audio
publication and hardware transitions matter. Terminal application-pointer
excess384 and no XRUN remain a separate unresolved vendor/accounting mechanism.
Starvation is the leading trigger; this evidence does not prove sole causality.

## Exact evidence missing before another diagnostic build

Prepare the following offline first; missing items must appear explicitly in
the proposed diagnostic's design rather than be rediscovered after installation.

* **Dynamic tile-call population:** full/clipped call counts, `LineCount`1..8
  distribution, dispatches per BG/screen/math mode, actual `Lines` batches and
  clip bands. Existing row sums cannot recover these. Obtain from the owned
  deterministic C replay; no host/QEMU timings become A7 prices.
* **Actual compositor branch population:** clipped width/start/flip; bit depth;
  blank returns; full-row rejected/all/partial masks; fixed/subscreen and half
  math branches. Existing mode sums and visibility counts do not fully specify
  `d35_blend` or scalar edge work. Establish representative data shapes offline.
* **Cache causality:** relative/absolute tile-buffer placement, bucket key and
  miss reason (tile collision, palette, epoch, bit depth, new row), palette
  invalidation events and reuse distances. Match source/runtime identities and
  fingerprint cache state; identical guest snapshots alone are insufficient.
* **Physical path prices still to collect:** entire dispatch+preamble,
  complete full-row paths by branch, clipped scalar paths by shape, whole
  cache hits/misses, and BG/clip traversal. Prices include observers and live
  workers; price warm and representative working-set conditions separately.
  State which aggregate hypothesis each price can falsify using the thresholds
  above. Avoid timing every individual row.
* **Aligned later inputs:** qualified effect-middle/late and recovery snapshots,
  matching command/state/output identities and documented host-cache warmup.
  These allow unit measurements beyond the early stop, as separate PCM epochs;
  they cannot establish uninterrupted whole-effect playback by themselves.
* **Observer budget and validation:** provisional maximum1% of16.688ms is
  166.88us/call. At observed1.49..1.74us/clock,32 clock endpoints account for
  47.68..55.68us before bookkeeping, counters and wall-clock endpoints. This
  is a planning allowance, not an overhead bound: use paired controls to verify
  total perturbation, retain it in measured time, and reject an over-budget
  instrument. Existing4,295 endpoints and9.294ms perturbation fail this target.
* **Acceptance/causal audio evidence:** full onset-to-recovery accepted/hardware
  reserve with within-call publication gaps; first pointer divergence matched
  to exact owner syscall/status; live worker CPU and CPU/wall gaps. This requires
  a viable measurement plan that survives long enough. Frequency remains
  unavailable; record that fact, do not infer A7 cycles from666MHz.

The next build should be specified only after offline call/branch/cache
populations choose the smallest discriminating set of physical prices and
clock boundaries. A candidate must then explain both cheaper and failing
states, predict held-out timing with error small relative to its claimed net
margin, preserve exact output, and meet both the late-call gate and sustained
cadence or a complete repayable finite deficit. Current evidence supports
prioritization; it does not support a qualified speedup forecast.
