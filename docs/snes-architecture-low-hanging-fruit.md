# Remove repeated host work before redesigning 2005 Plus

2026-10-13. Audit of the exact combined1/profile1 core
`e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129`.
No card access, rearm or production changes. An owned observer-only clone
passes9600 original-command calls across the eight problem contexts with exact
graphics, native PCM, geometry and periodic normalized state. These are work
counts, never QEMU timings or measured A7 savings. No optimization candidate
is installed or performance-qualified by this audit.

## The proposed scalar final composite is already NEON here

In stock-style `gfx.c`, the nested `while(d<e) / if(*d==0) / if(*s)` is indeed
a vectorization candidate. Our current A7 build already calls `d35_backdrop`
immediately before each applicable scalar body, then advances p/d/s by the
returned pixel count. `a7_tile.h:192` handles `count & ~7u` pixels in groups
of8 with vector depth equality, mask selection and stores. The existing scalar
body processes only `count%8` pixels **per contiguous clip span**. An ordinary
256-pixel span has zero scalar remainder, not256 branchy iterations.
Disassembly of the exact core's `S9xUpdateScreen` confirms `vceq.i8`, `vbsl`
and `vbit` operations; this is not just an unused helper in source.

The pass fills/composites the backdrop only where main depth is0. Foreground
color math already occurs in tile rendering. Fully foreground-covered8-pixel
blocks skip color work inside `d35_backdrop`; it is not unconditionally blending
every RGB pixel for a third time. A full256x224 span scan is7168 vector groups,
not57344 scalar decisions. Clipped tails and unsupported build paths differ.
Do not credit this NEON conversion as a new improvement or infer8x whole-call
speedup from lane width. A new opportunity would be proving whole rows/spans
have no uncovered pixels and avoiding their *scan*, with summary-maintenance
cost included. That coverage information is not currently measured or free.

## Findings ranked by usefulness to the current failure

### 1. VRAM DMA invalidation/copy bookkeeping: strongest new common candidate

Every `REGISTER_2118/2119` variant writes a VRAM byte, calculates three tile
indices and sets2/4/8bpp decode-cache flags false. Most flags are already false:

| Context,1200 calls | Byte invalidation groups | All3 flags already invalid |
|---|---:|---:|
|Pearl/Holy|1,381,952|98.29%|
|Meteor|1,315,592|98.20%|
|Meltdown|1,183,088|98.02%|
|Siren|1,078,656|98.35%|
|Bahamut|924,488|98.24%|
|Carbunkl|1,265,944|98.14%|
|Quasar|1,182,032|98.00%|
|Lullaby Rage|1,193,008|98.02%|

Meteor384-415 averages1420 such writes,1400.5 already-invalid groups per call.
Quasar496-529 averages915.529 writes,895.765 already-invalid groups. This is
roughly4202/2687 repeated logical flag stores per heavy call, plus address work.
Instruction scheduling may combine some stores; logical stores are not DRAM
transactions or microseconds.

The sensible change is a **guarded contiguous VRAM DMA path**, not testing all
three flags before every byte. For supported linear mode1/5 uploads, a bulk
span copy plus once-per-affected-tile invalidation removes repetition. An
aligned1024-byte span currently requests3072 flag stores; invalidating64+32+16
affected tile flags needs112, a96.35% reduction in that bookkeeping population.
Data transfer remains O(B) because every byte must arrive; invalidation work
scales with touched tiles rather than bytes. This is not an O(B^2)->O(B) claim.

The pinned DMA implementation flushes pending rendering before VRAM DMA and
handles HBlank after the transfer; keep those boundaries and identical emulated
cycles/address updates. Before implementation, qualify forward/fixed/decrement
source modes, direct mapping and4KiB/bank boundaries, VRAM wrap, odd lengths,
VMA.High/increment, full-graphic remapping and custom-chip cases. Start with
strict supported guards and original fallback. The observer counts all byte
helpers; it does **not** prove all of them fit the contiguous fast path.

No millisecond saving is priced. Supplying the entire current Meteor1.308ms
gap from1400.5 redundant groups would require~0.934us net per group; Quasar's
0.803ms gap needs~0.897us/group. Those are required prices, not predictions.
There is no basis to promise this bookkeeping change alone fixes either effect.

### 2. Audio ring wrap: a small, definite algorithmic defect

`apu_blargg.c:resampler_read`, in the `r_step==65536` direct-copy branch,
computes `bytesUntilBufferEnd` once, outside its loop. After rb_start wraps to0,
that old tail size still caps every following copy. The result is correct
bytes but avoidable repeated `memcpy` calls. Copying the remaining contiguous
prefix should take one more copy, not repeatedly using the old tail length.

The actual extracted C branch and a two-span implementation match230785 valid
ring states, including output canaries and final rb_start/rb_size. A synthetic
32768-byte ring with4 bytes left and1024 int16 samples requests512 old copies
versus2 new copies. **That synthetic extreme is not the workload forecast.**

Each actual1200-call replay uses2400 direct reads. The old code makes3063-3070
copies; two spans need2555. There are77 reads requiring more than2 copies,
with an actual maximum103 copies/read. This eliminates508-515 copy calls over
1200 emulated calls, about0.42/call on average. Meteor's heavy interval has
5.3125 old versus2.125 minimum copies/call; Quasar has2.2059 versus2.1471.
It is a clean local fix and tail cleanup; it cannot receive a large average
CPU saving from the synthetic example. A7 cost remains unmeasured. Preserve
output rate, samples, ring state and callback ordering.

### 3. Narrow sprite layout invalidation: real, but not these peaks

`REGISTER_2104` marks `IPPU.OBJChanged` after changing tile name, palette,
priority or HFlip. `S9xSetupOBJ` does not use those fields to build its line
schedule: it uses positions, sizes, VFlip, first-sprite/rotation and limits.
Drawing reads the appearance fields later. Keep the original flush before
changing appearance; suppress only unnecessary layout rebuilding. `$2101`
tile-base changes similarly need not invalidate geometry if size is unchanged.
Rotation, OAM addressing/latches, VFlip and geometry dirtiness remain intact.

An exact geometry-key observer finds unchanged-layout rebuilds in every
1200-call context:32/306 Holy,11/344 Meteor,15/327 Meltdown,15/466 Siren,
11/277 Bahamut,20/188 Carbunkl,11/188 Quasar,13/138 Lullaby. Rebuilt schedule,
width and visible-tile bytes match previous results in every equal-key case.
This is3.2-10.6% of layout rebuild calls, **not** PPU CPU time. Both Meteor and
Quasar peak intervals have zero redundant layouts: no peak-saving credit here.
The production implementation should use dependency-specific dirty flags at
write sites, not a128-sprite key comparison before every rebuild. The observer
is evidence, not the proposed hot-path implementation.

### 4. Renderer selection and full-width clipped dispatch: bounded candidates

`DrawOBJS` can repeatedly choose the same renderer pair per sprite/scanline.
Siren records93725 selections,70385 redundant within their owning OBJ draw.
Resolve the stable selection once or memoize its two local classes. Do not
introduce an untracked global pointer cache: state writers and hires handling
can change the valid family. Meteor and Quasar have zero selections in this
branch, so this does not explain their present failure.

`X+8<NextPos` sends equality through the clipped renderer even when StartPixel0
and Width8. Count actual eligible calls before normalizing: only144 Meteor and
48 Quasar over1200 calls, and **zero in both captured peak intervals**. Other
contexts range0-480. This source gap is real, but the new census rejects it as
a current-peak explanation. Keep separate Z1 test/Z2 write, sprite order and
exact clip geometry. No NEON benefit is priced from the call count.

## Quadratic-looking loops and already completed work

OBJ window endpoints are built with insertion/memmove (O(K^2)), but K is a
small bounded clip count; at most a handful of endpoint entries. The ordinary
sprite scheduler visits each sprite's covered rows and the rotation variant
visits line/sprite pairs, bounded by128 sprites and the SNES line count. Neither
is an established large unbounded quadratic hot path in these failures. A
bitset scheduler may be possible for rotation, but that branch must occur and
be priced before receiving priority.

Window validity already uses ordered prefix summaries; BG full-tile work is
already banded with local palette reuse; warm decoded tiles are cached; the
composite bulk is already NEON. These were the original repeated-work targets
and are already in the measured core. Counting them again would invent savings.

The largest known remaining pool is still PPU row production/composition. The
existing offline fused candidate removes hidden index-row work and sparse masked
stores without spell IDs; it remains unpriced on A7. This audit adds smaller
architectural cleanup candidates and rules out tempting but inactive mechanisms.
It does not establish that low-hanging fruit alone supplies the~4.65/4.14ms
needed for20% margin. No device diagnostic or installation is requested here.

Reproduce with prepare/build/qualify-architecture-audit and
check-architecture-ring. All input/current-core hashes and bounded results are
published under [architecture audit evidence](../evidence/2026-10-13/architecture-audit/).
