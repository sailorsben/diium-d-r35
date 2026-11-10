# One-shot Super FX timing test

Armed and independently verified on I: from `d1eede0`.
Readback matched both markers, all seven payloads and 1,919 protected
files. FAT and normal boot init passed. A fresh sparse archive hit the
NTFS hard-link limit for an old log. A full hash comparison confirmed
the same 1,920 files as the previous archived return, so staging used
that verified archive. Both physical pairs subsequently completed.
[Installation receipt](../evidence/2026-11-10/snes-raster-batches/superfx-device-installation.json).

The D-R35 runs two paired Star Fox replays. The first compares the
full-tile raster baseline from the previous physical test with the
combined Super FX build. The second loads two copies of the same
toggle-enabled binary, with batching disabled on one arm and enabled
on the other. This measures the effect of the fast paths with the
executable bytes held fixed.

Each arm runs the same 8,656 warmup ticks with raster output disabled,
then draws all 1,200 measured ticks. The runner checks pixels, generated
PCM, sample counts and callback layout against the frozen reference.
Kernel thread CPU and wall timing are retained alongside the callback
observer cost. The full-tile baseline measured 15.793 ms mean core CPU
against the 16.688 ms NTSC period in the prior run. Evaluate the first
three ticks, the 398 previously over-budget ticks, the full-window mean
and p95, and the number of ticks over budget.

This is a core timing measurement. Native display, PCM playback and
the cumulative audio reserve require a separate device run. The
[offline results](snes-superfx-batching.md) and
[physical raster baseline](snes-raster-device-test.md) record those
separate measurements.

## Physical return

Both pairs completed. All 4,800 measured calls matched the frozen
pixels, generated PCM, sample counts and callback layout. The figures
below subtract the CPU time spent checking the callbacks.

| Comparison | Mean CPU before → after | Mean saved | p95 before → after | Over 16.688 ms |
|---|---:|---:|---:|---:|
| Full-tile versus combined build | 15.904 → 15.283 ms | 0.622 ms (3.91%) | 25.002 → 24.147 ms | 398 → 396 |
| Identical binaries, batching off versus on | 16.483 → 15.273 ms | 1.209 ms (7.34%) | 26.869 → 24.189 ms | 398 → 397 |

On the 398 tick IDs that exceeded the budget in the previous full-tile
run, the combined build saves 0.733 ms against full-tile and the toggle
saves 2.154 ms against its own control. The two controls have different
executable bytes. Use the standalone comparison to budget the combined
build and the toggle to measure batching with code layout fixed.
The combined build leaves 1.406 ms of mean core time under the NTSC
budget. Native playback cost and audio reserve remain unmeasured.
[Return evidence](../evidence/2026-11-10/snes-raster-batches/superfx-device-return.json).

The sparse return archive hashes all 1,936 files. Saves and states
match the preceding archive. Among preexisting files, the dispatcher
and stock swapfile changed. Both boot markers were consumed. The
collector wrote only to the host archive.

Windows reports the FAT32 volume dirty and gives it a Full Repair
Needed status. Read-only CHKDSK completed on the mounted volume and
reported no filesystem problems. The dirty flag persisted after the
scan. The Windows system log records an I/O retry and a paired disk
error at reconnect for the disk holding I:. That trace does not identify
whether the card, reader or preceding shutdown set the flag.
[Windows dirty-bit behavior](https://learn.microsoft.com/windows-server/administration/windows-commands/fsutil-dirty) ·
[CHKDSK behavior](https://learn.microsoft.com/windows-server/administration/windows-commands/chkdsk).

## Boot and return

Safely eject I:, insert it with the handheld powered off, connect
charging power and boot once. The screen may go dark after the splash
and the test is silent. Allow up to 15 minutes for stock to appear.
The test consumes both markers before it begins. A later boot goes
directly to stock.

When stock appears, shut down normally and reconnect I:. If it has
not appeared after 15 minutes, return the card for collection of
the partial logs. Archive before changing the card. Results are under
`retro/snes-superfx-test1/results/run-*`. The wrapper log gives each
pair's exit status and ends with `complete pairs=2` when both finish.
The pair CSV schema matches the previous raster device test.
