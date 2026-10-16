# ROM-free renderer and device pressure lab

The current software has not established a hardware ceiling. This lab replaces
game-driven discovery with controlled command streams, isolated stages and load
sweeps. Games remain integration/regression evidence after a general change;
they are no longer the only source of workloads or bottleneck clues.

`render-pressure1` is built and qualified offline, **not installed or armed**.
No I: access or changes occurred. The persistent UART fix and returned FFVI
evidence remain intact. A physical run is still needed to price these cells.

## What the test can decide

| Question | Controlled comparison | Useful outcome |
| --- | --- | --- |
| Is color production expensive? | Same generated rows through pinned scalar gfx.h, project NEON, cached-color kernels | Actual kernel cost with pixel/depth equality, without CPU/APU/game scripting |
| Does reuse pay? | Small repeated working sets versus palette/tile churn and cache collisions | Cache benefit and invalidation/lookup cost, rather than assuming every repeating effect is cacheable |
| Is direct output worthwhile? | Heap render plus copy versus render into owned chunk slot | Price chunk-memory accesses against the payload copy they avoid |
| Is memory traffic limiting us? | Fill, copy, fill+copy on heap/chunk at three sizes | Measured payload throughput and mapping sensitivity |
| Is the display path itself slow? | Prebuilt frames, no renderer/audio, serial versus queued | Achieved scaler/flip throughput and backpressure, without emulation work |
| Are producer/driver stages badly serialized? | Identical render in serial/queued display routes | Price useful overlap and avoid summing asynchronous waits as CPU work |
| Does audio fail independently of emulation? | Audio-only, render+audio, controlled steady/burst CPU loads | PCM reserve, pointer consistency, starvation/failure thresholds |
| Are the tools distorting the result? | Detailed/aggregate runs, then reversed order | Additional frame-instrumentation cost, while inherited instrumentation stays constant |
| Is background system work changing? | Bounded proc/UART/clock snapshots at phase boundaries | IRQ growth, CPU accounting, memory and available clock context |

These comparisons can falsify claims such as “the device cannot render this
many pixels within a frame.” They cannot prove that no better implementation
exists. The fastest achieved implementation is evidence of feasibility, not a
mathematical lower bound on execution time or the device's theoretical optimum.

## Workloads and phase plan

There are70 bounded phases:

- 18 CPU-render cells: six scenes × scalar/NEON/cached rows,32 frames each.
- 18 memory cells: three sizes × fill/copy/fill+copy × heap/chunk,32 iterations.
- 6 prebuilt-display cells: three sizes × serial/queued,180 frames.
- 1 audio-only cell,180 production quanta.
- 16 combined cells: NEON/cached × copied/direct × serial/queued × audio off/on.
- 4 steady CPU-load cells: additional4/8/12/16ms CPU-clock targets per frame.
- 3 burst cells: additional24/48/80ms CPU-clock targets every30th frame.
- 4 instrumentation controls: detailed/aggregate, then aggregate/detailed.

Sizes are256×224,512×448 and640×480 RGB565. Payload sizes are114,688/458,752/
614,400 bytes; payload traffic is not the same as total DRAM bus traffic.
Scenes cover repeated rows, eight-layer color math, early depth rejection,
per-line windows with palette/tile churn, high resolution and native output.
Flips, transparency, subscreen/fixed math and depth remain dynamic in cached
paths. Cache keys are explicitly invalidated across all generated tile/palette
epochs. The scalar oracle uses the pinned Snes9x gfx.h arithmetic and ZERO table;
its loop auto-vectorization is disabled while explicit NEON intrinsics remain.
It is a correctness/control implementation, not an asserted fastest scalar.
Rendering measurements include the shared deterministic input preparation and
depth/subscreen setup; they are not isolated instruction prices for a single row.

These are decoded row-command workloads, not an implementation of the entire
SNES PPU. They do not price65816 instruction dispatch, SPC/DSP execution, VRAM
bitplane decoding, PPU register timing, exact OBJ limits or real-game cache
invalidation. Those need separate subsystem fixtures and eventual full-core
regression. A cache win here is not permission to ship a game-cache change.

Audio uses the physically used native PCM owner and negotiated output rate,
fractional sample accounting per16.688153ms quantum, real priming/admission,
preserved partial transfers, joined owner and explicit finish. It generates a
quiet deterministic triangle signal with20ms endpoint ramps; sound/DAC fidelity
is not inferred from accepted bytes. Long load cells may deliberately fail the
audio budget. They are recorded as failures and cleaned up before the next cell.
Requested CPU load is measured under the kernel CPU clock, not assumed MHz.

## Measurement and interpretation

Per-frame timing separates admission, reservation, rendering, submission and
explicit serial display joins. Main/display/audio CPU counters stay separate.
The total phase interval includes display drain, but excludes initial audio
priming, final audio tail/drain, oracle work, snapshots and file persistence.
Audio worker's final CPU count includes its drain, so do not sum differently
bounded thread counters into an allegedly exact phase CPU budget.

Every final produced image is copied before releasing the direct slot and
compared with the scalar oracle, including depth. That last-frame validation
copy is declared overhead: total phase time includes it; per-frame performance
distributions exclude the first eight frames and that final frame. CRC/input
equality does not prove panel delivery or cache coherence at DMA read time.
Submitted/scaled/flipped equality is driver accounting, not optical capture.

Detailed runs retain bounded RAM rows and complete native PCM transaction
histories. Phase results/snapshots are persisted only outside timed work after
display drain and audio-owner stop. PCM reserve minima are restricted to active production
timestamps, so deliberate final draining cannot become a false starvation result.
The reporter checks pointer/accounting identities, retained-history completeness,
no dropped drawings and copied/direct byte counts. It rejects mock timing as
physical evidence and requires an installation receipt plus strict archive for
physical reporting. Aggregate controls remove the lab's additional frame clocks;
the inherited board metrics/native PCM tracing still have cost. They are not an
entirely uninstrumented control.

The first pass finds costs and failure transitions. Repeat/reverse physical
measurements and A/B a concrete general improvement before declaring savings.
Thermal/frequency/system context must accompany a plateau. We have not recovered
every hardware clock/cache/DMA contract, so a plateau alone cannot close the case.

## Code and driver review, started from actual bytes

The audit pins recovered kernel SHA256
`21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321`.
It inventories11 actual scaler/chunk/native-audio functions and direct calls;
private instruction listings remain local. This is the beginning of a system
review, not a claim that every driver has been semantically audited.

One formerly unresolved contract is now established from the matching code:
`gp_pscaler_ioctl(0x80045004)` takes a scalar unsigned millisecond timeout,
clamps it to5,000 and passes it to the helper using `__msecs_to_jiffies`.
That helper uses `prepare_to_wait_event`, `schedule_timeout`, completion-flag
rechecks and `finish_wait`. The vendor's3000 is a3-second maximum timeout,
not a mandatory delay or evidence of busy-spinning. This does not price the
actual scaler hardware operation; previous measured completion waits were much
shorter and must be repriced under the corrected UART environment.

Kernel open/release semaphore and allocation/free call sites are now available
for targeted follow-up. Queue/retrigger symbols and fields do not by themselves
qualify persistent FDs, pipelined DMA, buffer release or new ioctl sequences.
This test retains the working driver calls and ownership boundaries.

`build/uart-fix-private/reconstructed.config` is our module-build reconstruction,
not the recovered boot configuration. Its HZ/HIGH_RES/PREEMPT/CPU_FREQ choices
must not be cited as physical device facts. The measured coarse waits remain
valid evidence; exact configuration recovery and clock policy remain open.

## Recovery and qualification

The frozen board/audio support is byte-identical to the physically returned
FFVI suite. The new controller still needs its own physical acceptance. It
retains owned chunk buffers, bounded queue credit and joins before freeing;
the splash must exit before board initialization. Every frame services the
stock heartbeat/input outside detailed operation brackets.

The wrapper requires healthy active UART correction, consumes both one-shots
before hardware startup, then uses a finite ARM supervisor. The child has a
240-second budget; the supervisor permits300 seconds, then TERM/3s/KILL with
bounded reap. Forced/uncertain child termination withholds stock until reboot,
including when the final UART check also fails. The next boot is stock with
the permanent UART correction. Select+Start aborts. No scheduler priority,
clock policy, kernel text, FIFO/scaler queue bits or MMIO experiment is added.

Offline qualification passes60 full-frame oracle/guard cases, all70 short mock
controller cells, ARM child supervision, ABI/local-header dependency checks,
NEON instruction presence, exact firmware shell syntax/consumption/replay and
four further wrapper faults (absent/faulty UART, forced+UART fault, unexpected
child exit). The short mock deliberately skips real PCM/DMA and does not run
every long burst; those thresholds require the physical test. No QEMU speed
figures are published. [Qualification](../evidence/2026-10-15/render-pressure1/qualification.json),
[fault checks](../evidence/2026-10-15/render-pressure1/fault-qualification.json),
[exact-kernel audit](../evidence/2026-10-15/render-pressure1/device-path-audit.json).

Rebuild with `prepare-render-pressure.py`, `build-render-pressure.sh`,
`audit-device-render-path.py`, `qualify-render-pressure.py` and
`check-render-pressure-faults.py` under build/. Preparation requires a fresh
private directory. `install-render-pressure.py <fresh-archive>` is explicitly
install-only: clean pushed source, archive/FAT/stock/init/ROM checks, separate
versioned package and readback precede arming. It has not been invoked.
No ROM or private state is part of the test or publication.
