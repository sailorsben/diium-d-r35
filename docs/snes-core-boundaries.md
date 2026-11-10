# SNES work scheduling on the D-R35

## Where game-specific symptoms come from

The SNES CPU, PPU, sound CPU and DSP each have timing and state that games
can observe. The D-R35 runs their emulation on one Cortex-A7. Inside each
`retro_run`, this core advances the sound subsystem at the end of every
scanline, synchronizes it again when the CPU touches a sound port, draws
pending PPU rows before state changes that can affect those rows, and hands
off finished RGB565 and PCM buffers. These are several different kinds of
work. Guest timing controls which value a game sees. Host staging controls
how much A7 time the core spends delivering the result.

The board scaler accepts completed chunk-backed RGB565 surfaces. The audio
worker feeds the native PCM ring, which the device consumes at its negotiated
rate. Neither worker supplies extra CPU capacity for the emulated chips. The
physical five-game return puts audio and video worker CPU at roughly 1.2 ms
per call in the four completed scenes. Star Fox already averages 27.5 ms of
core CPU across its first three valid calls, against 16.69 ms for NTSC. The
kernel's PCM repeat and DROP behavior converts that deadline miss into a
stream failure. [Hardware contracts](boot-and-hardware-contracts.md) ·
[Physical return and reserve analysis](snes-throughput-architecture.md)

The current Rendering Ranger fix is a concrete example of a guest timing
problem. The core can stop just before an SPC instruction that checks the
old acknowledgement and then publish the CPU's replacement byte. Ranger's
handshake stalls. The existing ROM-scoped policy finishes that instruction
before the write. Enabling the same policy everywhere preserves Ranger and
two other replay windows, but changes PCM in 337 F-Zero calls and all 1,200
Star Fox calls after the cold sequence. Keep this ordering decision tied to
observable port timing. A more accurate replacement would implement the
port-access cycle and validate it against an independent timing reference.
The current Snes9x APU has explicit CPU-to-SMP synchronization at the ports,
and ares synchronizes on the SMP-side I/O accesses. Neither source establishes
the cost of porting its scheduler to this handheld.
[Ranger trace](five-gameplay-fixes.md) ·
[Snes9x APU source](https://github.com/snes9xgit/snes9x/blob/master/apu/apu.cpp) ·
[ares SMP I/O source](https://github.com/ares-emulator/ares/blob/master/ares/sfc/smp/io.cpp)

## Measured work in 1,200 calls per game

| Scene | HBlank APU service calls | CPU reads and writes to sound ports | SPC interpreter entries with no executable instruction |
|---|---:|---:|---:|
| Mario, PAL | 374,400 | 225,028 | 114,889 of 597,871 |
| Metroid | 314,400 | 16 | 4,618 of 313,046 |
| F-Zero | 314,400 | 4,800 | 3,448 of 318,377 |
| Star Fox | 314,400 | 924 | 29,911 of 307,663 |
| Rendering Ranger R2 | 314,400 | 43,803 | 17,796 of 357,304 |

The scanline clock is nearly the same work schedule across NTSC games.
The CPU-to-SPC communication pattern varies by orders of magnitude. A policy
based on one game's rate of port access therefore generalizes poorly.

| Paired ARM replay experiment | Mean core CPU saved | Output decision |
|---|---:|---|
| Specialize NTSC and PAL clock conversion | 0.8–3.4% across five scenes | Exact in replay |
| Finalize DSP spill at PCM publication | 0.5–3.8% | Exact in replay |
| Bypass the empty unity-rate ring | 1.6–3.6% | Exact in replay |
| Skip all empty SPC interpreter entries | 1.2–2.3% in the other four, 8.6–8.8% slower in Star Fox | Exact with a repeatable Star Fox regression |
| Skip empty entries only at CPU audio ports | 1.5% slower to 1.1% faster | Exact with mixed timings |
| Group two, four, or eight scanlines | 3.0–5.9% in the passing Metroid scene | F-Zero and Star Fox change PCM |
| Corrected combination of clock, spill and ring changes | 1.3% in Star Fox, 4.4–6.5% slower in the other four | Exact with substantial regressions |

- **Combine two, four, or eight scanline service intervals.** All three
  variants flush pending time before every CPU-side APU port access, before
  a normal mid-frame PCM publication and before returning to the frontend.
  They preserve total video callbacks and PCM frame counts in the five
  replays. Even groups of two change the PCM bytes in 119 F-Zero and 115
  Star Fox calls. Preserving those outer barriers alone leaves an observable
  timing change inside the APU. The current `spc_end_frame` catches up the
  timers and DSP as well as shifting the clock reference. The precise first
  divergent internal event remains to be traced. Metroid happens to pass
  all three group sizes and saves 3.0%, 4.8% and 5.9% mean CPU in paired host
  runs. Reject these grouping rules for the shared core.
- **Return directly when no SPC instruction can execute.** This keeps the
  original port timestamp and checks the existing instruction cycle table
  before entering the interpreter. All five output checks pass. The added
  entry guard belongs on a path used often enough to cover its branch and
  linked-code costs. Moving the guard to the ports avoids most of the Star Fox
  regression but fails to deliver a broadly useful gain. The instrumented
  port version skips 106,178 entries in Mario, 14,920 in Ranger and only
  37 in Star Fox. Even a high hit count needs a net cost measurement.
- **Keep scanline service and simplify its clock arithmetic.** At the exact
  original call site, compute elapsed SPC clocks and remainder from one
  numerator. Default NTSC and PAL have constant divisors. Other tempo ratios
  use the original runtime divisor. This preserves fractional time and every
  guest event. All five output and callback-layout checks pass.
- **Retire the DSP output spill when handing off PCM.** The current core
  gathers the DSP's extra output after each scanline. In the frontend's normal
  mode, the extra data is read when a PCM batch is finalized and the DSP is
  given its next output destination. Move this bookkeeping to that boundary
  while leaving SPC execution, timers and DSP advancement at their original
  times. The legacy synchronized-sound mode retains its original path.
- **Bypass an empty unity-rate ring.** The current core copies finished PCM
  from the DSP landing buffer into a core ring, then immediately copies it
  into the libretro output buffer. When the ratio is unity, the ring and lag
  are empty, and the destination has capacity, copy directly into the same
  output buffer. The counted build took that path for all 11,602 finalizations
  across the five replays. This removes one copy of roughly 2.1 KiB per NTSC
  call and 2.5 KiB per PAL call in these windows. The existing board conversion,
  queue, and negotiated device PCM rate are separate stages.

The combined candidate uses the clock, spill and unity-ring changes. The
first combination skipped spill capture on the direct path, which changed
PCM in all five windows even though each standalone change passed. The
corrected direct path captures the spill before resetting the DSP destination.
The corrected combination passes all five 1,200-call output checks with matching
PCM callback sizes and order. It also passes the strict FFVI Meteor and
Quasar state comparisons and 2,400 calls from Ranger cold boot. Those checks
compare pixels, PCM and normalized serialized state. They use the exact
returned core as the baseline. The isolated unity path passes the same
three held-out comparisons.

## Where one pass can replace several

Use the next interaction that a guest component can observe as the end of
each block. A render span can consume a stable tile, palette and window
state for several rows. A CPU block can run straight-line instructions
until it reaches an interrupt or an I/O access. A memory-only DMA span can
move a run of bytes together under the existing mapping and timing guards.
At each boundary apply the effects in guest-clock order. A CPU write between
two SPC reads must affect the second read at the proper cycle. DSP reads and
writes of SPC RAM, timer side effects, DMA, and PPU raster writes also set
boundaries. Adjacent pieces can share setup and vector operations when the
same inputs and ordering apply.

The current port-gated scanline grouping proves why a list of outer events
is incomplete. It synchronizes before the CPU ports and before output
publication, but two scenes still produce different PCM. An event scheduler needs
the internal dependencies and correct timing as well. The opportunity with
the strongest existing cost evidence is to widen stable PPU spans and fuse
their host rendering work while continuing to model visible writes at the
correct time. Keep device publication on the host clock so a large block
does not delay ready PCM behind unrelated drawing.

## What to pursue on the device

Price the clock and direct PCM changes individually on the A7. The combined
build loses too much in four scenes to rank ahead of the individual changes.
Keep the larger engineering target on the renderer's actual state changes
and span work. An APU architecture intended to replace per-game timing rules needs a
testable CPU/SPC port timestamp, DSP shared-RAM ordering and timer behavior.
Consolidating host buffer work can proceed independently of that more exact
timing model. F-Zero and Star Fox belong in the acceptance set for every
change to those boundaries. Ranger belongs in it from cold boot.

All new timing pairs execute ARM code under QEMU on the PC. They alternate
which core goes first each frame and use the same frozen inputs. The A/A
control compares the returned binary with a rebuild whose executable text
is byte-identical. The project still needs uncensored A7 time for the full
Star Fox scene. Collect core and worker CPU, PCM production and consumption
on the same host clock, then compare each shared APU change and any raster
candidate independently. Require complete video and PCM, valid
device pointers and replenishment of reserve through the scene. The new A7
net savings and remaining audio deficit are unmeasured, so the install gate
remains pending.

Reproduce with `build/build-snes-throughput.sh`, the `scheduler-verify` batch
of `build/run-snes-throughput.py`, the scheduler modes of
`build/run-snes-throughput-pair.py`, and `build/check-snes-scheduler-state.py`.
Each uses private, previously qualified fixtures. The summary publishes
counts, timing aggregates and hashes.
[Results](../evidence/2026-11-10/snes-core-boundaries/analysis.json)
