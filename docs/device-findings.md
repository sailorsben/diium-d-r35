# Device findings

Evidence collected on one DIIUM D-R35 through 2026-10-04. **Observed** means returned device data or exact binary/source evidence. **Inferred** means supported but not a direct census or measurement. Unknowns remain explicit. Evidence filenames and hashes are indexed in [the evidence manifest](../evidence/manifest.json).

## Platform identity

| Property | Finding | Boundary |
|---|---|---|
| OS | Linux 4.19.128, Buildroot 2020.02, glibc 2.30, ARM hard-float | Not Android; `/system` alone does not imply Android |
| CPU | One Cortex-A7 r0p5, ARMv7, NEON, VFPv4/D32, integer divide | Exact Generalplus silicon SKU unknown |
| Device tree | Generalplus EMU Board, GPA7XXXA family | GPA7740A is a candidate relative, not identified silicon |
| CPU frequency | DT declares 666,000,000 Hz | Live/sustained CPU, DDR and bus clocks unmeasured |
| Memory | 48 MiB boot RAM plus 16 MiB chunk reservation; Linux MemTotal 43,120 KiB | Consistent with 64 MiB arrangement, not physical RAM census |
| Reserved region | Chunk memory at physical 0x03000000–0x03ffffff | CPU cache policy and maintenance contract not established |
| Display | Exported 640×480, lcd1_mipi_NV3051F | Physical panel cadence not measured |
| Sound | `/dev/dsp`, vendor playback/ALSA nodes | `/proc/asound` absent; period/underrun semantics not fully known |
| GPU | `vivante,gc` DT node exists | No working galcore/runtime/device established |

One CPU means display/I/O threads can overlap peripheral waits, but cannot add emulation compute capacity. The vendor runtime's gameplay memory headroom was tight. Configured 256 MiB swap is not physical RAM; sampled vrtemu VmSwap was zero and swap use was stable, so ongoing swap thrash was not demonstrated.

cpufreq, thermal/cache inventory and clock summary were absent in tested locations. Software perf task-clock worked; hardware cycles/instructions/branch/L1/L2 counters returned ENOENT and no PMU DT node was established. Cache sizes from a related chip specification must not be promoted to this device's measured properties.

## Runtime and storage

Observed route:

```text
internal Linux -> SD retro/init -> main supervisor -> vrtemu menu/host
               -> selected libretro core -> frontend callbacks -> driver.so
               -> chunk memory / display / scaler / OSS devices
```

`/media/sdcardb1` is the card; `/usr/retro` is its active runtime view. The SD contains executable software as well as games. `main` is a small supervisor; `vrtemu` is the host and includes bundled libraries, not RetroArch. Numbered folder `002` is observed SNES/SFC and `003` NES/FC. Other category numbers were not guessed from empty directories.

## Two essential boot/input discoveries

The boot animation remains a display owner until its marker handshake completes. It can overwrite the replacement UI during cleanup. [The exact handoff](boot-and-hardware-contracts.md#splash-handoff) is required before InitVFB.

The stock GPIO decoder emits native masks, which must be interpreted by the final libretro callback table. **GPIO200/201/202/203 are Up/Down/Left/Right**, not Up/Left/Right/Down. An early review got this wrong; the source and independent fixture now use the complete translation.

## Clock failure: measured and repaired in our runtime

A device startup probe returned:

```text
direct kernel CLOCK_MONOTONIC:    8.361471000 s
libc CLOCK_MONOTONIC:           447.327424168 s
direct kernel CLOCK_BOOTTIME:     8.361507000 s
```

Earlier input-loop snapshots showed the main thread stuck in the same absolute `clock_nanosleep` six seconds apart. The intended 8 ms delay was based on a disagreeing libc timestamp. Our timing layer bypasses the libc/vDSO fast path for scheduling, calculates a relative remaining duration, and recomputes after interruption. Launcher/game/state loading then worked on-device. This proves the discrepancy and a working userspace repair; the exact kernel/vDSO clocksource defect has not been recovered. Other firmware users of libc clocks need their own validation.

## Display and scaler

Normal heap RGB565 data passed to the vendor scaler produced corruption in earlier tests. Owned chunk-memory buffers, compact pitch and completion-aware reuse fixed it. An apparently clean pause-menu preview was not proof live frame ownership was correct.

Driver DWARF exposes `vfb.c` and `driver.c`, 37 recovered types and 32 functions. It identifies an SDK GCC 9.3 Cortex-A7/NEON/VFPv4 hard-float build. `gpPScalerPara_s` is 228 bytes; queue-related fields exist, but do not establish a usable continuous queue contract.

`PScaleRun` performs open/configure/start/status/stop/close per job. Its recovered not-done fallback sleeps ten times for 1ms without rechecking status; avoidable delay is a concrete lead, not the proven cause of a returned spike. The real asynchronous `ScaleDisplayThread` is already in driver.so. A same-named vrtemu function is a stub. Stock releases its source/pending flag after DrawVFB and before FlipVFB; MVP1.5 releases only after both. Separating source completion from scanout and using an ordered bounded queue is proposed. A persistent fd or A/B hardware queue is not yet an implemented or proven speed improvement.

Compact `width*2` RGB565 pitch avoids a known row repack. Direct core drawing into uncached chunk memory may lose CPU efficiency; removing a copy is not automatically faster. Scaler/PPU IRQ counts are not panel refresh measurements.

## Audio and SNES frame budget

Tested Plus reports 32,040 Hz native audio and 59.922743404 FPS. The host uses 44,100 Hz stereo S16_LE. Keep fractional resampling continuous across callbacks. A fixed 735-sample/44.1-kHz policy is not the core's native timing contract.

Stock `sound_driver_playframe` has **void** return type in DWARF. A tailcalled write register is not a supported integer-return API. Our runtime owns nonblocking OSS writes and preserves all unaccepted frames across partial/EAGAIN writes. Concatenated PCM sounding clean on a PC does not preserve wall-clock submission gaps or prove absence of device underruns.

FF6 map scenes clicked even with the same music that was clean in the party menu. Speakers/headphones/ground-loop-isolator tests did not identify an analog-only issue. ROM/APU comparisons and write audits did not establish corruption or simple lost partial writes as the cause.

v9 normal core calls averaged 19.958 ms wall time versus 6.752 ms with internal rendering disabled. The native frame budget is about 16.688 ms. These are callback/preemption-inclusive wall measurements, not isolated PPU CPU attribution. v10's mixed listening test held about 5.012% of drawings and sounded clean; that percentage is not a 5% CPU deficit. Expensive scenes are disproportionate. v11/MVP through1.5 retain adaptive internal drawing suppression while keeping emulation/audio running.

The MVP 1.4 returned session ran 2,465 steps with 749 held drawings, 1,716 video submissions, two pauses and no write errors. It demonstrates function; it is not a controlled speed comparison.

MVP1.5 physically confirms all four directions, game start and imported state
loading. The [returned report](../evidence/2026-10-04/snes-mvp-1.5/last-session.txt)
contains 23,872 calls, 2,826 held drawings (11.838%) and 21,046 video submissions.
Mean core-call wall14.591ms/CPU13.230ms includes callbacks and held calls;
p95[19,20)ms, p99[21,22)ms, maximum40.844ms. Video callbacks averaged1.893ms per
submission and reached19.713ms. Zero write errors; software-ring peak2795/8192;
sampled device queue1024–2048 frames. Brief starvation and physical frame
presentation remain uncounted. The user heard occasional lag and rare random
normal-play crackles in story/map. No assigned cause or full-render speed claim.

Plus currently publishes video before completed audio, so a slow video callback
also delays PCM delivery. The host polls GPIO twice per core call. The pinned
tile/color implementation is predominantly scalar even though compiler flags
permit NEON; some DSP paths already contain compiler-generated SIMD. A tailored
renderer and corrected host ownership are proposed in the
[full-speed plan](full-speed-snes-plan.md), with exact output retained.

[MVP1.6](snes-mvp-1.6.md) implements A7 ordinary2/4bpp tile/color kernels,
audio-first independent delivery, three-source ordered display queuing and
full rendering without adaptive holds. Local exact pixel/native-PCM comparisons
pass1200 frames, including the latest private snapshot; independent scalar color
checks and actual FIFO/transport seams pass. It is installed/armed with stock,
hook and original progress preserved. Its physical run failed: very choppy
sound, slow movement, clean-looking graphics and whole-device power-off. The
returned one-shot is consumed; startup and early thread snapshots survive, but
the final report is stale 1.5 data. Early process RSS is about 12 MiB with zero
swap; neither OOM, watchdog expiry nor a particular shutdown cause is proven.
See the [failure review](snes-mvp-1.6-failure.md). Do not re-arm it unchanged.
Mode7/clipped/backdrop paths, persistent scaler and audio-cursor timing remain
unchanged/unqualified as documented; no speedup is inferred from QEMU.

## UART investigation and its negative result

The kernel identifies `c0070000.uart`, ttyS0, IRQ19 (GIC hwirq69), primary console. Runtime v2 saw about 6,968 IRQ/s and 85.61 reported TX bytes/s. v3 redirected both host/supervisor stdout/stderr to `/dev/null`, but still saw about 6,953 IRQ/s, similar comparable high-load CPU phases, and unchanged perceived behavior.

This rules down ordinary stdout/stderr redirection as a useful performance fix for that test. FD10/FD11 remained `/dev/console`; kernel/polling console writes and the actual interrupt source/cost remain unresolved. Interrupt count times a guessed handler duration is not measured CPU cost.

`ignore_loglevel=N`, printk `7 4 1 7`. Level-7 scaler clock messages remain in the ring. About 239–240 messages/s, often grouped in six, do not prove messages-per-frame or panel cadence. The analyzer's old regex confused source-line `[247]` with a timestamp; corrected analysis anchors timestamps at line start.

## Access and remaining unknowns

Readable kallsyms supplied real addresses. Built-in-module entries are not exported loadable `.ko` files. `/proc/mtd` had no registered partitions; `/proc/kcore` returned ENOENT. No kernel-text recovery, flash rewrite, MMIO experiment or `/dev/mem` fallback was performed.

Open questions include actual clocks/cache/DRAM behavior, scaler lifecycle cost and completion identity, supported audio periods/positions, physical panel cadence, IRQ19 handler duration/source, battery/suspend behavior, and sustained per-game performance. Tracefs availability was proposed for IRQ pricing, not established by the collected returns.
