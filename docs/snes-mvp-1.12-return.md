# MVP1.12 return: audio fails and the flight history is missing

Read-only collection at 2026-10-06 04:25 UTC (October 5 in America/Chicago)
archives and hash-verifies 43 MVP and 49 lab files. The exact 1.12 payload,
stock/hook/core, all snapshots and current SRAM match the protected baseline.
Nineteen prior game-progress files match; the updated SRAM backup is archived
and retained. Both one-shots are consumed. No card writes occur during collection.

The fresh final report contains 1,106 calls and one successful snapshot load.
It fails on `SYNC_OBSERVE errno=77 state=1`, with no intentional held drawings
and software high 2,823/8,192. The fatal call lacks its video callback: 1,105
submitted frames, not a successful 1,106-frame presentation test. Active-loop
rate is 59.819 calls/sec over 18.489 seconds; mean core wall/CPU are
10.527/9.791ms, maximum wall 23.264ms. These are aggregate timing measurements,
not proof of smoothness, continuous audio or sustained full speed.

The second priming epoch again ends with `appl_ptr - epoch_transferred = 384`.
Fresh state is SETUP; its raw pointer difference of 101 frames is not playable
audio. Accepted accounting still balances, with 705 software frames remaining.
The minimum sampled running reserve is 134 frames, about 3ms. Neither the
stop's origin nor the pointer discrepancy is explained by this report.

The diagnostic failed its physical persistence contract. `last-pcm-fault.txt`
is absent, `last-run.log` is empty, and the latest progress file contains only
`wrapper_start`. One early diagnostic-copy checkpoint remains. The library
records READY after the error and B exit with joined display cleanup, but no
final wrapper status survives. We cannot determine whether the fault file was
created in RAM, whether READ_ALL worked, or exactly why later copies are missing.
The `.bak` session is explicitly **1.11**, not another 1.12 attempt.

[1.13](snes-mvp-1.13.md) removes the fault capture's dependence on the periodic
copy path: the native client writes directly to the card and synchronizes the
file and containing directory before returning the PCM error. Capture success,
errno and byte count accompany the final error detail. Playback behavior is
unchanged; this repairs observability, not the native stream failure.

See [analysis](../evidence/2026-10-05/snes-mvp-1.12-return/analysis.json)
and [fresh final report](../evidence/2026-10-05/snes-mvp-1.12-return/session-final.txt).
