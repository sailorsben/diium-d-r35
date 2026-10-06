# MVP1.15 return: the expensive scene owns a real CPU deficit

The owner reports an audio failure on first FF6 launch, a working retry, then
an immediate failure after loading the older snapshot. Read-only return archive
`snes-mvp-return-20261006T055533Z` preserves 45 MVP and 49 lab files. Exact1.15
payload, stock/hook and all21 game-progress files match the installation hashes.
Both one-shots are consumed. No card writes occurred during collection.

Three attempts appear in stderr/startup. Only the second and third final reports
survive; retries rotate the report and replace the latest PCM history. The first
fault has SYNC_OBSERVE/errno77/SETUP metadata, but no retained per-call history.
Its precise cause remains unpriced. This loss is corrected in1.16 by separate
failed-session records, bounded to eight per launcher process.

Both retained snapshot loads succeed, with zero rejection. They then execute
19 and18 calls before controlled audio failure/library return. The logs record
normal display-worker teardown; they do not establish a new whole-device
poweroff, snapshot corruption or a segmentation fault.

| Retained attempt | Ordinary post-load mean wall | Mean main CPU | Median admission wait | Sampled PPU CPU |
|---|---:|---:|---:|---:|
| Second,819 total calls |19.312ms|17.996ms|0.181ms|10.028ms|
| Third,196 total calls |19.497ms|18.060ms|0.185ms|10.131ms|

Ordinary statistics exclude the first restored call, sampled call and terminal
fault capture. The exact derived statistics are in the
[verified analysis](../evidence/2026-10-06/snes-mvp-1.15-return/analysis.json).
Two sampled expensive calls are attribution clues, not a latency distribution.
Kernel thread-clock sampling itself adds roughly2ms to sampled calls; APU
regions include audio callbacks. The terminal30ms calls include fault capture.

Display reservation waits total only3.416ms across819 calls and0.835ms across196.
The software ring never fills. Native PCM accounting remains exact. The final
history again shows accepted production falling behind, followed by application
pointer offsets128/256/384 and SETUP. The exact vendor pointer/stop response
remains unknown. A batch split at software-ring wrap creates a missing large
anchor; its long anchor interval must not be mislabeled one slow core call.

The producer's ordinary CPU alone exceeds the16.688ms native frame period.
Short admission waits cannot explain that deficit. The custom planar decoder
and O3/LTO bundle did not close it. Local replay of the exact same private state
then identified the PPU work described in [the1.16 repair](snes-mvp-1.16.md).
No unchanged1.15 re-arm is appropriate.
