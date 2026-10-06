# Getting the full value of the hardware — 2026-10-05

The goal is an understood, efficient device platform. Smooth FF6 is an
acceptance workload, not proof that the hardware is exhausted. Preserve the
interface contract, ownership, measured cost, concurrency boundary and next
qualification for each subsystem. Existing evidence is indexed in
[device findings](device-findings.md); Linux contracts and vendor-specific
unknowns are separated in [interface research](platform-interface-research.md).

| Resource | Established capability/cost | Current use | Remaining opportunity and evidence needed |
|---|---|---|---|
| Cortex-A7 | One ARMv7 core, NEON/VFPv4; declared 666MHz, sustained clocks unknown | Specialized vector tile/color/backdrop/window paths with exact-output checks | Profile remaining scalar PPU/APU and memory traffic by meaningful workload; optimize a demonstrated cost while retaining exact output. Extra threads cannot add CPU capacity. |
| Timers/device events | Short timeout methods average ~10ms; audio poll can wake ~2.77ms in one OSS transport | 1.9 removes short-sleep gameplay gates in favor of PCM consumption/events | Qualify native periods/readiness and CPU spent on observations. Fine timestamps are not proof of fine scheduling. |
| PCM/DMA | Native PCM accepts44100Hz/128-period/3712-buffer and2823 priming frames; startup then fails before emulation | One nonblocking interleaved owner, explicit playable priming, direct native-rate path when accepted | Qualify1.10 state-aware startup, consumption and long-game starvation/latency; alternate rates remain bounded candidates. Compare mmap only after DMA mapping/pointer ownership is known; do not presume copying 128KiB/s is the bottleneck. |
| Hardware scaler | 960 matched 256×224 jobs average 2.26–2.29ms lifecycle, ~1.88ms wait, ~0.37ms other syscall brackets | Existing asynchronous worker, owned chunk input, ordered source/output release | Recover completion/release contract for persistent fd and A/B operation. Price CPU/syscall savings and producer stalls; lifecycle wall is not all CPU. Every observed status includes FRAME_DONE, so fallback removal has no demonstrated benefit here. |
| Display/scanout | Two output-A addresses alternate; worker display waits average 10.46–11.82ms | Producer overlaps peripheral waits; three source slots release after scaling, output retained through flip | Establish panel cadence and actual presentation/backpressure. Queue/status names alone do not qualify continuous hardware queuing. Direct compatible scanout is a candidate only after geometry/ownership are known. |
| Chunk/cache/DRAM | Reserved 16MiB region and working chunk-backed scaler inputs; normal heap inputs previously corrupt | Compact RGB565 pitch avoids known repacking; core renders in its normal memory then copies | Recover cache-maintenance/coherency contract, measure CPU read/write/copy cost and working set. Direct rendering into chunk memory may lose more cache efficiency than its copy saves. |
| UART/kernel activity | ~7k IRQ19/s persisted with stdout/stderr suppressed; tracefs unavailable in tested paths | Console redirection demoted; no guessed interrupt duration | Matching kernel/driver source or a supported duration interface would price it. Count × guessed duration is not measured load. Prioritize costs with a demonstrated frame/audio consequence. |
| Power/watchdog | Autonomous watchdog feeder exists; recovered power-key shutdown path | Existing services retained; diagnostics preserve fresh identity/phase | Establish late shutdown evidence, helper state and battery/suspend semantics. Earlier whole-device poweroffs are unresolved, not proof of a thermal/CPU limit. |
| Possible GPU | DT names a Vivante node; usable device/runtime not established | No acceleration claim | Find matching module/runtime, API and useful workload before planning a port. A DT node is not usable compute or graphics throughput. |

Work proceeds through source/recovered ABI first, software fixes second and
physical qualification where vendor behavior or sustained timing remains
unknown. Tests should answer a specific contract/cost question, not rediscover
standard commands. Negative findings remain part of the map.

The1.9 startup failure provides no emulation cost data.1.10 repairs that seam
and preserves precise startup diagnostics with the same core. After successful
startup, use core CPU, audio-owner CPU, playable
minimum/tails, producer display wait and negotiated settings to choose the next
software target. That choice may be core specialization, PCM service cost or
display lifecycle. A custom scaler owner, cache-aware renderer or smaller
runtime remains in scope if its contract and payoff justify it. No current
result establishes the maximum attainable device performance.

The 1.10 return now proves native startup and some real consumption, then
WRITEI fails. Literal queue overflow is ruled out; stale source admission is
reproduced independently. 1.11 uses fresh worker admission and post-HWSYNC state/
pointers and exercises native retry/snapshot/resume with a consuming provider.
The short second interval's 59.70 calls/sec and 9.93ms mean main-thread core CPU
are evidence of remaining timing/controller questions, not hardware exhaustion
or sustained acceptance. Keep vendor pointer/state-transition and actual
playable reserve separate from the initial silence target.

## 1.11 physical failure and 1.12 diagnostic boundary

The 1.11 return reaches playback and explicitly succeeds at one snapshot load,
then stops in post-fault SETUP. Two final reports contain 2,195/253 calls, with
no intentional holds and no full software queue. An earlier stderr fault and
both reports have a 384-frame pointer/count difference; its origin is unproved.
Current SRAM/snapshots match; the changed SRAM backup is archived. User confirms
audio error/our library. See [return](snes-mvp-1.11-return.md).

1.12 keeps the core/settings/controller and adds a bounded RAM transaction
history plus nonclearing kernel READ_ALL on fault, before audio cleanup. Its
wrapper persists fresh history and clears stale files. Software checks qualify
bounded capture; device kernel access and timing remain pending. This is not a
claimed stop/underrun fix, or proof of a hardware limit. See
[capture contract](snes-mvp-1.12.md).

## 1.12 return and 1.13 durable fault capture

The [1.12 return](snes-mvp-1.12-return.md) fails after 1,106 calls and one
successful snapshot load, with post-fault SETUP and the same 384-frame
pointer/count discrepancy. No intentional holds or full software queue occur.
The fresh final report survives; PCM history is absent, stderr empty and later
periodic/final diagnostic copies missing. Their exact loss mechanism and the
native stop cause remain unresolved; the backup report is historical 1.11.

[1.13](snes-mvp-1.13.md) writes fault history directly to the card and fsyncs
file and directory before returning the error. Capture errno/sync status/bytes
are explicit; failed temporary evidence survives cleanup. Actual client,
runner and immediate-exit wrapper fixtures pass, including injected sync
failure without changing PCM errno. Core/settings/admission remain unchanged.
Independent install readback retains all 22 private and 49 lab files and
stock/hook/core hashes. Physical capture, native continuity and full speed
remain pending; this is not a hardware-limit conclusion or a playback fix.
