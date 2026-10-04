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

## Proposed full-speed path

MVP1.5's controls are physically confirmed. Occasional lag, rare crackles and
11.838% held drawings remain. The chosen proposal is a tailored Plus renderer
and a host pipeline that overlaps core work with peripheral operation; see the
[full-speed plan](full-speed-snes-plan.md) for instruction choices, ownership,
CPU allocations and acceptance. This is proposed behavior, not the current MVP.

Release the chunk source after scaling rather than scanout, preserve an ordered
bounded queue, publish audio before video, and service queued PCM independently.
Keep one pacing owner and accurate Blargg behavior. Add exact A7 NEON tile/color
kernels before asking the device to prove full rendering. Qualify audio cursor
and scaler completion semantics; record timings in memory and flush after play.
Persistent scaler ownership is a next backend extension with recovered ioctls,
not permission to assume undocumented hardware queues work.

Reproducible minimal userspace around the known kernel remains the broader
product direction. A new kernel/GPU/bare-metal port requires matching
source/build/recovery and an established useful acceleration path.

The source prototypes the main plumbing. It does not yet provide a general core catalog, broad content support, final audio clock, GPU path, battery/suspend design or complete Buildroot image.
