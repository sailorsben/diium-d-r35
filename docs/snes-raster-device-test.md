# One-shot A7 raster measurement

All 12 replay pairs completed on the D-R35. Full-tile strips cut Star Fox
mean core CPU by 30.1%, from 22.603 to 15.793 ms per emulated tick. They
are the best of the two raster builds tested on hardware. The one-shot
markers were consumed.
[Physical results](../evidence/2026-11-10/snes-raster-batches/device-return.json).

The card profile runs the stock returned core against separate raster
candidates with the frozen inputs already on the card. The experiment opens
neither the display API nor native PCM. This lets Star Fox reach the whole
1,200-call window even when native PCM would have ended the old test early.
The test measures emulation, including rendering to memory and PCM
generation. It does not measure panel delivery, actual speaker continuity
or the physical audio reserve needed for a gameplay build.

Both arms use the same Cortex-A7 process and alternate call order. The first
two pairs exercise Star Fox with clipped and full-tile strips. The same
two arms are compared in Mario, Metroid, F-Zero and Ranger. Mario also
compares the wider sprite band guard and F-Zero compares the plain guard.
The package stages all six raster variants as separate cores. The matrix
includes four of them. Each Star Fox arm replays 8,656 cold calls with video
disabled, then renders all 1,200 measured calls with the expected inputs.

Each frame records kernel thread CPU and wall intervals, plus CPU spent
checking the callbacks. Subtract the recorded observer CPU to estimate
core cost, and retain the raw inclusive and wall timings for comparison.
The observer's cache effects and clock-call cost can still affect the
result. QEMU under WSL sometimes reports CPU intervals longer than wall
intervals. The host rehearsal qualifies the output path and CSV format.
Both arms check frozen RGB565, PCM and sample-count hashes per call
and their callback layout. The test stops on a mismatch and records the
game, arm, frame and mismatched field. This comparison supplies a matched
A7 core saving. Native display and audio costs and the complete reserve
curve still need a separate playback qualification.
See the [raster experiment](snes-raster-batches.md).

## Physical results

The original armed payloads and frozen inputs matched their hashes on
return. All 28,800 measured calls across both arms matched RGB565, PCM
and sample counts, and all 12 pairs matched the expected callback layout.
The returned CPU identity matched Cortex-A7. The sparse archive hashed
1,920 files and retained 809,833 new evidence bytes. FAT was clean and
saves, stock binaries and earlier evidence matched their hashes. The
only changes among files present before arming were the installed boot
dispatcher and the stock swapfile. Collection wrote nothing to the card.
[Installation receipt](../evidence/2026-11-10/snes-raster-batches/device-installation.json).

Times below are thread CPU less the measured callback checks. The
observer averaged 1.69–1.81 ms per call across the matrix. Its cache
effects and clock calls remain part of the measurement context.

| Star Fox pair | Baseline mean / p95 | Candidate mean / p95 | Mean saving | Calls over 16.688 ms |
|---|---:|---:|---:|---:|
| Clipped strips | 22.597 / 31.775 ms | 17.171 / 26.301 ms | 24.0% | 1,190 → 398 |
| Full-tile strips | 22.603 / 31.800 ms | 15.793 / 24.830 ms | 30.1% | 1,190 → 398 |

Full-tile strips leave 0.895 ms of mean core time before the 16.688 ms
NTSC budget runs out, or 0.812 ms using wall time less the same callback
checks. Their first three ticks still average 20.039 ms. All 398 calls
with a changed RGB565 picture in the replay meet the core budget with
either variant. The over-budget calls occur on the first call and on
calls whose picture repeats. This is an output correlation. A repeated
picture gives no safe basis for dropping the emulation work on that tick.

Across the other games, full-tile strips move mean core CPU by +0.6%
saving in Mario, −0.9% in Metroid, essentially zero in F-Zero and −1.3%
in Ranger. The sprite checks save about 1% each in Mario and F-Zero.
All of these calls fit their respective core budgets in this replay.

An ideal serial model releases one call every 16.688 ms and carries
unfinished work to the next call. Full-tile strips reach 38.715 ms of
peak backlog and finish at zero with no extra cost. Adding a hypothetical
0.5 ms to every call raises the peak to 147.553 ms, even though average
cost remains below budget. At 1 ms the window ends with 125.321 ms of
backlog. This model uses measured call durations. It has no PCM publication
timestamps, accepted audio, hardware consumption or queue depth, so it
cannot establish native audio reserve.

The next physical comparison should use the full-tile build with native
display and PCM. For mean throughput, the measured 6.811 ms saving must
exceed baseline core time plus added critical-path cost minus 16.688 ms.
Measure the remaining native audio deficit directly by tracing sample
publication, acceptance, hardware consumption and reserve through the
entire replay. Require every draw accounted for, exact generated PCM,
valid pointers, no fill or DROP, and reserve recovery after each burst.
The gameplay install gate remains unmet.

To regenerate the results, run
`python build/report-snes-raster-device.py <return-archive> <output.json>`
with the private return and pre-arm archives plus the hash-matched
frozen oracle.

## Boot and return

Safely eject I:, insert it with the handheld powered off, connect charging
power and cold boot once. This is a silent test. The screen may stay dark
after the splash finishes. Allow up to 28 minutes for stock to appear.
Each pair has a bounded process alarm and opens no native display or PCM
owner. The wrapper consumes both markers before starting any replay.
Another boot goes directly to stock.

When stock returns, shut down normally and reconnect I:. If stock has
not returned after 28 minutes, power off and return the card for partial
evidence collection. Collect sparsely before changing anything. Results
live under `retro/snes-raster-test1/results/run-*`. Check `wrapper.log`
for the per-pair exit status and `complete pairs=12`. Each pair CSV starts
with both warmup CPU totals. Its frame rows contain the call index,
baseline and candidate CPU nanoseconds, wall nanoseconds, and observer CPU
nanoseconds, in that order. The final records contain published frame
counts, PCM sample counts and the oracle result. Each matching pair log
retains cold and gameplay progress. Boot init and existing test results
remain in place.
