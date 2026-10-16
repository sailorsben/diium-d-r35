# Matched FFVI physical return — 2026-10-16

The returned card completes 78 clean bounded windows out of 80. Both 48 ms
blocking controls fail with native audio publication/pointer errors; both
policy-1 candidates complete all 1200 renders, all audio accounting and all
seven bursts. This supports the presentation policy's recovery benefit on this
device. It does not establish sustained interactive gameplay acceptance.

Ben reported **“No obvious issues”** when asked about clicks/gaps, choppy
visuals and the return to stock. This is a user observation, without independent
optical or DAC capture.

| Workload | Blocking policy 0 | Scratch policy 1 |
| --- | --- | --- |
| 18 original contexts, two repeats per policy | 36/36 clean | 36/36 clean; four total skips |
| HOLY +24 ms, seven bursts per run | 2/2 clean, no skips | 2/2 clean; one and two skips |
| HOLY +48 ms, seven bursts per run | 0/2 clean | 2/2 clean; 12 and nine skips |

Every successful cell renders 1200 frames; presentation skips do not skip
emulation or audio generation. All 40 paired comparisons retain identical
logical effect/input progression and generated PCM sample counts over their
shared recorded frame indices. These comparisons do not prove byte equality
of physical DAC output. Total intentional presentation skips: 28.

The 48 ms controls stop after 480 and 360 recorded renders. Both have only 360
valid CPU-prefix calls. The first control's later apparent third burn is beyond
the valid prefix and cannot count as successful recovery. Both terminate with
`Audio publication failed: File descriptor in bad state`. The suite joins its
audio workers and idles display, closes the board, and exits normally with
diagnostic status 1 for two failures; supervisor reaped=1, forced=0.

The candidates' minimum valid sampled reserve is 237 frames, or 5.374 ms at
44.1 kHz. Each regains at least 2823 frames after all seven bursts. Across the
two runs, the longest interval from the minimum observation to the first
reprimed observation is 306.087 ms. All 42 bursts in the six successful loaded
runs have such a recovery observation within their frame-boundary brackets.
The brackets use the fresh PCM observation before the load frame through the
observation 119 frames afterward. They are not exact burn-onset timestamps;
sampled minima are not continuous minima, and a reprime crossing is not proof
of an uninterrupted reserve floor.

For ordinary contexts, matched warm valid-index mean recorded-thread CPU
savings range from -0.04765 to +0.11944 ms per call, with median +0.00347 ms
across 36 pairs. This is little consistent ordinary-work CPU benefit. Main,
audio and video thread observations include instrumentation; they are not
whole-machine CPU measurements. Reduced wall waiting is not CPU saving.

## Preservation and collection

Read-only collection `a7-pair-before-20261016T174559367837Z` has a clean FAT,
zero card writes and no armed test or firmware trigger. All 95 installed
payload hashes match the frozen installation receipt. Both consumed marker
receipts match. Of 10,093 pre-install files, 10,090 remain byte-identical;
the only differences are the authorized dispatcher, consumed last-launch
receipt and stock-boot swapfile. All 636 outside-retro files, permanent UART
and init, stock binaries, ROMs, SRAM, snapshots and prior evidence remain exact.

UART remains attached, FIFO8, with full/fault/bypass/cap counters zero. During
1652.75 seconds, IRQ19 and calls each increase by 118,401 (71.64/s);
118,401 = 110,201 added + 8,200 fallback, and 110,201 = 110,199 writes + two
empty stops. This verifies the retained correction, not a CPU-speed claim.

The sparse collector retains 436,803,285 new bytes of selected logs/progress,
including its first seed of older evidence. Supplemental collection adds zero
content bytes. Static payloads are hash-only; retained content is deduplicated
by SHA256 hard links. No new full rollback backup was created. I: remains
unarmed; a subsequent boot follows stock with the persistent UART fix.

## Reproduction and limits

[Public aggregate and raw-input hashes](../evidence/2026-10-16/presentation-ffvi/return.json)
bind the return inventories and original installation receipt. Private logs,
states, ROM and vendor dependencies remain excluded from publication.

Run `python build/report-presentation-ffvi.py <archive> --installation
evidence/2026-10-16/presentation-ffvi/installation.json`, then
`python build/evaluate-presentation-ffvi-return.py <archive>`.
Reporter regression checks cover frozen proof reconstruction, changed/wrong
proof rejection, invalid CPU/PCM-tail censoring and mock rejection.

After deployment, the local installer was requalified for sparse archives.
Its newer private qualification file differs from the deployed one. The
reporter now reconstructs the original proof's exact LF/CRLF bytes from the
frozen published qualification and checks the installed receipt's SHA256.
All 95 returned payload hashes still must match; raw evidence is unchanged.

The installed package remains a measurement experiment. Sustained interactive
gameplay, panel/input behavior and speaker acceptance remain unqualified.
No production promotion, new installation or rearm occurred on this return.
