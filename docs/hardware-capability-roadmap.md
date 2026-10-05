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
| PCM/DMA | Native ALSA playback node exists; standard negotiation/state/drain contract researched | One nonblocking interleaved owner, explicit playable priming, direct native-rate path when accepted | Establish actual settings and long-game starvation/latency. Compare mmap only after DMA mapping/pointer ownership is known; do not presume copying 128KiB/s is the bottleneck. |
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

After the native game return, use its core CPU, audio-owner CPU, playable
minimum/tails, producer display wait and negotiated settings to choose the next
software target. That choice may be core specialization, PCM service cost or
display lifecycle. A custom scaler owner, cache-aware renderer or smaller
runtime remains in scope if its contract and payoff justify it. No current
result establishes the maximum attainable device performance.
