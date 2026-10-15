# Draw-order return: all18 contexts clean twice, Quasar regression remains

All36 candidate regression windows pass:18/18 contexts clean twice, including
Meteor and Rage032, which failed the previous v3 suite. All four extra candidate
pricing runs pass too. This is the first complete clean result for this archived
18-context suite, with full frame/PCM histories and valid pointers throughout.
The hardware implementation is useful, but it fails the no-regression and20%
headroom promotion gate: Quasar becomes measurably slower. Preserve the candidate
and this result; do not promote the whole build as a general performance upgrade.
No emulator recoding, card writes or rearm occurred during evaluation. I: is
unarmed and the next reboot takes stock.

Strict private archive `device-evidence/a7-pair-before-20261015T011612Z` preserves
7,797 files /1,937,074,272 bytes, clean FAT. All85 installed payloads and the
dispatcher match the installation receipt; the marker is consumed.7,357 prior
protected files remain exact, with only stock `retro/swapfile` changed. Stock,
adapter, production core, init, original progress and live ROM hash verify.
All48 epochs ran and workers/display joined/freed. Frozen APU/candidate proofs
and all926 prior published hashes remain intact.

| Group | Clean windows | Result |
| --- | ---: | --- |
| Candidate,18 contexts twice | 36/36 | All1,200 calls, full drawings/PCM and valid pointers |
| Candidate Meteor/Quasar price blocks | 4/4 | Both effects clean in both orders |
| Raw-v3 Meteor controls | 0/2 | One audio failure533 calls; one nominal completion with pointer drift |
| Fixed-APU-only Meteor controls | 0/2 | Both audio failures489 calls, earlier pointer drift |
| Raw-v3/fixed-APU Quasar controls | 4/4 | All clean |
| All suite epochs | 44/48 | Three reported runner errors plus one invalid nominal completion |

The40 candidate runs have every requested scaled/flipped frame, no holds or
duplicates, exact final PCM software accounting, complete retained traces and
zero pointer divergence. All successful output is direct; copied payload bytes
remain0. Its full retained running-sync histories recover reserve by193–321
frames relative to the initial2,823 frames. Vendor logical accepted-minus-HW
growth equals reserve change exactly. The minimum valid running reserve is
1,704 frames (38.64ms at negotiated44,100Hz) over all candidate runs. Meteor's
four candidate runs retain2,031–2,059 minimum frames; the two Rage032 runs retain
2,031/2,060. This qualifies these bounded effect/recovery windows, not every
conditional spell branch, whole-game timing or independently observed DAC sound.

The raw Meteor controls first drift at zero-based frame512/528. The fixed-APU
controls drift474/472. Their complete trustworthy running prefixes lose about
2,074–2,137 reserve frames, with minimum valid running observations138–205.
The final raw Meteor control reports1,200 calls and no runner error, but ends
with384-frame application/transfer bias and fails qualification. Completion or
zero XRUN fields cannot override that failure. No post-drift reserve is certified.

The price blocks use the same three cores in forward/reverse orders. Positive
saving means the new build costs less CPU. Values below sum disjoint recorded
main/audio/display CPU increments; these are aggregate build prices, not isolated
APU or renderer instruction prices. Core-only comparisons retain the same broad
directions. All-common valid windows and fixed intervals accompany the original
reference-selected peaks to prevent selective reporting.

| Comparison | Meteor | Quasar |
| --- | ---: | ---: |
| Fixed-APU control vs raw v3, warm common CPU cost | +0.180 /+0.214ms | +0.199 /+0.215ms |
| Draw order vs fixed-APU control, warm common saving | +0.187 /+0.169ms | -0.365 /-0.239ms |
| Draw order vs raw v3, warm common saving | +0.070 /+0.037ms | -0.565 /-0.454ms |
| Draw order vs raw v3, fixed earlier heavy384–415 saving | +0.615 /+0.540ms | -0.553 /-0.728ms |
| Draw order vs raw v3, fixed late heavy496–541 saving | Not fully common-valid | -0.639 /-0.696ms |

Meteor's designated late interval is496–535; its controls lose valid pointers
before the whole interval can be compared. No complete late-interval saving is
invented. The earlier fixed interval demonstrates a net0.54–0.62ms saving over
raw v3, sufficient to change the observed reserve outcome in these runs. It does
not price every later phase. The warm averages include early overhead: draw order
costs raw v3 another0.179/0.328ms in frames120–239. Savings depend on workload.

The candidate's Quasar warm cost is0.45–0.56ms/call above raw v3, including the
compiler-boundary cost. Even against the same-APU control, draw order costs another
0.24–0.37ms warm and0.375–0.492ms in the late fixed interval. Quasar's candidate
minimum reserve1,704/1,705 is below raw2,058/2,058 and boundary2,026/2,057, though
all those runs remain pointer-clean and recover. The user's observation that the
middle runs struggled is consistent with this measured regression. We cannot
assign the observation to an exact epoch or independently reconstruct panel
smoothness from cumulative frame counters.

The byte-identical non-LTO APU object remains stable and21 linked SPC/DSP sizes
match. Stabilizing compilation by this build boundary nevertheless has a measured
whole-build cost of about0.18–0.215ms/call over common warm windows. Linked layout
and other LTO output also change, so this is not an isolated APU-function tax.
Future work must retain the successful draw-order mechanism while reducing the
boundary and low-payoff traversal/guard overhead, using rendering-state criteria
rather than spell IDs. Quasar removes much less redundant RGB work in the prior
observer census, so paying the extra pass everywhere is not justified by Meteor's
benefit. Exact causal prices for individual guards/traversal remain unmeasured.

The highest candidate worst16 recorded CPU is16.727ms in a Quasar price run,
slightly above16.688ms nominal quota. Candidate Meteor price windows are16.332/
16.328ms and regression windows16.297/16.368ms. These are each run's own worst
windows, not matched subtraction targets. The conservative service proxy still
reports NOT_MET for the20% headroom target in Meteor and Quasar; its overlap can
double-count worker time and is not a physical missed-flip counter. Passing
bounded reserve recovery is real progress, while system margin and the Quasar
regression remain unresolved.

Reproduce with `python build/evaluate-draw-order-return.py <strict-archive>`;
`--verify-live` adds read-only I: checks. The evaluator preserves full input hashes,
all epochs, valid-prefix comparisons, complete retained PCM transaction counts
and cumulative reserve identities. The
[published analysis](../evidence/2026-10-14/draw-order-return/analysis.json) trims only
the long invalid-sync index lists to counts/first index; raw histories remain
private and exact. The [installation receipt](snes-draw-order-installation.md)
is historical; no new candidate is installed or armed by this evaluation.
