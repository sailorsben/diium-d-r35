# Userspace platform architecture

The implemented MVP is SNES-only. The longer [platform review](reference/platform-redesign/proposal.txt) is a design proposal, not a completed multi-emulator product or a speed claim.

## Implemented owners

```text
boot wrapper
  consume one-shot -> archive/log -> finish showlogo -> start one child

main/UI
  scan library -> first paint -> suppress held inputs -> navigate
  release library allocations -> runner -> pause UI -> library/exit

runner
  bounded ROM/ZIP loading -> exact core -> environment/input callbacks
  continuous resampler -> bounded PCM queue -> OSS transport
  native-FPS scheduling + adaptive internal drawing -> board video submit
  ROM/core-qualified SRAM/snapshot -> explicit unload

board + timing
  GPIO/mixer -> chunk source slots -> owned display worker -> vendor driver
  kernel clock -> relative waits -> durable bounded lifecycle diagnostics
```

This is one executable with separated C modules. Menu/library allocations are released during gameplay; the core's synchronous load-from-memory ownership permits reclaiming duplicate ROM input after load. The existing vendor kernel, board initialization and driver remain bring-up dependencies.

The display producer owns compact source copies; the worker owns a submitted slot until draw/flip completes. One pending job and alternating slots permit overlap without retaining core-owned pointers. Shutdown joins the worker before tearing down display/chunk allocations.

Audio callbacks enqueue every converted frame. Nonblocking transport preserves unsent frames and partial stereo-frame tails. The runner reserves capacity before entering the core, so it cannot silently discard a callback the core will not replay. Startup/resume priming is accounted separately. Snapshot operations qualify the core/ROM and roll back on failed load.

## What is retained deliberately

Plus and its known conversion/render-budget policy remain the baseline while host piping is qualified. Adaptive suppression applies to internal drawing, while audio/emulation continue. The initial clock is native-FPS monotonic control; an audio-led production controller is not yet implemented.

The vendor already has asynchronous display work and CPU-specific emulator paths. Adding more threads on one CPU does not add compute. The design seeks correct ownership, bounded memory, useful overlap and measurable policy rather than assuming fewer layers alone are faster.

## Next measurements and earned changes

1. Confirm all physical directions, pause/state/save flow and sustained sound/video.
2. Attribute `PScaleRun` open/configuration/trigger/status/stop/close and producer waits separately. Keep timing in memory during frames and flush bounded results after a session.
3. Measure actual audio position/period/queue behavior before selecting an audio-led clock.
4. Consider persistent scaler configuration/queueing only with supported ioctls and completion identity. Preserve DMA ownership and recovery.
5. Compare plain2005/Plus/2010 on the same corrected host with compatible SRAM and per-core timing/state qualification. NEON presence alone does not pick a winner.
6. Reproducible minimal userspace around the known kernel is the intended broader product. A new kernel/GPU/bare-metal port is not a prerequisite; it requires matching source/build/recovery and a priced bottleneck.

The source prototypes the main plumbing. It does not yet provide a general core catalog, broad content support, final audio clock, GPU path, battery/suspend design or complete Buildroot image.
