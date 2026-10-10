# Device findings

Evidence collected on one DIIUM D-R35 through 2026-10-10. **Observed** means returned device data or exact binary/source evidence. **Inferred** means supported but not a direct census or measurement. Unknowns remain explicit. Evidence filenames and hashes are indexed in [the evidence manifest](../evidence/manifest.json). Dated entries below preserve earlier investigation states; the latest result supersedes their pending statuses.

**Current boot/storage state:** [both Vesper screens are installed and verified](vesper-static-firmware-update.md): the user accepts Vesper static -> Vesper animation -> stock launcher, and two complete 8 MiB reads match expected SHA256 `509cdc305deca2654fbf48184eb16d523b4b6cae0effffc4a3cba6845622d9fd` byte for byte. Original normal SD init restored; stock/progress and prior reader profiles unchanged, FAT clean. [Focus1 has returned](snes-focus-1-return.md); only the cost1 measurement one-shot is now armed; Code.bkp is absent. External write recovery unqualified; audio unresolved.

**Current SNES result:** [Focus1 returned with the Bio Blast audio failure](snes-focus-1-return.md).
The unchanged1.19 core accepts38,480.644 frames/sec against44,100Hz near failure.
Six phase samples show PPU CPU5.741 ->8.904ms while APU-inclusive stays4.529..4.898ms.
Late ordinary calls average17.991ms wall /16.725ms CPU plus0.211ms admission.
Emulated358,416 master clocks/call predict534.688 native /735.948 sink frames;
actual native average534.650 is consistent with that quota. Complete effect
onset/recovery and candidate A7 unit costs remain unmeasured. The window patch
fails the five-condition prediction gate.60 runtime/progress and49 lab files,
all58 prior files and12 unchanged progress files verify; FAT clean, no card
writes or rearm. B/display teardown/wrapper copies complete. The unexplained
three128-frame pointer increments and SETUP/EBADFD mechanism remain unresolved.

**Current cause map:** [ROM reconstruction and window experiment](ff6-bio-blast-cause-map.md)
byte-match the entire owner ROM and expose103,538 native instruction addresses
in private C.178 wave copy-kernel executions match the semantic model. In replay
frame320, scroll writes trigger zero pending-render flushes; circular window
edges trigger123. A separate per-row BG1 window patch passes an independent
524,288-state clip oracle and3,600 frame comparisons, including full Bio Blast.
Effect PPU update entries fall78.97% while color-row materializations rise34.58%.
This narrows a code-level inefficiency, not the exact vendor audio failure.
Candidate remains private/instrumented and uninstalled; no A7 speed or audio
acceptance inferred from work counts.

**Current measurement:** [cost1 suite](snes-a7-cost-suite.md) is staged after a fresh60-file/49-lab archive,141 protected hash checks and clean FAT. A separate baseline diagnostic measures setup, color payload, window helpers, frequency and complete PCM history in aligned replay. Sparse row sampling and a dense cross-check expose observer costs; no QEMU timings or work-count reduction become A7 evidence. Original production core/adapter/progress remain exact. Physical unit costs and candidate longer-span/cache coverage remain pending.

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
| Sound | `/dev/dsp` (14:3), `/dev/snd/pcmC0D0p` (116:16), controlC0 and ALSA timer nodes | 1.10 starts 44100Hz/128-period/3712-buffer PCM in two attempts, then WRITEI fails; sustained native continuity unqualified; `/proc/asound` absent |
| GPU | `vivante,gc` DT node exists | No working galcore/runtime/device established |

One CPU means display/I/O threads can overlap peripheral waits, but cannot add emulation compute capacity. The vendor runtime's gameplay memory headroom was tight. Configured 256 MiB swap is not physical RAM; sampled vrtemu VmSwap was zero and swap use was stable, so ongoing swap thrash was not demonstrated.

The [1.15 return](snes-mvp-1.15-return.md) measures ordinary main-thread CPU
about18ms and wall19.3–19.5ms in the restored scene, before loop/platform work.
Sampled inclusive PPU cost is about10ms; admission waits about0.18ms. Snapshot
loads succeed, then production falls behind. First-launch detailed history is
lost across retries, so its specific cause remains unknown.

Exact local replay finds214 pending fixed-color `$2132` flushes per frame with
no effective color change. The [1.16 repair](snes-mvp-1.16.md) reduces PPU update
jobs217–223 to4–10 while preserving tile rows and exact output. This is a work
census and correctness result. Its physical return now establishes one sustained
near60-call/sec session; cold-start reliability and effect fidelity remain pending.

cpufreq, thermal/cache inventory and clock summary were absent in tested locations. Software perf task-clock worked; hardware cycles/instructions/branch/L1/L2 counters returned ENOENT and no PMU DT node was established. Cache sizes from a related chip specification must not be promoted to this device's measured properties.

## Runtime and storage

The October9 [read-only FAT re-verification](fat-verification-2026-10-09.md)
corroborates the latest return's damage: CHKDSK repeats invalid backup clusters
and lost chains, while independent reads fail with Windows1392 on the same
entries. Ben subsequently approved [repair/recovery](fat-recovery-2026-10-09.md):
healthy checks now pass,14 chains survive privately and the actual1.18 fault
records are recovered. All412 readable files survived repair; verified pre-test
SRAM replaces the empty current file. Neither audio causality nor defective flash
hardware is established. At that recovery boundary splash was not installed
and both tests were unarmed; current boot and test state is recorded above.

The2026-10-05 [lab2 contract review](platform-lab2.md) identifies the exact
scaler/flip command values and argument shapes. In particular,0x80045004 gets
scalar3000, not a pointer justified by ioctl direction bits. Status is a bitmask;
FRAME_DONE=2, A_DONE=4 and B_DONE=8 are recovered names, not a qualified hardware
queue. The [lab2 return](platform-lab-2-return.md) records actual configuration/
output addresses, status, readiness and per-call timing. All 973 successful
statuses are 6; the ten-sleep fallback never runs in this workload.

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

Lab2 separately establishes coarse **wake timing**: 1/2/5ms requests through
libc nanosleep, direct kernel clock_nanosleep, timeout-only poll and timerfd have
cell means 9.844–10.003ms, idle/loaded and with 50us/1ns slack. Kernel getres and
timer-list bases report 10ms. Direct syscalls/timerfd/slack reduction do not repair
these short waits. Audio readiness wakes around 2.77ms in one transport; use
device progress events for refill/admission. Exact CONFIG_HZ/HIGH_RES_TIMERS are
unknown; fine timestamp hardware does not establish high-resolution user waits.

## Display and scaler

Normal heap RGB565 data passed to the vendor scaler produced corruption in earlier tests. Owned chunk-memory buffers, compact pitch and completion-aware reuse fixed it. An apparently clean pause-menu preview was not proof live frame ownership was correct.

Driver DWARF exposes `vfb.c` and `driver.c`, 37 recovered types and 32 functions. It identifies an SDK GCC 9.3 Cortex-A7/NEON/VFPv4 hard-float build. `gpPScalerPara_s` is 228 bytes; queue-related fields exist, but do not establish a usable continuous queue contract.

`PScaleRun` performs open/configure/start/status/stop/close per job. Its recovered not-done fallback sleeps ten times for 1ms without rechecking status; avoidable delay is a concrete lead, not the proven cause of a returned spike. The real asynchronous `ScaleDisplayThread` is already in driver.so. A same-named vrtemu function is a stub. Stock releases its source/pending flag after DrawVFB and before FlipVFB; MVP1.5 releases only after both. Separating source completion from scanout and using an ordered bounded queue is proposed. A persistent fd or A/B hardware queue is not yet an implemented or proven speed improvement.

Compact `width*2` RGB565 pitch avoids a known row repack. Direct core drawing into uncached chunk memory may lose CPU efficiency; removing a copy is not automatically faster. Scaler/PPU IRQ counts are not panel refresh measurements.

Lab2's 960 matched 256×224 scaler jobs average 2.261–2.287ms open-through-close,
including 1.874–1.891ms in the scalar3000 wait and 0.361–0.372ms in other syscall
brackets. All statuses include FRAME_DONE. Display wait averages 10.46–11.82ms,
including native notice jobs; the worker overlaps production, so these are not
additive core CPU costs. Output-A alternates two addresses; output-B and queue/
drop flags stay zero. Continuous A/B operation and panel cadence remain unknown.

## Audio and SNES frame budget

Tested Plus reports 32,040 Hz native audio and 59.922743404 FPS. Stock and MVP
through1.8 use 44,100 Hz stereo S16_LE.1.9 prefers negotiated native32040Hz and
bypasses conversion when accepted; other accepted rates retain continuous
fractional resampling. A fixed735-sample/44.1-kHz policy is not the core's timing
contract. Native settings remain physically unqualified.

Stock `sound_driver_playframe` has **void** return type in DWARF. A tailcalled write register is not a supported integer-return API. Our runtime owns nonblocking OSS writes and preserves all unaccepted frames across partial/EAGAIN writes. Concatenated PCM sounding clean on a PC does not preserve wall-clock submission gaps or prove absence of device underruns.

Upstream Linux 4.19 OSS source already describes accepted partial-fragment
staging outside GETODELAY. POST starts without flushing that tail; SYNC flushes/
drains and RESET discards. Lab2 accepts every target byte but still has accounting
residue at zero-delay shutdown, so its fade/drain cannot qualify silent endings.
The user also hears clicks during tests. Native ALSA supplies a documented
alternative with explicit parameters, priming, readiness and stream state;
matching vendor behavior remains to be qualified. See [interface research](platform-interface-research.md).

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

The original Plus publishes video before completed audio, so a slow video callback
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

Stock boot was subsequently confirmed by the user. The authorized
[MVP1.7 logging retry](snes-mvp-1.7.md) was installed and armed with the exact
same core and pipeline. It adds fresh session/phase progress and bounded
persisted thread/kernel/memory/helper data plus instrumentation-duration
accounting. The [physical return](snes-mvp-1.7-return.md) reaches a Save Point
and normal save/exit without a crash, but remains laggy; FF6's party menu helps
partially. Fresh 7,068 calls have zero holds and roughly54.63 calls/sec active
loop throughput, mean core wall15.384ms/CPU13.986ms, p95[21,22)ms and
31.08% definitely over budget. PCM accounting is complete, while sampled empty
device queue and71.280ms write gap leave starvation risk. Stock/new private
progress are preserved, card unarmed. Missing head prevented system CPU/memory/
IRQ collection; the attempted sed replacement also fails on firmware, as the
1.8 return later establishes. Current source uses shell builtins and tests
with both commands absent. Display
worker waits overlap producer work and do not establish a scaler-only deficit.

## Forward A7 renderer build

[MVP1.8](snes-mvp-1.8.md) is the forward A7 build requested after that return.
Source/disassembly establish specialized tile modes, deinterleaved palettes and
vector backdrop/window spans. Exact pixels/PCM/state and clipping checks pass;
device speedup is not established. A reversed backdrop interval caught by the
real intro must be clamped before unsigned vector counts. Gameplay shell work
is reduced to one platform capture plus small30-second checkpoints without
global sync. Continue uses the new preserved Save Point SRAM; the separately
migrated snapshot remains older progress. The1.6 shutdown cause remains open.

The [1.8 return](snes-mvp-1.8-return.md) records clicking and confirmed whole-device
power-off. A fresh previous checkpoint has1,648 calls, zero holds and about
57.93 calls/sec of active-loop time, mean core wall13.33ms and audio-lead wait
3.00ms/call. PCM accounting balances, but a sampled empty device queue and40.004ms
maximum accepted-write gap leave starvation risk. Latest checkpoint/tails are
empty and the final report is stale1.7; neither crash time nor shutdown cause
is established. All19 existing private files and stock/hook hashes are intact;
card unarmed. Firmware lacks sed as well as head. Source capture is repaired
but not installed. The exact returned core passes10,000 output-equivalence
frames; this does not prove physical speed or system stability. Next work is
bounded audio-headroom production and durable targeted crash records.

## UART investigation and its negative result

The kernel identifies `c0070000.uart`, ttyS0, IRQ19 (GIC hwirq69), primary console. Runtime v2 saw about 6,968 IRQ/s and 85.61 reported TX bytes/s. v3 redirected both host/supervisor stdout/stderr to `/dev/null`, but still saw about 6,953 IRQ/s, similar comparable high-load CPU phases, and unchanged perceived behavior.

This rules down ordinary stdout/stderr redirection as a useful performance fix for that test. FD10/FD11 remained `/dev/console`; kernel/polling console writes and the actual interrupt source/cost remain unresolved. Interrupt count times a guessed handler duration is not measured CPU cost.

`ignore_loglevel=N`, printk `7 4 1 7`. Level-7 scaler clock messages remain in the ring. About 239–240 messages/s, often grouped in six, do not prove messages-per-frame or panel cadence. The analyzer's old regex confused source-line `[247]` with a timestamp; corrected analysis anchors timestamps at line start.

## Access and remaining unknowns

[Hardware lab1 returned](platform-lab-1-return.md) with normal stock handoff,
240/240 completions per display phase and buffered sound under12ms CPU load.
NEON beats its scalar tile fixture; this color cache loses.5ms deadline lateness
averages5.48ms. Negative GETOSPACE and non-mmap OSS staging require care before
using counters as a clock. Lab2 resolves the short-wait/slack question above.
Both short synthetic runs prove neither full-game speed nor a shutdown fix.
Lab2's four controllers complete 240/240 drawings each, but occasional 28ms CPU
bursts overrun nominal queue lead. A 23.22ms queue at 44100Hz cannot bridge a
roughly 30ms production blackout. One coherent PCM owner, a playable reserve
and earlier correctly synchronized audio publication are the next source-based
runtime work. Card unarmed; no new game build installed.

[MVP1.9](snes-mvp-1.9.md) now implements the researched native PCM path and one
coherent production owner. Explicit64ms priming, device/event admission, bounded
drain/faults and native-rate bypass replace split OSS/timer gates. Already-mixed
PCM publishes at existing in-frame APU synchronization points;1200 exact-output
frames pass,1196 with multiple earlier batches. Independent ARM32 and actual
owner fixtures qualify software contracts, not vendor settings or handheld
speed. The1.9 return accepts44100Hz/128-period/3712-buffer and2823 priming
frames, then EBADFD before emulation. No performance inference follows. The
reported PREPARED state is a prewrite sample; exact failure operation/state is
missing.1.10 fixes state-aware startup and retains precise failure diagnostics.
Its independent ARM fixtures cover automatic and explicit START, invalid
states and parameter mismatch. Native audible playback/consumption and
full-render/stability acceptance remain pending. See [return](snes-mvp-1.9-return.md)
and [repair](snes-mvp-1.10.md). The
[capability roadmap](hardware-capability-roadmap.md) keeps wider opportunities
in view; no current evidence establishes maximum attainable performance.

Readable kallsyms supplied real addresses. Built-in-module entries are not exported loadable `.ko` files. `/proc/mtd` had no registered partitions; `/proc/kcore` returned ENOENT. No kernel-text recovery, flash rewrite, MMIO experiment or `/dev/mem` fallback was performed.

Open questions include actual clocks/cache/DRAM behavior, scaler completion/release identity, native PCM consumption/positions and alternate configurations, physical panel cadence, IRQ19 handler duration/source, battery/suspend behavior, and sustained per-game performance. Lab2's two probed tracefs paths, clk_summary and proc/config.gz return ENOENT; no IRQ duration was measured. Source research should establish standard contracts before physical tests qualify remaining vendor behavior and real game timing.

## Native PCM 1.10 return and 1.11 software correction

Both 1.10 attempts start playback with 44100Hz/128-period/3712-buffer, then WRITEI
returns EBADFD after 72/605 calls. Software high 2823/8192 and 705 remaining frames
rule out the UI's literal queue-overflow diagnosis. The second short interval
has 59.70 active-loop calls/sec, 10.61ms mean core wall, 9.93ms main-thread CPU,
one pause and re-priming. No intentional holds occur; audio failure prevents
the final video callback. This does not qualify sustained full rendering/sound.
Sampled playable minimum 134 frames is only 3.04ms, not the 64ms initial reserve.

Cached admission is reproduced in shipped source. 1.11 waits for a new worker
observation, reads post-HWSYNC state/pointers using preserved GET controls,
restores drain readiness and reports worker errors accurately. Independent
ARM and real-core consuming-native retry/snapshot/resume fixtures pass. Vendor
state transition and long-game audio/stability remain unproved. Nineteen prior
progress files/snapshots match; updated FF6 SRAM is archived. dmesg is absent,
and stock return follows a recorded B exit/cleanup, with no new poweroff
record. See [return](snes-mvp-1.10-return.md) and [repair](snes-mvp-1.11.md).

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

## 1.13 return changes the working failure model

[1.13](snes-mvp-1.13-return.md) preserves the fault history and kernel READ_ALL.
It fails after 26/230 calls; the second attempt loads/resumes a snapshot. The
retained phase produces about 37k accepted frames/sec against negotiated44.1k,
then application pointer diverges by three128-frame increments and SETUP.
Reserve erosion precedes that divergence: starvation is the leading trigger,
but the exact vendor response and audio contents during it remain unknown.
Display reservation is only1.066ms over230 calls. All20 private progress files
and stock/hook/core hashes match. Card unarmed, zero writes or new build.

The [execution-budget review](execution-budget-review.md) supersedes a sequence
of further small diagnostic retries: attribute the expensive phase, qualify a
whole-program A7 build and optimize the actual core/frontend work. More initial
silence or automatic restart cannot repair sustained underproduction. Existing
fixtures establish lifecycle/correctness, not the device's repeated slow phase.

## 1.16 sustained gameplay and1.17 diagnostic isolation

The [1.16 return](snes-mvp-1.16-return.md) records31,601 core calls/video
submissions over526.812 active seconds (59.985 calls/sec), zero holds/duplicates
and audio-write errors, one snapshot load and clean save/exit. User reports
combat/menu/playability substantially improved. All generated PCM is accounted
for; this is not panel scanout or effect-fidelity evidence. Two changed SRAM
files are archived;19 prior game-progress files and all original snapshots match.

The retained first70-call failure has roughly9ms main CPU but18–39ms wall
stalls, overlapping wrapper discovery/card copies at11.27–11.57s uptime. This
is a strong observer-workload hypothesis, not confirmed causality or the old
sustained18ms CPU deficit. [1.17](snes-mvp-1.17.md) removes routine diagnostics
from child lifetime, preserving durable faults and the exact1.16 core.
Installed/read back13:21 UTC, all26 private/49 lab files preserved and armed.

Both wind and blowing snow are reported missing in opening outdoor Narshe.
12,000 local frames match clean-core pixels/PCM/state; a private no-input capture
shows the outdoor mine entrance without visible blowing snow in inspected
frames. Baseline accuracy, expected effect/phase and audible wind remain
unresolved. No speculative weather/DSP change ships.

## 1.17 first launch and Magitek effect deficit;1.18 derived-color reuse

First FF6 attempt succeeded.35,763 calls average59.978/sec active, zero holds or
duplicates; snapshot load works. Terra Magitek Bio Blast (not Edgar Tools) leads
to audio error/our library. Final ordinary wall17.981ms/CPU16.638ms and sampled
inclusive PPU8.150ms identify transient effect cost; PCM production falls to
about40,066 frames/sec before reserve erosion and128-frame pointer steps.
Fresh native reports outrank stale1.16 wrapper run/backup logs. No new power-off
or core segfault established. Snow expectation was withdrawn by the user.

1.18 uses a bounded36KiB pre-math RGB tile cache with actual decode/CGRAM/
brightness/load invalidation. Complete Magitek replay equals clean output;
93.36% tile reuse and48.71% fewer lookup rows are work counts, not measured A7
speed. The earlier Lab1 cache lost; its result remains applicable evidence that
cache overhead/memory can exceed savings. [Details](snes-mvp-1.18.md),
[returned evidence](snes-mvp-1.17-return.md).

## 1.18 return: audio exit and FAT evidence loss

Magitek Bio Blast again returns to the library with a user-reported audio
descriptor error. Exact1.18 payloads verify; the candidate has not fixed that
failure. Two FAT backup entries are unreadable, and fresh fault/session files
plus current SRAM are zero bytes. A read-only check confirms invalid allocation
units and lost chains. Full readable card contents are privately hash-backed
up; snapshots and earlier SRAM survive. Repair/recovery consent is pending;
no card updates or re-arm. Stale1.16 stderr cannot price1.18 cache speed or the
latest stop. Filesystem damage is established; its cause and relationship to
audio remain unknown. [Return](snes-mvp-1.18-return.md).

Requested [Vesper boot art](vesper-boot.md) is qualified through original ARM
ZIP/sprite routines; stock code/handoff stays exact. Its guarded installation
waits for a healthy filesystem. No new core or audio policy ships from this
incomplete return.

## Physical boot return: Vesper unchanged — 2026-10-09

Ben saw unchanged solid boot and stock animation, then stock launcher. Returned
patched showlogo still has SHA ab56a67ae629e816a5752b1ad7cec2c335b46c82df84856f8a41376d2f919ebe.
FAT is healthy; strict archive snes-mvp-return-20261009T160157Z preserves51 MVP
and49 lab files. SD init does not launch showlogo. Actual early-boot owner is
unverified; offline sprite qualification did not establish executable ownership.
A passive consumed-once probe captures startup scripts, mountinfo and any active
showlogo executable privately. It never launches a splash, signals processes,
controls display or writes firmware. Offline capture fixture and archived device
BusyBox syntax checks pass. SNES/lab remain unarmed; audio remains unresolved.
On next return archive retro/vesper-boot-probe/results first, then restore exact
init.before-probe from the installation receipt. Physical acceptance has failed.

## Actual animation owner captured — 2026-10-09

Second physical test remains stock. Passive capture proves PID447 executes
`/showlogo` from internal root: captured198408-byte executable SHA
436d8018808b150c926274575a195f664e61db646f44713371019e9ae10caf3b
matches stock, not patched SD copy. Source-script capture failed because firmware
PATH lacks tr. Correct filename mapping uses shell case only; capture fixture
passes. Strict51-MVP/49-lab archive and all probe files preserved privately in
`device-evidence/snes-mvp-return-20261009T161740Z`; original init restored exactly
before corrected capture installation. No firmware mutation or audio changes.
Next capture must recover init.rc/init.project.rc and mountinfo to identify a
reversible startup seam. Internal solid-logo owner remains unproven.

## Captured boot route and SD-stage animation test — 2026-10-09

Corrected capture succeeds: init.project.rc launches /showlogo before sleep2,
mounts card /retro at /usr/retro, then launches SD init. Internal rootfs is RAM
rootfs; no firmware replacement is attempted. Captured stock owner and boot
scripts are archived privately in snes-mvp-return-20261009T162604Z. Diagnostic
init was restored exactly. New one-shot launch-vesper-boot.sh signals stock via
/tmp/vrtemu.log, waits for all non-zombie showlogo owners to exit, removes only
the RAM stop marker, launches qualified SD showlogo for3 seconds, signals it,
then waits/reaps its owned child before stock launcher. A release timeout refuses
replacement; an owned-child stall waits rather than starting a competing display.
Device BusyBox syntax and independent dummy-executable one-shot/reap/no-op checks
pass; physical display remains pending. Early solid firmware logo remains stock.
Installer checks healthy FAT, exact init/splash, archives progress and arms last.
No SNES/lab arming or audio change. This is a userspace animation handoff test,
not replacement of the earlier internal boot interval.

## Physical success is an added SD-stage animation — 2026-10-09

Ben observed: static D-R35, animated D-R35, then Vesper. Vesper is physically
accepted as an added SD-stage animation, not a replacement of either stock screen.
Returned startup log reports stock_released=1, owned child484 exit0 and reaped
before launcher. Strict51-MVP/49-lab archive plus complete animation files are
preserved in device-evidence/snes-mvp-return-20261009T163638Z. Marker consumed;
no rearming. The next boot follows stock. Audio remains unresolved.

Captured /init.project.rc starts internal /showlogo before sleep2 and SD init.
The internal executable matches the qualified stock ZIP owner. Replacing that
original animation requires an earlier boot hook or modifying the embedded root
filesystem image; SD init alone cannot change already displayed frames. Rootfs
is RAM-backed at runtime; editing its live copy would not establish persistence.
The static screen asset/owner remains unknown: bootloader or kernel is a hypothesis.
Prior investigation found no registered /proc/mtd partitions. No verified firmware
image/repack/flashing/recovery route is established. Do not flash or claim both
screens can be replaced yet. Next engineering scope is read-only firmware/boot
image inventory and recovery-method verification, not another SD display test.

## Persistent second-splash replacement requested — 2026-10-09

Ben explicitly authorizes discarding/replacing the original second animation.
Preserving its appearance is not a requirement. Current obstacle is persistent
boot-image access: kernel cmdline rootfstype=ramfs; internal init starts /showlogo
before SD init; no registered MTD partitions or verified flash updater/image or
recovery route established. Online D-R35 Plus card-restoration reports do not
establish internal firmware flashing for this unit. No raw-device or flash writes.
Original SD init restored after archived successful animation test. A passive
firmware-route probe inventories proc partitions/mtd/cmdline and device/tool
names, and captures sysinit/BusyBox privately for offline updater inspection.
Device BusyBox syntax passes. It does not open raw devices or touch displays.
Next return: archive probe results, restore exact init, inspect storage/update
owner before deciding whether persistent replacement is achievable.

## Firmware route return and USB dispatch correction — 2026-10-09

Complete passive capture archived privately in snes-mvp-return-20261009T165057Z
with strict51-MVP/49-lab progress preservation. Original init restored exactly;
no test armed. Only SD and RAM block devices; empty /proc/mtd and sys/class/mtd.
Vendor /bin/nand_part_info and /bin/nandsync exist; /dev/spidev0.0 exists but
its attached peripheral is unidentified. This does not establish flash access.

Offline exact sysinit disassembly: main at0x11540 dispatches only argument core;
other arguments, including usb_gadget, are ignored. sysInit at0x1151c initializes
PPU/DLA/audio/ADC only. Unreached usb_gadget_init at0x11260 loads usb-common only.
The script command /sysinit usb_gadget is therefore not evidence of active USB
gadget support; earlier suggestion overstated it. No button recovery sequence
found in this dispatch. This does not rule out boot-ROM/bootloader recovery.
Next work: inspect vendor NAND tools and identify SPI peripheral/boot storage
without raw writes; a persistent splash replacement remains unimplemented.

## Reusable passive device survey and test catalog — 2026-10-09

Build native Cortex-A7 inventory collector, exact firmware BusyBox one-shot
wrapper, guarded install/rearm/collect/restore commands, SHA-mapped analyzer and
private offline ELF review. Prioritize NAND helpers/module candidates, SPI/USB
identity and device tree; also capture platform/process/memory/power/input/audio
metadata and runtime/module inventories. Bound reads, bytes/jobs and scheduling;
explicitly retain errors, missing paths, truncation, caps and stale-run rejection.
16 independent native/ARM/timeout/sparse-shell/analyzer checks pass; physical
capture pending. Archive progress and restore exact init before repeats. No raw
hardware reads, vendor utility execution, flash writes or active lab rearming.
Catalog19 investigation questions and reuse existing active labs with their
ownership/contracts. NAND tools already preserved privately contain driver-load
and storage-operation code; inspect copies before invoking anything on-device.
[Suite coverage and next run](docs/device-survey.md).

## Survey1 storage failure and exact updater recovery - 2026-10-09

Survey1 returned329 of901 captures.521 missing nonempty captures occupy exactly
17,856 KB at32 KiB allocation granularity, matching521 recovered chains. All789
readable files survive approved repair; saves/runtime/lab hashes match baseline.
Old ROM deletion preceded the clean install check. Directory-growth/persistence
is plausible; exact media/driver/shutdown cause remains unproved. Survey2 uses
one indexed CRC32 bundle/report and a fresh-health restoration gate.21 software
checks pass; healthy-card rearm completed, physical return pending.

SPI0.0 DT node names NOR flash; UDC/gadget paths absent despite an enabled USB
controller declaration. Exact vrtemu main calls the Code.bkp updater; WQW/ZIP/CRC
checks precede flash programming. SPI_ROM.bin is a string, not a proven trigger.
No raw SPI transaction or recovery path qualified. See device-survey-1-return.md
and firmware-update-contract.md for evidence and next test.

## Survey2 intact return and SPI owner — 2026-10-09

All905 indexed captures verify on return:1,989 jobs,4,046,126 bytes, no failed or
truncated reads/caps, matching consumed run identity and wrapper exit0. Returned
FAT is clean;51 MVP/progress and49 lab files are preserved. Exact init was
restored after a fresh health check. This is one successful physical storage
return, not general media/driver/shutdown qualification.

The census finds stock vrtemu PID521, executable `/usr/retro/vrtemu`, FD8 owning
`/dev/spidev0.0`, character major153/minor0. The separately armed ID probe runs
synchronously before stock main, refuses another owner and sends only05/9f.
Eleven software checks pass; physical SPI identification remains pending. No
flash/configuration writes, full dump, recovery, original-splash replacement or
audio fix is qualified. See [return](device-survey-2-return.md) and
[probe](spi-identify.md).

## Physical SPI ID and pending full readback — 2026-10-09

Three physical responses are c84017c84017, with status00 before/after, five
successful messages, no competing owner or timeout and matching consumed marker.
SPI mode1024/eight bits/default20MHz is reported; single-lane at most1MHz succeeds
without global changes. Manufacturer/kernel references match the identifying
triplet C8 40 17 to GigaDevice64-Mbit NOR/nominal8MiB. Exact revision/package
and readable firmware layout remain unverified. FAT is clean and private progress
is preserved; exact init restored after fresh health check.

A separately armed two-pass reader keeps the working1MHz fields, uses fixed
03/24-bit/4KiB reads over the nominal range and compares both copies byte-for-byte.
Nine software checks and protected install/health readback pass. Physical full
readback is pending. No flash/configuration write, recovery, original splash
replacement or audio fix qualified. [ID return](spi-identify-return.md),
[readback procedure](spi-readback.md).
