# MVP1.11 return: native stream stops during gameplay

The user confirms an audio error and return to our library, rather than a new
whole-device power-off. The snapshot load succeeds before the final failure.
The consumed return is archived read-only at 2026-10-06 04:00 UTC (October 5 in
America/Chicago): 43 MVP and 49 lab files, exact 1.11 payload and unchanged
stock/hook/core. Nineteen prior game-progress files, including all snapshots
and current SRAM, match; a changed SRAM backup is archived and preserved.

The two retained final reports contain 2,195 and 253 calls. Both fail with
`SYNC_OBSERVE errno=77 state=1`, no intentional drawing holds and software high
2,823/8,192. SETUP is now a post-fault observation, rather than the earlier
pre-write sample. This is not software queue exhaustion. The first final
report reaches 59.897 active calls/sec over 36.65 seconds, with 10.78ms mean
core wall and 10.03ms mean core CPU; its longest call is 26.57ms. The final
report records one successful snapshot load, one pause and a second priming
epoch before failing. Neither is a clean sustained-play acceptance result.

An earlier stderr fault and both final reports share a new anomaly:
`appl_ptr - epoch_transferred = 384`, exactly three 128-frame periods. Their
raw application/hardware pointer differences are 92, 107 and 101 frames.
Those gaps are not valid playable PCM in SETUP. No retained transaction history
establishes when the discrepancy begins, whether a partial/faulting transfer
changes a pointer, or what stops the stream. Do not label it a proven vendor
bug, underrun, pointer corruption, or hidden write. The running minima of
140/134 frames are only about 3ms; admission minima of 747/741 also show the
initial 64ms reserve is not maintained throughout these sessions.

The software defects corrected in 1.11 remain real, but they did not resolve
this physical failure. A consuming fixture models ordinary Linux behavior;
it does not substitute for this driver's state transitions. The first-192-line
stderr snapshot lacks the later faults, while the final reports preserve them.
Kernel capture still has no ring contents because `dmesg` is absent.

[1.12](snes-mvp-1.12.md) keeps the same core, parameters and controller while
adding a 96-entry RAM history of PCM syncs, writes, thresholds and lifecycle
requests. On the first sticky fault it captures the history and read-only
kernel READ_ALL before cleanup. Direct kernel capture avoids the missing
utility; permission/unsupported failures are recorded explicitly. This is a
targeted diagnostic, not another claimed fix or a hardware-limit conclusion.

See the [returned analysis](../evidence/2026-10-05/snes-mvp-1.11-return/analysis.json)
and [final report](../evidence/2026-10-05/snes-mvp-1.11-return/session-final.txt).
