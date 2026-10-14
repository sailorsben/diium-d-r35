# Quick A7 CPU breakdown: 1.19-profile1

User authorized a quick benchmark and staging on I:. Four epochs use the exact
returned combined1 core, SHA256
`e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129`.
No renderer algorithm changes or performance-candidate promotion. Both core
filenames contain identical bytes; state payloads and identity headers reuse
the matching combined1 snapshots unchanged.

Predicted renderer saving is zero: this test measures the current bottleneck.
Additional profiling cost is unmeasured and can worsen an already failing
interval. No new headroom or audio-deficit closure is claimed before return.

Meteor runs control then profiled; Quasar runs profiled then control. Each caps
at 800 calls (~13.35 emulated seconds), covering the previously observed late
peaks and failures around calls 392-549 if native audio permits reaching them.
Four complete epochs total ~53.4 emulated seconds plus startup/cleanup. Allow
two minutes. A native error ends its epoch normally, preserves fault evidence,
joins workers and continues. MENU stops the suite. No manual B input.

## Measurements and limits

The owned runner enables the core's existing `d35_profile_begin/end` ABI only
on zero-based call indices congruent to 3 modulo 8 in profile epochs. Controls
disable both phase hooks and callback CPU clocks. All calls retain ordinary
whole-call, worker and PCM observers. Profiling adds no emulated-time control,
frame omission or audio suppression. There are no clocks inside pixel loops.

`phases.csv` retains every call in RAM: whole-call CPU/wall time, sampled PPU
CPU, APU-inclusive CPU, audio/video callback CPU and callback counts. Clocks
use the kernel syscall `CLOCK_THREAD_CPUTIME_ID`. Existing `frames.csv` keeps
main-step and audio/display worker CPU, frequency observations, pacing, PCM
pointers and observer cost. Both workers remain live. Files flush after audio
join and display idle, using the qualified wrapper with no live background
SD diagnostic monitor. Ordinary RAM progress and native fault traces remain.

The startup 129-read CPU clock loop estimate is reported, not subtracted.
Observer overhead remains inside all results. Aligned profile-minus-control
CPU distributions show measurement disturbance plus run noise; one pair does
not identify exact observer cost. Compare sampled and unsampled populations.
The profile build retains a few control-path checks and RAM record stores,
so this control is comparable within the test, not a zero-overhead original.

PPU time spans `S9xUpdateScreen`, including setup, tiles, windows and finishing
work. APU time spans `S9xAPUExecute`, including its audio callback. Audio
callback time must not be added again to APU-inclusive CPU. Video submission
CPU is separately measured; its nesting must be checked before any subtraction.
Core-call time includes the ability observer. The residual after PPU/APU is
SNES CPU, port-driven SPC work, dispatch and observer cost; it cannot simply be
called SNES CPU time. This first split does not price individual scalar/NEON
kernels or solve the still-missing inward PPU attribution.

Frequency inspection/pinning uses the existing guarded sysfs procedure and
restores the original minimum after each run. Missing frequency is `-1`, never
assumed to be 666 MHz. First 120 calls are retained but excluded from warm
distributions; cache steady state is not proven by a warmup count alone.

## Falsifiable result

Returned evidence will split the observed ~16.41-16.48 ms Meteor core-call cost
into PPU, APU-inclusive and residual contributions in aligned expensive calls.
If PPU explains most growth, optimize the renderer next. If APU or residual
dominates, a PPU-only rewrite has a smaller ceiling than the current hypothesis.
Callback and worker results identify resampling/submission/display costs outside
the renderer rather than charging them to it. A single pair gives directional
evidence, not a precise speedup guarantee or hardware-limit proof.

The known nominal full-call budget is 16.6881545 ms; 20% target is 13.3505236 ms.
Add main-step CPU and disjoint worker CPU deltas for CPU occupancy; do not add
overlapping worker time to wall time as an exact service measurement. Retain
invalid PCM-pointer counts. Truncated effects or invalid PCM reserve cannot
prove sustained headroom, even when a reported CPU interval is cheap.

`build/report-quick-profile.py` reads only an archived return. It reports warm
and known expensive phase means/median/p95/p99, whole-call distributions,
aligned observer disturbance and worst 16-call CPU occupancy. Sparse p99 from
a small sample is descriptive, not a tail guarantee. It rejects mock CPU times
as A7 evidence. The actual ARM controller, phase ABI, callback counts, unchanged
gameplay observations, frame/PCM accounting, wrapper and ABI are qualified
offline; unchanged core exactness and native-provider seams reuse frozen proofs.

## Staging

Archive I: completely before any writes; verify all archive hashes, clean FAT,
stock boot files, production core, original ROM and progress. Freeze the owned
source/payload/proof hashes, publish bounded receipts, commit and push source
before staging. Install only the separate `retro/snes-profile1` payload and
owned one-shot dispatcher/marker. Verify protected files and payload readback
and clean FAT after staging. No `emu_sfc.so` replacement. The production gate
remains false; no A7 benchmark numbers exist until the card returns.
