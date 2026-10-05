# Hardware lab 1 and the custom-code route

Ben authorized a bounded test program to discover useful hardware behavior,
rather than repeatedly asking FF6 to reveal it. Lab1 is an isolated native ARM
executable; it does not start an emulator or access game progress. Its physical
run completed and returned to stock; see the [return findings](platform-lab-1-return.md).
It uses the existing qualified board/display implementation,
kernel clock and UI, not a newly invented private driver contract.

Initially installed and armed on the inspected D: card after a fresh39-file read-only
archive. All20 protected private progress/report entries, stock binaries,
boot hook, game runner and core hashes are preserved. Lab executable SHA256:
`4deb0571b4500c727c036a50a2e64f01cb9ee23874a3d19df7e6d59b7f919cee`.
Returned lab1 markers were consumed and its card archived unarmed. The next
[lab2 infrastructure test](platform-lab2.md) has its own guarded update and run.

## Engineering judgment

We have **not established a hardware ceiling**. The1.8 checkpoint reports about
13.31ms of timed core/audio/display CPU per emulation call, versus a16.688ms
native period. That excludes other kernel/system/producer costs and is an
average; it is evidence of a possible route, not a guaranteed20% reserve.
The actual loop delivered about57.93 calls/sec and had long tails.

The credible larger changes are:

1. **Reuse derived tile colors, then composite every frame.** Pinned Plus
   already caches decoded palette indices; it still resolves those indices to
   RGB565 on draws. Lab1 implements a small generation-tagged color/mask cache
   for ordinary4bpp tiles and compares it with scalar and current NEON lookup.
   Current depth, transparency and flip are applied on every draw. This is
   reuse of intermediate work, not reuse/suppression of a completed frame.
   More memory traffic can defeat the idea, so reuse, thrashing and palette
   churn are all measured. No predicted percentage is claimed.
2. **Publish PCM as it becomes available.** The Blargg APU already has an
   in-frame samples-available callback, but the libretro layer accumulates
   samples and publishes them after S9xMainLoop. Its1024-scalar-sample threshold
   is512 stereo frames, nearly16ms at32040Hz. A smaller publication quantum can
   let the audio worker consume already-emulated PCM during later CPU/PPU work.
   CPU/APU register timing remains synchronous; an independent speculative APU
   thread would be the wrong optimization. This core change is not in lab1.
3. **Own the scaler lifecycle and overlap peripherals where legal.** The current
   worker serializes DrawVFB and FlipVFB; source release before flip only hides
   some producer waiting. Persistent scaler setup and scale-N+1/scanout-N
   overlap require qualified output ownership/completion contracts. Existing
   queue fields do not establish those contracts. Lab1 prices the working
   DrawVFB/FlipVFB service and CPU overlap; it does not call unqualified queue
   modes or concurrently call the vendor display API.

The current compiled tile helpers also spill/reload palette vectors per row and
do some lookup work before checking for an empty row. A compact hand-written
A7 kernel may be preferable to a color cache if the cache loses. Actual
disassembly, not an intrinsic count, must qualify that next change. The A7 has
ARMv7 NEON table lookup and masked selection; it does not acquire a second CPU
through pthreads. See [Arm's intrinsics reference](https://arm-software.github.io/acle/neon_intrinsics/advsimd.html).

Do not call native32040→44100 conversion a redundant double resampler: this
Blargg implementation already directly copies when its internal ratio is1.0.
Changing its playback rate would select its Hermite resampler and alter the
host/native-PCM contract. This is not automatically less work or the first lever.

## What the executable measures

- Read-only CPU/cache/frequency/clock-tree discovery where the kernel exports
  it; absence is recorded. Bounded CPU/memory/IRQ/kernel snapshots before and
  after work. It only reads trace_clock availability, never enables tracing.
- Kernel-clock5ms wake lateness over200 waits.
- Nine bounded tile benchmarks: scalar, current NEON and a128-entry color
  cache under reuse, larger working set and palette churn. The reported cache
  allocation includes keys, generations and masks; no cache size is guessed.
- OSS requests32000,32040,44100 and48000Hz, recording accepted rates, actual
  fragments/capacity and configuration errors. Rate discovery does not submit
  audio. Timed sound phases request44100 and use the accepted rate.
- Five4-second phases: display only, audio only, both, both plus12ms of
  producer-thread CPU work, and the same CPU budget with voluntary1ms yields.
  The latter is a scheduling experiment; CFS yields need not improve service.
- A quiet400Hz triangle stream, byte-preserving nonblocking writes, partial
  writes/EAGAIN and maximum accepted-write gaps. One thread owns writes and
  all OSS observations; no software-ring/in-flight double counting occurs.
- Timestamp-bracketed raw GETODELAY, GETOSPACE and GETOPTR records in bounded
  memory every5ms when scheduled. Query error codes are retained. DAC movement
  during the queries means this is a bracket, not an atomic hardware snapshot.
- Submission/completion counts, producer reserve/copy costs and worker
  DrawVFB/FlipVFB CPU/wall costs. The original ordered FIFO remains unchanged.

Measurements buffer in RAM. Journal records and CSV/platform snapshots are
flushed/fsynced at boundaries outside the timed phase. The audio tail includes
display draining; record the timing limits when comparing intervals. There is
no per-frame SD logging or gameplay-wide global sync.

**Interpretation limits:** accepted PCM is not uninterrupted playback;
GETODELAY=0 is not an xrun count; a vendor flip return is not optical panel
cadence; synthetic tile/CPU cost is not whole-game speed. GETOPTR resets,
wraps, initial startup and OSS recovery must be qualified before treating it
as an audio clock. Upstream4.19 OSS can recover underruns internally, so zero
write errors are insufficient ([kernel source](https://raw.githubusercontent.com/torvalds/linux/v4.19/sound/core/oss/pcm_oss.c)).

Lab1 does not change frequency, MMIO, IRQ routing, watchdogs, unknown GPIOs,
kernel scheduling priorities, GPU state or undocumented SRAM/DMA/PPU modes.

## Qualification and run contract

The exact ARM build passes12,300 independent scalar-versus-NEON/cache cases for
pixels, depth, flip, transparency, tile/palette generation changes and cache
reset. The same byte-offset writer used by OSS passes a4096-byte fixture with
arbitrary byte-sized shorts, EAGAIN and EINTR. Actual ARM/QEMU runs qualify the
five-phase null-backend control flow and a stuck child's TERM/KILL/reap. These
are correctness and lifecycle evidence; they are not physical performance.
The ABI uses device glibc2.30 or older symbols.

Actual wrapper tests have only sh/mv/mkdir/sleep/sync available, reproducing
absence of head and sed. They cover unarmed/normal/zombie/releasing/stuck splash
and deadline recovery. First paint waits for active showlogo cleanup. Both
one-shot markers are consumed before starting. Per-boot/PID result directories
refuse existing-directory reuse, so a prior result cannot silently become this
run's report.

The supervisor owns the child for the whole run, with a60-second deadline.
Normal completion/cancellation drains/joins before freeing and returns to stock.
Timeout captures child state, requests TERM, then KILL after3seconds, and reaps
the child. It never returns while a blocked child remains alive. After forced
termination, the wrapper holds for reboot instead of starting another display
owner on unqualified peripheral state. Kernel/SD stalls and whole-device power
loss cannot be made recoverable merely by a userspace deadline. The following
boot takes the consumed-marker stock path.

To remove the lab dispatcher later: with both markers absent, restore the
preserved retro/snes-mvp/launch-game-1.8.sh bytes to launch.sh. Do not arm the
failing game release merely to remove this dispatcher. The lab's results should
be collected first. No boot-hook rewrite is necessary.

Install guards require the exact unarmed1.8 runner/wrapper, boot hook and stock
hashes. The installer archives logs and private progress first, retains the
byte-identical1.8 wrapper as launch-game-1.8.sh, then installs a small dispatcher
at the existing /bin/sh entry. The hook, runner, core, ROMs and private progress
are preserved; arming is the final step. Historical1.8 installers deliberately
refuse this changed dispatcher baseline.

Build in the existing owner-supplied Linux cross-build environment:

```sh
sh build/build-platform-lab.sh
python3 build/check-platform-lab.py
```

Publish with build/install-platform-lab.py; its --install --arm option is guarded
for the exact Windows D: card. Read its guards before use. After return, use
build/collect-platform-lab.py for a read-only archive, then
build/analyze-platform-lab.py on one archived results/run-* directory.
Games, saves, vendor libraries, sysroot and raw private archives stay local.

## Next decision

The physical result selects NEON over this color-cache implementation and
demotes blanket CPU slicing. Coarse-looking wake latency and OSS staging make
timer/consumption qualification and coherent event-driven production control
the next targets. Keep the original proposal below as rationale, not a claim
that the returned cache should now enter the core.

Choose the cache or a compact register-resident row kernel from actual A7
costs, then qualify its real-core invalidation and output. Production cache
keys must cover physical tile identity/format, selected palette, brightness
and direct-color context. Every VRAM/CGRAM/brightness write and reset/state
load must invalidate correctly, preserving upstream FLUSH_REDRAW ordering.
Lab1's4bpp fixture is not a proof of those emulator hooks.

If peripheral service is healthy but audio under burst load has gaps, shorten
core PCM publication and repair the producer's consumption/accounting controller.
If display service blocks native throughput, build the persistent backend with
explicit output completion before enabling hardware overlap. Full-speed FF6
remains the acceptance test after that engineering, not a claim from this lab.
