# Ability3 return: reject as a deficit fix — 2026-10-13

Archive `a7-pair-before-20261013T172104Z` verifies5,021 returned files, all79
installed payload hashes, exact dispatch and consumed marker. All4,811 prior
protected files match; only runtime swap differs. FAT/serial is clean. The
wrapper attempts all18 fixtures and finishes. No card writes or rearm occur;
the next boot is stock. Original progress/production remain unchanged.

The pass set is identical to ability2: Ultima, Slow2, GrandTrain, Terrato,
Bio Blast and Confuser complete1,200 calls. The same12 other contexts fail
native PCM SETUP/errno77. All requested properties and Rage selections appear;
software PCM accounting is exact and native quota is99.999997%.12,134 core
calls produce12,122 drawings; the12 terminal audio-aborted calls explain the
difference. No C/signal crash is retained. All12 terminal application pointers
exceed accepted-transfer counts by384 frames; late reported reserve is inexact.

## Same-frame result

[Measured receipts](../evidence/2026-10-13/ability3-return/verdict.json) compare
the last16 ordinary calls common to both runs. This prevents an earlier failure
from appearing as a zero saving. The original ability2 failure tail is also
retained when available; Bahamut ends too early to retain that whole tail,
and Siren/Quasar/Slow2 Rage overlap only part of it. Units below are milliseconds.

| Case | Net matched CPU saving | Current tail step | Remaining deadline deficit |
|---|---:|---:|---:|
| Holy | +0.030 | 17.755 | 1.066 |
| Meteor | -0.050 | 18.629 | 1.941 |
| Meltdown | +0.070 | 17.480 | 0.792 |
| Siren | -0.016 | 18.467 | 1.779 |
| Bahamut | -0.086 | 17.181 | 0.493 |
| Carbunkl | +0.096 | 17.490 | 0.802 |
| Quasar | -0.175 | 17.792 | 1.103 |
| Lullaby Rage | +0.098 | 18.630 | 1.942 |

Terrato/Bio Blast/Confuser controls also save0.102/0.101/0.050ms in their aligned
tails. Thus Carbunkl's0.096ms does not establish a benefit larger than ordinary
cross-run variation. The pooled meanCPU12.136ms versus12.201ms previously also
does not prove local deficit closure. The pass/failure set is unchanged.
For example, Meteor's cycle-quota/step proxy is about39,505 sink frames/sec against
44,100; the deadline needs1.941ms more saving before headroom. Every measured
native failure rejects continuity even if pooled FPS stays near60.

Whole-call clocks include observers; no calibration is subtracted. CPU frequency
remains unexposed and there is only one paired physical run. These observations
price net behavior, not separate math/cache/predicate unit costs. The measured
verdict is **REJECT AS DEFICIT FIX**; production gate false. Ability2 remains the
baseline for further source work, with its measured useful batching retained.

## Why the hypothesis did not earn a fix

Removing4,600–6,000 fixed-operand row operations did not remove milliseconds.
The new C checks every active math row for fixed-only eligibility before its
existing compositor classification. Existing optimized ARM `DrawTile16Add1_2`
shows the added vector-to-ARM predicate transfers/branches, table selection and
stack accesses; stack allocation grows76→148 bytes. These are direct static
observations, not proof of a particular A7 cost or a memory-bandwidth limit.
The old true-subscreen half-add shortcut already performs cheap vector math.
New eligibility cost on unaffected rows can cancel savings on fixed rows.

The old prewritten sensitivity assumptions were explicitly unmeasured; the
physical net result rejects using them as candidate prices. Do not divide
inclusive CPU by eligible-row counts or fit collinear whole-call counters and
present the result as measured unit costs. No QEMU timing enters this verdict.

## Next work and missing evidence

1. **Fixed-color fragmentation:** Siren/Carbunkl/Lullaby retain approximately
   158–164 real `$2132` flushes and162–168 renderer entries. The useful analogue
   to successful Window2 batching is per-row fixed-color capture with every
   BG/OBJ/backdrop consumer honoring it. First establish exact consumer coverage,
   independent output qualification and added bookkeeping/materialization costs.
   Simply ignoring genuine flushes changes graphics. Unused-color skipping
   already saved zero work and remains rejected.
2. **Pixel/subscreen work:** Holy/Meteor and ordinary28-entry cases retain heavy
   row/depth/color traffic. Avoid adding a second classification to every row.
   Examine existing mode-specific ARM loops and register/stack behavior before
   proposing a kernel change; preserve true-subscreen and mixed-depth semantics.
3. **Missing A7 evidence:** sparse phase sampling or owned warm path batches must
   directly price entry setup, row composition, palette construction and added
   capture/lookup cost with audio/display live. Dense per-row clocks previously
   added milliseconds and remain unsuitable. Whole-call savings alone cannot
   identify which of these costs dominates. Record frequency availability and
   included instrumentation; never convert with an assumed666MHz clock.

Before another hardware candidate, supply the actual mechanism, exact-output
qualification, matched remaining deficit, added costs and explicit conditional
prediction. This return warrants no unchanged rearm or production promotion.
