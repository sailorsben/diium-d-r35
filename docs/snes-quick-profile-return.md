# A7 profile return: rendering dominates effect growth

Archive `a7-pair-before-20261014T033243Z` preserves6317 retro files,
1,657,276,489 bytes. FAT is clean, all18 installed payload hashes and frozen
local source/proof identities match, stock boot/core and previous progress
remain unchanged. Original ROM ZIP hash rechecked read-only. Only the expected
owned dispatcher and swapfile differ from the preinstallation archive. The
one-shot marker is consumed; I: remains unarmed. Card writes: zero.

## What actually ran

| Epoch | Context | Calls | Submitted/flipped drawings | Phase samples | First invalid PCM pointer |
|---|---|---:|---:|---:|---:|
|0|Meteor, control|417|416|0|411|
|1|Meteor, profile|411|410|51|406|
|2|Quasar, profile|509|508|64|496|
|3|Quasar, control|529|528|0|520|

All four epochs ended with native PCM `SYNC_OBSERVE errno77`, not a captured
CPU signal crash. The terminal interrupted call does not submit its drawing.
No intentional frame skipping, duplicate drawing or hold is recorded. The
wrapper finishes, joins both workers and frees the display. Total recorded
core calls1866, drawings1862. This is useful profiling evidence, not a full
effect or production-gate pass. Remaining PCM is preserved/accounted, not
silently cleared. Frequency remains unexposed (`-1`); no assumed MHz conversion.

## What grows

These are measured, observer-inclusive CPU milliseconds per sampled call.
The early warm reference is calls120-239 (15 samples each). Meteor's narrow
heavy comparison uses387,395,403; Quasar uses499,507. The latter stops before
the previous worst508-529 interval, and its PCM pointer is already invalid.
It establishes rendering cost, not healthy playback or the complete peak.

| Region | Meteor early | Meteor heavy | Quasar early | Quasar heavy |
|---|---:|---:|---:|---:|
|Whole core call, including callbacks/observer|12.312|17.595|12.368|16.635|
|PPU `S9xUpdateScreen`|3.320|7.908|3.321|7.044|
|APU `S9xAPUExecute`, inclusive|3.880|4.277|3.895|4.234|
|Video callback, outside both regions|0.825|0.824|0.809|0.859|
|Residual after PPU/APU/video|4.287|4.586|4.343|4.499|
|Audio callback, overlaps APU/residual above|0.190|0.210|0.191|0.187|

PPU grows4.587ms of Meteor's5.283ms whole-call increase (**86.83%**).
For Quasar it grows3.723ms of4.267ms (**87.26%**). APU-inclusive growth is only
0.397/0.338ms. Video callback growth is negligible for Meteor and0.049ms for
Quasar. This independently supports the rendering diagnosis for both effects;
the exact percentages are descriptive of these finite intervals.

Broader samples support the direction: Meteor352-407 has7 samples averaging
6.863ms PPU; Quasar416-479 has8 averaging6.842ms PPU, before its first invalid
pointer. The narrow late intervals describe higher load, not the entire effect.
Full distributions and sample counts are in the bounded analysis receipt.

Source correction to earlier broad-profile labels: the video callback is after
`S9xMainLoop` in `libretro.c`, hence outside PPU and APU regions. Audio can be
published inside `S9xAPUExecute` via `sa_callback`, while the final
`audio_upload_samples` call is outside it. Total audio callback CPU is therefore
partly nested, not universally nested. Do not add it again or subtract it
wholesale from either residual or APU. Residual still includes SNES CPU,
port-driven SPC/DSP execution, final audio upload, dispatch and observer costs.
It is not a measurement of pure65C816 time. The frozen runner/report metadata
is retained unchanged; this return analysis supplies the narrower interpretation.

## Measurement disturbance

| Profile minus aligned control CPU | Meteor | Quasar |
|---|---:|---:|
|Sampled calls, mean|+1.271ms (36 warm samples)|+1.315ms (49)|
|Sampled calls, median|+1.260ms|+1.308ms|
|Sampled calls, p95|+1.406ms|+1.477ms|
|Unsampled calls, mean|-0.007ms|+0.042ms|

The profiler is not free. One-in-eight sampling implies roughly0.16ms/call of
sampled-call disturbance spread over time, before unsampled differences; this
is an estimate from one matched pair, not an exact observer-price calibration.
It is consistent with earlier profile failures (6/20 fewer calls), not proof
that instrumentation alone determines the fault call. APU entry clocks execute
at scanline boundaries, so this seemingly coarse profile still performs many
kernel reads on sampled calls. Startup clock loops report1.24-1.50us/read;
never subtract these from phase results or assume the entire difference belongs
to APU. Sparse timing lets the effect progress; it does not make each sample
unperturbed. Means and p95/p99 with2-3 late samples are not reliable tail forecasts.

## Actual budget: use controls, exclude the interrupted terminal call

Sum main-step CPU plus disjoint audio/display worker deltas. This measures CPU
occupancy of the timed threads; it does not double-count worker overlap with
main wall time. Other OS work and small observer tails remain outside it.

| Worst16 nonterminal control calls | Meteor400-415 | Quasar509-524 |
|---|---:|---:|
|Core call CPU|16.513ms|15.990ms|
|Other main-step CPU|0.199ms|0.197ms|
|Audio worker CPU|0.503ms|0.525ms|
|Display worker CPU|0.781ms|0.780ms|
|Total timed CPU|**17.997ms**|**17.491ms**|
|Saving to nominal16.688ms deadline|**1.308ms**|**0.803ms**|
|Saving to13.351ms target,20% margin|**4.646ms**|**4.141ms**|

These windows contain5 invalid PCM-pointer samples each, so their CPU costs
cannot certify healthy reserve. Restricting windows to valid pointers yields
17.949ms Meteor394-409 and17.437ms Quasar504-519: still1.261/0.748ms over deadline,
and4.599/4.086ms above the20% target. No choice of healthy versus late window
changes the need for substantial additional saving. The old broad report's
maximum includes the terminal failed call; this analysis excludes that call.

## Ranked work and savings arithmetic

1. **Shared PPU work elimination and scalar/NEON selection.** This has the best
   evidence and largest effect-dependent pool. Existing C/replay evidence
   points to repeated partial-row index/palette/masked stores for Meteor,
   completely hidden4bpp work and growing OBJ/clipped work for Quasar. Share
   visibility masks and state/palette setup, retain sparse scalar payloads and
   dense NEON, avoid producing hidden rows, and cover legal full-width clipped
   sprites. Choose by rendering state/work shape, not ability name. Broad PPU
   clocks do not yet rank these subpaths by time or price their guards.
2. **Frame copy and submission.** `board_video_submit` copies224 rows of256x2
   bytes into an owned compact chunk buffer in the observed256x224 mode:
   114,688 payload bytes/frame, plus source reads. Callback CPU is0.82-0.86ms;
   display worker CPU is separately~0.8ms. The copy is a concrete, shared target:
   inspect emitted row-copy code, optimize the supported stride copy, or design
   a retained chunk-backed output-buffer handoff with exact pitch/ownership.
   No unrestricted zero-copy pointer swap: the core may reuse rows, stride can
   change, and the scaler reads asynchronously. Eliminating *all* callback CPU
   would only credit~0.85ms; real copy saving is smaller. Do not credit the
   display worker again. Scaler/flip wall waits are not equivalent CPU savings.
3. **The remaining CPU/SPC/APU engine.** There are two sizeable pools: measured
   APU-inclusive~4.2ms and residual~4.5ms, with observer costs included. Optimize
   exact interpreter dispatch/memory/state work and DSP work only after locating
   the inner owner. SPC port accesses call `spc_run_until_` outside the APU timer;
   a separate65C816 and SPC/DSP split is needed to avoid targeting the wrong
   interpreter. The current core already selects no-SA1/no-SFX loops and removed
   unused DSP interpolation, so neither can be claimed again. Ten percent of an
   actual4ms engine pool would be0.4ms, but this profile has not proved that such
   a change exists or established the uninstrumented pool precisely.
4. **Host audio conversion/publication.** The callback costs~0.19-0.21ms, not
   the whole4.2ms APU region. Even removing it completely cannot cover either
   full deadline gap. Keep exact samples/timing; this is a secondary target.

Conditional planning scale using the *observer-inclusive sampled PPU*, not a
measured candidate prediction:

| Hypothetical PPU reduction | Meteor | Quasar |
|---|---:|---:|
|10%|0.791ms|0.704ms|
|20%|1.582ms|1.409ms|
|30%|2.372ms|2.113ms|
|50%|3.954ms|3.522ms|

On that approximate scale, closing the nonterminal control gap alone needs
16.5%/11.4% PPU reduction. Supplying the entire20% margin from PPU alone needs
~58.8% for either effect. That is a required fraction, not an achievable-speedup
claim. A20% PPU gain could address the recorded CPU deficit, but would not give
the requested room to spare. Combining disjoint savings matters; local speedup
percentages cannot be multiplied across the whole call.

Earlier exact workloads give~3971-3977 Meteor sparse hits and570 Quasar hidden
tiles in their aligned intervals. They make good mechanism candidates, not
new prices for the returned peak. Multiplying45% fewer *one class* of index rows
by the whole PPU time would manufacture a false saving. The required next evidence
is integrated hit/miss/guard cost and inward BG/OBJ/clip/composition attribution,
plus the residual's65C816 versus port-SPC split. No new diagnostic was built or
staged during this return analysis. Lower-perturbation sampling or bounded phase
groups should replace per-scanline clock pairs in a future inward measurement.

Reproduce with `build/analyze-quick-profile-return.py <archive>`; it verifies
identities and prior progress before analysis. Publish only bounded derived
JSON via `build/publish-quick-profile-return.py`. Raw ROM/state/SRAM/archives
remain private. [Measurements](../evidence/2026-10-13/quick-profile-return/analysis.json).
