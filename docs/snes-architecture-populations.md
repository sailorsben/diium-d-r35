# Test architectural hypotheses against actual successful work

2026-10-13. The two user-supplied analyses propose whole-layer rejection,
recipient-aware color math, sprite-window preparation, brightness caching,
deferred color math, strip rendering, main/sub source sharing and RGB-cache
replacement. We tested populations in the current combined1/profile1 C, not
an untouched upstream tree. No optimization, card write, rearm or A7 test was
performed. Three isolated observer iterations total28800 exact replay calls;
the latter two add traversal and pixel-provenance counts. No QEMU time is used.

## Two proposed savings are already installed

The large scalar final backdrop loop is preceded by `d35_backdrop`, which
handles all complete8-pixel groups with NEON; scalar code handles only a
0-7-pixel tail per clip span. It is not57344 scalar color-math decisions in
the current A7 build. This was checked in actual `S9xUpdateScreen` assembly.

The36KiB RGB materialization cache is historical. Current `a7_color_cache.h`
has80 palette-table entries. The exact measured core's ELF symbol is0x0f00
bytes, **3840 bytes /3.75KiB**. The suggested small-table replacement is already
present, alongside batch-local palette reuse. Current generic/OBJ cache hits
are99.56% Meteor and99.72% Quasar in the counted peaks. Do not credit that
representation change again. Further reuse across OBJ calls remains a separate
setup/ABI question; it is not removal of an installed RGB cache.

## Deferred math: test the amount actually discarded

The observer records successful ordinary scalar and NEON main-screen stores,
labels semantic math-enabled pixels and counts a math result only when a later
successful store replaces it. Rejected depth tests are not counted as wasted
math. Region boundaries reset provenance, respecting raster state lifetimes.
It verifies zero foreground-depth pixels missing store provenance, zero source
table overflow, zero unsupported layouts in these eight contexts, and the
per-call identity `math writes - overwritten math = final math owners`, including
separately counted backdrop math. Original pixels/PCM/state remain identical.

| Mean per emulated call | Meteor384-415 | Quasar496-529 |
|---|---:|---:|
|Successful main RGB pixel writes|85684.5|63227.4|
|Those RGB results subsequently overwritten|28596.5|6139.4|
|Discarded RGB-write fraction|33.37%|9.71%|
|Tile color-math pixel writes|40528|47493.3|
|Math results subsequently overwritten|2250|2792.4|
|Discarded tile-math fraction|**5.55%**|**5.88%**|
|Surviving tile-math pixels|38278|44700.8|
|Backdrop math pixels in these intervals|0|0|

The important distinction: Meteor does discard substantial **plain RGB** work,
but deferring *only math* removes a much smaller population. Semantic pixel
counts are not retired vector instructions: one8-lane operation can include
inactive lanes or mixed operand classes. No unit price follows from this table.

A simple one-byte metadata design would write metadata for each successful
main result, scan it in the existing final pass and read/write surviving RGB
again to apply deferred math. That model adds about295885 logical bytes/call
Meteor and299119 Quasar: metadata writes+reads and4 bytes per survivor for an
additional RGB read/write. It is not measured DDR traffic. Bitsets, tighter
fusion or other ownership designs change the model and their own costs.

Deferred-only math therefore moves **down** the initial implementation queue.
It must price the removed2250/2792 semantic math operations against metadata,
surviving-pixel RGB traffic, dispatch/cache effects and changed hot-loop shape.
This is a negative prioritization result, not proof that deferred math cannot
win. A whole winner-before-RGB architecture could target the larger plain
overdraw population, but is a broader change than the requested small fixes.

## Main/sub source sharing exists, but is not free production

Only warm nonblank full-tile rows are counted here. Identity requires the same
BG, destination offset, decoded-index row pointer, HFlip and palette pointer,
inside the same synchronous redraw. Main/sub depth and math remain separate.
Clipped/scaled/affine source descriptors are outside this metric.

| Full-tile source-row requests/call | Meteor | Quasar |
|---|---:|---:|
|Subscreen|4664|4704|
|Main screen|13102|11897.2|
|Identical main/sub requests|**3094**|**4410**|
|Matching fraction of main requests|23.61%|37.07%|
|Generic/OBJ palette-cache queries|1358.9|2065.9|
|Global palette-cache misses|6|5.85|
|All NEON palette-table preparations, including local tables|16|15.85|

This justifies investigating shared geometry/setup, not automatically a new
descriptor cache. Decoded indices already exist; a descriptor can add more
memory traffic than rereading a short cached row. Quasar's4410 matching rows
also equal the earlier hidden4bpp-row opportunity. Those populations may
overlap; their intersection has not been recorded. Do not add sharing credit
to hidden-row rejection credit. Eliminating a hidden consumer is preferable
to preparing a reusable intermediate for it, if the guard is profitable.

## Population results for the first pasted proposal

| Candidate, mean per difficult call | Meteor | Quasar | Consequence |
|---|---:|---:|---|
|Entirely clipped BG rendering calls|0|0|No peak credit;8/29 such calls over the whole1200-call replay. Actual tile loops already reject empty spans.|
|Entirely clipped OBJ rendering calls|0|0|Zero across all eight complete replays.|
|Conservative no-main-math-recipient entries|2|2|These cover only8 scanlines/call, not a whole screen. Qualify a small guard, not a huge traversal saving.|
|Full-width clipped sprite calls|0|0|Real source dispatch gap, absent at these peaks.|
|OBJ window searches|1071.7|1556.2|A possible bounded specialization; preparation/lookup costs still unpriced.|
|OBJ tile-loop visits|3577.4|4476.9|Keep genuine geometry, overflow and clip behavior.|
|Brightness palette rebuilds|2|2|One brightness0 and one nonzero rebuild per call:512 entries recomputed.|

The no-recipient predicate excludes pseudo-hires and color-window controls and
keeps backdrop math as a potential recipient. These are conservative population
counts, not qualification of a branch replacement. Depth values and other
derived renderer state may differ even when visible colors match, so use exact
output/state tests for any optimization.

Brightness is a useful small refinement: `mul_brightness[0]` contains zeros,
so its brightness0 rebuild can use zero fills for component/pixel arrays while
retaining XB pointer assignment, palette invalidation, flags and timing. That
avoids256 per-color lookup/packing operations per call in these peaks. It is
not skipping a palette change or the previously implemented fixed-color work.
No A7 time is assigned to it. Reusing arbitrary brightness palettes requires
correct CGRAM invalidation and cannot simply retain16 stale tables.

## DMA population now has a strict eligibility count

The first audit found~98% of VRAM byte helpers repeatedly clearing flags already
false. The followup counts a deliberately narrow contiguous-DMA envelope:
forward RAM/ROM source, one4KiB map block, VRAM mode1/5 via$2118/$2119,
increment1 after the high byte, no remap/custom chip, even byte count, no VRAM
wrap. Original fallback remains necessary outside it.

| Eligible DMA bookkeeping/call | Meteor | Quasar |
|---|---:|---:|
|Transfers|27|11.06|
|Contiguous bytes|1344|839.53|
|Existing3-per-byte flag store requests|4032|2518.59|
|Once-per-touched-tile flag store requests|165|101.82|
|Logical flag stores avoidable in this envelope|**3867**|**2416.76**|

This is a concrete span-copy/invalidation candidate, not a full DMA rewrite.
Transfer cycles, pending render flush, register/address results and HBlank
processing must remain identical. The observer calls the existing mapping
helper only for direct RAM/ROM blocks and all outputs remain exact; no optimized
DMA path has yet been implemented or timed.

## Memory ledger and decision

Both narrow peak intervals record a114432-byte **upper estimate** for explicit
main/sub depth initialization,512 bytes of explicit scalar RGB initialization
and57088 bytes of final backdrop depth scanning per call. The depth counter
charges a whole row even for a clipped sub-depth fill: its frozen field name
`explicit_depth_initialization_bytes` is broader than its true precision. It
must not be reported as exact transferred bytes. The backdrop usesNEON here.
The external256x224 strided display copy reads/writes114688 bytes each way.
These are separate logical request populations; they omit other tile loads,
masked vector read/modify/write traffic, scalar tails, CPU/APU/cache-line traffic
and vendor scaler accesses. They are **not** total DRAM bytes or bandwidth.

Start with the measured small repeated-work cases: strict DMA span bookkeeping,
the eight-row no-recipient decision, brightness0 rebuild and the proven ring-wrap
copy simplification. Keep sprite-window/OBJ setup sharing and hidden-row
elimination as larger, existing-renderer candidates. Give a full deferred-math
metadata pass a higher evidence bar; it is not first merely because the design
is elegant. Strip rendering is unmeasured and can undo the existing scanline
batching gains by repeating setup. Retain the timing core and exact reference.

No sum of these counts proves the1.31/0.80ms deadline saving or4.65/4.14ms
20% margin requirement. Price the complete isolated changes on A7 after
original-output qualification, including guards and interaction costs.
[Bounded measurements and input identities](../evidence/2026-10-13/architecture-populations/).
