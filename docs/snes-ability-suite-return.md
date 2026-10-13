# Ability1 physical return — 2026-10-13

The sweep attempted all400 cases.376 completed1,200 calls;24 ended with native
PCM errno77.344 completed cases also contain the requested spell/skill property
observations;32 completed Rage cases have no requested spell-property match.
All255 Rage selections and all8 Dance selections are observed correctly.
Those32 are a branch/observation coverage gap, not established missing commands
or renderer failures. Property observations alone still do not prove every
animation thread completed or that every possible branch was exercised.

Archive `device-evidence/a7-pair-before-20261013T063819Z` preserves4,605 files
with source/copy/source hashes. Verify all1,607 staged payload files, dispatch,
consumed marker and clean read-only FAT/serial.575 prior files remain unchanged;
only the normal runtime swapfile changes among the576 protected pre-install
files. Original ROM identity matches; stock/emulator binaries and gameplay progress are intact.
Card writes0; unarmed; no installation, repair or rearm. Wrapper closes display
and returns status1 after reaching case399; this is its collected failure count,
not an early process crash. Normal cleanup is retained.

## What failed

Group by the last observed requested graphics identity, not just Rage ID.
Repeated Holy/Meteor/Meltdown/Slow2 across different Rage entries provide useful
cross-command replication. All requested properties were observed in failed
cases before native audio stopped.

| Observed effect | Failed cases | Final16 nonterminal calls: observed step deficit versus16.688ms |
|---|---:|---:|
| Holy |6|2.521–2.877ms/call|
| Meteor |4|2.748–2.992ms/call|
| Ultima |1|1.457ms/call|
| Meltdown |3|0.759–0.851ms/call|
| Slow2 |3|0.284–0.554ms/call|
| Siren summon |1|2.001ms/call|
| Bahamut summon |1|0.507ms/call|
| Carbunkl summon |1|0.978ms/call|
| Quasar |1|0.984ms/call|
| GrandTrain |1|2.965ms/call|
| Lullaby |2|2.017–2.051ms/call|

All27 summons fired,24 completed their full windows. Bio Blast, Confuser and
Tools Bio Blaster completed1,200 calls each around59.99–60 active calls/sec.
Every Magitek, Tools, Blitz, Bushido and Dance case completed its bound with
requested properties observed. This qualifies the exercised contexts and seeded
outcomes only; it does not certify the entire game or every animation branch.

23 terminal faults occur in SYNC_OBSERVE and one in WRITEI_FRAMES. All report
errno77 and device SETUP/state1, with no normal XRUN counter. Terminal application
pointer exceeds owned transfers by384 frames in22 cases and256 in two.
Running pointer bias changes before failure, so later reported reserve values
cannot be treated as an exact physical reserve. One completed Ifrit case has a
transient128-frame bias: pointer discrepancy alone is not proof of a fatal
failure. This matches the earlier vendor PCM failure family; no signal/C memory
crash is shown. Native failure stays fatal within its case; next case starts an
independent closed-and-reopened audio context.

## Measured costs and prediction

460,615 nominal calls produce246,285,455 native frames:100.000058% of the
cycle-derived quota. Generated44.1k frames338,987,304 equal accepted-minus-prime
338,970,383 plus16,921 retained software frames in failed cases. No missing PCM
accounting, held/duplicate frames or unexpected selection failures appear.
460,591 drawings are24 fewer than calls: each fatal publication call omits its
final video submission. Completed cases have one drawing per call.

Whole-core CPU mean11.747ms, p9914.822ms; wall mean12.596ms, p9916.214ms across
all calls. The pooled59.985 active calls/sec obscures local failures. In the Holy
spell's final16 ordinary calls, CPU17.737ms, wall19.189ms and full observed step
19.565ms exceed the16.688ms budget. Meteor's equivalent values are17.942,
19.364 and19.681ms. Core CPU alone already exceeds the deadline in these tails;
audio/display contention and admission/loop work add to wall cost.

The table describes one explicit tail window per failed case, not the peak cost
of every call or a guaranteed production saving requirement. Admission includes
intentional pacing, not just removable overhead. A candidate must show aligned
full-effect cumulative reserve and recovery, not merely subtract a mean tail
deficit. CPU frequency is not exposed/writable in these runs; no MHz or cycle
conversion is inferred. Frequency/accounting observer mean13.271us and animation
observer mean8.671us are included, reported separately, and never subtracted.
Rare observer wall tails include scheduling interruptions; they are not a pure
CPU calibration. Typical observer intervals are far smaller than the Holy/
Meteor deficit. No per-frame SD logging occurs.

The strongest renderer lead remains the independently analyzed
[Window2 fallback](ff6-effect-safety-screen.md): simultaneous BG masks and
irrelevant edge writes retain repeated flush/tile preambles. Holy/Meteor/Ultima/
GrandTrain now fail on hardware as predicted by that workload lead. The existing
generalized renderer completes11 newly archived failing command contexts in
13,200 exact graphics/PCM/state comparison calls against original1.19, with
verified initialization/table-use/deinitialization. No new core build or card
write is needed for that check. Offline timing is not A7 performance evidence.

It is still premature to predict that this candidate closes every deficit.
Earlier illustrative0.4us tile-preamble prices were assumptions; their counts
come from another aligned replay window, not these physical final16 calls.
Do not transfer them into a numeric installation verdict. Siren/Carbunkl/Lullaby
also have heavy glow/tile leads; Bahamut/Quasar/Meltdown/Slow2 need finer aligned
attribution. Missing: actual incremental removed-preamble/entry prices, added
mask/banding/cache cost, matched physical candidate timing, and full reserve
trajectory through completion/recovery. Existing e/r/b production gate remains
unmet. The newly observed tail deficits and repeated command contexts now make
the next optimization's physical predictions falsifiable.

Bounded [summary](../evidence/2026-10-13/ability-return/summary.json),
[case table](../evidence/2026-10-13/ability-return/cases.csv),
[failure tails](../evidence/2026-10-13/ability-return/failure-analysis.json) and
[offline correctness receipts](../evidence/2026-10-13/ability-return/offline-summary.json)
exclude ROM/state/SRAM/vendor/core bytes. Raw returned files remain private.
