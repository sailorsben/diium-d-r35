# Shared CPU-demand candidates, qualified offline

2026-10-14. Implemented fresh isolated candidates and two combined refinements
against the preserved measured core `e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129`.
The preferred **offline measurement candidate** is
`build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so`, SHA256
`1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8`.
It has the greatest qualified work elimination in these contexts; its A7 net
CPU saving and ranking against the isolated variants remain **unmeasured**.

No card access, installation, rearm, ROM modification, frame skipping, effect
disablement, CPU/APU simulation reduction or production promotion occurred.
All previously qualified trees and the exact measured reference remain intact.

## What changed

The new geometry producer chooses the first **eligible dual-plane background**
from live PPU state, once per synchronous redraw. It covers ordinary 2/4bpp
8×8 and16×16 tiles, scroll/tilemap wrapping, flips, original priority, different
consumer clips and captured per-row Window2 boundaries. Each plane still runs
its own transparency/depth and final math; the subscreen completes before
main-screen math. The producer stores compact tile geometry, never a decoded-row
or RGB cache. One layer is shared per redraw; unsupported modes/families retain
the original walker. OBJ traversal remains, with common last-palette preparation
reuse covering OBJ, clipped and other global-cache callers.

The qualified fused-toolbox-v2 sparse/hidden-row implementation and explicit
cache-alignment implementation are reused in fresh combinations. The initial
combination passed, but its census exposed a better Quasar mechanism: every
shared BG1 main cell in the heavy interval was hidden. The final refinement
uses a conservative maximum-priority depth test for each main clip before
per-tile setup. It handles plain main-screen clips only, respects clip boundaries
and scalar tails, and vetoes further probes after the first visible result in
that background call. A fully hidden clip changes neither RGB nor depth.

The strict DMA path is placed **inside the existing mode1/5 transfer**, after
the original pending-render flush, cycle charge and A-address update. It accepts
forward direct RAM/ROM within one4KiB map block, $2118/$2119, high-byte increment1,
even lengths and no VRAM wrap, remap or custom-chip complications. It copies
the span and clears each affected2/4/8bpp tile flag once. FirstVRAMRead, HBlank,
transfer-register finalization and every unsupported fallback remain in their
original control flow. This is DMA bookkeeping elimination, not fewer emulated
transfers or CPU cycles.

The audio ring replacement copies at most two spans for a valid direct read.
An initially qualified version used a generic modulo to update the start;
v2 removes that needless division with one bounded wrap subtraction. Brightness0
still advances palette epochs and sets XB, then zero-fills the four derived
color arrays. Appearance-only OAM changes retain flushes and latches but avoid
setting geometry dirtiness when position/size/VFlip are unchanged; rotation
remains conservative. The no-recipient guard hoists normal-renderer selection
without switching compositor branches, screen identity, clipping or depth bases.

## Direct output and retained ownership

The fresh runtime is `build/demand-private-v1/runtime-v1`, with compiled runner
`build/demand-private-v1/owned-output-runner`. Its producer reserves both an
existing free source slot and FIFO publication credit before entering the core.
`board_video_target` exposes that reserved slot with a32-byte prefix/tail.
The core acquires it only at the visible-frame boundary, for eligible256-wide
lores geometry. It updates Screen/S, SubScreen, both depth pointers, Delta,
DepthDelta, RealPitch/Pitch/Pitch2, PPL/PPLx2 and ZPitch together.

Compact auxiliary planes persist in core-owned buffers across direct frames.
The full original buffers remain available. Before hires, interlace, pseudo-hires
or unsuitable geometry expands output, the completed main prefix and all required
subscreen/depth rows migrate to the persistent layout. State load/cancellation
also restores it. Initial unsuitable frames use the original buffer. Extended
239-row lores is covered by the bounded allocation and synthetic tests.

An eligible callback publishes the reserved slot without copying its visible
payload. The core drops its main pointer after the callback and cannot read the
slot after ownership transfers. The worker releases the source only after
DrawVFB returns, retains output ownership through FlipVFB, and drains/joins before
teardown. Three slots/two READY jobs, FIFO order and cancellation remain intact.
Persistent-buffer fallback copies still use the normal submit path.

Additional footprint is explicit:35,520 bytes for240 bounded geometry-band
entries;247,808 bytes for compact auxiliary planes;192 additional chunk bytes
across the existing three slots for prefixes/tails. The full persistent buffers
remain allocated. Initial/transition auxiliary migration copies245,760 payload
bytes, plus any completed main prefix; each memcpy entails source reads and
destination writes. Successful steady-state direct frames copy only32 prefix
bytes into the safety margin, not114,688 visible bytes. Actual chunk cache and
coherency behavior, locality, code footprint and full CPU costs require A7 evidence.

## Optimization scorecard

These means use original replay indices384–415 Meteor and496–529 Quasar,
not a new physical timing run. Source requests, pixel stores, vector operations
and logical bytes are distinct units. All A7 unit prices below are missing.

| Optimization / implementation | Exercised coverage and removed work | Added costs / interactions | Exactness / remaining A7 measurement |
|---|---|---|---|
|Shared BG geometry: implemented, generic layer choice|Meteor BG0:91 main bands reuse16×16/window geometry;2038 main cells. Quasar selects BG1,19 bands; v3 rejects all570 main cells before descriptor consumption.|Meteor:12,012 tile-record write bytes and19,800 consumer-read bytes; Quasar:2508/2432. Also16 metadata write bytes/band, metadata reads,33 producer cells/band, guards and35,520-byte footprint. No decoded-row sharing saving claimed.|All18 original contexts and independent stock-walker fixtures. Price geometry/grouping removed versus complete production/consumption costs.|
|Hidden-clip rejection: implemented v3|Quasar19 clips eliminate570 per-tile setups and2280 descriptor-read bytes versusv2. Its4410 index rows were **already removed** by fusion.|Quasar exchanges4410 fused depth-vector checks for4410 clip checks: aggregate5319 before/after. New clip setup/veto costs. Meteor adds one failed vector probe and then vetoes.|Raw original replays plus3976 clip-bound checks. Price complete loop/setup change; no second4410-row saving.|
|Sparse/hidden-row fusion: reused qualified v2|Meteor keeps1940.0625 one-pixel and2038.6875 two-pixel sparse rows,3978.75 total in this interval. Quasar retains the prior hidden-index rejection.|Existing policy samples/veto, depth checks, sparse selection, ABI/code costs. Survivor index-row requests remain12,752/5288, unchanged by the new clip guard.|Original isolated evidence reused; new combination exercised across18 contexts. New A7 saving remains unknown.|
|Owned direct output: implemented core + runtime|One direct frame/call in both heavy intervals;114,688 visible bytes avoid source reads and slot writes on256×224 frames.|Acquisition/publication,32-byte prefix copy, compact aux footprint, transition migration, chunk-memory PPU access and ownership waits remain.|Original frames,1691 layout fixtures, real-core resolution/state seams, actual FIFO and native-client integration. Need real driver/cache/total-thread CPU costs.|
|Explicit alignment: reused qualified implementation|All three tile allocations and80 split palette tables retain64-byte guarantees; palette metadata/tables3840→3520 bytes.|Tile allocator over-allocation up to67 bytes/allocation on ARM32; linker padding. New last-palette key/table adds44 bytes of symbol payload plus independent padding.|Alignment asserted in every new combined context. No A7 baseline heap-pointer or cache-miss saving inferred.|
|Strict VRAM DMA: implemented|Meteor4032→165 flag-store requests; Quasar2518.588→101.824, removing3867/2416.765 requests per heavy call.|27/11.059 span guards; same1344/839.529 copied VRAM bytes, three range invalidations and original flush/cycles/HBlank.|12,000 actual-branch fixtures plus all18 replay contexts. Need native net transfer/bookkeeping price, not a store-count percentage.|
|Ring wrap: implemented; division removed in v2|Meteor5.3125→2.125 copy calls; Quasar2.20588→2.14706. PCM byte quota unchanged.|Two-span dispatch/wrap arithmetic; no ring modulo in the final ordinary path. Most calls save little.|1,501,760 actual replacement ring states, full-capacity reads, canaries; all18 PCM streams. Price actual distribution, never the synthetic512-copy example.|
|Brightness0: implemented|One zero rebuild/heavy call avoids256 lookup/packing computations.|Four array zero fills; palette epoch, XB and caller flags/timing retained.|All18 replays and full periodic state. Measure actual rebuild costs and nonzero guard misses.|
|OAM geometry dirtiness: implemented|4.719/14.971 appearance write sites avoid setting the dirty flag; these are **not** removed rebuild counts.|VFlip/position/size comparison and conservative rotation handling. Later geometry writes may already demand a rebuild.|2048 original complete scheduler/latch fixtures and replays. Earlier peak rebuild census was zero redundant rebuilds: **zero peak credit**.|
|No math recipients + last palette: implemented|Normal-selection guard covers8 scanlines/heavy call. Last-key reuse avoids958.594/1586.353 global palette queries, including OBJ callers.|Predicate/key checks on all relevant calls, last-table/key stores on misses and epoch invalidation. Separate screen/depth semantics retained.|All18 raw graphics/PCM/state contexts. Guards/materializations/ABI costs unpriced.|

The old BG0-only shared-geometry experiment remains rejected for zero positive
hits. A full deferred-math/RGB-winner architecture is not introduced: only5.55%/
5.88% of tile math was overwritten, while metadata and survivor traffic would be
new costs. The existing NEON backdrop and small palette cache receive no new
conversion credit. A duplicated OBJ row/RGB descriptor cache is not introduced
without evidence that its tags/stores/reads beat the existing cached8-byte indices.

## Qualification, including a negative boundary result

V1's five isolated/combined pairs pass216,000 original-command calls. V2 andv3
each add43,200: **302,400** comparisons across18 contexts. Every call compares
raw graphics and native PCM bytes and dimensions; normalized emulated state is
compared every30 calls. Completed unchanged peak replays were reused, not rerun.
This is offline correctness, not physical input/audio/display or A7 performance.

The independent original walker covers8/16 tiles, all four layers, flips,
priorities, scroll/wrap, separate/empty clips and per-row windows. V2 additionally
checks a dual-enabled but ineligible BG0 followed by eligible BG1. The final
clip guard adds3976 endpoint/vector/tail bounds and a wholly hidden original
command-stream test; actual ARM NEON executes in the original replays.

The unmodified synthetic239-line test initially matched pixels/PCM but failed
state at frame240. **Two byte-identical reference binaries reproduced it.**
`S9xStartHDMA` clears current pointers but leaves base pointers stale; an immediate
zero-line termination subtracts NULL minus the stale base and writes allocator-
derived low bits into IndirectAddress and$43x5/6. This is not a legitimate emulated
field to mask away. The original failure/control receipts are retained.

Fresh test-only reference/candidate clones initialize both HDMA host pointers
together. No emulated state fields are masked and all DMA/CPU/APU execution
continues. Each v2/v3 clone pair passes8400 real-core synthetic calls across
Mode5/6 promotion, interlace,239-row and pseudo-hires transitions, positive initial
hires fallback and repeated state loads. **Final candidate HDMA code is unchanged.**
These common-fixture tests isolate output layout; they do not resolve the baseline
HDMA defect or prove universal stock-register fidelity in artificial height schedules.

Actual board FIFO fixtures cover mixed direct/copied jobs, cancellation, full
READY credit while FlipVFB blocks, source release and joined teardown. The actual
final core/new runner with an independently consuming44100/128/3712 native provider
passes149 direct callbacks, truthful failure/retry, two snapshot/resume cycles,
drain, preserved failed-session evidence and sustained-deficit rejection. The
physical vendor scaler/coherency path remains unqualified.

Setup failures remain private: a local symbol collision, a test allocation's
missing16-byte alignment, fixture compile/include/link errors, and the counter
ABI expansion in the transition harness. None is a suppressed output failure.

## Saving model and next A7 test

Use net incremental prices in a declared order:

`S_total = S_fused + S_alignment + S_DMA + S_small + S_geometry + S_owned + S_clip - A_interactions`.

Geometry prices grouping/map/flip elimination against extra producer cells,
record writes/reads and guards. Clip rejection prices removed tile setup and
descriptor reads against its replacement depth loop/setup. Quasar's aggregate
depth-vector count stays5319; its4410 hidden index rows receive no new saving.
Owned output prices the removed strided copy against chunk PPU access, acquisition,
publication and migration. Do not add the whole callback0.82–0.86ms or count
worker CPU twice. Alignment has no assigned cache-miss or millisecond saving.

All prices and therefore net milliseconds/remaining audio deficit are **unknown**.
Prior failure windows need approximately1.3083/0.8033ms to reach16.6881545ms and
4.6460/4.1409ms for a20% CPU margin. These are requirements, not predictions that
the new combination closes them. APU-inclusive4.2ms and residual4.5ms remain
inclusive buckets. Actual C shows SPC port reads/writes call `spc_run_until_`
outside `S9xAPUExecute`; the residual is not pure65C816 time. CPU/APU rewriting
requires disjoint inner attribution before further surgery.

The [72-epoch local plan](../evidence/2026-10-14/demand-optimization/measurement-plan.json)
compares nine counter-free variants on the exact Meteor/Quasar states in repeated
forward/reverse orders,1200 calls each. It is **not staged or armed**. Use kernel
syscall scheduling/thread-CPU clocks around complete calls/steps; disable nested
phase clocks/work counters, include observers and disjoint worker CPU, never
calibration-subtract or assume sustained666MHz. Record both zero-based replay
index and one-based runtime call so late-window alignment is explicit.

Measure complete effect/recovery, accepted PCM, consumption and capped reserve
with valid pointer accounting. Require matched reduction in total main+audio+
display CPU without new output, ownership, pointer or native PCM failures.
No gain, regression, unchanged/worse reserve drawdown, a missing drawing/sample
or failure falsifies the corresponding benefit claim. Compute the remaining
deadline/headroom deficit from that result; buffering needs complete maximum
prefix deficit and capped-reserve drawdown plus declared margin.

Future card work requires new explicit authority, a fresh full log/progress
archive, identity/FAT/stock hashes, an exact pushed source and independent payload
readback. Preserve `emu_sfc.so`, existing candidates and saves. A measurement
experiment does not promote a candidate or waive the documented installation gate.

## Reproduce and review

Use fresh output directories; preparations refuse existing trees. Required private
original inputs, frozen source trees, ARM compiler/QEMU and2.30 sysroot must exist.

1. `prepare-demand-v1.py`, `build-demand-v1.sh`, `qualify-demand-v1.py`;
   `check-demand-seams.py`, `check-demand-oam.py`, `check-demand-runtime.sh`.
2. `prepare-demand-final.py`, `build-demand-final.sh`, `qualify-demand-final.py`,
   `check-demand-final-seams.py`, `check-demand-native.py`;
   `prepare-demand-transitions.py` / `build-demand-transitions.sh`, then the
   reference control and fresh `--deterministic` transition tests.
3. `prepare-demand-visible.py`, `build-demand-visible.sh`,
   `qualify-demand-visible.py`, `check-demand-visible-seam.py`,
   `check-demand-visible-integration.py`.
4. `publish-demand-review.py` verifies frozen artifacts/old publications and
   writes bounded receipts plus input/source hashes. It publishes no binary,
   ROM, SRAM, state, raw PCM, full archive or attachment/account material.

[Analysis and qualification](../evidence/2026-10-14/demand-optimization/analysis.json),
[symbolic saving model](../evidence/2026-10-14/demand-optimization/saving-model.json),
[source/input identities](../evidence/2026-10-14/demand-optimization/inputs.json).
