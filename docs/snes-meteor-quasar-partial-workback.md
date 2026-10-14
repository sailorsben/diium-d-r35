# Meteor and Quasar: visibility-first workback

2026-10-13. Offline analysis and exact alternatives; no card access or staging.
Current combined1 physical logs remain pending. Ben reports Pearl completed on
its third opening attempt (latest combined) and Meteor failed all three. Those
are qualitative observations, not measured timing, headroom or failure cause.

## New evidence changes the diagnosis

Replay the actual original-ROM inputs and archived failing snapshots. The new
observer preserves original pixels/PCM and all352 old work counters on every
call; normalized state checkpoints remain every30 calls. Counts below are means
per expensive call: Pearl399-414, Meteor391-406, Quasar427-442. They describe
only the common indexed full-tile background path, not every PPU operation.

| Work | Pearl | Meteor | Quasar |
|---|---:|---:|---:|
| Active common rows |6608|15057|11297|
| Partial common rows |688|8182|741|
| Partial plain rows |420|8161|668|
| Plain one-pixel rows |1|1937.6875|63|
| Plain two-pixel rows |25|2040.875|69|
| Sparse candidate hits |26|3978.5625|132|
| Entire partial depth store already unchanged |0|0|0|
| Full direct depth store legal for partial row |0|0|0|
| Partial row is exactly one full four-pixel half |34|145|45|

Meteor's partial work is mostly plain BG1 on main/sub and plain BG2, not
subtraction: mainBG1 has2304.1875 partial rows, subBG1 has3186.625, mainBG2 plain
has2369.1875. Only21 of its partial rows use math. Quasar has only741 partial
rows, largely opaque output and a different hidden-background opportunity.
Earlier suspicion of one shared partial-merge bottleneck is not supported.

## Exact optimization implemented offline

`partial-merge-selective.h` preserves the ordinary supported renderer and adds:

1. For plain rows with one or two active pixels, select their original indexed
   palette colors directly, write only those RGB565 pixels and their depth bytes.
   Dense rows retain NEON. Depth/zero-index/flip rules are unchanged. This avoids
   full-width palette expansion and old-RGB read/merge on3978.5625 Meteor rows,
   48.6% of its partial rows. No pixels or emulated frames are omitted.
2. Expand canonical00/ff visibility bytes by signed widening. All256 canonical
   mask shapes match the old duplication helper. Standalone emitted helper uses
   one NEON instruction versus five; this does not price an inlined invocation.
3. Snapshot stable plain-row state explicitly to reduce alias-driven reloads.
   Keep the old color-math state path: the broad prototype increased mode3 saved
   NEON registers from d8-d13 to d8-d15 and scratch124 to140 bytes. That is an
   unpriced register-pressure risk, not a measured slowdown. Selective refinement
   restores the original register-save sets; scratch is100/108/108 bytes for
   plain/add/sub versus prior116/124/124. Scratch allocation is not byte traffic.

The sparse hit replaces the terminal path's16-byte old-RGB read,16-byte RGB
store and8-byte depth store (40 logical bytes) with n index-byte reads,2n palette
byte reads,2n RGB writes and n depth writes (6n bytes), n=1 or2. Initial decoded
index and depth reads remain. Modeled reduction is123025.875 logical bytes per
Meteor call,4074 for Quasar,734 for Pearl. This excludes guards, spills, tables,
cache lines and write allocation; it is not DRAM bandwidth or a timing estimate.

Rejected shortcuts:

- Skipping depth stores: zero sampled partial rows qualify. 4345.5625 Meteor
  partial rows already have equal RGB in active lanes, but depth must still
  change. Equal visible color does not imply equal rendering state.
- Writing the whole depth vector unmasked: zero qualify; foreground depth would
  be destroyed. Direct half-row stores cover only145 Meteor rows, not8182.
- Optimizing subtraction to fix these merges: only21 Meteor partial math rows.
- Reusing a whole BG1/BG2 main/sub image: existing eligibility census is zero.
- Applying the 4bpp depth prepass everywhere: poor Meteor hit rate below.

## Quasar's different target: reject fully hidden 4bpp tiles earlier

Quasar's main BG2 plain path visits4410 rows, all hidden by depth. The existing
early-reject guard handles only plain2bpp main tiles. A new observer-only4bpp
probe (without changing rendering) measures:

| Probe work per expensive call | Meteor | Quasar |
|---|---:|---:|
| Eligible4bpp tile attempts |2743|849|
| Entire tile hidden |90.3125|570|
| Probe depth-row visits |3059.5625|4693|
| Single-row eligible tiles |1714|0|
| Hidden single-row tiles |61.875|0|

Quasar's hidden-tile rate is67.1%; Meteor's is3.3%. A blind prepass duplicates
work on survivors, including already cheap blank returns. This is a separate
promising Quasar hypothesis, not an implemented/qualified early-reject fix.
The full-depth prepass break-even is `570*h - 4693*p - B4 > 0` for Quasar and
`90.3125*h - 3059.5625*p - B4 > 0` for Meteor: h is original work avoided per
fully hidden tile (including its original row loop), p probe cost per visited
row, B4 all other costs. Prices require aligned A7 measurement. Probe rows
must never be treated as free. A generic selective policy needs its own census
and output oracle before inclusion; hard-coded spell identifiers are unnecessary.

## What could this save: conditional accounting, not invented A7 prices

For Meteor's selective sparse path, in A7 microseconds:

```
S = L + 1937.6875*s1 + 2040.875*s2 - 8161*q - B
```

L is the net whole saving from non-sparse changes; s1/s2 are sparse-hit credits
including their lane selection and scalar loads/stores, excluding the common
density check q. q is paid on all8161 plain partial rows; B includes extra
full-row checks on10054 plain active rows, instruction-cache effects, spills,
palette materialization changes and interactions. All prices remain unmeasured.
Do not obtain them by dividing inclusive renderer time by row counts.

| Assumed equal credit per sparse hit | Meteor gross credit | Quasar gross credit |
|---|---:|---:|
|0.05us|0.199ms|0.0066ms|
|0.10us|0.398ms|0.0132ms|
|0.25us|0.995ms|0.0330ms|
|0.50us|1.989ms|0.0660ms|

These are sensitivity examples, not predicted savings. A0.05us density guard
alone costs0.408ms for Meteor. Row-local gains and other added costs still need
measurement. Sparse eligibility is about30 times greater in Meteor than Quasar;
one successful microkernel is not a shared multi-ms cure.

Prior measured fullpaths-combined conservative service proxy was19.572-19.632ms
for Meteor:2.883-2.944ms beyond16.688ms,6.221-6.281ms beyond13.351ms/20% target.
If G is the new current combined1 gain over that old control, the remaining
requirements become those gaps minus G. G is unknown until the card returns.
Even with G=L=q=B=0, sparse hits alone would need0.725-0.740us each to close the
old deadline gap, or1.564-1.579us for the old20% gap. These are optimistic
thresholds, not an asserted achievable unit cost or a hardware lower bound.
The service proxy itself can double-count worker overlap.

## Qualification and next falsifiable boundary

18000 original-output calls:3600 mask census,3600 depth-preflight census,
7200 broad/local/sparse prototype comparisons,3600 selective comparisons.
387072 scalar tile cases compare original full/clipped tile functions across
all seven modes, both bit depths, priorities, blank states, flips, strides and
canaries. Another32768 independent canonical-mask/sparse-store fixtures cover
all256 masks, both flips and2/4bpp; unchanged reference/mask proofs reused by
hash for refinement. No QEMU duration is A7 performance evidence.

Current48-run I: experiment remains unchanged. On return archive first and
measure G, exact failure stage, complete effect/recovery and valid audio reserve.
Only then calculate the remaining target for the selective candidate. A future
isolated A7 comparison must charge density checks on misses, cache/branch/spill
costs and final worker work; a positive gross hit saving is insufficient. This
turn installs nothing and claims no production gate pass or hardware limit.

Reproduce with prepare/build/analyze-partial-merge, prepare/build-partial-preflight,
prepare/build/check/qualify-partial-candidates, prepare/build-partial-selective,
inspect/summarize-partial-assembly and report/publish-partial-workback scripts.
Raw states/ROM/input logs remain private; bounded counts and qualification hashes
are published under evidence/2026-10-13/partial-merge.
