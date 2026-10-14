# Demand-v3 physical spell results: remaining issue narrows to Meteor

Evaluate first, as requested; no emulator/runtime/test recoding or card writes.
All40 epochs ran, with no user abort, and the owned workers/display closed.
**32 of36 demand-v3 windows are clean;16 of18 contexts pass both repeats.**
The two unresolved contexts are Meteor and Rage032, whose recorded branch uses
Meteor effect19. Quasar's old failure reproduces in both controls, while demand-v3
passes both complete Quasar windows with valid pointers and exact audio accounting.

## Integrity and result boundaries

Private strict archive `device-evidence/a7-pair-before-20261014T151744Z`
preserves6,721 retro files/1,730,576,357 bytes. Every archived hash verifies.
Read-only FAT clean/serial11EB-1465. All82 installed payloads, both core binaries,
controller, dispatcher, boot/stock/adapter/production core and original ROM verify.
6,338 prior protected files remain exact; only stock swapfile changed. Original
progress remains intact. Marker consumed; no armed/update trigger, next boot stock.

Ben's interim observations were that Grand Train, Ultima and Pearl seemed to
work and Meteor did not seem complete. They agree with the resulting logs, but
were not an independent panel/speaker review of every epoch. A clean window means
1,200 calls, all frames submitted/flipped, expected properties observed, full
bounded PCM trace, valid pointers and final accounting. It is finite fixture
acceptance, not every random branch or a universal physical visual comparison.

| Demand-v3 context | Clean windows | Worst16 recorded thread CPU, repeats | Minimum valid running reserve |
|---|---:|---:|---:|
| Holy/Pearl |2/2|14.562–14.662 ms|2,184 frames|
| Meteor |0/2|16.919–16.943 ms before drift|138–139 frames|
| Ultima |2/2|15.265–15.289 ms|2,184 frames|
| Meltdown |2/2|15.396–15.458 ms|2,062–2,158 frames|
| Slow2 |2/2|15.305–15.325 ms|2,129–2,162 frames|
| Siren |2/2|15.015–15.093 ms|2,183–2,184 frames|
| Bahamut |2/2|15.261–15.355 ms|2,152–2,154 frames|
| Carbunkl |2/2|13.360–13.361 ms|2,191–2,193 frames|
| Quasar |2/2|16.067–16.073 ms|2,059–2,090 frames|
| Grandtrain |2/2|15.595–15.666 ms|2,126–2,150 frames|
| Rage004 |2/2|13.728–13.766 ms|2,184 frames|
| Rage005 |2/2|14.550–14.562 ms|2,185 frames|
| Rage032, Meteor branch |0/2|16.934–16.958 ms before drift|141–174 frames|
| Rage086 |2/2|15.478–15.537 ms|2,065–2,128 frames|
| Rage088 |2/2|15.237–15.291 ms|2,066–2,097 frames|
| Terrato |2/2|15.223–15.259 ms|2,059–2,094 frames|
| Bio Blast |2/2|14.840–14.869 ms|2,192 frames|
| Confuser |2/2|15.062–15.073 ms|2,161–2,164 frames|

## What changed on the actual A7

Matched reference-heavy16-call intervals, with all observer costs included:

| Effect | Same-index recorded thread CPU saving | Reference outcome | Demand-v3 outcome |
|---|---:|---|---|
| Meteor |1.088 /1.102 ms|fails both,421 calls each|557 calls/error once;1,200 calls with drift once|
| Quasar |1.466 /1.436 ms|fails557 /569 calls|1,200 clean calls both|

These are aggregate combination savings, not individual cache/DMA/geometry prices.
The compared Meteor intervals are400–415; Quasar526–541 and525–540. All matched
indices precede pointer drift in both compared runs. Demand-v3's own worst valid
interval is selected independently and can occur later than the reference peak.

Direct output is now physically exercised, not inferred from a small copy timer:
every clean demand-v3 epoch records1,200 direct submissions and zero copied
payload bytes. Reference Meteor/Quasar use copies; their failed epochs copy
48.17–65.14 MB. This proves the test path exercised copy avoidance; it does not
isolate its share of the aggregate A7 saving or certify every geometry transition.

## Meteor: close to the deadline, not accepted

Nominal cycle-derived quota16.688153ms;20% target13.350522ms. The worst valid
Meteor/Rage032 thread-CPU intervals exceed the bare quota by0.231–0.270ms, roughly
1.4–1.6%. That is substantially smaller than the reference Meteor gap1.083–1.097ms.
It is a measured-region gap, not a guarantee that0.27ms additional optimization
will suffice: other process/kernel costs and cumulative deficit remain relevant.
The corresponding conservative wall-plus-worker proxy is18.43–18.53ms, but can
double-count CPU overlap and must not become a purported irreducible requirement.

Valid running PCM reserve falls to138–174 frames, about3.1–3.9ms, then pointers
diverge. Direct Meteor becomes invalid at call532 /536, about8.93 /9.00 seconds
after the first valid running observation; reference diverges at416/~7.00 seconds.
Rage032 diverges at480 /481, about8.07 /8.08 seconds. The finite buffer survives
longer in direct Meteor; it does not sustain the full effect with valid accounting.

The driver advances application position without the same recorded transfer:
first bias128 frames, final bias128–384 frames. Four reference epochs and one
demand Meteor epoch report errno77/SETUP. Crucially, the other Meteor epoch and
both Rage032 epochs reach1,200 calls with empty error fields and exact *software*
PCM totals, yet their physical pointers drift. They remain invalid; zero reported
xruns and nominal completion cannot override that evidence. Reserve after drift
is not credited. This is consistent with reserve exhaustion preceding the known
native fault mechanism; it does not independently establish why the kernel moves
the application pointer or quantify speaker silence.

Quasar remains valid with reserve floors2,059–2,090 frames (~46.7–47.4ms), and
0.615–0.621ms recorded CPU margin below the nominal quota. Its failure is resolved
in these two windows. It still lacks20% margin and universal effect coverage.

## Decision before further implementation

Retain the exact demand-v3 candidate. The remaining reproducible issue is the
Meteor effect reached by two contexts; these results do not call for a broad
renderer rewrite. The next investigation should isolate Meteor's remaining
heavy interval and cumulative deficit before choosing caching or more buffering.
The trustworthy trace stops at pointer drift, so it cannot certify a complete
Meteor reserve requirement or prove that a particular extra buffer size fixes it.
Most contexts are close to functional playback; worst-effect20% headroom is
still not established. Production gate remains false.

No emulator, runtime, core, test fixture, original progress or card state changed
during this evaluation. I: remains unarmed. Prior frozen sources/artifacts and
published receipts verify unchanged.

[Evaluated evidence](../evidence/2026-10-14/demand-spells-return/analysis.json).
Reproduce: `python build/report-demand-spells.py <archive>` then
`python build/evaluate-demand-spells-return.py <archive>`; these analyze only the
archive. Optional `--verify-live` performs read-only I: identity/ROM checks.
