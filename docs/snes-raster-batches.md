# Larger SNES raster batches

The Mode 2 strip walker is the first candidate to price on the Cortex-A7.
It changes the order of independent draws within a raster flush. It leaves
CPU, Super FX, PPU event timing, audio production and frontend publication
at their existing boundaries. There is no title check. Star Fox was the
only frozen scene that reached the Mode 2 strip path.

## What each batch shares

- **Offset strips.** Take the rows already available inside one raster
  flush and group them by the recorded horizontal and vertical scroll for
  the offset map and target layer. Resolve the offset map once for each
  horizontal fragment in the group. Walk down that fragment and call the
  current clipped tile renderer for up to eight rows at a time. Each call
  stops at its own decoded tile boundary, including the quadrant transition
  for 16×16 tiles. Clipping, flips, priority and main/subscreen composition
  stay in the existing renderer. Unsupported layouts retain the scanline
  path. No tile or scroll data survive the flush.
- **Full-tile and NEON strips.** Use the same geometry. An aligned, complete
  eight-pixel span can use either the existing full-tile renderer or the
  warm indexed NEON path with a shared palette table. Both retain clipped
  draws at edges. The NEON variant falls back for cold tiles. The isolated
  NEON variant keeps the strip implementation out of the common background
  dispatcher to test whether compiler inlining caused cross-game regressions.
- **Sprite bands.** Group up to eight rows only while each row has the same
  visible sprite list, ordering and tile quota and each sprite stays inside
  its decoded tile. The conservative version covers plain, unclipped
  sprites. The wider version also tries the existing clip and color-math
  renderers when per-row fixed color is inactive. Both preserve draw order
  at each pixel, including ties between sprites.

Star Fox's counted build grouped 900,600 layer-scanline visits into 16,698
stable bands. It replaced 29,269,500 one-row tile draws with 3,782,268
draws, an 87.1% reduction. Of the original tile-row visits, 96.9% were
eligible for a full-width draw. In the sprite census, the wider path grouped
230,242 of 231,519 Metroid sprite-scanline visits and removed 92,274 list
entries from the drawing loop. The measured CPU benefit was smaller because
checking list equality costs time and every remaining pixel still has to
be rendered.

## Timing and exactness

Each timing pair alternates which ARM core runs first on the same pinned
host lane under QEMU. CPU figures use 1,080 calls after the first 120
of each 1,200-call gameplay window. The Star Fox bootstrap runs 8,656
scripted calls with video disabled in both arms, then draws all 1,200
gameplay calls. The same-binary measurements use two copies of identical
executable bytes, with the candidate path enabled in only one copy.
This separates the actual path from link-time inlining and code placement.
The standalone builds are also compared against a rebuild whose executable
text matches the returned physical core.

Positive percentages are lower mean core CPU. Star Fox p95 is included
because a faster average can still miss the audio production deadline.

| Path on vs. off in identical binaries | Mario PAL | Metroid | F-Zero | Star Fox mean | Star Fox p95 | Ranger |
|---|---:|---:|---:|---:|---:|---:|
| Offset strips, current clipped renderer | −1.45% | 0.42% | 0.13% | **34.29%** | **26.82%** | −0.88% |
| Offset strips, existing full-tile renderer | 0.62% | 0.75% | 0.59% | **34.98%** | 24.49% | 0.99% |
| Offset strips, inline NEON | 0.66% | −0.12% | 0.26% | 26.61% | 18.82% | 0.41% |
| Offset strips, out-of-line NEON | 0.61% | −1.45% | −0.12% | 32.21% | 21.02% | 1.81% |
| Sprite bands, plain and unclipped | 2.02% | −0.41% | 2.82% | 0.56% | 2.31% | −2.19% |
| Sprite bands, wider | 2.16% | 0.83% | 0.68% | −0.35% | 3.03% | 0.81% |

| Standalone build vs. rebuilt baseline | Mario PAL | Metroid | F-Zero | Star Fox mean | Star Fox p95 | Ranger |
|---|---:|---:|---:|---:|---:|---:|
| Returned core vs. rebuild, identical executable text | 0.72% | 0.55% | 0.75% | −0.21% | 1.00% | 1.41% |
| Offset strips, current clipped renderer | 2.90% | 2.98% | −2.23% | 35.68% | 26.26% | 1.75% |
| Offset strips, existing full-tile renderer | 4.29% | 3.37% | 1.57% | 37.35% | 28.11% | 4.01% |
| Offset strips, inline NEON | 2.36% | −19.89% | −3.95% | 39.64% | 26.63% | 3.15% |
| Offset strips, out-of-line NEON | 4.73% | 3.24% | 0.36% | 37.84% | 26.43% | 4.33% |
| Sprite bands, plain and unclipped | 2.84% | 1.52% | 1.67% | 0.80% | −0.08% | 3.59% |
| Sprite bands, wider | 2.57% | 1.53% | 2.07% | 1.22% | 1.28% | 2.23% |

The Mode 2 branch never ran in four scenes. The inline NEON build's
19.89% Metroid loss and the change after moving the function out of line
show how sensitive this linked core is to the compiler's placement and
inlining decisions. Use the clipped path first for its strongest p95
saving with code placement fixed. The full-tile variant has the best
standalone Star Fox p95 and positive mean timings across the suite. Price
both paths separately on the A7.

All five replays verify per-call RGB565 and PCM hashes and sample counts
against the frozen oracle. The callback layout matches the returned core.
The Mode 2 geometry comparison
expands each draw into its tile, row, pixel and priority and matches the
original scanline walker in 2,048 generated ranges. Those cases vary clip
edges, flips, tile size, both map shapes, VRAM wrap and scroll changes.
The clipped and NEON builds also pass strict pixel, PCM and normalized
state comparisons through FFVI Meteor and Quasar (1,200 calls each) and
Ranger cold boot (2,400 calls).

## Physical deadline

The NTSC deadline is 16.688 ms (59.923 Hz). The PAL Mario replay runs at its
native 50.320 Hz. The four existing Star Fox returns show 27.483–27.656 ms
mean **core CPU** over the first three valid calls, followed by PCM DROP.
That opening needs at least 10.795–10.968 ms (39.3–39.7%) of core savings
before any additional time on the critical path.

If the 34.29% QEMU mean saving transferred to that physical opening, core
time would be 18.06–18.17 ms, equivalent to about 55 calls/s before host
work. This sensitivity calculation still leaves 1.37–1.48 ms of core time
above the deadline. It uses the prior physical opening and an offline
gameplay ratio. The A7 saving, added host costs, sustained frame delivery
and remaining cumulative audio deficit are unmeasured.

Keep the performance install gate pending. An instrumented A7 comparison
must measure the net change in core and host time for the same workload.
The required inequality is
`core saving > old core time + other critical-path time − 16.688 ms`.
Use the existing cycle-derived quota and full accepted-minus-consumed PCM
reserve trace. The physical prediction is falsified if 1,200 calls cannot
keep up at native cadence with valid pointers and reserve recovery, or if
RGB565, PCM or sample counts diverge. The previous trace ended after four
calls and cannot establish the full reserve curve. See
[physical audio accounting](snes-focus-1-return.md).

## Reproduction

Run `build/check-snes-raster-offset.py` against the private corrected source.
Build the `raster-*` arms with `build/build-snes-throughput.sh` and verify
with `build/run-snes-throughput.py <build> raster-verify`. Run the baseline
and standalone builds with the `--raster` mode of
`build/run-snes-throughput-pair.py`. Build the same arms with a `-toggle`
suffix for `--raster-ablation`. Use `build/check-snes-scheduler-state.py`
for the held-out checks. `build/report-snes-raster.py` combines the timing,
verification, hashes and prior physical data into the
[results](../evidence/2026-11-10/snes-raster-batches/analysis.json).
