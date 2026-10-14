# Combined A7 measurement: 1.19-combined1

The user authorized archive-first staging of all combined improvements for the
eight failing ability contexts, retaining every frame and measuring actual A7
savings and headroom. This is an experimental measurement installation only;
`production_gate_passed=false`. The existing production core is unchanged.

## Frozen comparison

48 independent epochs: eight contexts x three cores x two reversed case/core
orders. Cases are Pearl/Holy, Meteor, Meltdown, Siren, Bahamut, Carbunkl,
Quasar, Lullaby Rage004; 1,200 nominal calls each and 120 warmup calls. The
original command/target/property fixtures and logical snapshot payloads remain
unchanged; only core identity headers migrate. Each effect appears six times.
Nominal gameplay is 16.02 minutes; allow 20-25 minutes including startup,
load and post-join logging. Earlier control failures shorten the sequence.

- Baseline: unchanged ability2 core, SHA256 53c6d1f6c0253cb1c6e7b81ba22192f3739fa3f9605837c64691085918e1106b.
- Prior: unchanged fullpaths combined, SHA256 6608a657a1e4eae9ac067dc305310f5ee1e19844374c92a8f4f2ec8ba47b1483.
- Combined: common-band v3, SHA256 e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129.

Latest combines generalized Window2, fixed-color batching, true-subscreen
composition, dead DSP interpolation removal, early depth rejection, sole-BG3
subscreen production, constant-mode background bands, eight batch palettes
and opaque depth stores. Reuse exact binary correctness receipts by hash;
43,200 final-core ordinary/instrumented replay calls are offline correctness,
not A7 performance. The new actual controller, native provider fault/retry/
drain/deficit, wrapper and ABI seams are separately qualified.

## Measurement contract

Kernel scheduling and thread CPU clocks; audio/display workers live. Inspect
cpufreq, attempt existing maximum-frequency pin if exposed, record before/after
samples and restore policy. Report unavailable frequency honestly; do not use
666 MHz or convert CPU time to cycles. Warm distributions follow 120 calls;
all raw calls remain available, including effect onset and recovery.

RAM frame records and included accounting/frequency/animation observers; flush
after worker joins/display idle. Per-epoch pre-start/result durability writes
occur outside gameplay. No calibration subtraction, per-row instrumented core,
frameskip, quota change, reprime, fatal suppression or recovery masking.

358,416 master clocks per call imply 534.688 native stereo frames, 735.948
converted frames and 16.6881545 ms nominal deadline. Proposed 20% headroom target
is 13.3505236 ms. Compare aligned emulator call indices, reporting mean, median,
p95, p99, extrema and incomplete overlap. Measure total baseline-to-combined,
new increment prior-to-combined, and baseline-to-prior control independently;
isolated historical gains must not be summed into a combined prediction.

Service proxy = step wall - verified pure pacing + all audio/display worker
CPU. It conservatively double-counts overlap and is not isolated core cost.
Final worker CPU after the last live sample is reported and conservatively
charged to the last sample by the archive analyzer; cleanup audio-drain/display-
idle wall is separate. On-card summary explicitly covers warm sampled calls;
only the archive analyzer includes final worker residuals in distributions.
Final PCM must satisfy enqueued = accepted + remaining + cleared; remaining,
cleared, final audio error, pointer drift, bad clocks, missing submissions/flips,
failed/partial windows or missing observed properties invalidate acceptance.

## Gate and falsifiable predictions

The October 14 UTC return of fullpaths1 completed 100 scheduled epochs; 55
reported runtime failure. Prior combined completed Meltdown, Siren, Bahamut,
Carbunkl and Lullaby in both orders; Holy, Meteor and Quasar still failed.
Measured old combined savings were substantially smaller than some forecasts.
See [return analysis](snes-fullpaths-return.md). Frequency was unexposed.

New band work is shared across all eight contexts. Source model for new
increment: S = D*e + O*r + H*h + T*s - b (microseconds at aligned state).
D is eliminated per-cell setup, O eligible opaque merges, H early hidden-tile
rejections, T sole-subscreen work, and b all added branching/cache/band costs.
These unit prices remain unmeasured; counts alone do not meet the production
installation gate. Whole-combination crossover directly measures actual
savings without manufacturing unit prices from inclusive time / counts.

Prediction: identical pixels, PCM quota and emulated state, all 1,200 frames
submitted/flipped for a complete epoch, no holds or discarded PCM. Latest
should reduce aligned main CPU for affected work, but its magnitude and 20%
headroom are unknown. A non-positive incremental saving falsifies the proposed
transfer; failure or invalid accounting cannot be relabeled a performance pass.
A complete window also needs full effect/recovery and valid cumulative reserve
review. This suite supplies evidence, not a guarantee for every plausible spell.

## Operation and preservation

[Instructions](snes-combined-test.txt). Separate `retro/snes-combined1`, unique
identity header, fresh one-shot dispatch under snes-mvp, no B required. MENU
stops safely. Next reboot is stock after marker consumption. Archive all retro
files first, verify runner/core/wrapper/fixtures, original production/boot/saves,
then require clean read-only FAT checks before and after writes. Never overwrite
emu_sfc.so. See prepare/finalize/install/report/publish-combined-test scripts.
Raw ROM/states/SRAM/vendor dependencies stay private; publish bounded receipts.
