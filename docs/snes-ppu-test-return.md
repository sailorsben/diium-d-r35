# PPU physical return — combination rejected

All56 epochs ran without user abort. Final PPU combination retains32/36 clean
windows and16/18 contexts passing twice, exactly the previous acceptance count.
Meteor and Rage032 (observed Meteor effect19) still fail. These new PPU changes
do not close the gap; do not promote the combined candidate or treat isolated
savings as additive. No emulator changes or card writes/rearm during evaluation.

Strict archive `device-evidence/a7-pair-before-20261014T231531Z` preserves7226
files/1827485639 bytes. FAT clean, all91 installed payloads exact,6,719 prior
files unchanged; only stock swapfile differs, excluding authorized dispatcher.
Stock/adapter/boot/init/original progress and live ROM hash verify. Marker
consumed, workers joined/display freed, I: unarmed and next boot stock.
All frozen qualification/payload/proof/source and prior publication hashes verify.

## Combined candidate versus matched demand-v3

| Measurement | Forward | Reverse |
| --- | ---: | ---: |
| Meteor valid warm-common mean CPU saving | -0.0710ms | -0.1200ms |
| Meteor fixed384–415 interval saving | -0.0470ms | -0.0582ms |
| Meteor candidate first invalid frame | 480 | 484 |
| Meteor control first invalid frame | 496 | 505 |
| Meteor candidate completed calls | 497 | 502 |
| Quasar fixed496–541 interval saving | +0.0044ms | +0.0237ms |
| Quasar valid warm-common mean saving | -0.0344ms | +0.0188ms |

Positive values save time; negative values cost time. CPU is main-step CPU plus
distinct worker increments. No assumed MHz, QEMU duration or inclusive nested
phase clocks enter these prices. Frequency observations are unavailable (-1),
so do not assert stable clock or compare absolute prices across older returns.

Selecting only each control's heaviest common16-frame window reports a
+0.0544–0.0547ms Meteor saving. That is real for those selected indices but
misrepresents the broader result: the combination is slower across the common
warm prefix in both orders and loses valid pointers earlier. The analyzer now
reports all common contiguous16-frame windows, whole common warm means, and
fixed intervals alongside the old selector. It excludes invalid frame-pointer
prefixes rather than crediting post-failure speedups. The496–535 late-Meteor
window is not fully valid in both candidates/controls; no matched late-window
gain is claimed.

Combined Meteor worst valid16-frame recorded CPU is17.1116/17.0528ms,
0.4234/0.3646ms above16.688153ms quota. Rage032 reaches17.0801/17.0798ms,
about0.392ms above quota and fails457 calls in both orders (first invalid
440/442). These are recorded-region gaps, not guaranteed sufficient fixes:
kernel/other work, residual worker costs and full cumulative reserve matter.
Trustworthy candidate reserve falls to141 frames for Meteor and144/207 for
Rage032 before drift. Full effect/recovery reserve never qualifies in these
failed epochs; do not extrapolate a recoverable audio deficit from the prefix.

All other16 contexts, including Holy, Ultima, Quasar, GrandTrain and Confuser,
complete both1200-call runs with clean bounded frame/PCM/pointer evidence.
That is bounded fixture acceptance, not every random branch or an independent
panel/speaker review.20 percent production headroom remains unqualified.

## Isolated family prices

Each family uses unchanged v3 controls in forward/reverse blocks. These are
family aggregate prices; the shapes family groups opacity, clipped and sparse
plain/math and cannot price those kernels separately.

| Family | Meteor control-heavy common16 saving | Quasar fixed496–541 saving |
| --- | ---: | ---: |
| OBJ lookup | +0.0590 / +0.0928ms | +0.0035 / +0.0189ms |
| Shapes | +0.0642 / +0.1723ms | +0.1518 / +0.2247ms |
| Bulk depth | +0.1811 / +0.2152ms | +0.0957 / +0.1311ms |

Bulk is the most consistent useful lead: Meteor fixed384–415 saves
0.0391/0.0405ms, and Quasar whole warm means save0.0885/0.1328ms. Meteor
whole common warm means are only0.0027/0.1085ms, so heavy-window savings must
not be advertised as every-frame gains. Bulk delays first Meteor drift to
528/540 versus its controls516/500. Both bulk runs reach1200 with empty core
errors but pointer biases384/256: both FAIL. They are not recovered runs.

OBJ and shapes Meteor whole-warm prices change sign across order; OBJ Quasar
whole-warm is slower by0.0184/0.0349ms. Shapes Quasar improves the fixed heavy
interval yet saves only0.0522/0.0279ms over the whole warm run. Limited repeats,
clock unavailability, worker sampling, order/cache interaction and code layout
prevent universal microkernel-price claims. Their sum does not predict combined
behavior. Code footprint/inlining/cache effects are possible explanations for
the combined regression; this run does not identify the cause.

Across all56 epochs42 are clean,14 invalid. The suite reports12 runner errors;
the other two invalid epochs are the nominally complete bulk Meteor runs.
All14 invalid windows lose pointer integrity; exact software accounting and
empty errors do not override that. No finished-but-invalid run is counted clean.

## Decision

Reject the combined PPU candidate as an improvement. Retain demand-v3 as the
comparison baseline, with its Meteor gap still unresolved. Preserve the bulk
and shapes results as narrower leads; any future subset must requalify and
measure its own full effect/recovery and reserve. Do not assume removing OBJ
will restore additive savings. The source-row cache was absent from this test
and has no new physical result. No recoding, deployment or rearm is part of
this return evaluation.

[Machine-readable evaluation](../evidence/2026-10-14/ppu-test-return/analysis.json).
