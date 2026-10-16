# Presentation-independent audio recovery candidate

Pressure3 removes display-credit waits from queued render+audio production.
It is separately versioned, qualified offline and armed once on I: from pushed
`678643a`; physical benefit remains pending. The pressure1/2 source and returned evidence remain
unchanged. This is a controlled platform candidate, not an already-qualified
production emulator speedup.

The producer atomically tries to reserve both a FREE chunk source and FIFO
credit. With credit, it renders/submits normally. With no credit, it renders
the same complete frame into existing heap scratch, runs the same CPU load,
and produces every audio quantum, but skips presenting that generated frame.
This is an intentional presentation tradeoff, recorded per frame and in totals.
No READY job is replaced, no SCALER/READY source is written, and no audio sample
is dropped to catch up. Render work itself is retained, isolating presentation
backpressure rather than manufacturing savings through omitted rendering.

The actual display worker releases the mutex around scaler/flip operations.
The new reservation takes only the existing ownership mutex; it never waits on
the display condition or hardware completion. An owned reservation is
idempotent; full FIFO/no free source leaves all board state unchanged; closed
or stopping board is an error. Submission still uses the existing worker,
buffer lifecycle and draw/flip calls. Drain/join precedes source/display free.
Serial/no-audio/memory/prebuilt paths retain blocking behavior. Native PCM and
its joined drain owner are byte-identical to pressure2.

The first70 phases retain pressure2's order, scene, load, count and audio
parameters. Queued render+audio cells use the candidate policy. Phases70–76
repeat the exact four steady4/8/12/16 ms and three burst24/48/80 ms light cells
with the original blocking policy. Each pair's begin metadata must match except
`presentation_policy`. All have180 quanta, bursts every30th frame, unchanged
prime/rate/admission limits. Candidate-first ordering is recorded, not a
randomized/reversed or long-duration qualification. Expected issues in heavy
or80 ms cells do not imply a controller crash.

Successful video accounting is now `submitted + presentation_skipped == completed`
and `submitted == scaled == flipped`. Detailed rows independently count
presentations; direct/copied byte accounting uses submitted drawings. Final
rendered pixels/depth are still checked against the scalar oracle, including
when the last presentation is skipped. Actual panel cadence and the visual
effect of skipped presentations need physical observation.

## Evidence gate before installation

Pressure2's clean post-first48 ms interval measured4.385 ms main CPU plus
11.452 ms median reservation wait per quantum, with native reserve below prime.
That is measured **wall opportunity**, not CPU saving. Added costs are the
ownership lock/try, policy branch/counting, heap-versus-chunk rendering on a
skip and any subsequent presentation effects. Their A7 delta is unmeasured.
ARM text grows1,488 bytes/data8 bytes versus pressure2; BSS is unchanged.

Break-even for a blocked quantum is `avoided wait > try cost + scratch render
delta + additional downstream recovery cost`. Every render and load still
runs, so this does not repair the dense20.341 ms CPU deficit. In the light
case, if producer work stays near4.4 ms and removal of the11.45 ms wait allows
quanta to be produced faster than16.688 ms, lead can recover. Pricing those
terms on hardware is the purpose of this experiment; no numerical CPU saving,
exact remaining deficit or production margin is claimed before its return.

Falsifiable result: at the same48 ms load, the candidate should exhibit busy
credit/skipped presentations, near-zero display reservation wait, valid PCM
pointer/count histories and restored prime lead before the next burst, while
the matched blocking control retains its recovery deficit. Failure to restore
lead, equivalent added cost, pointer fault or unacceptable presentation behavior
rejects the proposed benefit.24 ms and steady8 ms passes must not regress.
80 ms can still exceed the reserve before any recovery opportunity.

## Validation and run

- All77 ARM mock cells, paired sweep parameters and mock-performance rejection.
- 60 full-frame scalar/NEON/cache oracle/guard cases.
- Actual patched board:192 combinations of FREE/RESERVED/READY/SCALER ownership
  and FIFO credit, idempotence/cancel and closed/stopping/null guards. Busy state
  stays byte-identical; existing READY/SCALER buffers are untouched.
- Actual controller plus frozen threaded audio owner with a fake device:
  exhausted display credit skips all presentations while full rendering/audio
  and oracle/accounting pass, no blocking reserve calls, blocking control still
  reserves, single finish/error propagation and six executed bursts. Reintroduced
  double-finish remains rejected. Fake backends do not price physical recovery.
- Actual firmware-shell startup/replay/UART/forced-child fault checks, source/
  header pins and firmware-compatible time32/glibc ABI.

[Qualification](../evidence/2026-10-15/render-pressure3/qualification.json),
[ownership/controller checks](../evidence/2026-10-15/render-pressure3/controller-qualification.json),
[wrapper faults](../evidence/2026-10-15/render-pressure3/fault-qualification.json).
The kernel audit is reused; no new driver/MMIO/clock/scheduler mode is enabled.

Installer requires fresh archive, clean pushed source, source/payload hashes,
healthy FAT and preserved stock/ROM/init/private progress, then stages separate
`retro/render-pressure3` and its two one-shots. After independent readback,
safely eject and cold boot. Allow5–6 minutes; Select+Start aborts. If stock has
not returned after six minutes, power off and return I:. Forced/uncertain
termination holds stock until reboot; consumed markers make the next boot
stock with the permanent UART fix. Results live in
`retro/render-pressure3/results/run-<boot_id>-<pid>`; archive before rearming.

Installation archive: `device-evidence/a7-pair-before-20261016T041539Z`.
Before staging, after payload verification and after arming, FAT is clean.
The only changed prior file is the owned SNES dispatcher. Independent readback
verifies all9,034 protected prior files, new payloads, exact marker bytes and ROM;
stock/progress/prior tests and permanent UART correction remain intact.
[Installation receipt](../evidence/2026-10-15/render-pressure3/installation.json),
[readback](../evidence/2026-10-15/render-pressure3/live-verification.json).
