# Combined renderer: manual extended gameplay qualification

The user authorized a longer gameplay test with manual Bio Blast casts after
the A7 pair1 return. This separate test uses **the exact measured combined
core**, SHA256 ee0b241c3b7c561e76efbedbbdcf37bf8e104bb6754d7b0493c3ed4774172155,
and the exact regular1.19 runner, SHA256
c0b56975ea847ecfa737eee43bab0781d8d039b9f3bcc6af5508e7bbfd231310.
No new renderer optimization, audio policy, input script or frameskip is added.

## Measured gate and prediction before staging

The [physical pair1 return](snes-a7-pair-return.md) prices the full changed
paths together, including added gathers, cache queries, window capture and
bookkeeping. Matching RUNNING effect calls save2.885–2.972ms of CPU and
3.125–3.250ms of core wall. These are whole-path net prices, not manufactured
isolated e/r/b costs. Both full combined replays complete500 drawings, all162
effect calls and recovery with no PCM fault. All six baseline passes fail.

The break-even comparison on measured overlapping calls is
`S_net >= 1.514283ms` for the prior late floor, or `S_net >= 2.436981ms` for
the separate earlier PCM proxy. The measured wall-saving range exceeds those
targets by1.610–1.736ms and0.688–0.813ms respectively. Those are conditional
comparisons, not prices for unmatched late calls; late baselines stop before
warming. Direct whole-path measurement includes the candidate's added costs,
but does not identify the separate unit contributions. The old entry-only
scorecard does not describe the measured combined design.

Over the full effect, combined core wall means are15.420/15.530ms, leaving
1.268/1.158ms before admission/other loop work against16.6881545ms. Observed
complete-step means are16.667/16.673ms because queue admission spends available
margin pacing the faster producer. RUNNING endpoint accepted rates are
44,139.95/44,135.09 frames/s, with reserve3,046→3,053. Thus the observed bounded
replay has no remaining sustained-deficit accumulation. This finite-interval
result cannot be extrapolated to unbounded play, every effect or unknown clock
conditions. Frequency sysfs remains unavailable; no assumed MHz or QEMU timing
enters this decision.

The falsifiable longer-test prediction is that repeated manual Bio Blast in
comparable scenes stays complete and smooth, preserves full rendering/audio,
and finishes without PCM stop or pointer divergence, with normal save/exit.
Core-wall means near15.4–15.5ms are a prior for comparable effect state, not a
guarantee for other gameplay. A PCM error, shutdown, incomplete/corrupt effect,
sustained underproduction or failure to save/exit rejects broader acceptance.
Extended gameplay remains pending; this authorization is a guarded physical
qualification, not a claim of final production acceptance.

## Normal path, preserved progress

Owned card folder: `retro/snes-combined-gameplay1`. The existing one-shot
launch dispatch points to its wrapper, which consumes the established marker
before starting the regular library. The splash process must exit before
display initialization. All controls and pause/save/load/exit menus remain live.
There is no automatic battle or forced replay. The next unarmed boot is stock.

The existing SRAM files are copied into this folder's separate saves directory.
The current1.19 snapshot gets a separate combined-core identity header after
exact-output qualification; its serialized payload is byte-identical. Originals,
backups, existing diagnostics and production binaries remain unchanged. New
gameplay progress belongs to the test folder and must be archived on return.
Do not silently merge it back into original progress.

This reuses the regular1.19 diagnostic budget: cumulative CPU/wall/audio/video
counters, recent frame history and sparse phase samples, plus native fault
history. It does not enable pair1's per-call frequency/worker records or deep
phase/row clocks. Existing wrapper progress stays in RAM while the child runs;
no platform polling/background card checkpoint competes with gameplay.
Normal in-game saving and failure persistence remain part of the regular path.
Recent/sparse history is not a complete per-effect reserve timeline; later
analysis must state those coverage limits instead of inventing missing costs.

## Qualification and guards

The unchanged core already passed6,000 offline exact-output comparisons and
six A7 independent passes. The manual setup adds2,400 exact-output frames using
the copied current snapshot,180 frames through the actual regular binary,
native consuming-client fault/drain/deficit checks with two real load/resume
menu operations, and wrapper one-shot/splash/startup/no-live-card-write checks.
QEMU checks establish contracts only. Long physical gameplay remains pending.

Fresh archive: `device-evidence/a7-pair-before-20261012T040022Z`. All retro files
are hash-verified before clean readonly CHKDSK. The installer verifies card
serial11EB-1465 on I:, source/proof/payload hashes, stock/init/adapter identities,
the current pair1 dispatch and no other armed marker/update trigger. It refuses
an existing gameplay target. All earlier files except the owned dispatch stay
hash-identical; payload and arm readback plus clean FAT follow staging. Only
owned paths can be rolled back after a fresh health check. ROMs, private
progress, vendor core/dependencies and raw card archives remain unpublished.

[Physical test instructions](snes-combined-gameplay-test.txt).
