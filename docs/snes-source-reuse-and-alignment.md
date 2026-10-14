# Source sharing, cache layout and output ownership

2026-10-13. Investigated the supplied 2010/bsnes proposals against the exact
combined1/profile1 core. Built an isolated alignment variant and a deliberately
narrow geometry-sharing experiment. Neither was installed; I: was not accessed.
All performance figures below come from earlier A7 returns. This review uses
ARM/QEMU for correctness, addresses in that process and work populations only.

## A concrete, qualified cache-layout change

The measured core's ELF has `d35_palette_entries` at offset `0x13db28`, size
`0x0f00` (3840 bytes). Its load segments have4096-byte alignment. Consequently
ASLR does not change its offset40 within a64-byte cache line. The ARM layout
is48 bytes per entry, including a32-byte NEON table at member offset16. Table
starts cycle through offsets56,40,24,8; **40 of80 tables straddle two lines**.
This is an actual property of the installed experimental binary, independent
of unrecorded heap addresses. Aligning only the array would leave a48-byte
stride and some split tables; that alone is not the complete solution.

The owned alignment variant:

- Allocates all three decoded-tile buffers explicitly at64-byte boundaries,
  retaining the original allocation sizes, initial zeroing and paired frees.
- Separates palette metadata from its32-byte tables. A64-aligned table array
  has32-byte stride, so every table fits in a single64-byte line. Metadata is
  960 bytes and tables2560 bytes: **3520 bytes total**,320 bytes less than before,
  excluding independent linker padding. Epoch/key invalidation is retained.
- Changes no SNES color, depth, timing, frame or audio decision.

This variant passes **9600 original-command calls across all eight contexts**:
graphics/native PCM/geometry match each call, normalized emulated state every30
calls, including normal teardown. Every case asserts64-aligned tile pointers
and all80 nonstraddling tables. Its ELF table symbol is `0x154900`, size2560;
metadata is960 bytes. Private core SHA256:
`832531a13f4e7b2355c5a5ade0963a7e4b54d006fa460f2f06219ad59e160291`.
This is a separate offline candidate, not the production core or a card payload.

Baseline decoded tiles use ordinary `calloc`, with no explicit64-byte contract.
Their addresses in the ARM/QEMU process were offset8 within64-byte lines.
**The returned A7 logs do not record those heap pointers**; do not present the
QEMU addresses as physical-device observations. The new allocator guarantee
does not depend on the host allocator's incidental alignment.

2010's decoded-tile allocator uses an architecture-dependent alignment helper.
The inspected32-bit ARM branch returns32-byte alignment; copying that helper
unchanged would not guarantee the A7's64-byte data boundary. See
[2010 tile allocation](https://github.com/libretro/snes9x2010/blob/master/src/memmap.c),
its `libretro/libretro-common/memmap/memalign.c`, and the
[Arm A7 technical reference, section6.1](https://documentation-service.arm.com/static/5f042da1dbdee951c1cd8c11).
Local2010 source revision reviewed:
`fe690dd321fa5a46b5234a2bde089d2518c62b0e`; exact file hashes are published.
Online moving master and this pinned checkout need not have identical line numbers.

A cache-line footprint is **not a cache miss or a time measurement**. Adjacent
decoded tiles can share warm lines. Our8-byte row loads at offset8+k*8 do not
individually cross64-byte boundaries. Alignment can help whole-tile locality
without halving the existing memory traffic. Highly reused palette tables may
already hit L1. This variant's net A7 saving remains unknown and could be zero.
Do not credit the historical large RGB-cache replacement again: the current
cache was already only3840 bytes.

## Shared source work: identify the actual consumers

The [bsnes fast background renderer](https://github.com/bsnes-emu/bsnes/blob/master/bsnes/sfc/ppu-fast/background.cpp)
can feed one produced source pixel to both above/below consumers. That suggests
source/geometry reuse, while keeping main/sub depth, windows and color math
separate. It does not make their final pixel operations identical.

The earlier3094/4410 matching-source numbers counted backgrounds only. A separate
observer now splits BG0-3 and includes eligible ordinary full-tile OBJ requests.
It records complete source keys: redraw, layer, destination, decoded row pointer,
palette pointer and HFlip. Retaining all keys also captures matching earlier
overlapping OBJ requests, rather than only the last subscreen writer at a
destination. Zero table overflow or unsupported-layout counts;2400 exact
original-command calls. Clipped/scaled/Mode7 requests are outside this metric.

| Mean requests per heavy call | Sub | Main | Matching main requests |
|---|---:|---:|---:|
|Meteor BG0|4664|3230|**3094**|
|Meteor BG1|0|6330|0|
|Meteor BG2|0|3542|0|
|Meteor OBJ|828.59|1464.09|**827.59**|
|Quasar BG0|0|4546|0|
|Quasar BG1|4704|6330|**4410**|
|Quasar BG2|0|1021.21|0|
|Quasar OBJ|1236.76|1856.47|**1220.71**|

BG3 has zero requests here. Meteor matches95.79% of its BG0 main requests;
Quasar matches69.67% of its BG1 main requests. Matching OBJ requests are56.53%
and65.75% of main OBJ requests respectively. These are source-row populations,
not vector instructions, successful pixel stores or microseconds. A matching
consumer may still be hidden by depth. Do not add its prospective saving to
the earlier hidden-row/fused saving without measuring their intersection.

The correct generic rule is to consider **whichever layer both planes use**.
Hard-coding BG0 would miss Quasar's background sharing entirely. There is no
need for a spell ID or ROM change to choose the appropriate layer.

### The first restricted implementation is rejected

An owned experiment records packed8-byte BG0 tile-geometry commands during
the sub pass, then would replay them through the main pass's original tile
producer. It preserves the order: finish all subscreen work before main-screen
math can read it. Eligibility deliberately requires mode1,8x8 tiles, both
planes enabled, unrestricted clips, no Window2 target, no horizontal partial
tile and an existing supported batch family. Its8192-command allocation costs
64KiB even before useful work is admitted.

Across eight1200-call replays it records and reuses **zero commands**. The9600
matching-output calls therefore qualify only its fallback behavior; they are
**not positive-path qualification** or evidence of a useful optimization.
A separate2400-call guard probe explains the exclusion:

- Meteor's heavy BG0 visits include16x16 tiles, nonempty clip descriptions
  and Window2 targeting. The restricted whole-geometry plan cannot cover them.
- Quasar's BG0 is not enabled on both planes in those heavy entries. Its
  duplicated background source work belongs to BG1.

This version should **not** go to A7: it has no demonstrated removable-work
population, adds guards and storage, and has unpriced overhead. The experiment
does not disprove source sharing. It rejects the simple whole-BG0 bypass.
Two initial comparison exports were hidden by the build's default visibility;
the checker stopped before running emulated calls. Exports were corrected and
those setup-failure logs retained separately. No failed pixel replay is hidden.

A useful next shared producer would need bounded8/16-tile geometry, separate
consumer clips (including per-row Window2), and exact priority/flip handling.
It should reuse tilemap/geometry setup without an extra whole-screen RGB cache.
For OBJ it must preserve sprite order, palette-dependent main math, clipping,
overflow and different test/write depths. The producer's stores and consumer's
loads must cost less than traversing the original source twice. Our current
decoded indices are already cached; a descriptor lookup is not automatically
cheaper than rereading them. This larger path is designed here, not implemented
or performance-qualified.

## Direct owned output: useful, with a measurable ceiling

[2010's frontend](https://github.com/libretro/snes9x2010/blob/master/libretro/libretro.c)
acquires a writable framebuffer after planned dimensions are known, validates
RGB565/data/pitch, redirects output, and falls back to its persistent buffer
if a mid-frame resolution promotion outgrows the acquired region. This is
useful ownership and fallback structure to adapt, not a ready-made driver.

Our `board_video_submit` copies224 rows of512 visible bytes from1024-byte core
pitch into a compact chunk-backed slot:114688 bytes read and114688 bytes
written. The asynchronous scaler accepts a compact chunk source, not an arbitrary
heap pointer or padded pitch. A single contiguous114688-byte memcpy would be
incorrect with the current source layout.

The existing [lab2 return](platform-lab-2-return.md#memory-and-remaining-work)
measures direct chunk fill0.1435ms versus heap-fill-plus-copy0.5178ms per simple
114688-byte iteration:0.3743ms advantage in **that fixture**. It does not measure
real PPU depth tests, sparse read/modify/write, cache behavior or ownership waits.
It is evidence to pursue the experiment, not0.3743ms of qualified emulator gain.

A restricted output experiment should:

1. Reserve the existing free chunk slot **and FIFO publication credit before
   entering the core**. The core owns it exclusively while drawing.
2. Acquire only at the visible-frame boundary. Update all coupled layout fields
   (`Screen`, `S`, `Delta`, pitches, PPL and depth stride); do not copy2010's
   smaller field list into this different2005 layout. Maintain the existing
   renderer safety margin and bound the complete allocation and pointer deltas.
3. Use compact RGB565 rows for admitted lores frames. On hires/interlace or
   unsuitable geometry, restore the full persistent layout before any expansion
   reads/writes. Include any required subscreen/depth state migration, not only
   the visible main RGB. Qualify mode switches, restore-state and frame reuse.
4. Publish the same reserved slot without copying. Retain READY/SCALER ownership
   until DrawVFB completes; only then return the source to FREE. Preserve worker
   output ownership through FlipVFB. Drain/join before freeing anything.

No direct-output implementation or driver change was built in this review.
The chunk mapping's actual cache/coherency contract and whole-core net CPU cost
still need A7 evidence. Generic DMA-buffer synchronization calls cannot simply
be applied to this private `/dev/chunkmem` ABI.

Observed sampled video callbacks average0.824ms Meteor and0.8585ms Quasar, including
copy and publication. Consider an intentionally optimistic scenario where the
**whole callback** becomes free and rendering gets no slower:

| Scenario | Meteor | Quasar |
|---|---:|---:|
|Earlier unprofiled deadline deficit|1.308ms|0.803ms|
|After removing the sampled mean callback cost|**0.484ms still short**|**0.055ms slack**|
|Additional saving still needed for20% margin|**3.822ms**|**3.282ms**|

These combine sampled means and different unprofiled late windows; they are an
illustration, **not an aligned saving prediction or strict bound on each call**.
Actual publication remains, and chunk accesses, guards, restoration and waits
have costs. Even this generous scenario does not deliver comfortable headroom.

## Generalized spans: steal dependency rules, not a thread queue

The inspected [2010 PPU](https://github.com/libretro/snes9x2010/blob/master/src/ppu.c)
snapshots registers and queues incremental palette/OBJ updates. Its no-render-thread
path immediately drains each recorded span. VRAM writes, status reads and resolution
changes also impose drains. That organization enables a separate render worker;
it does not itself eliminate all state boundaries or source work.

On our one-core A7, moving equal work onto another runnable thread cannot create
extra compute capacity. Keep the dependency lesson: mutable VRAM/OAM/CGRAM must
remain version-correct for every consumer; resolution promotion must happen after
older output is complete. A one-thread snapshot/update queue adds copies and
dispatch unless a separate proof shows it enables worthwhile coalescing.

We already batch Window2 and fixed-color rows. The next low-impact cases remain
the [measured repeated-work candidates](snes-architecture-populations.md):
strict contiguous VRAM DMA invalidation, redundant sprite-geometry dirtiness,
brightness0 rebuilding and ring wrap copying. These can remove host work without
deferring arbitrary register changes. Do not merge palette/VRAM/OAM writes across
visible spans just because the final register value matches: earlier rows may
depend on the previous contents. No new generalized span queue is proposed for
installation from this audit.

## What remains unknown before an A7 decision

The alignment candidate is ready for a **measurement experiment**, not production
promotion. Pair it with the exact current core in matched Meteor/Quasar replay
states, keep all frames and workers live, record actual pointer residues and
frequency availability once, and use kernel thread-CPU clocks around complete
calls. Include observer and worker costs; do not subtract calibration. Accept a
gain only if repeated matched tail windows show lower total CPU demand without
new graphics, PCM, ownership or reserve failures. No numeric alignment saving is
assigned beforehand; the falsifiable prediction is improved layout with identical
output, and a possible measurable cache-related reduction that may also be zero.

For shared sources, missing evidence is a qualified window-aware8/16-tile producer,
its consumer/intersection coverage and its complete added costs. For direct output,
it is real PPU access cost in chunk memory plus fallback/ownership qualification.
Neither is supplied by the row-count table. The known1.308/0.803ms deadline gap
and4.646/4.141ms requirement for20% margin remain open.

Before adding more hot-loop clocks, check whether this kernel exposes a usable
PMU, permissions and nonmultiplexed counters through
[`perf_event_open`](https://man7.org/linux/man-pages/man2/perf_event_open.2.html).
If available, aggregate counters around complete calls first; sampling and group
reads have overhead too. PMU availability on this device is not established here.
Scheduling priority can alter jitter and starvation; it is not additional CPU
throughput or a replacement for removing work.

This review totals24000 exact comparison calls, including observer/fallback
cases. Only9600 exercise the actual alignment change. Source, identities, negative
results and bounded receipts are in
[source-reuse review evidence](../evidence/2026-10-13/source-reuse-review/).
No frame dropping, ROM edits, card writes, rearm or production promotion.
