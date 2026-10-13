# Systematic FF6 effect screen — 2026-10-12

The [Confuser candidate returned successfully](snes-confuser-gameplay-return.md).
Ben then requested finding and fixing other effects that could stop gameplay.
This investigation screens shared renderer mechanisms offline. It finds a
concrete Window2 coverage gap and produces an output-qualified generalization.
It does **not** establish another physical crash, an A7 speedup, or universal
game compatibility. I: remains archived/unarmed with its working binary intact.

## Coverage and independent checks

The pinned, byte-matched ROM disassembly defines406 `AttackAnimProp` records at
D0/7FB2,14 bytes each. Every record is screened on the current renderer and
the generalized window candidate, with independent original1.19 callback sinks:
visible-pixel CRC, native PCM CRC/count, geometry and normalized serialized state
every30 calls. Each case verifies the actual animation-table read and actual
ROM initialization PC. All406 pass both versions; no new C crash or mismatch.

The screen substitutes one record into Bio Blast's animation-table slot **in
memory in both cores**. It retains the original attack mechanics, Terra/single
enemy context and derived battle state. This exercises graphics assets/scripts
and initialization, while avoiding pretending406 ordinary commands were cast.
Most cases run600 calls; selected high-risk cases run1,200. The legacy reused
harness's final “Bio Blast” phrase is a label; CASE/index/table/init evidence
identifies the substitution. No claim of whole-animation completion is made
for those bounded screens.

Eight additional normal menu-selected abilities use the original ROM without
any table overlay or new RAM pokes: Fire/Bolt/Ice Beam, Bio Blast, Heal Force,
Confuser, X-Fer and TekMissile. All pass1,200 comparisons and actual animation
init/deinit assertions. They retain the earlier derived encounter's provenance;
they are not the exact two-fight physical input history. The generalized clip
code also matches original `ComputeClipWindows` on1,572,864 exhaustive
single-layer and524,288 randomized multi-layer states, both screens/all pixels,
with retained-row/reset/prefix/unsupported-mode/Window1/OBJ/color guards.

Across the broad screen,23 paired inward traces,19 negative-hypothesis cases and
eight normal casts, **567,000** exact comparison calls pass. This is correctness
and operation-count evidence. QEMU wall/CPU durations supply no A7 prices.
ROMs, states, screenshots, cores and raw per-call traces remain private.
Published [coverage/counts/proofs](../evidence/2026-10-12/effect-safety-screen/analysis.json)
are bounded metadata; older evidence is preserved.

## Shared window fix

The current guard snapshots one BG1 or BG3 Window2 target. Ultima and Meteor
enable Window2 on BG1 **and** BG3, which rejects that guard and restores repeated
flushes/tile preambles. Holy and Snare also retain edge-triggered work where no
rendered background is currently using Window2. The inward census confirms
rendered `$2128` flushes, rather than assuming every register write draws.

[Generalized helper](../build/plus-a7-multi-window.h) captures a background bit
mask plus each target's inside/main/sub masks in the same7-byte row record.
It covers BG1/BG2/BG3 together in Mode1, ignores that mode's absent BG4, and
defers irrelevant Window2-edge writes when no rendered layer uses it. Enable,
mask, brightness, color and other control changes retain their original flushes.
Window1 combinations on affected layers, OBJ/color Window2, mosaic/hires and
other modes retain fallback. Every target uses its own saved row clip; later
edges cannot change an earlier row. There are no spell IDs in the renderer fix.

Aligned counts below use the first302 calls after verified initialization for
each paired replay. That is a consistent analysis window, not a claim that
every spell lasts302 calls. Pixel/PCM/state comparisons cover the full1,200 calls.

| Effect | Removed full tile calls/call | Removed clipped calls/call | Removed renderer entries/call | Conditional saving at d=0.4us, e=b=u=0 |
|---|---:|---:|---:|---:|
| Holy |4,277.086|0|83.166|1.711ms|
| Snare |2,249.636|0|21.192|0.900ms|
| Meteor |1,943.642|0|74.437|0.777ms|
| GrandTrain |1,605.894|0|61.404|0.642ms|
| Ultima |888.060|56.066|52.781|0.378ms|

These figures remove preambles/traversal, **not the pixel rows**. Relevant paired
row/decode/palette populations remain in the published analysis. The unchanged
Confuser/Bio behavior is explicitly checked. Incidental irrelevant-edge queries
can disappear without reducing tile work; they receive no invented speed credit.

For each effect, `S = delta_full*d_full + delta_clip*d_clip + delta_entries*e -b-u`
in incremental A7 microseconds. `d` excludes pixel work; `e` excludes work inside
entries; `b` includes additional mask detection/capture/banding/cache; `u` is
other loop change. The displayed0.4us is a sensitivity assumption, not a price
inferred by dividing PPU time or transferring the entire Bio optimization.
The row record remains7 bytes, but extra mask logic still has a CPU/cache price.

## Remaining leads and a rejected shortcut

The highest remaining tile-preamble population is **El Nino**:23,202.25 full tile
calls/call in its busiest contiguous32-call window. Imp Song, Siren, Carbunkl,
Mind Blast, Megazerk and Lullaby follow at about17.7–18.1k. These are workload
rankings, not confirmed crashes; scenes with different math/depth/occlusion
cannot be assigned A7 milliseconds from tile counts alone.

The inward traces show frequent **effective `$2132` fixed-color changes** in
gradient/glow cases such as Berserk. Their remaining flushes are not repaired
by batching Window2. Source review identifies a safe unused-color predicate:
fixed color is not consumed when color math is disabled; pseudo-hires must fall
back because it overrides the math registers. A separately tested hypothesis
keeps every register update and skips only those unused-color flushes. All19
cases remain output-equal but remove **zero renderer entries, tile calls,
clipped calls or NEON rows** over aligned common calls. Reject this as a
performance candidate for these cases; extra predicate work has no count credit.
Its files preserve a negative result rather than shipping another diagnostic as
a fix. Removing the real fixed-color changes would change the rendered effect.

Mode7 appears in the Odin/Raiden, Crusader, H-Bomb, S-Cross and Overcast screens.
It retains scalar transformed-pixel work outside these Mode1/NEON tile counters.
Do not rank it as cheap just because tile counts are low. Wider coverage still
needs normal multi-target/reflected/side/back attacks, weapon/monster attack
properties, real event/field/cutscene states and repeated-cast recovery. Those
paths are explicitly outside the406-record claim.

## What can be predicted before hardware work

The fix should eliminate the enumerated window flushes and retain every pixel,
sample and emulated state. Its counts and clipping behavior are falsifiable now.
On hardware, saving requires removed preamble/entry prices to exceed added mask
costs; a neutral/slower result would falsify the speed claim despite correct output.

At unchanged quota, `T_after=T_before-S/1000` milliseconds/call and the local
production proxy is `735.94752/(T_after/1000)` converted frames/sec. Compare with
44,100/sec and16.688ms per nominal call, including admission/other loop costs.
The returned two-fight run supplies no aligned Holy/Meteor/Ultima baseline,
incremental unit prices or complete effect reserve trace. Consequently there is
**no defensible numeric A7 cadence/deficit-closure verdict or production gate
pass for this generalized candidate**. The prior Confuser0.803/1.020ms deficit
belongs to a different pre-fix scene and cannot be imposed on another spell.

The next useful physical comparison would price the working core versus this
separate counter-free candidate in matched Holy/Meteor/Ultima/Snare/GrandTrain
states, with El Nino/glow and Mode7 controls, live normal audio/display workers,
actual kernel clocks, recorded frequency conditions, warm-up and full effect/
recovery reserve. Capture bounded RAM telemetry and write after worker exit.
Do not log per operation, assume666MHz, subtract timer calibration, hide PCM
errors, change audio quota or re-arm unchanged Bio/Confuser builds as a new test.
No new A7 suite, installer, card write or production promotion occurs here.

Reproduce preparation/build/screen with the `prepare-ff6-*`, `build-ff6-*` and
`run-ff6-*` owned tools; preparation refuses existing private trees and cases
retain failures. `analyze-ff6-effect-screen.py` verifies all completed populations,
hashes/proofs and publishes only derived counts. Preserve the successful
counter-free Confuser binary and current separate progress before any next stage.
