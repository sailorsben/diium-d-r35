# Pearl: work backward from C, test shapes, then price the replacement

2026-10-13. Offline investigation only. No card access, installation or rearm.
The fullpaths1 measurement already staged on I: stays byte-for-byte unchanged.
Every frame, native PCM and logical state remain part of qualification.

## What the 3.310 ms means

Pearl is HOLY/0x0e. The matched ability2 expensive tail, calls 399–414, averages
17.6605625 ms per step. The cycle-derived deadline is 16.6881545 ms; the proposed
20% capacity target is 13.3505236 ms. Total required saving is 4.3100389 ms.
The staged three-path forecast is a **judgmental 1.0 ms**, not a returned result.
Thus 3.3100389 ms is the *conditional remaining target*, not measured remaining
cost or a claim that the staged build has already saved 1 ms. Whole-effect and
recovery service remain necessary; this tail mean is not a worst-case bound.

## Actual executed rendering work

The owned census subdivides plane/layer, full/clipped entry, row visits,
depth rejection, opaque masks, visible pixels, overdraw and math mode. It uses
the actual C at the aligned replay state, with no elapsed-time interpretation.
The census itself passes 1,200 exact original-core pixel/PCM/state comparisons.

Mean work per expensive call, on the staged combined source:

| Plane and layer | Full tile calls | NEON row visits | Entire row hidden by depth | Active rows | Active pixels |
| --- | ---: | ---: | ---: | ---: | ---: |
| Main BG1 | 849 | 136 | 0 | 132 | 738 |
| Main BG2 | 849 | 6,330 | 255 | 6,075 | 47,339 |
| Main BG3 | 5,143 | 4,723 | 4,275 | 401 | 2,250 |
| Main OBJ | 2,208 | 1,345 | 97 | 660.0625 | 3,539.6875 |
| Sub BG3 | 4,569 | 4,569 | 0 | 4,569 | 36,552 |

There are also 270 clipped calls on each BG3 plane. Blank tiles can return before
a row visit; full-call counts and row visits are different populations. BG1/BG2
are 4bpp, BG3 2bpp. Main BG2 performs 4,166 full-add and 1,909 full-subtract rows.
Row/mask/pixel counts in this table cover the full-tile NEON helper; they are
not a census of scalar clipped-pixel work. The separate clipped-call count is
retained rather than silently treated as zero pixel cost.

**Why the work grows:** rendering is repeatedly entered while the effect changes
scanline state. The tile walker still visits BG3 underneath already drawn higher
priority pixels. `DrawTile16` originally performs address/cache/palette setup
before its row loop discovers that all eight depth comparisons fail. Separately,
the subscreen draws BG3 through the generic competition/masking path even though
it is the only enabled subscreen layer. Most of this is implementation work, not
additional SNES emulated cycles or an audio quota error.

This identifies redundant work; it does not establish its microsecond share.
The older roughly 71% PPU growth attribution concerns a Bio Blast interval and
must not be relabeled a Pearl phase measurement.

## Tested hypotheses and corrections

1. **Share BG1/BG2 between main/sub: rejected for Pearl.** The census finds zero
   eligible shared rows. The subscreen is BG3, not a duplicate BG1/BG2 image.
2. **Reject a hidden tile before its preamble: activates.** An eight-lane NEON
   depth check tests every requested row using the original strict `Z1 > oldZ`
   rule. If every pixel loses, return before indexed cache/palette setup. Mean
   Main BG3 full calls reaching the original preamble fall from 5,143 to 380:
   **4,763 preambles removed**, covering 4,803 requested rows. Surviving row visits
   fall from 4,723 to 448. The difference includes formerly blank tile returns;
   do not add those populations as independent savings. The function call itself
   still occurs in this prototype. Moving the test into the caller is a possible
   next refinement, not credited here.
3. **Constant-color whole-band fill: rejected as a Pearl optimization.** Exact
   independent fixtures pass, but real Pearl never activates it. The follow-up
   shape probe finds 147 eligible sole-subsurface scanlines, **16x16 tiles**, and
   zero full rows with equal indices or equal colors. All 4,569 are opaque.
   Flat opacity is not flat color. No speed credit is assigned to this path.
4. **Inline sole-layer 2bpp subscreen production: activates.** Full tile cells
   whose indexed cache is valid expand directly inside the background walker.
   The sole-layer guard excludes OBJ/other subscreen layers, pseudo-hires,
   scaled output, direct color and incompatible depth pitch. There is no competing
   depth, so opaque rows use direct color/depth stores; transparent rows preserve
   old destinations with a transparency mask. Cold tiles use the unchanged
   converter/fallback. Palette context lives only within one background call.
   Pearl takes the opaque path for **4,569 rows/calls**, with zero transparent
   fast-path rows in this interval. Pixel production/stores remain; these rows
   are accelerated, not eliminated.

The ARM symbol table contains no out-of-line `d35_sub2` helper in the qualified
counter-free combination, consistent with actual inlining into `DrawBackground`.
The original `DrawTile16` remains for fallback/other work. Do not count removal
of all tile address/cache/palette work: the specialized producer still needs it.

Both successful mechanisms are state/data predicates, with no spell names or
effect IDs in the renderer. Unsupported shapes use the original renderer.

The first subscreen integration failed original-output comparison at frame 264:
an inserted unbraced `if` captured an outer flip `else`. Preserve private v1;
v2 wraps each replacement in a block. This was an offline C integration error,
not evidence that the sole-layer invariant is false. Initial census export
visibility and a nested build sysroot path also failed and were corrected before
qualification. A legacy 406-overlay checker was attempted but rejected the new
core at startup for missing diagnostic symbols; no overlay coverage is claimed.

Independent fixtures compare the real original scalar renderer, not another
copy of our optimization: 64,512 depth/full/clipped tile cases, including equality,
all-hidden/all-visible depth, flips, 2/4bpp, clipping, negative X, pitches and
canaries; 2,304 sole-layer cases cover blank/transparent/opaque indexed data,
flips, pitches and edge preservation. A separate scalar planar/map walker passes
258,048 flat-band cases and four rejection-without-partial-write cases, despite
that mechanism having no Pearl applicability. The public qualification receipt
records the original-command replay results and core identities. None is A7 timing.
Across the five separate/combined experiments, counted and counter-free builds
pass **216,000** original-command calls (18 contexts x 1,200 x 10), in addition
to the initial 1,200-call census and 1,200-call shape probe. See the bounded
[qualification](../evidence/2026-10-13/pearl-workback/verification.json),
[work and shapes](../evidence/2026-10-13/pearl-workback/shapes.json), and
[threshold calculation](../evidence/2026-10-13/pearl-workback/prediction.json).

## Break-even calculation before another A7 build

Define h as net microseconds saved by each of the 4,763 successful early rejects
after its successful depth probe; s as net microseconds saved by each of the
4,569 inlined subscreen calls, including retained expansion/stores/palette work;
b as other added cost per expensive call, including failed probes, eligibility
checks, context/cache effects and interactions. All must ultimately be measured
in the aligned A7 context, with workers live and observer costs included.

```
additional saving us = 4763 h + 4569 s - b
20% target requires 4763 h + 4569 s - b >= 3310.0389
```

This is conditional on the earlier 1.0 ms staged-build forecast. Replace that
forecast with measured combined saving P when the staged crossover returns:
the right side becomes `4310.0389 - P` microseconds. Do not sum separately timed
path gains in place of the measured combination.

| Hypothetical net h us | Net s us required, if b=0 |
| --- | ---: |
| 0 | 0.724456 |
| 0.20 | 0.515964 |
| 0.35 | 0.359595 |
| 0.50 | 0.203226 |

Early rejection alone would require h >= 0.694948 us. Equal net prices require
about **0.354698 us** per affected call, before b. With a further 250 us of added
cost that equal-price threshold becomes about 0.381487 us.

For sensitivity only: h=s=0.30 us gives 2.7996 ms, **0.5104 ms short**. At 0.40 us
each, gross saving is 3.7328 ms, **0.4228 ms beyond** the conditional target before
b; after b=0.25 ms, 0.1728 ms remains. Conditional total step in the latter case
is 13.1777625 ms, about 21.04% margin to the nominal deadline. These are arithmetic
scenarios, not measured units, a forecast band, confidence limits or a passed gate.

Past mixed A7 transitions make this an attractive test surface, but do not price
it: Bio Blast removed thousands of tile calls together with palette/cache changes;
Holy's earlier gain also includes renderer restarts and a different tile mix.
Hidden rows already avoid palette expansion inside the old row loop, and the
new subscreen path still does decoding lookup/expansion/stores. Treating either
as a removed generic full tile at an invented price would exaggerate the saving.
**The evidence supports these two concrete levers; it does not yet justify
predicting that they supply the whole 3.310 ms with room to spare.**

## What other implementations contribute

Pinned sources were read without running their code or publishing vendor files:

| Source | Useful mechanism | Applicability boundary |
| --- | --- | --- |
| [Supafaust, 642d1d1](https://github.com/libretro/supafaust/tree/642d1d1b6684aa7e306a02a89885f3f5456a5157) | Separate layer production, priority selection, then final main/sub color math in `ppu_render_common.inc` | Genuine Cortex-A7-oriented implementation; its recommended dual-core clocks do not prove a limit on this single-core runtime. It also offers a single-thread renderer. Representation/order differ from our RGB565 pipeline. |
| [Snes9x 2010, fe690dd](https://github.com/libretro/snes9x2010/tree/fe690dd321fa5a46b5234a2bde089d2518c62b0e) | NEON tile color composition; direct frontend framebuffer opportunity | Much of the tile SIMD pattern is already present here. Its `apu.c` Gaussian function is scalar: README SIMD wording does not establish a drop-in NEON Gaussian implementation. Display ownership/chunk requirements constrain zero-copy reuse. |
| [Snes9x 2002, 6ffbf9e](https://github.com/libretro/snes9x2002/tree/6ffbf9ef4f0063e1f1b78a40d10c50fc52f2524c) | A7 build tuning and optional ARM/SPC assembly | A7 flags are already used; assembly enablement and state/timing ABI must be established. Compiler flags alone are no predicted saving. |
| [ARM SPC, 609c02b](https://github.com/nathancassano/snes-spc-arm/tree/609c02b00851bddc6adeda90c073fcccb784c346) | Actual SPC700 ARM assembly and interleaved Gaussian coefficients | Borrow layout while preserving each truncation/overflow stage. The fast DSP approximation changes arithmetic and is rejected under exact PCM. Not an A7 timing receipt. |
| [quickerSnes9x, 7deccd9](https://github.com/SergioMartin86/quickerSnes9x/tree/7deccd9baacb3b1a77296ce8582ba50f7bd2bcdb) | Headless TAS/re-recording optimization approach | No demonstrated A7 full graphics/audio timing transferable to this target. |

Supafaust's final-mix architecture is worth retaining as a design alternative,
but Pearl has one dominant math layer: 6,075 BG2 rows. Only 2,250 later BG3 pixels
overwrite previous main pixels, at most 281.25 eight-pixel rows' worth of avoidable
math from that overwrite (about 4.63% of BG2 row work if all overwrote math).
That does not support crediting several milliseconds to deferred math alone;
additional tag buffers and composition also cost time.

The remaining approximately 2,905 interpolations would each have to save about
1.139 us to supply 3.310 ms by themselves. Coefficient layout/assembly deserves
investigation as a secondary path, but no measured isolated price supports that
credit yet. Do not switch to approximate interpolation, cheaper envelopes,
frameskip or a smaller simulation/audio quota to manufacture a pass.

## Missing evidence and falsifiable result

First archive and analyze the already staged fullpaths1 return. It should identify
P, interaction, frequency visibility, heavy-interval service and reserve, and
whether pacing/observers consume the tiny old forecast margin. No new diagnostic
or card change is needed to discover that result.

For these new paths, remaining measurements are h, s, b and their combined A7
distribution in aligned heavy state, not more work counts. Whole-effect/recovery
deadlines, cold behavior, repeated casts, frame delivery and final audio/display
worker accounting must accompany any acceptance claim. If a future explicitly
authorized measurement compares staged-combined, early-depth, sole-sub and both,
the prediction is exact output plus eliminated main BG3 preambles and direct
subsurface rows at the populations above. A result below `4310.0389 - P` us saving
fails the proposed 20% tail gate. A tail pass without complete-effect/recovery
capacity evidence still does not establish a production fix or universal safety.

## Conditional table for the failed contexts actually staged on I:

The current staged version is1.19-fullpaths1: ability2 baseline, fixed rows,
subscreen, DSP and combined variants, each repeated in ten contexts. The two
newest depth/sole-sub paths are offline prototypes and are **not installed**.
Eight staged contexts failed the earlier ability2 physical test; Bio Blast and
Confuser are completed controls. Their healthy paced wall time is not a new
service/headroom forecast and is excluded from this failed-tail table.

To compare all eight with explicit assumptions, transfer the historical
fixed-row restart-bundle range and scale Pearl's unmeasured subscreen/DSP
allowances by each context's eligible counts. Price the newest successful depth
rejects and sole-sub calls at0.30–0.40us net each, with other added cost b=0.
These are **illustrative engineering scenarios, not an observed range or
confidence interval**. The new price and transfer assumptions can be wrong;
additional cost reduces saving. Whole-effect/recovery acceptance remains missing.

| Ability | Last A7 tail ms | Total scenario saving ms | Conditional new service ms | Interpretation against16.688ms deadline /13.351ms target |
| --- | ---: | ---: | ---: | --- |
| Pearl/Holy |17.66|3.79–4.77|12.89–13.87|Below deadline;20% target crossed within scenario range |
| Meteor |18.47|0.76–0.87|17.60–17.70|Still misses deadline |
| Meltdown |17.56|1.02–1.12|16.43–16.54|Below deadline with thin margin |
| Siren |18.52|3.63–4.03|14.49–14.89|Below deadline, below20% target |
| Bahamut |17.09|1.07–1.17|15.92–16.02|Below deadline with modest margin |
| Carbunkl |17.57|4.02–4.50|13.07–13.55|20% target crossed within scenario range |
| Quasar |17.55|1.14–1.24|16.31–16.41|Below deadline with thin margin |
| Lullaby Rage |18.70|3.99–4.47|14.24–14.72|Below deadline, below20% target |

New-path populations are not uniform across effects: Pearl has4,763 successful
early rejects plus4,569 sole-sub calls. Meteor/Meltdown/Siren/Bahamut/Quasar have
488 early rejects and zero sole-sub calls; Carbunkl/Lullaby have1,058 and zero.
The newest paths consequently contribute2.800–3.733ms to Pearl in this scenario,
0.146–0.195ms to the former group,0.317–0.423ms to the latter. Do not transfer
Pearl's gain wholesale to Meteor. Meteor remains the clearest unresolved target.

Reproduce with `python build/forecast-pearl-cases.py`; the bounded
[case calculations and assumptions](../evidence/2026-10-13/pearl-workback/forecast-cases.json)
pin every compared census log. No new build, replay, card access or returned
fullpaths result was used for this table.
