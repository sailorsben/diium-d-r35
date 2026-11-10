# One-shot Super FX timing test

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
the cumulative audio reserve require a separate device run. The new
A7 saving and its effect on the playback margin are pending. The
[offline results](snes-superfx-batching.md) and
[physical raster baseline](snes-raster-device-test.md) record those
separate measurements.

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
