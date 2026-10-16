# Pressure3 physical return: recovery without presentation backpressure

**The 48 ms burst case passes with pressure3 and fails with its same-boot
blocking control.** Pressure3 renders/produces all180 quanta, executes all six
bursts, presents175 frames and intentionally skips five presentations. All
observed production PCM pointer identities and accepted-sample accounting remain
valid; normal drain succeeds. This establishes the recovery benefit for this
bounded synthetic workload, not sustained full-core gameplay or optical quality.

All77 phases complete without crash/forced termination:62 accepted,15 failed.
The original70 candidate phases have59 passes; appended seven blocking controls
have three passes. Wrapper exit1 reflects diagnostic failures; supervisor
forced0/reaped1/raw_status256 is normal child exit1. Failed prefixes are kept
separate from accepted cells and censored at first invalid pointer or PCM error.

## Same-boot comparisons

Candidate phases59–65 and blocking phases70–76 have identical scene, native
audio, prime, count, requested CPU load and spacing. The policy flag is the
only differing begin parameter. Each full cell is180 quanta, approximately
three seconds. Candidate cells run first; ordering/frequency/temperature effects
are not independently excluded.

| Load | Pressure3 | Blocking control | Candidate presentations skipped |
| --- | --- | --- | ---: |
| +4 ms CPU every frame | 180/180, pass | 180/180, pass | 0 |
| +8 ms every frame | 180/180, pass | 180/180, pass | 0 |
| +12 ms every frame | 61 complete, failed | 58 complete, failed | 0 |
| +16 ms every frame | 11 complete, failed | 11 complete, failed | 0 |
| +24 ms every30th frame | Six bursts,180/180, pass | Six bursts,180/180, pass | 0 |
| +48 ms every30th frame | Six bursts,180/180, pass | Stops during second burst,59 complete | 5 |
| +80 ms every30th frame | Stops during first burst,29 complete | Same | 0 |

This fixes a recovery constraint, not a sustained CPU deficit. The steady
operating point remains about12 ms main-thread work in the light route;
adding12/16 ms still fails. Dense rendering/audio also still fails. An80 ms
CPU burn can exhaust available audio before presentation recovery can help.

## Did audio actually recover?

For the48 ms candidate, every running PCM observation remains consistent with
accepted application frames, hardware position and boundary. All135,293
enqueued frames/channel (2,823 priming plus132,470 generated) are accepted,
with zero remainder/clear, no PCM error, no invalid running pointer and one
normal drain. The scalar oracle validates final rendered pixels/depth. The
175 submitted drawings equal175 scaled and175 flipped; detailed rows count
175 presentations plus five explicitly skipped presentations.

| Burst frame (zero-based) | Lowest valid observed reserve | Time from observed minimum to primed lead |
| --- | ---: | ---: |
| 29 | 486 frames /11.02 ms | 19.742 ms |
| 59 | 420 /9.52 ms | 19.517 ms |
| 89 | 483 /10.95 ms | 20.029 ms |
| 119 | 417 /9.46 ms | 19.739 ms |
| 149 | 480 /10.88 ms | 19.573 ms |
| 179 | 414 /9.39 ms | Final frame: no subsequent production window |

The primed target is2,823 frames,64.01 ms at44,100 Hz. The first five bursts
regain it well before their next scheduled burst. The sixth completes and
drains, but cannot establish a subsequent recovery interval. These are sampled
native-reserve/recovery measurements, not exact continuous minima or DAC proof.
The minimum9.39 ms reserve is relatively thin; six successes do not establish
unbounded or arbitrary-frequency burst tolerance.

The blocking48 ms control drops to486 valid observed frames after its first
burst, never regains prime before the second, and then stops with SETUP/errno77.
This run does not retain an intermediate invalid RUNNING pointer before that
fault; no low-reserve claim is made from invalid/faulted observations. The earlier
pressure2 control independently failed the same48 ms workload, though later.

For24 ms, candidate and control both pass all six bursts, with1,438-frame
(32.61 ms) minimum observed reserve and no skipped presentations. Candidate
first-five recovery intervals are5.178/10.801/10.781/10.808/10.693 ms after
their observed minima; control intervals are5.198/10.697/5.205/10.797/5.147 ms.
There is no demonstrated24 ms improvement, and no pass-to-fail regression.
Both80 ms cases execute one burn and stop before completing its frame; there
is no completed-iteration timing row or sampled in-burn minimum to invent.

## Presentation cost and mechanism

**Exactly five presentations are skipped across all77 phases.** All occur in
the48 ms candidate at zero-based frames32,62,92,123,152: one in each of the
first five post-burst recovery intervals. That is5/180 (2.78%) of this cell's
produced frames; all180 frames are still rendered and all audio produced.
There are no skips in other candidate cells or any blocking control. Existing
queued/scaler-owned drawings are preserved; the new frame is rendered into
scratch when no source/FIFO credit is free. No READY replacement or missing
audio is being relabeled as successful recovery.

The first clean post48 ms interval, frames30–58, isolates the scheduling change:

| Per-frame median | Pressure3 | Blocking control |
| --- | ---: | ---: |
| Display reservation/try wall | 0.004 ms | 11.480 ms |
| Main CPU | 4.204 ms | 4.372 ms |
| Render wall | 4.439 ms | 4.660 ms |
| Audio admission wait | 12.349 ms | 0.094 ms |

Pressure3 gets ahead enough to restore its audio lead, then admission resumes
normal pacing. The control instead waits for display credit while lead remains
low. That direction of change, matched parameters, explicit skips and valid
reserve recovery support the proposed mechanism. The11.48 ms avoided wait is
wall service, not a claimed11.48 ms CPU saving.

For the passing steady4/8 ms cells, candidate phase-average main CPU costs
8.089/12.089 ms versus control8.051/12.066 ms—about0.039/0.022 ms extra per
quantum in this run. Both retain identical52.93/50.02 ms valid observed reserve
minima and skip nothing. These order-dependent short measurements are not an
exact isolated try-lock cost or broad CPU speedup. Presentation policy has a
small observed cost when it is not solving a backpressure event; repeat/reverse
measurements would be needed to price it more tightly.

## Conclusion and next qualification

Pressure3 demonstrates that the old controller could fail a recoverable48 ms
event because presentation gated catch-up. Keeping emulation/audio production
independent from every presentation is a supported general direction. The next
step is bounded integration and real-core equivalence/gameplay qualification,
including visible cadence, input, audio continuity and owned-buffer teardown.
This synthetic return does not by itself install or qualify a production
emulator policy, solve sustained heavy rendering cost or make80 ms safe.

No new code, driver mode, firmware, installation or rearm accompanies this
return analysis. The first/second tests, ROM/private progress and stock core
remain intact. I: is unarmed; the next boot is stock with permanent UART fix.

## Evidence

Strict archive `device-evidence/a7-pair-before-20261016T044419Z`:9,457 files,
2,034,404,915 bytes, clean FAT. Of9,035 pre-install prior files,9,031 remain
exact. The four expected changes are the owned dispatcher, consumed launch
marker, stock swapfile and healthy new UART helper boot log. Installed binary,
wrapper, qualification, dispatcher, source/local-header and private support
hashes all verify. ROM and normal patched init also verify directly on I:;
there is no armed marker or firmware trigger, and collection writes zero bytes
to the card.

UART remains attached with fault/bypass/full0. IRQ19 increases8,598 over118.805 s,
72.37/sec. Module8,716 calls reconcile as8,029 added services (8,027 writes/two
empty stops) plus687 fallbacks; RX/break grows32, frame/parity/overrun0. No
frequency/temperature or serial-wire claim is inferred.

[Source-bound report, comparisons and418 raw input hashes](../evidence/2026-10-15/render-pressure3/return.json).
The frozen original reporter independently accepts62 cells. Prior published
proofs retain their original hashes. Private payloads, saves, ROM and vendor
binaries are not published.
