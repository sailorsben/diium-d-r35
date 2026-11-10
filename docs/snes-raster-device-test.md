# One-shot A7 raster measurement

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
result. Both arms check frozen RGB565, PCM and sample-count hashes per call
and their callback layout. The test stops on a mismatch and records the
game, arm, frame and mismatched field. This comparison supplies a matched
A7 core saving. Native display and audio costs and the complete reserve
curve still need a separate playback qualification. The physical opening
requires 10.795–10.968 ms of core saving before other critical-path work.
See the [raster experiment](snes-raster-batches.md).

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
