# Execution-budget review after the 1.13 return

The current approach became too reactive to the final PCM errno. The
[retained flight history](snes-mvp-1.13-return.md) now shows production falling
behind before the unusual pointer increments and stream stop. The next build
must address the execution budget, rather than merely make the same failure
easier to observe. No new device executable is installed in this review.

## What we were treating too casually

**Initial latency is not a maintained safety reserve.** The owner primes
2,823 frames (64ms at 44,100), then admits whenever total estimated lead is at
or below that target. This upper bound prevents excessive latency; it does
not guarantee sufficient sound before every long call. When already low, the
current code does produce immediately. Adding a lower-bound wait would be
wrong: this same producer is the only source of new samples. Useful low-water
behavior removes optional blocking and prioritizes production; it cannot
manufacture throughput that the core lacks.

**Buffering bridges jitter, not repeated underproduction.** The failing stretch
produces about 37k accepted frames/sec against a negotiated 44.1k sink. Its
19.88ms batch cadence must drop below the native 16.688ms frame period, about
a 16% duration reduction, with further headroom. This is a measured target for
that interval, not a universal CPU speedup estimate. A bigger buffer delays
failure if the same deficit persists. Earlier publication of already-correct
samples helps blackout length, but does not increase total samples per second.

**A Cortex-A7 flag and a few NEON kernels are not a fully tailored core.** The
actual build uses ARM Cortex-A7/NEON hard-float, but upstream unix `-O2`, PIC,
`-fno-builtin`, no LTO and no compile-time hidden visibility policy. Our patches
specialize seven full-tile modes and backdrop/window spans. Clipped paths,
Mode7 and CPU/SPC/DSP execution remain broader candidates; no trace attributes
the failing phase to one of them yet. Exact-output success establishes
correctness, not speed or hot-path coverage.

**Threads provide peripheral overlap on one CPU.** Audio and display workers
already overlap emulation with device waits. Separate CPU/APU/renderer threads
would still share the same execution capacity and add synchronization. The
display reservation wait is tiny in this return, so continuous scaler queueing
is not the first explanation for its missing frame budget. Peripheral service,
preemption and source-copy costs still count against the same CPU.

**Reported lead becomes suspect at the pointer divergence.** Before divergence,
application pointer and accepted writes agree. Later, the reported queue
includes unexplained 128-frame increments. A future controller should reconcile
accepted counts and reported pointers, identify the transition and report
qualified reserve only while that relationship holds. Subtracting a fixed 384
forever is wrong; the offset begins at zero and grows during failure. Exact
vendor recovery behavior is still unknown.

**The fixtures prove different things.** The real-core/native fixture has a
consuming provider, injected failure, retry, snapshot resumes and occasional
25ms stalls. It runs on a different compute environment and does not reproduce
the device's repeated 19–21ms phase. Isolated stalls can be replenished by a
fast producer afterward. Output equivalence and owner lifecycle checks remain
useful, but neither proves sustainable handheld production.

## Proposed next engineering bundle

1. **Use the actual expensive state as the budget owner.** Measure main-thread
   CPU and wall work by phase: 65C816 dispatch, SPC/DSP, PPU compositing, frontend
   conversion/publication and waits. Keep tiny RAM accumulators across an entire
   gameplay run, so one broad qualification gives both attribution and physical
   acceptance. Local state replay can reveal work counts and correctness first;
   QEMU timings cannot decide A7 performance. Aim below 16.688ms with margin,
   provisionally 13–14ms for main production plus remaining platform service.
2. **Build the core as a locally owned program.** Qualify `-O3`, LTO and internal
   visibility/binding while explicitly exporting the libretro API. Audit cross-
   module globals/declarations and snapshot pointers. Inspect emitted code and
   check exact logical state, pixels and native PCM. Do not promise a speedup
   from flags or add blanket fast-math/unsafe aliasing. GCC documents the
   interposition and visibility opportunities in [optimization options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html)
   and [code-generation options](https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html).
3. **Spend custom code where the expensive phase actually runs.** Extend A7
   kernels to the measured clipped/affine/color-math paths if they own the loss;
   consider CPU/SPC dispatch specialization if they dominate. An exact cache of
   unchanged background/composite spans could remove repeated work while still
   submitting every complete frame. Such a cache must account for raster-time
   VRAM/CGRAM/OAM/register changes, priority, windows and color math; a crude
   whole-frame reuse shortcut would be incorrect. This is a candidate design,
   not an established implementation or assumed benefit.
4. **Remove frontend work without compromising emulated time.** Current
   32,040-to-44,100 linear conversion can use a specialized 245/178 phase cycle
   with preserved rounding/state; batch servicing can reduce duplicate syncs.
   Publish smaller valid batches at existing APU synchronization boundaries
   where beneficial. Do not run the APU ahead of CPU register writes. Simply
   changing Blargg output to 44,100 is not an automatic win: its current unity-
   ratio path copies, whereas a changed ratio enables Hermite conversion.
5. **Qualify the complete budget once.** Sustained expensive-phase production,
   sound continuity, every frame callback, input, pause/snapshot/resume and
   clean shutdown must pass together. Replay the observed repeated deficit in
   local controller checks rather than another isolated-delay success. No
   automatic stop/re-prime may be presented as complete sound; lost samples,
   altered speed and repeated silence would violate the requested outcome.

This review does not establish a hardware limit or promise 60fps. It identifies
a sustained production deficit and sets a concrete path to determine whether
software can close it. Compiler changes, custom rendering and tighter ownership
are still real engineering possibilities; none has yet been measured as the
required gain on this workload.

## Engineering follow-through

[MVP1.14](snes-mvp-1.14.md) implements a whole-program A7 core/runtime candidate,
custom planar decoder, exact reduced-ratio frontend conversion and less
duplicate PCM servicing. Output/lifecycle checks pass; sampled inclusive
APU/PPU and recent per-call costs accompany its physical gameplay test.
This is the first bundle following this review, not a claim that compiler
flags or a cache-miss decoder already close the measured device deficit.
