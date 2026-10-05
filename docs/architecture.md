# Userspace platform architecture

The implemented MVP is SNES-only. [MVP1.6](snes-mvp-1.6.md) implements full
rendering with a tailored A7 core and corrected peripheral ownership; its
physical run failed with severe lag/choppy sound and whole-device power-off;
see the [failure review](snes-mvp-1.6-failure.md). The longer [platform review](reference/platform-redesign/proposal.txt) is a design proposal, not a completed multi-emulator product or a speed claim.

[MVP1.7](snes-mvp-1.7.md) retains that exact core and pipeline for the user's
requested logging retry. Fresh RAM progress and bounded wrapper persistence
repair the lost-final-report gap; physical performance remains unqualified.

The [1.7 physical return](snes-mvp-1.7-return.md) confirms zero holds and normal
save/exit, but only ~54.63 emulation calls/sec of active-loop time. FF6 party
menu relief and the expensive-call distribution point toward workload-dependent
cost. Producer display blocking and audio-lead control are separately priced;
overlapping scaler/flip wall must not be mistaken for additional CPU. The
source diagnostic command correction is incorporated in1.8.

[MVP1.8](snes-mvp-1.8.md) moves forward on A7 at the user's direction: emitted
tile-mode specialization, cheaper palettes, vector backdrop/window passes and
less shell logging during play. Exactness/lifetime checks pass; physical speed
and sound acceptance remain pending. The existing producer, audio worker and
display queue retain their timing/ownership contracts.

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
  native-FPS scheduling + every drawing -> reserved board video submit
  ROM/core-qualified SRAM/snapshot -> explicit unload

board + timing
  GPIO/mixer -> chunk source slots -> owned display worker -> vendor driver
  kernel clock -> relative waits -> durable bounded lifecycle diagnostics
```

This is one executable with separated C modules. Menu/library allocations are released during gameplay; the core's synchronous load-from-memory ownership permits reclaiming duplicate ROM input after load. The existing vendor kernel, board initialization and driver remain bring-up dependencies.

The producer reserves one of three source slots plus FIFO credit before the
core. The worker releases a source after scaling, holds output through flip,
and completes jobs in order. No core-owned pointer is retained or READY image
superseded. Shutdown drains/joins before display/chunk teardown.

Audio callbacks enqueue every converted frame. One audio worker owns nonblocking
transport, preserving unsent frames and partial stereo-frame tails. Reserve
capacity before the core; stop/join before transitions reset/clear the stream.
Priming, clears and remainder are accounted separately. Snapshot operations
qualify core/ROM and roll back on failed load.

## What is retained deliberately

Plus's accurate sound and continuous conversion remain. 1.6 removes adaptive
suppression and publishes audio before video. Kernel-monotonic native timing
remains the clock; a qualified audio-led production controller is not yet
implemented. The stock driver/kernel remain dependencies; lifecycle/queue
semantics beyond the known backend need qualification.

The vendor already has asynchronous display work and CPU-specific emulator paths. Adding more threads on one CPU does not add compute. The design seeks correct ownership, bounded memory, useful overlap and measurable policy rather than assuming fewer layers alone are faster.

## Full-speed implementation and remaining qualification

MVP1.5's controls were physically confirmed; its run recorded 11.838% held
drawings alongside reported occasional lag and rare crackles. MVP1.6 removes
that suppression, implements exact A7 NEON tile/color kernels, releases source
buffers after scaling, queues display jobs in order, and services PCM through
an independent worker. Source reservation happens before the core runs. The
[implementation record](snes-mvp-1.6.md) documents exactness and ownership checks;
the [full-speed plan](full-speed-snes-plan.md) retains the proposed acceptance
criteria and remaining backend work. Physical full-speed acceptance failed;
the return lacks fresh phase totals, so no individual change is exonerated.

Kernel-monotonic pacing and accurate Blargg behavior remain. A hardware audio
cursor, audio-led production control, and persistent scaler ownership require
device qualification before replacing the known transport/backend. The first
full-render test records core, scaler, flip, queue and audio-worker measurements
in memory. From 1.7, it publishes coherent checkpoints outside callbacks and
the wrapper persists them periodically during a bounded diagnostic window,
as well as retaining final reports after play. These measurements decide which
remaining extension is justified; undocumented hardware queues are not assumed.

Reproducible minimal userspace around the known kernel remains the broader
product direction. A new kernel/GPU/bare-metal port requires matching
source/build/recovery and an established useful acceleration path.

The source prototypes the main plumbing. It does not yet provide a general core catalog, broad content support, final audio clock, GPU path, battery/suspend design or complete Buildroot image.
