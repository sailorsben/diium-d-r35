# Five-game physical return — 2026-10-16

This run was **aborted during Star Fox's cold replay**, with the previous
F-Zero picture still displayed. Ben initially reported a crash during F-Zero,
then confirmed pressing Select+Start. F-Zero completed its full measured window.
The recorded normal child exit 5, stopped=1 and warmup-abort error match the
user abort path. No process crash, forced timeout or native audio error is
recorded. The exact replay call at abort was not logged.

| First blocking-policy window | Measured calls | Minimum sampled audio reserve | Result |
| --- | ---: | ---: | --- |
| Super Mario World, PAL | 1,200 | 2,440 frames / 55.33 ms | Clean bounded window |
| Super Metroid | 1,200 | 2,191 frames / 49.68 ms | Clean bounded window |
| F-Zero | 1,200 | 2,184 frames / 49.52 ms | Clean bounded window |
| Star Fox | 0 | Native PCM not opened | Cold replay aborted |
| Rendering Ranger | 0 | Not tested | Not started |

The three completed windows each render, submit, scale and flip all 1,200
frames, with no skips, complete native histories, exact final PCM accounting
and worker/display cleanup. All three still report the conservative sampled
20% headroom gate NOT_MET. Sampled reserve is not continuous DAC proof.
There are **zero matched policy pairs**: none of the candidate windows ran.
This return cannot establish a presentation-policy benefit or qualify all
five games as fixed.

Star Fox's failed session lasts 40.666245 seconds, with zero measured renders
and no native PCM period/buffer. There is no warmup completion receipt or
measured frame history. Its retained input.csv and pcm-full.txt are byte-for-byte
copies of F-Zero's preceding buffers; exclude them from Star Fox analysis.
The reporter now distinguishes failed-before-measurement from not-started
windows rather than labeling both missing.

The suite records four attempted windows, one failure and stopped=1. Its audio
worker and display are released, board_closed=1, supervisor reaped=1, forced=0,
raw_status=1280 (normal exit 5), and wrapper lab_exit=5. The wrapper safely
permits stock startup. The unchanged final F-Zero picture and silent replay
gave insufficient visible progress feedback; the next test should display
replay progress and record abort source/call before repeating the unchanged
matched measurement windows. No replacement package or rearm was performed.

## Preservation

Private sparse archive: `a7-pair-before-20261017T004643653155Z` (UTC name;
collected October 16 local time). It retains 6,065,591 new content bytes, all
deduplicated by hash; no full backup and zero card writes. FAT is clean,
serial 11EB-1465, both one-shot markers consumed, no firmware trigger.
All 27 installed payload hashes match the published installation.

Of 10,759 pre-install files, 10,755 remain byte-identical. The four differences
are the authorized dispatcher, consumed launcher receipt, normal swapfile and
UART latest-boot log. All 636 outside-retro files are exact. Saves, private
states, stock binaries, permanent UART/init and older evidence are unchanged.
UART remains attached, FIFO8, with full/fault/bypass/cap zero; 7,755 calls =
7,213 added + 542 fallback, and 7,213 = 7,212 writes + one empty stop.
This verifies correction continuity, not CPU savings.

Public metadata: [return receipt](../evidence/2026-10-16/fivegame/return.json).
Raw logs, states and ROMs stay private. Reproduce with the sparse archive:

```powershell
python build/report-fivegame.py device-evidence/a7-pair-before-20261017T004643653155Z --installation evidence/2026-10-16/fivegame/installation.json
```
