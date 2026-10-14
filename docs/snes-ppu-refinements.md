# General PPU refinements — 2026-10-14

**Physical result supersedes offline preference:** the combined candidate
does not improve acceptance and regresses Meteor's warm-common CPU/pointer
survival versus matched v3. Reject as an upgrade. Bulk shows isolated savings
but still fails Meteor pointer integrity. Source-row cache was not tested.
[Returned evidence](snes-ppu-test-return.md). Offline results below remain exact.

Implemented on request after the automatic demand-v3 return. These paths select
on current PPU geometry, visibility, depth and color-math state; there are no
spell IDs or animation predictions. The final offline candidate is
`build/ppu-refinements-private-v5/combined/snes9x2005_plus_libretro.so`, SHA256
`623fd5386a78ffdda40e48ebd58fbdaa15bfc06cdfc3f337f9b6677197c78c4d`, 882648 bytes.
I: was not written or rearmed. This is an exact-output-qualified candidate;
new A7 savings, audio recovery and production margin remain unmeasured.

## Changes

- Reuse initial OBJ window seeks during each synchronous DrawOBJS invocation.
  Simple/empty windows use direct starts; complex windows lazily build 263
  starts for X=-7..255. Stock window construction, sprite order/limits,
  subsequent window traversal and main/sub depth rules remain intact.
  Table state occupies 1060 bytes on the stack and never survives the call.
- Store all eight depth bytes directly when all lanes are visible. Depth still
  loads for visibility; opaque RGB stores already existed and earn no new credit.
- Normalize eligible full-width clipped indexed tiles to the full-tile path in
  seven plain/math modes. Guard pitch, row alignment, bounds and format; retain
  the final fixed-select offset side effect and original fallback for unsupported
  formats/geometry. Cold decoding and tile preamble still execute.
- Extend plain sparse output from existing one/two-pixel kernels to three
  visible lanes and an exactly opaque four-lane half. Preserve every hidden
  pixel/depth byte. Share this kernel with the fallback full-tile path.
- Use exact scalar color math for one/two visible lanes across six modes,
  including fixed/subscreen selection, half rules, HFlip and depth. Final v5
  forces inlining; assembly contains no call to d35_sparse_math.
- Clear contiguous main/sub depth planes with two fills when pitch equals
  rendered width, then retain all existing per-row window/color handling.
  Stride mismatch keeps row fills. Every depth byte is still initialized.

Existing CPU/APU/DMA/libretro sources remain byte-identical to demand-v3.
Changed existing sources are gfx.c, tile.c, a7_common_batch.h and
a7_partial_kernels.h. New headers provide the kernels and optional counters.
Ordinary cores compile counters away; observed counts are not A7 timings.

## Qualification

Against frozen demand-v3, all 18 archived effect contexts ran their original
commands for 1200 calls per variant. Eight isolated/combined v4 cores contribute
172800 comparisons; ordinary/counted row-cache experiments contribute 43200;
ordinary/counted final v5 contribute 43200: **259200 raw graphics/PCM/geometry
comparisons**, with normalized state checked every 30 calls. Every comparison
passed. No frame or audio omission was introduced.

Independent seam checks passed 1052000 initial-window lookups against the actual
stock seek; 129024 clipped cases against original scalar C covering all seven
modes, flips, 2/4bpp, both pitches, edges, blank/covered/equal depth and canaries;
1769472 sparse math cases against actual NEON; and 96000 source-cache dependency
checks. Each clipped entry has positive independent fixture coverage even though
six math clipped entries were not exercised in the archived spell corpus.
The cache checks cover writes, palettes, reverse reads, warmth and epoch wrap;
they do not establish exhaustive unrelated-pointer collision coverage.

Actual unchanged owned-output runner plus ordinary cores passed the consuming
native PCM provider: 149 direct callbacks per integration run, truthful fault
and retry, two snapshot restores, drain/deficit and failed-history preservation.
V4 combination, row-cache and v5 combination each passed seven synthetic
resolution/state transitions (8400 calls each, **25200 total**): modes 5/6,
interlace, 239 lines, pseudo-hires, initial-hires fallback and repeated restores.
These are offline seams, not physical driver/performance acceptance.

The synthetic 239-line baseline already diverges against an identical baseline
because of HDMA host pointers. Both comparison clones use the same TEST-ONLY
NULL/NULL host-pointer reset; no emulated fields are masked, and shipping HDMA
is untouched. Do not cite that test as universal unmodified 239-line acceptance.
All prior frozen hashes and published evidence hashes verify. Final ELF requires
at most GLIBC 2.7, below the 2.30 device ceiling.

## Work observed and costs still owed

Final counted late Meteor interval (calls 496–535), means per call:

| Mechanism | Eligible work | Added or retained cost |
| --- | ---: | --- |
| Opaque depth | 548.8 rows | Visibility/depth load retained |
| OBJ simple starts | 516.15 | Guard and direct start |
| Complex OBJ reuse | 804.15 reads | 526 table-entry writes, 1060-byte stack state |
| Plain three-lane | 1513.8 rows | Classification, scalar loads/stores, register transitions |
| Plain half-row | 232 rows | Half guard and four-lane output |
| Bulk depth | 446 old fill requests to 2 | Same 114176 depth bytes |
| Sparse math | 15 visible pixels | 21 partial classifiers |
| Full-width clipped | 0 | No peak saving credit |

Quasar has 993.87 opaque rows, 274.61 three-lane rows, 147.07 half rows,
123.20 sparse-math pixels and the same depth bytes. Its OBJ reuse pays 526
table writes for 939.13 reads. The whole corpus has 1216 full-width plain
clipped hits; the peak benefit remains unknown. Classifier misses, code
footprint, spills, cache effects and GPR/NEON transitions must be priced.
Many plain classifications and one/two-lane paths already existed: do not
count that shared work as a new saving or charge all of it as newly introduced.
Bulk fill savings concern setup/call cost, potentially compiler-inlined;
they do not remove memory bandwidth.

Net saving is removed old costs minus all added costs. All new A7 prices are
missing. Prior Meteor/Rage valid recorded CPU exceeded the 16.688153ms quota
by 0.231–0.270ms, excluding unpriced kernel/other costs and cumulative reserve
debt. Predicted remaining deficit is therefore unknown. A 20 percent margin
requires about 3.59–3.61ms more saving. As a conditional price example,
0.270ms / 1513.8 three-lane hits is about 0.178 microseconds net per hit,
before extra guard/miss costs; it is not a throughput forecast.

## Source-row cache experiment, excluded from final candidate

`build/ppu-refinements-private-v4/rows-v2` separately caches canonical unflipped
eight-pixel RGB spans before visibility/depth/math. Thirty-two direct-mapped
32-byte entries consume 1KiB plus alignment. Keys include decoded row pointer,
palette pointer, bits and palette epoch. Epoch wrap clears the cache; tile
conversion invalidates matching decoded-row entries. Every final row still
composes with current depth/subscreen/math. This is source-span reuse, not a
temporal finished-scanline cache or knowledge of future writes.

Late Meteor has about 4097 hits / 8471 misses (32.6 percent hit rate), Quasar
2600 / 10079 (20.5 percent). Every lookup costs metadata; misses still expand
colors and write RGB/cache metadata; conversion visits 32 entries. Palette
setup remains paid. Earlier larger RGB-cache results were negative. Keep
this separately qualified experiment out of the preferred combination until
matched A7 pricing demonstrates positive net savings.

## Reproduction and next physical test

Run the preparer, build, seam, qualifier and integration scripts named in
`evidence/2026-10-14/ppu-refinements/inputs.json` in their declared order against
the private frozen inputs. V4 must qualify before prepare-ppu-final.py; final
qualification and final integration precede publish-ppu-refinements.py.
Scripts refuse to overwrite evidence directories. ROMs, states, saves,
vendor sources/binaries and generated cores remain private; publication carries
only authored scripts/headers and metadata. No installer was added.

Preserved setup failures: initial ambiguous source anchor, initial cache owner
scope across translation units, and a missing integration harness include.
Fresh variants repaired these before qualification. V4 had an out-of-line
sparse-math call and mislabeled legacy sparse counters for new shapes; v5
inlines the call and restricts the old counters to one/two pixels. Use the new
PPU counters for v4 evidence. All earlier qualified trees remain intact.

Next authorized physical run should price isolated OBJ/shapes/bulk and final
combination against unchanged v3 on Meteor/Quasar in both orders, then run
all 18 contexts paired through full effect/recovery. Use ordinary cores, same
owned runner, kernel clocks, complete PCM/pointer history and cumulative
reserve; avoid nested PPU timers. Price the row cache separately. Archive
the card first and satisfy the measured-saving installation gate in
boot-and-hardware-contracts.md. No Meteor fix or production promotion is claimed.
