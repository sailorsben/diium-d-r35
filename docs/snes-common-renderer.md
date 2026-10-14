# Shared renderer work across the failing effects

2026-10-13. Offline source/assembly review and original-output qualification.
No card access, install or rearm. The staged version remains1.19-fullpaths1.
The common-band v3 candidate is separate and its production gate is NOT MET.

## Finding

All eight staged failures use the same ordinary indexed background renderer.
They do not need eight spell-specific C fixes. In their aligned expensive tails,
the main BG2 path visits about6,200–6,330 full-tile rows, including1,909 active
full-subtract rows in each case. Additional background planes differ by effect.
The full-tile ABI boundary and palette/depth/store work recur across those planes.

`DrawBackground` originally calls `DrawTilePtr` separately for each full8-pixel
tile cell. `DrawTile16*` computes address/cache/palette state, prepares vector
tables, loops over its rows and returns. ARM disassembly of the qualified Pearl
combination's `DrawTile16Add` shows nine GPR saves plus four double-register saves:
68 bytes saved/restored per entry, plus84 bytes of allocated scratch. Allocating
scratch is not itself84 bytes of memory traffic; stack traffic is not equivalent
to DRAM traffic or a measured cycle count. These quantities must not be converted
to microseconds with an assumed frequency.

The shared candidate processes the middle cells of an existing clip/scroll band
inside a constant-mode producer. It pays its ABI prologue once per band and keeps
the same tilemap wrap,16x16 quadrant, flip, indexed transparency, priority and
color rules inside that loop. Plain, full-add and full-subtract have separate
band functions, so color math remains constant and inline. The original converter,
clipped edges, unsupported arithmetic, direct color, mosaic, offset and hires
paths remain the fallback. The prior Pearl sole-subscreen/early-depth paths remain
part of the candidate; their original savings are not re-counted as common work.

Within each `DrawBackground` invocation, a valid mask owns up to eight palette
tables. First active use in a tile obtains its table; later rows use the local
vector value. Palette contents cannot change while this synchronous renderer is
running. The context expires at return, before the emulated CPU can perform its
next PPU write. No global palette epoch or VRAM tile-cache invalidation is removed.
Only the valid mask is initialized; unused palette slots are not read or cleared.

When every lane is visible, the existing RGB direct store is paired with a
direct depth store. Partial rows retain the original masked pixel/depth merge.
The old generic helper already optimized full RGB stores; only the additional
depth/branch consequences are new. Do not claim that every visible row's pixel
production or math is eliminated.

## Measured offline work, not measured A7 time

Means per expensive call, at each case's archived ability2 tail indices:

| Context | Former full-tile calls handled inside bands | New band calls | Opaque rows eligible for direct depth store | Batch palette materializations |
| --- | ---: | ---: | ---: | ---: |
| Pearl/Holy |2,078|378|5,920|7|
| Meteor |8,208|332|6,875|10|
| Meltdown |6,726.75|237|14,190.125|11|
| Siren |6,102.0625|222.625|5,869.6875|9|
| Bahamut |4,827.5|195.5|12,674.25|13|
| Carbunkl |2,057.5|103|5,739.8125|8|
| Quasar |10,055|353|10,556|10|
| Lullaby Rage |3,750.1875|161|3,463.8125|8|

The former calls include warm blank returns. Do not price them as rendered pixel
rows. The table excludes the already qualified early-hidden and sole-subscreen
work from its former-call credit. Band calls still have a cost: subtracting counts
does not establish that a new band call has the price of an old tile call.
Sprite calls and clipped edges are still present. No universal game coverage or
universal positive net saving follows merely from nonzero eligibility.

## Why these choices follow from the C

The review followed CPU dispatch/WaitAddress ownership, Blargg interpolation,
envelopes and DSP clock scheduling, PPU register flushes and captured state,
background/OBJ/mosaic/Mode7/clipped renderers, NEON color/cache/store helpers,
and runner resampling/publication/display ownership. This is a review of the
shared execution path and each effect's archived work, not a claim to optimize
every line of the emulator or replace the game's animation scripts.

| Candidate area | Evidence and judgment |
| --- | --- |
| Full-tile dispatch, palette setup, opaque stores | Thousands of recurring operations in every failure; implemented and qualified as common-band v3. |
| Further Window2/fixed-color restart removal | Already reduced to five top-level renderer entries in these sampled calls. Old mixed restart-bundle prices do not price an individual tile ABI entry. |
| Tile decoding alone | Only0–21.75 decodes per sampled heavy call across these eight, versus thousands of dispatches. It cannot receive a multi-ms credit from occurrence counts. |
| General early-depth prepass | Hidden rows vary sharply by layer/effect. A blind extra prepass on every4bpp/math tile adds work to the many visible tiles. Retain the qualified guarded2bpp case; do not assume a universal win. |
| Fixed-math cache / arithmetic alone | Ability3 is a physical negative result. Existing NEON arithmetic remains exact; do not reuse its small/negative physical gains as a new millisecond claim. |
| SPC/Gaussian optimization | Remaining interpolation is shared, about2,509–3,122 voice interpolations per heavy call. An interleaved coefficient layout/ARM implementation remains a secondary option; approximate DSP arithmetic, fewer clocks and altered envelopes are excluded. |
| CPU opcode state | `PCAtOpcodeStart` feeds real WaitAddress/PPU logic. It is not removable debug bookkeeping. Blargg builds already make the legacy `APU_EXECUTE` macro a no-op. |
| Resampling/logging/display | The runner already uses the exact178/245 constant-divisor conversion and RAM records. Do not remove audio, change cadence or omit display frames; actual worker/service costs still belong in the A7 gate. |

The band boundary is consistent with the previously researched
[Supafaust](https://github.com/libretro/supafaust/tree/642d1d1b6684aa7e306a02a89885f3f5456a5157)
principle of keeping layer production/composition together. This is a bounded
change to our pinned C/NEON renderer, not a port of its formats, state or threaded
renderer. Its hardware recommendations and other cores' benchmark claims do not
price this candidate on the D-R35.

## Offline negative designs and checks

Generic v1 passes43,200 original-command calls, but assembly exposes out-of-line
`d35_blend` calls inside the pixel-row loop. It is rejected as a performance
design: fewer tile calls can come with more row calls. No A7 regression is claimed
from assembly alone.

Constant-mode band v2 passes another43,200 calls and retains inline color math.
Its one-palette context still checks inside the row loop and rebuilds palettes
256 times in Quasar's tail. Final v3 moves the check to first active use in each
tile and retains eight palettes per background call; Quasar falls to10 batch
materializations. That is a **v2-to-v3 prototype comparison**, not a claim that
the staged core currently rebuilds256 palettes. The original global palette
cache has a different hit/preparation cost.

Final v3 passes43,200 calls across18 original-command contexts, counter-free and
counted: exact visible graphics, native PCM/geometry and periodic normalized
state. The three variants total129,600 new comparisons. Independent original
scalar rendering matches129,024 final tile cases, covering all seven arithmetic
modes,2/4bpp, depth equality/hidden/visible/partial masks, blank tiles, flips,
negative-X clipping and256/512 pitches. Another3,584 cases draw16 repeated palette
cells, covering all eight palettes and the final4bpp palette at color255.

The ARM assembly checks require actual named functions and reject out-of-line
blend calls in all three final band producers. Their cold-cache indirect fallback
remains deliberately present. Those checks establish the intended structure;
they supply no A7 time. Every frame/sample and the same emulated cycle contract
are retained. No per-row device clock instrumentation was added.

## What the common saving must buy

For each aligned call, define D as former tile calls handled by the common path,
O as its opaque rows, e as removable old entry/palette cost, r as incremental
opaque-store saving, and b as all new band/cache/mode/spill/interaction cost:

```
S_common_us = D*e + O*r - b
```

All terms require A7 prices or a matched whole-combination difference. Counts of
instructions, renderer entries, cache hits or inclusive PPU time do not provide
those prices. Larger local context, band-call prologues and cache effects belong
in b. The added cost must not be subtracted as observer calibration.

Conditioning on the **earlier unmeasured** all-new-code forecast, Meteor still
needs0.9123–1.0144ms to reach the16.688ms deadline, or4.2500–4.3520ms to reach the
proposed13.351ms/20% target. Normalized over its8,208 handled cells, that requires
about0.111–0.124us **net** per cell for the deadline, or0.518–0.530us for20%.
Net here includes allocation of all added costs and any row-store benefit; it is
not an isolated microbenchmark price or a prediction that we will achieve it.

Other effects also need headroom. Under that same conditional forecast, Bahamut
requires about0.532–0.553us net per handled cell to reach20%, Meltdown about
0.459–0.474us, Quasar about0.294–0.304us, and Siren/Lullaby smaller but nonzero
credits. A deadline-only Meteor pass therefore does not establish comfortable
headroom across the suite. Replace the prior forecast with actual staged-combined
and Pearl-path measurements rather than stacking assumed gains.

## Next physical boundary

Archive/analyze the already staged fullpaths1 return first; nothing here changes
its payload or consumes another hardware test. All160 frozen source,90 payload
and25 proof hashes remain exact. New common candidate identities and bounded
receipts are in [verification](../evidence/2026-10-13/common-renderer/verification.json),
[per-case scorecards](../evidence/2026-10-13/common-renderer/analysis.json), and
[final qualification](../evidence/2026-10-13/common-renderer/band-v3.json).

A later explicitly authorized A7 measurement must compare the same full-fidelity
baseline with the entire common candidate, include worker/observer costs, record
frequency conditions and complete effect/recovery/frame/audio accounting. No new
hardware install, production qualification or proof of hardware impossibility is
claimed by this offline work.
