# State-based scalar/NEON selection for the Plus PPU

2026-10-13, America/Chicago. **Design only:** no emulator/diagnostic recoding,
build, replay, card access or rearm. Derived counts reuse existing exact replay
logs and the archived combined1 A7 return. The installed core remains unchanged.

The design is a small family of state-selected producers and stores, not one
pixel-count threshold for the entire PPU. Scalar can do control, addressing and
sparse stores while NEON still computes a shared visibility mask. An eight-lane
input does not require an eight-lane color payload or read/modify/write.

## Evidence that constrains the policy

The latest native combination completes six of eight failure contexts twice.
It still fails Meteor and Quasar. Worst sustained 16-call main+worker CPU is
17.850-17.973 ms and 17.415-17.462 ms respectively, versus 16.6881545 ms available.
The proposed 20% target is 13.3505236 ms, requiring 4.500-4.623 ms and 4.065-4.111 ms
additional CPU reduction before other OS costs. These sums avoid counting worker
execution again as overlapping wall time. Observer costs stay included.

Current A7 core-call gains over the prior combination are only 0.350-0.513 ms for
Meteor and 0.446-0.563 ms for Quasar; Carbunkl regresses 0.055-0.075 ms. Those are
whole-path results. Dividing them by tile/row counts would manufacture unit prices.
Current runs have no inward PPU phase clocks, and frequency readings are all -1.

The older cost1 suite did measure warm source blocks: batch-mean CPU medians were
0.094 us for tile renderer selection, 0.094 us for its color-row materialization
payload, and 0.406 us for object setup/clip-list work. These describe an older
binary, early Bio Blast shapes and included timer/loop costs. They do not price
today's density classifier, sprite row, palette gather or sparse store. Their
32-operation batch p99 is not individual-operation p99. They establish that
selection/setup must be charged; they cannot set the new crossover thresholds.

See [native return](snes-combined-return-and-ppu-design.md) and
[cost1 price boundaries](snes-a7-cost-return.md).

## Read the C as a set of separate contracts

| Source path in the qualified common-band v3 tree | Relevant behavior |
|---|---|
| `gfx.c: DrawBackground`, `a7_common_band.h` | Dispatch plain/add/sub once per existing band. Only eligible full indexed cells enter this path. |
| `a7_common_batch.h: d35_batch_tile_mode` | Load indices/depth; construct mask; skip empty; lazily prepare palette; expand eight colors; merge partial output. Opaque RGB and depth already have direct stores. |
| `gfx.c: DrawOBJS` | Walk sprites in established order, with evaluation/tile limits and window boundaries. Main OBJ math eligibility depends on palette as well as registers. |
| `tile.c: d35_render_tile` | Full ordinary BG/OBJ tile helper. Uses NEON for supported 2/4bpp; RGB has an opaque direct store, but depth still uses a masked merge. |
| `tile.c/tile.h: DrawClippedTile16*` | Source-level scalar four-pixel helpers behind clip masks; fixed color is selected per row using the clipped offset. |
| `a7_tile.h: d35_blend` | Already distinguishes no enabled math, fixed-only, true-subscreen-only and mixed operands; several uniform subscreen fast paths are installed. |
| `a7_pearl_sub2.h: d35_sub2` | Sole-layer 2bpp sub producer omits competing-depth tests; expands colors before testing transparency. |
| `a7_tile.h: d35_backdrop/d35_window` | Vectorize complete eight-pixel output spans; caller handles remaining tail. Backdrop has no tile-style depth write. |
| `tile.c: ConvertTile`, `a7_tile.h: d35_decode_tile` | Decode only invalidated tiles. Supported safe 2/4/8bpp tile payloads already use NEON; boundary cases retain original fallback. |
| `gfx.c: mosaic/offset/Mode5/Mode7 producers` | Different source addressing, output layout or replication. Ordinary indexed eight-pixel assumptions do not transfer automatically. |
| `gfx.c: screen/depth clear and fill loops` | Contiguous bulk work; some source loops are scalar/word-based. Inspect emitted code before assuming the compiler did not vectorize them. |

These are source operations and coverage, not measured rankings of their CPU.
The input receipt hashes the exact C copies. Owned patches/build scripts recreate
them; no qualified source was edited for this analysis.

## Descriptor and dispatch lifetime

At an existing safe render boundary, choose a producer from format, BG/OBJ,
main/sub, math mode, output pitch/scaling, clip bounds and current state lifetime.
Keep BG tile traversal, sprite traversal and affine fetch as distinct producers;
reuse the same pixel-operation contracts where their inputs actually agree.
Do not force incompatible addressing loops into a branch-heavy universal kernel.

Use only cheap, already available facts inside the row loop:

- `w`: valid physical output lanes; a clipped source width is not necessarily the
  same number of output pixels in hires/replicated layouts.
- `V`: canonical visibility bytes from index-nonzero, clipping and the original
  strict depth comparison. `n` is the number of set lanes, not nonzero RGB colors.
- `M`: math-enabled visible lanes. Its population can differ from `n`; derive
  fixed/subscreen/mixed operand class only from lanes that need arithmetic.
- Palette format and whether its table is already available; distinguish a
  valid cache entry in memory from a table retained in vector registers.
- Known row count/run length over which setup can be reused. BG multirow cells
  and OBJ's one-row calls have different amortization even with the same mask.

Scalar handles control and irregular addressing. For supported full rows, keep
the existing NEON mask construction; feed its result to either scalar or vector
payload work. Do not add a second visibility walk, generic popcount, timing probe
or giant dispatch table to every pixel. Test empty/opaque cases before paying
for partial-row density classification. Mode and layout dispatch stay outside
the row loop; mask shape is the small remaining row-level decision.

Palette validity expires on the same changes as today. A background-local table
cannot survive a CGRAM/brightness/format change merely because its pointer or
palette number is unchanged. Main/sub views and different BG palette bases also
remain distinct. Reuse loaded masks and fixed-row values rather than querying
them again for each prospective implementation.

## Proposed selection rules across the PPU

**Retain** means existing implementation; **candidate** means correctness or
performance work remains before it can replace that implementation. None of the
unpriced rules below is authorized for installation by this document.

| Class | Selection rule | What the C predicts; what still needs measurement |
|---|---|---|
| Empty visible mask | Skip color and depth payload after required evaluation/state work. Retain existing generic fast exit. | Exact no-write result. Sole-sub ordering is a separate candidate; current archived sole rows contain no empty hits. |
| Opaque ordinary row, `n=8` | Retain dense NEON expansion/composition and direct stores. Candidate: share opaque depth-store handling with the full-tile OBJ/fallback helper. | That helper already directly stores opaque RGB; only its redundant depth merge is a new credit. Depth still must be loaded to establish visibility. |
| Plain indexed partial, `n=1/2` | First scalar-payload candidate, using the existing NEON mask and scalar lane extraction/palette loads/stores. Choose only in a class with positive measured net gain. | Already output-qualified offline for supported ordinary indexed paths. Classification, lane extraction, palette misses and spills are unpriced on A7. |
| Plain partial, `n=3` | Retain NEON pending a measured crossover; test this as a separate threshold, not automatic extension of `n<=2`. | Old Meteor interval has another 1431.5625 such rows. More eligible rows do not prove each scalar replacement is profitable. |
| Plain partial, `n=4..7` | Retain masked NEON by default. Separate candidate for an exact contiguous half/pair shape with aligned, bounded stores. | Old Meteor has 142 plain rows that are exactly one complete four-lane half, not all 413.25 rows with four visible lanes. Preserve every other depth lane. |
| Color math on no visible lanes | Skip payload. | Preserve traversal/status semantics. This is not the same as visible lanes whose math happens to be disabled. |
| Visible pixels but `M=0` | Use plain color/store behavior with the original visible mask and depth writes. Retain existing blend early exit. | No subscreen RGB or arithmetic needed; visible output is still required. Hoisting this earlier must retain exact eligibility and state effects. |
| Uniform fixed or true-subscreen operand | Retain installed specialized NEON math for dense rows. Candidate: scalar exact arithmetic for sparse math rows. | Fixed-only needs no subscreen RGB load. Existing uniform fast paths are not new savings. Plain sparse thresholds cannot price scalar add/sub/half paths. |
| Mixed math operands | Preserve per-lane disabled/fixed/subscreen and half-math rules. Retain NEON except separately measured sparse cases. | Splitting a row into runs may save work or add branches/setup. Measure classification and fragmentation; never use majority operand type for all lanes. |
| Clipped/negative/right-edge span | Retain bounded scalar edge handling initially. Candidate: normalize genuinely full, valid eight-pixel clips to an eligible full-row producer; use scalar tails or separately justified bounded staging for shorter spans. | Width 8 and source helper name alone do not establish safe vector memory access. Fixed-row side effects, flips, cache/state and layout must agree. |
| Sole-layer 2bpp sub | Retain no-competing-depth producer and opaque vector stores. Candidate: shared partial sparse stores and lazily prepared color work. | The no-depth-comparison premise must be proven from actual layer/window state; it cannot be generalized to any subscreen. Empty-row optimization gets zero credit in current traces. |
| Backdrop/window/fill/clear | Retain complete-vector bulk bodies plus bounded scalar tails. Candidate: specialize uniform fill/copy and sparse backdrop stores using each path's own write contract. | No tile/palette gather for a constant fill; backdrop does not acquire a tile-style depth store. Bulk word loops may already be optimized. Measure short-span setup and actual tail distribution. |
| Cold tile decode | Retain invalidation, full-tile validity and current bounded NEON decoder/fallback. | Warm heavy calls have few decodes. Decoding only selected rows would need new validity metadata; a partially decoded tile must not be marked fully valid or blank. No multi-ms decode credit is supported. |
| 8bpp/direct color | Retain original lookup semantics. Design candidate: scalar source/color lookup followed by dense NEON finishing when amortized. | Current small 2/4bpp register-table gather does not cover a 256-entry palette or arbitrary direct-color mapping. No crossover prices/coverage census here. |
| Mode7/affine and interpolation | Scalar coordinate-dependent VRAM fetch is the starting policy; consider vector coordinate arithmetic or packed finishing only after fetch/packing costs are known. Candidate: reuse a proven identical source sample across consecutive outputs. | Preserve wrap/repeat/flip, signed shifts, priority and interpolation stages. Repeat-mode fallback can depend on destination X even with zero matrix increments. Identical source color still needs per-output visibility/math. Arbitrary VRAM gathers do not become contiguous vector loads; retain the exact sampling filter. |
| Mosaic/offset/hires/interlace/scaled writes | State-specialized producer, scalar geometry and independently qualified vector payloads for sufficiently long legal spans. For mosaic, consider broadcast of the already selected source color plus per-output depth/math. | Large-pixel code already fetches one source sample per block: credit only reduced destination-loop work. Replication/stride and one-row offset traversal change masks/amortization. Ordinary-width kernels do not fit different layouts. |

Arm's [intrinsics reference](https://arm-software.github.io/acle/neon_intrinsics/advsimd.html)
shows the register-table `vtbl` family used by the current 2/4bpp gather. It is
not an arbitrary-address VRAM gather. This is why nonlinear source fetch and
contiguous pixel finishing need separate decisions. Arm also warns about
dependencies and register allocation in its [NEON optimization guide](https://developer.arm.com/community/arm-community-blogs/b/operating-systems-blog/posts/arm-Neon-optimization).
Those principles guide inspection; its example speedups on other CPUs do not
price this A7.

## Two concrete dispatch gaps and one non-opportunity

**Full-width clips:** `DrawOBJS` uses `if (X + 8 < NextPos)` for its ordinary
full-tile call. Equality goes through the clipped branch and can produce
`StartPixel=0, Width=8`. `DrawClippedTile16*` then uses scalar clip helpers even
though this particular span can be full width. This is a source-level candidate,
not a measured saving: the existing logs do not count these calls separately.
Normalize only after bounds, pixel scaling, fixed-row selection, flips and
observable state effects match. Do not change sprite/window traversal to force
this outcome or perform vector reads outside a valid row under a zero mask.

Inspection of the exact installed core SHA256
`e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129`
finds no vector memory/mask/gather instructions in the bodies of
`DrawClippedTile16` and `DrawClippedTile16Add`, versus such instructions in
`DrawTile16`. This checks the source-level coverage gap for those two functions;
it does not price it or claim all callees are scalar (cold decode is shared).
No binary was rebuilt or executed as an emulator for this inspection.

**Opaque OBJ depth:** `d35_render_tile` reaches `d35_store`, which already avoids
old-RGB merging for a full mask, but still merges its depth vector with old
depth. Sharing the common band's opaque-depth store can avoid that merge.
The visibility depth load remains necessary. Native frequency, invocation
counts and integrated saving are missing; count neither an eliminated RGB
merge nor a removed depth load here.

**Sole-sub empty guard:** the C expands colors before testing transparency and
does not have the generic row's explicit empty exit. But both sole-layer
contexts in the existing 18-context corpus contain zero empty hits over
2,729,944 row visits. Therefore no empty-row saving is predicted for this corpus.
Placing a new guard on every opaque sole row could add overhead. If retained as
a general policy, put its cost in the model and favor an opaque-first structure
or an already available emptiness fact; correctness alone is not a speed case.

## Semantics that constrain every selector

The original strict comparison is `test_depth > old_depth`; equality is hidden.
Its stored depth can differ from its test threshold. In `DrawOBJS`, `GFX.Z1`
is set separately from priority-derived `GFX.Z2`. Sorting sprites by stored depth
or using a single max-priority reduction would change established sprite-order
semantics. Batch only adjacent compatible work while preserving order, tile
limits, palette-based math eligibility and evaluation/overflow status.

Index zero is transparent even if palette color zero is nonzero. Equal RGB does
not justify skipping a required depth update. The mask census found no sampled
partial row where a whole unmasked depth store was legal. Preserve main/sub
ownership, clipped destination bounds, fixed color selected for the proper row,
RGB565 green representation and packed half-subtract behavior. A scalar/NEON
choice changes host implementation, never emulated clocks, PCM quota or frames.

## The crossover calculation

For one legal class `c` (operation, format, layout, operand kind and setup state),
compare integrated costs:

`C_scalar(c,n) + C_select(c,n) + C_added(c,n) < C_NEON(c,n)`.

Shared visibility is paid once on either side. Added cost includes detection on
misses, GPR/NEON transfers, lane extraction, cache changes, ABI saves/spills and
code footprint. Choose scalar only when the measured margin also survives tail
and integration checks. Otherwise retain that class's existing kernel. There
may be different thresholds for one-row OBJ, multirow BG, ready palette, cold
palette, plain copy, full subtract and mixed half math; thresholds need not form
one monotone global pixel-count rule.

Palette setup is amortized across its actual lifetime. A scalar early row does
not save a table build if a later dense row still requires that table. Cache
validity in memory is not free register residency. The current offline fused
plain band saves six D registers rather than the selective control's four:
16 extra bytes saved and restored (32 logical ABI bytes per such band), with
a 176-byte rather than 168-byte frame. That is an added-cost clue, not measured
DRAM traffic or microseconds.

For the plain sparse candidate, an auditable call model is:

`S = L + N1*s1 + N2*s2 - Npartial*q - B`.

`s1/s2` are payload credits excluding the common classifier; `q` is its integrated
extra cost on every eligible partial row, including misses. `L` covers distinct
setup/reuse changes and `B` other added costs. Do not count palette setup once
per sparse hit or credit removal of the shared visibility load. Broad row-loop
improvements need separate accounting to avoid double-counting the same work.

## Predictions available without new execution

Current native-peak frames are matched to already qualified full replay logs.
The candidate's selection opportunities there are:

| Quantity per peak call, two orders | Meteor | Quasar |
|---|---:|---:|
| Plain one-pixel rows |1936.625-1937.125|86-94.375|
| Plain two-pixel rows |2034.6875-2039.875|88.125-95.25|
| All eligible plain partial rows paying a sparse check |8131.625-8156.1875|785.5625-825.375|
| Sparse hits |3971.3125-3977|174.125-189.625|
| Modeled terminal logical bytes avoided |122816.5-122978.75|5391.5-5875.75|

The byte model compares 16-byte old-RGB reads plus 24-byte RGB/depth writes with
the existing sparse helper's extra index/palette reads and selected stores:
`40-6*n` bytes per plain partial row, excluding shared initial loads and guards.
For n=1..7 this gives 34,28,22,16,10,4,-2 bytes. It is source access accounting,
not cache-line/DRAM traffic or a time conversion. Fewer bytes alone do not make
several scalar lane extractions faster than vector operations.

Granting `L=B=q=0`, sparse hits alone would need the following average net saving:

| Target | Meteor | Quasar |
|---|---:|---:|
| Close current CPU deadline gap |0.293-0.323 us/hit|3.835-4.444 us/hit|
| Supply the entire proposed 20% margin |1.133-1.162 us/hit|21.436-23.612 us/hit|

These are required prices, not measured prices, forecasts or impossibility
proofs. Quasar's sparse population makes it a much weaker sole-lever candidate.
For Meteor, a purely hypothetical 0.05 us classifier on all eligible partial
rows costs about 0.407 ms. Equal payload credits of 0.10,0.25,0.50 us/hit would
then give approximately -0.010,+0.586,+1.580 ms before B and with L=0. These are
sensitivity examples only. They demonstrate why miss costs can reverse a
seemingly attractive microkernel and why a 4.5 ms promise is not justified.

The earlier detailed mask census contains 1431.5625 additional Meteor plain
three-pixel rows and 142 contiguous four-lane half rows. The former is about
36% more potential hits than n<=2, not 36% more speed. Those detailed histograms
cover the earlier interval only; late math and sprite masks were not captured.

Quasar's other established opportunity is 570 completely hidden 4bpp tiles,
covering 4410 row-index loads in both current peak windows. The offline selector
visits 4411 depth probe rows. Its model must charge probes and eligibility checks:

`S4 = 570*h - 4411*p - Neligible*q4 - B4`.

If this alone supplied Quasar's 20% CPU margin, `h` would need 7.131-7.213 us per
hidden tile even before probe and other costs. `h` prices the entire old hidden
tile work, including its old depth checks; do not separately credit those checks
again. The old aligned census has 849 eligible 4bpp attempts for Quasar and 2743
for Meteor: a selector that makes only a few probes can still test many tiles.
Late exact eligibility counts and actual guard costs require confirmation.

A source-based sample/visible-result-veto selector already qualified offline
keeps Quasar's favorable runs and reduces Terrato's full-replay tile probes from
67940 to 3640, giving up 13910 index-row eliminations. This is an explicit
work tradeoff with unpriced net time; a previous hidden hit is not a permanent
promise that probing every subsequent tile is profitable.

Quasar's late OBJ main/sub active rows grow to about 1247/1180 from 664/577 in
the old window, while BG1 math activity shrinks. BG-only sparse selection cannot
price or eliminate that sprite growth. OBJ/full-clip density, operand class and
dispatch costs are essential next inputs to a shared policy.

## What still must be measured, in priority order

| Measurement | Why needed; reuse before requesting anything new |
|---|---|
| Current PPU CPU split into BG, OBJ, clipped, visibility/expansion/math/store and geometry | Latest A7 logs contain whole-call CPU, not this split. Rank actual time before pricing more source operations. Use the newly identified peak intervals and full onset/recovery, not only old tails. |
| Classifier cost in its real caller | Measure sparse hit/miss and opaque/empty bypass paths, mask transfers and cache/table readiness. Standalone popcount time is not an integrated guard price. |
| Plain n=1/2/3 and half/pair payloads versus current NEON | Establish separate scalar/NEON margins with actual mask shapes, flips, main/sub, palettes and one/multirow reuse. Old correctness fixtures cover bounded n<=2 cases; n=3/half changes are not implemented or qualified. |
| Sparse math by all seven modes and operand class | Need visible n versus math-enabled m, uniform fixed/subscreen and mixed cases. Older Meteor has only nine sparse math rows; late OBJ/clipped math distributions remain missing. |
| OBJ full-width clip counts, widths and density | Current aggregate clipped counts cannot tell how often an eligible width-8 normalization occurs or whether its gain repays the guard. Preserve order, Z1/Z2, evaluation limits and fixed-row side effects. |
| Opaque OBJ depth and repeated setup cost | Avoid crediting RGB direct stores already installed. Measure full caller/spill impact, not an isolated removed instruction. |
| 4bpp probe payoff, misses and ordering | Measure h,p,q4 and cache effects together for Quasar-like hidden runs and Meteor/Terrato-like poor runs; include every eligibility check. |
| Palette lifetime, actual reuse and memory/register readiness | Decide when avoiding one setup is real, and whether the chosen scalar path incurs extra palette misses or register saves. |
| Backdrop/window/tail, decode, affine and scaled-path populations | No current per-class prices establish bulk/short-span, gather/finish or scaled crossovers. Keep installed/reference paths until those classes justify specialization. |
| Whole-call combined saving and valid audio reserve | Kernel gains share cache/ABI costs and cannot simply be added. Verify every frame/PCM sample, repeated effects, cold transitions and reliable pointers; invalid post-drift reserve is not acceptance. |

Performance measurements must use the kernel scheduling/thread clocks on A7,
with the real audio/display workers live, warm and representative cold states,
frequency recorded or explicitly unavailable, and identical included observer
policy for controls/candidates. No clocks inside every pixel loop. Use bounded
RAM counts and grouped samples; flush after workers stop. Report CPU and wall,
median/p95/p99 and real-run tails separately. Batch-average quantiles cannot be
presented as individual-operation tail latency, and calibration is never
subtracted. Inspect emitted ARMv7 code for spills, scalar/vector transfers and
unexpected calls before treating a source-level kernel change as a saving.

When native class prices exist, apply them to the existing per-frame workloads,
charging dispatch on every attempt and setup once per actual lifetime. Predict
each call's net saving and cumulative debt; do not add component p99 values or
multiply local speedup percentages. Retain dependence on cache/shape/order and
report unpriced classes explicitly. Then validate the complete integrated path.

## Design decision now

Start the future policy with existing empty/opaque behavior, qualified plain
n<=2 scalar payload candidates, unchanged dense NEON, and state-specific operand
paths already installed. The next design priority is shared OBJ/clipped coverage,
mask/operand reuse and conservative hidden-tile selection. Treat n=3, half-row,
sparse math, affine finishing and bulk short-span thresholds as separate measured
choices. No universal scalar threshold or guaranteed frame-time saving can be
honestly selected yet. The architecture and its break-even conditions are now
specified without another diagnostic or spell-specific C branch.

Bounded calculations and input hashes: [selection evidence](../evidence/2026-10-13/ppu-selection-design/).
