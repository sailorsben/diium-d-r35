# Compose the renderer tools without charging for the same saving twice

2026-10-13. Offline work only. The running combined1 card test is unchanged.
No A7 saving or production installation gate pass is claimed.

## Window batching is already in the experimental builds

The earlier Bio Blast prototype reduced `S9xUpdateScreen` entries from134.537
to28.290 per effect call,78.97%. It increased RGB-row materializations34.58%:
entry counts were never equivalent to total CPU time. Later palette work changed
that tradeoff, and ability2 generalized scanline Window2 state to BG1/BG2/BG3.

All three cores in the installed combined1 experiment descend from ability2.
Its baseline is the generalized-window control, not original1.19. The staged
plan and independently read-back installation receipt agree on latest combined
SHA256 `e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129`.
The ability2 and common-band source copies of `a7_window.h` both hash to
`09aea539fd3a81c4770022c6bd6d0d86801c9dadecf46a1dec02fec961ebf740`.
Their `$2128/$2129` writes call `d35_window_defer()` before deciding to flush;
scanline capture/fetch preserves distinct row masks. Unsupported states still
use the original flush. The old uninstalled statement describes a historical
prototype. Production promotion remains pending.

See [current staging](snes-combined-measurement.md),
[installation receipt](../evidence/2026-10-13/combined-measurement/installation.json)
and [generalization](snes-ability-regression.md).

## Share the decisions and intermediate results

The isolated fused candidate combines constant-mode bands, a shared eight-table
palette owner, exact sparse scalar stores, NEON dense stores and earlier depth
rejection. Mode and sole-subscreen dispatch happen once per band. Eligible tile
checks still happen per tile; they are not free.

For main-screen2bpp work, carry the first visible row's loaded depth and mask
from the existing prefix test directly into rendering. For4bpp, sample a warm
nonblank tile per background draw. If fully hidden, try prefix rejection on
following tiles. Stop trying after a visible result. This is a cost selector,
never an approximation to visibility. No effect IDs select implementations.
Cold tiles and unsupported cases retain original rendering.

Only surviving rows reach index/palette/store work. One/two visible pixels use
individual exact RGB/depth stores; dense rows retain NEON. The sole2bpp subscreen
path shares palette ownership but needs no competing-layer depth comparison.
No additional Pearl palette saving is established: it already uses one table.

Aligned expensive-call means against common-band v3:

| Work | Pearl | Meteor | Quasar |
|---|---:|---:|---:|
| Generic plain index rows, prior |584|12752|9698|
| Generic plain index rows, fused |584|12752|5288|
| Sparse rows handled exactly |26|3978.5625|132|
| Added fully hidden4bpp tile rejects |0|0|570|
|4bpp depth probes: blind hypothesis -> selected |1016 ->1|3059.5625 ->3|4693 ->4411|
| Reused first-visible depth/mask |57|59|57|

Quasar avoids4410 index rows,45.47% of this specific population. Of570 new
hidden tile rejects,569 precede tile-cache metadata access; the initial policy
sample already read metadata. Meteor retains its3978.5625 sparse opportunities
without running the expensive blind4bpp scan. These are different mechanisms.
The source model also removes56 logical plain depth load requests per aligned
call in each case. That assumes the same warm2bpp prefix predicate and excludes
zero observed cold fallbacks. Intrinsic requests are not measured retired loads,
DDR traffic, cycles or microseconds.

## A negative case changed the design

The first fusion prototype kept4bpp prefix scanning enabled after one successful
sample. Across Terrato's1200 calls it attempted67940 tile probes with14903 hidden
hits: a poor population for repeated early checks. The refined visible-result
veto cuts attempts to3640, retaining1025 hidden hits. It consequently performs
13910 more index rows than the prototype across that complete replay. This is
an explicit tradeoff, not proof of a net speedup. Quasar's122108 attempts and
119700 hidden hits are unchanged, as are Meteor/Pearl's sample-only behavior.
All18 contexts retain identical active/store/palette populations every call.

The plain band saves six D registers rather than the selective control's four;
its stack frame is176 rather than168 bytes. Math save sets are preserved.
Selector guards, cache behavior, ABI saves/spills and code footprint must all
be priced on A7. Stack allocation alone does not measure stack traffic.

## What can be predicted now

For one disjoint row phase, let N be prior rows, H removed rows, c their prior
unit cost, c' the surviving-row cost and A the added selection/setup cost.
Then `saving = H*c + (N-H)*(c-c') - A`. This captures elimination followed by
cheaper surviving work without crediting eliminated rows twice. Whole-frame
percentages cannot be multiplied: CPU/APU, other PPU phases and worker costs
remain. Existing physical combination results already demonstrate non-additivity.

The receipts predict exact output, Quasar's eliminated work and preservation of
Meteor's sparse opportunities in these archived contexts. They do not establish
the corresponding A7 microseconds, tail behavior or comfortable headroom.
Collect the already-running combined1 return first. Against its measured gain,
price the remaining fused work, added costs and full-effect cumulative reserve
before defining another physical experiment. Keep every emulated/display frame
and PCM sample. No hardware-impossibility claim follows from a failed build.

## Qualification and reproduction

Both fusion variants pass18 contexts times ordinary/counted versions times1200
calls:43200 exact original-output calls each. Graphics and PCM compare every
call; normalized state checkpoints compare every30 calls. Each also passes
387072 scalar tile-policy cases plus9216 sole-layer cases. The observer-only
refinement adds3600 exact calls and preserves every pre-existing event field.
Thus this task adds90000 replay comparisons; prior mask fixtures are reused,
not counted as newly executed. QEMU provides correctness evidence only.

Run `prepare-fused-toolbox.py`, `build-fused-toolbox.sh`,
`check-fused-toolbox.py`, `qualify-fused-toolbox.py` and
`inspect-fused-toolbox.sh` for v1. Prepare/build the extra observer using
`prepare-fused-count.py`, `build-fused-count.sh`, `qualify-fused-count.py`;
then run `report-fused-toolbox.py`. For v2, use `--v2` on prepare/check/qualify/
inspect/report and build with `build-fused-toolbox-v2.sh`. Fresh private output
directories are required; preserve previous results. Existing private fixtures,
cross compiler, owner runtime and original-ROM references are prerequisites.
`publish-fused-toolbox.py` verifies both proofs, original staged identities and
prior workback sources before publishing bounded receipts. No ROM, state, PCM,
vendor binary or raw returned log is published.
