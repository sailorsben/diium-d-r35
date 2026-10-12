# A7 pair1 return: six combined completions, six baseline PCM stops

The returned physical test supports the combined window/palette/prefix design:
**every combined pass completes its bound, and every baseline pass stops with
native SYNC_OBSERVE errno77/SETUP**. In particular, the second and third passes
are the two combined full replays. Both reach500 calls, submit500 drawings,
finish all162 effect calls277..438 plus recovery, and drain all queued PCM.
This closes the deficit for this bounded replay; it is not yet extended-gameplay
or production acceptance.

The user initially reported that2–3 seemed to work and the others were buggy
or failed. Clarification: some stopped before the effect finished, killed the
wolf, or stuttered and then killed it. The later-state experiments deliberately
start partway through Bio Blast. Their shorter animation or game outcome is
not sufficient evidence of a rendering mismatch. Stuttering/premature stops
remain observations; no physical pixel capture establishes visual equivalence.
The preceding6,000 offline output comparisons remain the exact-output proof.

## Physical outcomes

Pass numbers below are one-based, matching the second/third observation.

| Replay start | Baseline outcomes | Combined outcomes |
|---|---|---|
|0, full500-call replay|passes1/4 stop at310/312 calls;309/311 drawings|passes2/3 complete500/500 drawings, no error|
|261,80-call section|passes5/8 stop at51/50 calls|passes6/7 complete80 calls/drawings|
|384,96-call section|passes9/12 stop at15/14 calls|passes10/11 complete96 calls/drawings|

All combined passes have zero held drawings, zero native PCM error and zero
remaining audio after orderly drain. Native production in each full replay is
534.688 frames/call, matching the534.688402 contract within integer rounding.
No quota reduction, drawing suppression or hidden recovery explains the result.
Failed baseline calls can abort before their video callback; their final missing
drawing is explicitly reported, not treated as intentional frameskip.

## Measured saving, including observer

Four pairs have32–34 overlapping RUNNING effect calls after the prescribed
warmup. Their mean main-thread CPU savings are2.892,2.908,2.885 and2.972ms;
core wall savings are3.125,3.214,3.149 and3.250ms. These price the complete
changed C paths together, including gathers, cache interaction and bookkeeping.
They are not isolated dispatch/e/r/b prices, and do not price unmatched late
calls. Both late baselines stop before their16-call warmup completes, so there
is no qualified warm late A/B saving distribution.

Across the complete effect in full combined replays:

| Quantity | Pass2 | Pass3 |
|---|---:|---:|
|mean main-thread CPU|14.288ms|14.368ms|
|mean core wall|15.420ms|15.530ms|
|p95 core wall|16.767ms|16.820ms|
|mean admission wait|1.077ms|0.979ms|
|mean complete step, observer included|16.667ms|16.673ms|
|minimum frame-observed RUNNING reserve, whole replay|2,768 frames|2,736 frames|

The16.688ms nominal budget leaves1.268/1.158ms on mean core wall. Some calls
exceed the deadline; reserve absorbs those tails. Admission waiting increases
because the faster producer fills the queue. Its increase of1.65–1.72ms on
matched calls absorbs part of the speedup into deliberate pacing. Consequently
the net complete-step mean reduction is only1.47–1.58ms in these pairs; that
does not negate the approximately3ms of actual execution work saved.

Frame-observed RUNNING snapshots across the two full successes show44,139.95
and44,135.09 accepted frames/s over8.320s, with reserve3,046→3,053 in both.
Treat these as finite-interval, reserve-sensitive measurements, not an
unbounded throughput claim or a new audio quota. The stable reserve and full
effect/recovery completions demonstrate closure over the observed intervals.
The older1.514ms late floor and2.437ms PCM proxy are useful targets, but are
from separate prior intervals. Do not extrapolate an early aligned saving
unchanged into the unmeasured late baseline.

Observer median is10–14us/call, generally13us on combined passes. All clocks
are direct kernel syscalls; observer costs are retained, never subtracted.
CPU frequency/governor sysfs is absent (ENOENT), so every frequency field is
-1. ABBA replication strengthens the observed association, but cannot prove
frequency parity or justify converting these times to assumed666MHz cycles.

## PCM failure mechanism and remaining limits

Full baseline reserves draw down and stop before the peak late section.
Last successful RUNNING traces retain application-pointer/transfer differences
of256 or384 frames, and every failed trace returns SETUP with errno77. Combined
passes finish their RUNNING epoch with pointer/transfer difference zero.
Exclude the normal teardown's epoch2 reset from that comparison; it clears the
transfer counter while stale configuration pointers can remain. All12 complete
native traces fit in RAM, with retained_from0 and no history truncation.

The A/B result strongly supports insufficient renderer throughput as the
trigger for this replay's failure. The exact vendor pointer/stop transition
remains unresolved; queue estimates carrying that pointer difference cannot
be treated as independently verified physical reserve. Improving throughput
prevented the observed stop without changing the native PCM client. It does
not prove every vendor audio lifecycle edge case is repaired.

The combined mechanism is now a measured promising candidate. The next useful
qualification is longer actual gameplay/repeated Bio Blast with this exact
core and the normal runner, checking cadence, tail reserve, visual fidelity,
save/exit and healthy-card contracts. No additional speculative optimization
is justified by this return. No install or re-arm was requested or performed
during collection/analysis; the consumed card's next boot remains stock.

## Preservation and reproduction

Return archive: `device-evidence/a7-pair-before-20261012T034845Z`; the historical
archiver's before prefix denotes collection before any writes, not pre-test.
Every returned retro file is source/copy/source hash verified; readonly CHKDSK
is clean, serial11EB-1465. Every staged payload hash matches.455 protected
original retro files remain identical. The owned dispatch remains its staged
hash; the only other original-file difference is the runtime swapfile, privately
preserved and explicitly reported. Stock/core/adapter/init/progress and cost1
results are unchanged. Card writes during return handling: zero.

`python build/analyze-a7-pair.py <archive>` reproduces the private analysis.
The public analysis contains bounded per-pass distributions, coverage, service
rates and fault events; it contains no ROM, state/SRAM, core binary or raw swap.
