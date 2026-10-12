# Bio Blast: remove tile repetition and cache palettes instead of RGB rows

2026-10-11. Six isolated ARM/QEMU experiments; no card access, no production
source/core change, no installation or measured A7 speedup. The combined design
is a materially stronger candidate than the earlier entry-only scorecard.

The earlier analysis left out thousands of repeated tile dispatches. Identical
rendered-row counts do not establish identical tile-call overhead. New counters
resolve that missing quantity: window batching removes8,340.864 full-tile calls
per effect frame, all in the plain renderer, while preserving the requested
row counts and visible output. This changes the hypothesis to test; it does
not turn QEMU counts into performance measurements.

## Three ideas tested together

**Batch work for the backgrounds unaffected by BG1's moving circular window.**
Retain BG1's actual bounds per scanline; existing guards and clip bands preserve
the original effect. Longer batches let other layers call a tile renderer once
for several rows instead of repeatedly recalculating tile address/cache/palette
state. The experiment starts with the prior bounded window patch, not a new
whole-frame reuse scheme.

**Cache the tiny palette lookup tables rather than expanded RGB tile rows.**
The current full-tile NEON path tests visibility, accesses a36KiB RGB-row cache,
checks tile/palette/epoch/bits keys, and then loads expanded colors. Misses also
rebuild a NEON palette table and store the expanded row. The alternative keeps
80 small palette tables keyed by palette/epoch/bits, preparing each lazily.
For each visible row it reuses the already loaded/flipped pixel indices, performs
the two NEON table lookups, then uses the existing exact color-math/store helpers.
It removes RGB-cache key checks, row stores, RGB loads and RGB flip work, at the
cost of palette gathers on former RGB-cache hits. A table is queried only on
the first visible row of a tile call. Direct-color and unsupported bit-depth
paths retain their original fallback; scalar clipped paths are unchanged.

This substitution makes the window patch's extra RGB materializations disappear
as a category: direct gather count is identical with and without batching.
It is not free. Lookup traffic, register pressure and the extra gathers must be
priced together. Removing a counter does not remove all equivalent computation.

**Replace repeated validity scans with a prefix summary.** The existing window
helper scans every pending row on each edge write. The new helper records a
cumulative invalid-row count while rows are captured in order. A pending range
is valid exactly when its two prefix values agree. Repeated last-row captures
update the summary; missing or out-of-order captures retain the original scan.
This makes ordered range queries constant-time. It adds1,036 bytes of prefix
state and a few operations per captured row, which remain unpriced on A7.

## Actual full-effect work

Means across all162 effect frames, zero-based277..438:

| Work | Current | Window only | Palette only | Palette + fast window |
|---|---:|---:|---:|---:|
| Renderer entries |134.537|28.290|134.537|28.290|
| Full-tile function calls |18,342.660|10,001.796|18,342.660|10,001.796|
| One-row full-tile calls |14,513.025|6,260.086|14,513.025|6,260.086|
| Eight-row full-tile calls |118.691|1,634.296|118.691|1,634.296|
| Clipped calls |224.012|224.012|224.012|224.012|
| Palette table constructions |4,117.290|5,541.210|12.957|12.957|
| RGB row materializations |4,117.290|5,541.210|0|0|
| Direct palette gathers |0|0|12,082.512|12,082.512|

The baseline still performs palette gathers on its4,117 materializations; the
zero direct-gather counter is not zero total palette work. The new path adds
gathers on7,965 former reuses. Do not price all avoided table constructions and
all avoided materialization as independent savings: those operations overlap.

Full-tile calls drop45.47%; the row populations, depth rejection, visibility
and scalar clipping populations remain unchanged on every effect frame.
Histogram-weighted call lengths exactly reproduce the existing requested-row
census on all1,200 frames, including calls that return for blank tiles.
All removed full calls are mode0/plain; color-math call counts stay unchanged.
The remaining missing price is therefore the removable plain tile dispatch/
preamble population, not an arbitrary average of all tile renderer modes.

The palette array occupies3,840 bytes in ARM symbol data versus36,864 for the
RGB entries. The smaller array is an86% footprint reduction, not a measured
hardware-cache miss reduction. Palette lookup table constructions drop99.69%.
There are4,955.951 table queries per effect frame in the combined design.
Its134.827 prefix queries cover ranges totaling9,619.204 rows; none uses the
fallback scan in this effect. Range-length sum is not an independently measured
count of original scan iterations if a range would fail early. The query's
constant-time mechanism is independently checked below.

## Correctness results and errors diagnosed

The experiments are baseline with new counters, prior window with new counters,
palette-only, palette/window, palette/fast-window, and a separate helper-count
copy. Every variant passes1,200 Bio Blast replay frames: per-frame visible RGB565
CRC, native PCM CRC/sample counts, geometry and one video callback; normalized
serialized state is byte-compared every30 frames. The palette-only and
palette/fast-window variants also pass2,400 frames each across intro and the
returned private snapshot. Total comparisons12,000 frames; this is six variants
of a replay plus two broader checks, not12,000 unique Bio Blast states.

The unchanged original `ComputeClipWindows` oracle matches524,288 clip states.
A separate original row scan matches38,400 prefix queries, covering eligible/
ineligible rows, gaps, repeats and out-of-order captures. The array/current-line
guards preserve the original scan's fallback behavior.

Initial harness compilation needed its Blargg define and explicit loop braces.
The first baseline comparison completed its output/state loop but aborted on
an old assertion requiring more PCM callback batches than an older reference.
Both cores here already publish early. The local harness removes only that
obsolete batching-gain requirement; every pixel/PCM/geometry/state comparison
remains. The failed log is retained privately. A signedness warning in the
independent prefix oracle was corrected with an explicit unsigned cast; the
candidate comparison already uses the equivalent implicit C conversion.
No graphics mismatch was observed. Existing upstream compile warnings are not
treated as new renderer failures or quietly repaired in production source.

The replay uses the preserved derived Magitek battle and original guest game
execution, not the exact returned physical encounter. Audio sinks accept
samples offline and do not reproduce vendor PCM, display or worker contention.
Keeping PCM comparisons is a correctness safeguard; no audio hardware is needed.

## Revised cost equation and falsifiable thresholds

Let `d` be removable plain tile-call dispatch/preamble overhead, excluding row
work and not inclusive tile function duration. Let `C` be the full net saving
of the palette substitution (positive or negative), including its4,956 queries,
12,083 gathers,13 table builds, register/memory effects and eliminated RGB work.
Let `b_fast` be all new fast-window bookkeeping/capture/band/cache costs, and
`u` any other changed traversal/loop overhead. All prices must be physical A7
microseconds aligned to the actual removed population.

`S_combined = 8340.864198d + 106.246914e + C - b_fast - u`

For comparison, the previously priced original window terms become:

`S_original_partial = 8340.864198d + 231.462 - 149.808 - 114.572 - u`

The measured warm setup/payload/short-helper terms remain partial; new dispatch
population alone does not make their weighting or long spans fully qualified.
At `u=0`, the original equation needs`d>=0.18550us` to reach the1,514.283us
late-call floor or`d>=0.29612us` to reach the separate2,436.981us PCM proxy.
These targets are much smaller than the old15.7..16.7us/renderer-entry target
because thousands of tile calls, not merely106 entry prefixes, are now counted.

| Hypothetical d | Original window partial S | Combined S if C=0, helpers=114.572us, u=0 |
|---|---:|---:|
|0.10us|0.801ms|0.951ms|
|0.20us|1.635ms|1.785ms|
|0.30us|2.469ms|2.619ms|

The right column is sensitivity, not a prediction that palette substitution is
free or fast helpers cost the old helper amount. Its thresholds are0.16754us
and0.27816us respectively under those stated assumptions. A negative `C`,
larger bookkeeping, worker contention or other loop costs can reverse a verdict.
Do not convert these hypothetical microseconds to cycles at an assumed frequency.
No QEMU elapsed time or instrumented ARM instruction count enters these prices.

## What to do with this result

The clever candidate is **longer tile batches + tiny palette tables + prefix
validity**, preserving raster state. It has a concrete, tested mechanism and
a much stronger count-based opportunity. It has not earned installation.
The earlier entry-only negative model remains valid for the components it
priced, but cannot settle the whole window candidate after this dispatch
population is known. This report supersedes a recommendation to shelve the
entire mechanism solely from that partial model.

Before a new physical diagnostic is designed, isolate the removed plain tile
preamble paths and their blank/visible/depth population; the histogram is now
known but bit-depth/BG/cache distribution still needs weighting. Price them
excluding pixel work. Compare complete current RGB versus palette-direct row
paths over their recorded tile batch and visibility shapes, including memory
working sets. Price prefix capture/query and band work over the actual longer
ranges. These are the minimal discriminating A7 prices, with a bounded observer
budget and live workers. Whole effect/recovery and vendor pointer/stop diagnosis
remain separate acceptance requirements. No new device build is authorized here.

## Reproduction and preservation

Existing experimental trees are retained under ignored
`build/bio-hypotheses-private/`. Preparation refuses to replace them. New tooling
does not alter`build/snes9x2005`, its shipping core, earlier censuses, card or
private progress. Source hashes and the production-core manifest are verified.
Fresh reproduction (when that private experiment directory does not exist):

```text
python build/prepare-bio-hypotheses.py
sh build/run-bio-hypotheses.sh
python build/prepare-bio-fast-window.py
D35_BIO_VARIANTS=palette-fast-window sh build/run-bio-hypotheses.sh
python build/prepare-bio-helper-counts.py
D35_BIO_VARIANTS=palette-fast-window-counts sh build/run-bio-hypotheses.sh
```

The two broader comparisons use the local equivalence runner with the returned
snapshot and1,200 iterations, without the Magitek input flag. The prefix oracle
uses the original clip source and generated `fast-window-check.c`, compiled for
ARM and executed with`qemu-arm -cpu cortex-a7`. All outputs stay private until
the analyzer verifies and publisher copies only bounded counts/proof text.
Do not run preparation merely to reproduce existing results.

Public [analysis](../evidence/2026-10-11/bio-offline-hypotheses/analysis.json),
[per-effect-frame counts](../evidence/2026-10-11/bio-offline-hypotheses/effect-counts.csv)
and comparison/oracle logs contain no ROM, state/SRAM, vendor core or private
memory trace. Existing historical evidence bytes and manifest entries remain
unchanged.
