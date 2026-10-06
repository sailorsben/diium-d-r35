# MVP1.13 return: production falls behind before the PCM stop

The October 6 return is archived read-only at 2026-10-06 05:09 UTC: 44 MVP and
49 lab files, exact released payload, consumed markers and unchanged stock/
hook/core. All 20 private game-progress files match the protected baseline,
including snapshots, current SRAM and its backup. No card writes or re-arm
occur in this review. The user reports another crash; retained logs show two
controlled audio failures and library cleanup, not a new demonstrated poweroff.

The two final reports are both fresh 1.13: first 26 calls with no pause/load,
then 230 calls with one successful snapshot load/resume. Both fail on
`SYNC_OBSERVE errno=77 state=1` and report a successful synchronized capture.
Neither has intentional holds, partial writes, EAGAIN or a full software queue.
The second trace replaces the first on retry; the first detailed history is
not retained. Current history is 96 operations from epoch 2 and contains a
successful nonclearing kernel READ_ALL result: 16,335 bytes. Recent ring contents
are scaler clock messages, with no explicit audio-stop explanation.

## Failure chronology from the retained history

Early observations agree: application pointer equals accepted epoch count.
The running reserve declines across successive production cycles, before any
pointer/count divergence. Matched large-write anchors 2477 through 2549 span
159.044ms. Accepted count advances 5,888 frames: 37,021/sec against negotiated
44,100. Reported hardware count advances 6,912 frames; accepted-minus-hardware
lead loses 1,024 frames. Nine large batches are 19.8805ms apart on average
(19.516–21.503ms), a frame-production proxy around 50.3Hz in this workload.
It is not a direct measurement of individual CPU calls or physical DAC rate.

| Sequence | Application pointer minus accepted count | Reported queued | Accepted count minus reported hardware |
|---|---:|---:|---:|
| 2530 | 128 | 198 | 70 |
| 2539 | 256 | 166 | -90 |
| 2558 | 384 | 0, SETUP | -283 |

These changes occur across read-only pointer observations, without corresponding
accepted transfers. No RESET/DRAIN/AVAIL_MIN request occurs in the retained
window. Before the last failing HWSYNC, reported queue is 741 frames; the
accepted-count comparison is only 485 frames because the pointer already
leads accepted writes by 256. After another 17.665ms, HWSYNC fails and the
non-HWSYNC read finds SETUP and the third 128-frame increment.

The evidence strongly supports production starvation as the trigger, followed
by an unusual vendor response. Period-sized padding or recovery is plausible,
but we have not recovered the responsible kernel path or the data it plays.
Do not label the extra counts actual silence, an unrelated writer, memory
corruption or a proven driver bug. Standard Linux 4.19 GET flags preserve
application control, while ordinary XRUN stops in XRUN rather than SETUP:
[SYNC_PTR implementation](https://raw.githubusercontent.com/torvalds/linux/v4.19/sound/core/pcm_native.c),
[PCM state update](https://raw.githubusercontent.com/torvalds/linux/v4.19/sound/core/pcm_lib.c).
That source comparison establishes a difference, not this vendor's cause.

## What the aggregate reports cannot settle

The second report averages 59.026 active calls/sec, 10.199ms core wall and
9.620ms main-thread CPU. Those averages hide the failing phase. It has fifteen
19ms calls and two 21ms calls, consistent with the repeated slow production
visible in the trace. Maxima of 30.669/43.330ms can include fault persistence
and mutex blocking; do not turn them into normal core worst-case estimates.
Display reservation totals only 1.066ms over the 230-call session (0.114ms in
the first): the previous-display admission wait is not the observed multi-ms
per-frame loss. Asynchronous scaler/flip and scheduling CPU costs still exist.

The first attempt fails without loading a snapshot, so snapshot corruption or
resume alone cannot explain all failures. The second fails at the same epoch
accepted count/pointers as 1.12, supporting a repeatable expensive workload.
No longer clean run or hardware ceiling is established.

[Execution-budget review](execution-budget-review.md) sets the next engineering
direction. More priming, a softer error label or automatic PREPARE would not
correct a repeated production deficit. Full rendering and complete sound need
the expensive phase to meet its throughput budget with service margin.

See [derived analysis](../evidence/2026-10-06/snes-mvp-1.13-return/analysis.json)
and [retained history](../evidence/2026-10-06/snes-mvp-1.13-return/last-pcm-fault.txt).
