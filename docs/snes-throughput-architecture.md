# D-R35 SNES throughput: what to remove next

The strongest remaining target is **the PPU work that produces the picture**,
with normal emulated CPU, Super FX, PPU status and APU timing kept intact. Use a
separate Star Fox startup optimization to omit pictures that the progress screen
already hides. Treat presentation scheduling as burst protection. It is already
working in that role and does not solve the sustained compute deficit.

No handheld or SD card was available to this investigation. All new timings are
CPU time for ARM code under QEMU on a Ryzen host; they rank mechanisms and put
bounds on available work. They are not milliseconds saved on the Cortex-A7.
The [physical baseline](fivegame-replay-return.md) and the new offline evidence
are kept separate. No deployment, firmware change, or card write occurred.

## Start with the actual deadline

The frozen NTSC replays run at 59.923 emulated frames/s (16.688 ms/call).
The Mario backup is PAL and should retain its native 50.320 (19.873 ms).
The physical service proxy subtracts identified pure pacing from each main
step and adds worker CPU, so it can count overlapping worker execution twice.
It is deliberately more conservative than measured CPU alone. Use its matched
values for the existing 20% headroom gate, not as a direct p95 deadline trace.

| Hardware scene, four windows each | Service p95 | Gap to 20% headroom at p95 | Result |
|---|---:|---:|---|
| Mario, PAL | 13.758–13.823 ms | Already below at p95 | All frames; maximum misses headroom |
| Metroid | 15.399–15.457 ms | 2.048–2.106 ms | All frames |
| F-Zero | 15.975–15.990 ms | 2.624–2.639 ms | All frames |
| Rendering Ranger | 15.959–16.092 ms | 2.608–2.741 ms | All frames |
| Star Fox | Invalid after frame 3, zero-based | First three valid calls: 27.483–27.656 ms **core CPU alone** | 4 renders in each run; native PCM stops |

Star Fox needs 10.795–10.968 ms/call (39.3–39.7%) back from that initial valid
core CPU average merely to reach the deadline, before accounting for the rest
of the loop. The fourth call interval includes the fault and is excluded.
This is the observed opening deficit; the physical archive does not measure
the sustained 1,200-call workload. All four other games already use owned
direct output on every frame with zero callback-copy bytes. Their whole-run
average audio + video worker CPU is roughly 1.19–1.25 ms/call, so even removing
all of it would not cover the 2–2.7 ms p95 target by itself. That worker average
does not quantify an individual frame or the unmeasured kernel share.

## What the PCM trace now explains

The UART-corrected kernel's PCM code matches the stock code byte for byte in
the audited ranges. `gpa7xxxa_dma_prepare` overrides the software start and
silence settings with two periods. On the low-reserve path, the callback
named `gpa7xxxa_dma_fill_silence` copies the **previous period's bytes** and
increments ALSA's application pointer by one period. After three fills in a
500 ms epoch, the fourth fill calls `snd_pcm_kernel_ioctl` with `0x4143`
(`DROP`). The exact HWSYNC function returns `-77` from SETUP. The
[ARM fixture](../evidence/2026-11-10/snes-throughput/vendor-pcm-fill.json)
executes the original fill code and ioctl dispatch with clock, memory copy,
mutex and low-level DROP side effects intercepted. It reproduces all three
advances, the exact command, SETUP HWSYNC failure, the timed reset and wrap.
The physical trace does not record each invocation; this exact code path
accounts for the observed signature across all four trials.

The last trustworthy reserve drawdown is 2,241 frames, leaving a sampled
minimum of 582. The terminal difference is **5030 accepted − 5375 hardware =
−345 frames**; the 384 frames added by the driver are not emulator audio.
At 44.1 kHz, elapsed demand minus accepted post-prime production is
3,387–3,415 frames across the observed opening by the stop. Adding the prior
864-frame margin gives a model requirement of 4,251–4,279 frames (96.4–97.0 ms)
for that truncated opening, versus the configured 3,712-frame ring and
2,823-frame prime. This is a startup bound with the recorded publication
cadence, not a buffer recommendation for the complete scene. Raising the
buffer or hiding DROP can postpone the symptom; neither increases generation.
The full cumulative reserve and eventual refill remain unknown.

## Experiments and decisions

The same five ROM/checkpoint/input/oracle identities are used. The unmodified
rebuild and returned core have identical executable `.text` bytes. The full
video arms check pixels, PCM bytes (per-call CRCs) and sample counts against
the frozen oracle. The no-raster arm checks audio and sample counts only, and
the alternating arm also checks the frames it draws. The oracle reuse arm uses
the *next expected frame hash* to decide whether to reuse the previous picture;
it measures opportunity, not a signal available during play. Separate timing
runs omit the hashes, with same-process alternating order used to control
for the large host variation in sequential trials.

| Paired ARM/QEMU experiment | Mean gameplay CPU saved | p95 CPU saved |
|---|---:|---:|
| Star Fox, turn off raster during gameplay (cost ceiling) | 51.8% | 35.6% |
| Star Fox, oracle chooses exactly when the previous image can repeat | 33.3% | 32.1% |
| Metroid, oracle reuse | 15.0% | 1.8% |
| Mario, oracle reuse | 7.5% | 6.6% |
| Star Fox, five hot Super FX opcodes inlined | 6.2% | 3.9% |
| Star Fox, local Super FX instruction counter | 4.1% | 4.4% |
| Star Fox, dispatch full Mode 2 rows to the existing full-tile helper | −2.4% | −0.4% |
| Star Fox, build with inactive no-offset bypass (two pairs; unattributed) | 11.8–12.1% | 7.7–8.1% |
| Star Fox, larger dispatch switch | −19.1% | −42.0% |
| Same VRAM span skips copy/invalidation, four measured games | 0.9–3.9% | −0.5 to 2.3% |
| Compare/copy/invalidate changed VRAM pieces, four measured games | 0.4–2.0% | −1.9 to 5.4% |

These are paired within the same process on the same host logical CPU, changing
which arm runs first each frame. Separate serial-process estimates had large
order/host variation and are retained only for audit. Quarter-to-quarter data
are included in the aggregate. A percentage in this table cannot be applied
to the physical prefix as a speed prediction.

- **Omit invisible startup raster work.** Keep all 8,656 emulation calls and
  the visible progress UI, discard warmup PCM as before, and enable rendering
  before live measurement. Both all-off and last-64-rendered warmups preserve
  the next 1,200 gameplay pixel/PCM/sample-count checks. The actual supervised
  controller with all-off warmup passes the same 1,200 checks and submits every
  measured picture. It is an isolated candidate, qualified offline for that
  exact replay. The paired warmup saves **28.3%** replay CPU, with no steady
  gameplay speedup. The older physical warmup used 135–136 seconds of main CPU;
  its actual shortened time remains unmeasured.
- **Reuse identical pictures or their component work.** Star Fox has 801 of
  1,200 calls with the previous pixel hash; Metroid 501 and Mario 338. F-Zero
  and Ranger have zero adjacent repeats. The oracle successfully reproduces
  the output while drawing just 399 Star Fox, 699 Metroid and 862 Mario images.
  A fixed every-other-frame policy would discard 196 actual Star Fox picture
  changes in this sequence. Whole-frame equality using a broad live PPU key
  admits zero Star Fox, Metroid, F-Zero or Ranger frames, and hits only 107
  Mario frames. That simple cache is not a viable general implementation.
  Splitting the equality census at actual raster flushes finds **96,760 of
  210,552 eligible Metroid rows (46.0%)** under matching keys, but zero matching
  rows in Star Fox, F-Zero or Ranger. This was a census that always renders;
  copying entire dependency snapshots for each span is too costly to propose
  as a runtime cache. Before building the smaller dependency key, compare
  the actual bytes of each hit span and price the maintenance.
- **Specialize Star Fox's Mode 2 renderer.** Its offset-per-tile walker sends
  29.27 million tile rows through the clipped route. **28.37 million (96.9%)**
  have an unclipped eight-pixel width. A guarded patch routes those rows to the
  existing full-tile renderer, preserves every frozen output in all five games,
  and still loses 2.4% mean CPU under the paired probe. One call per row still
  pays dispatch, cache and palette setup. The next candidate must eliminate or
  amortize that setup at the span boundary; using an existing SIMD function
  is insufficient by itself.
  The second prototype bypasses the offset walker only if the offset map has
  no enabled cells for the layer. Zero of 900,600 observed background scanline
  visits qualify. The existing offsets matter: keep them and optimize how
  their data is consumed. This build does run 11.8–12.1% faster in two paired
  host replays, despite zero qualifying rows. Linked code differs, including
  the size of `DrawBackground` and placement of the APU interpreter. The
  repeated timing difference deserves a compiler/layout control in the A7
  test; no portion is attributable to bypassing the offset walker.
- **Super FX execution.** Keep the real instruction count and pipeline.
  The local-counter arm removes a load/store and G-bit test from ordinary
  dispatch. Two other arms move handlers into a generated switch or inline
  just five high-count operations. The census sees 81.14 million instructions
  and 5,811 interpreter entries in the 1,200-call gameplay; its inclusive
  observer is not a hardware cost measurement. The large switch is a poor
  trade. The local counter and the five-opcode path are small second-stage
  options, far short of the physical opening deficit. The opcode count alone
  does not justify a JIT.
- **Reduce VRAM upload churn.** Test whole-span equality before the existing
  bulk copy, and separately test copying and invalidating only changed 16-byte
  tile pieces. All five retain output exactness under the frozen replay.
  Equal spans cover 25,344 bytes in Star Fox (21.1 bytes/call), 1,025,728 in
  Metroid and 980,048 in Ranger (855 and 817 bytes/call). Those are candidates
  for saved invalidation and later decode; the new comparison has its own
  read and branch cost, and the covered bytes do not price tile rebuilds.
- **Display scheduling and buffering.** The physical five-game comparison
  skips zero presentations in either policy and does not extend Star Fox's
  valid prefix. Prior [48 ms FFVI bursts](presentation-ffvi-return.md) are a
  positive recovery case: both candidate runs complete versus neither
  blocking control, at a cost of 9 and 12 presentation skips. Keep this
  path for bursts. Direct-output removal, more threads on one CPU, and a
  larger audio buffer are not first-line throughput changes.

## Next physical experiment

1. First get the uncensored Star Fox cost curve. Pair the frozen full-raster
   core with a renderer-off diagnostic and one exact renderer candidate in
   matched order. Run the opening and all 1,200 calls without a native PCM
   stream imposing an early stop. Record disjoint main/APU/PPU/GSU attribution,
   exact source sample publication times and worst contiguous windows with
   kernel syscall clocks. Use the inactive-bypass binary as a separately
   identified compiler/layout comparison if the candidate list can stay
   short. Retain the known-good game and heavier FFVI and
   Ranger regressions. Keep instrumentation priced against a control.
2. For production, specialize the expensive background/tile or compositor
   work at the existing flush boundaries. In Star Fox, price the Mode 2
   offset/tile walker and share geometry, palette and decoded-tile setup where
   consecutive rows or runs allow it; its attempted per-row redirect lost.
   In Metroid, prototype a bounded reuse key for the demonstrated repeated
   raster spans. Use narrow, dependency-based guards
   for anything retained across calls; fail open to original drawing for
   mid-frame writes, unsupported mode/geometry and unproved changes. Raster
   status, sprites, timing and PCM must remain exact. Price comparisons,
   invalidation, retained memory and copies before assuming a hit pays.
   Reject a candidate if its removed work does not cover these added costs.
3. Before installation, fill in `saving = removed A7 work − new A7 work`.
   For measured service time `T`, require `saving > T − period` to meet the
   deadline and `saving >= T − 0.8 × period` for the existing headroom goal.
   Compute complete `max(consumed − produced)` and refill-limited drawdown
   from sample publication time, including the in-frame splits and initial
   reserve. Then require a matched native run with every draw/presentation
   accounted for, bit-exact PCM before transport, valid accepted-minus-HW
   accounting, no vendor fill/DROP, and full recovery of reserve. Failure in
   those checks rejects the prediction. **New A7 net savings, added cost and
   remaining sustained audio deficit are unmeasured; install gate not met.**

Offline reproduction uses `build/build-snes-throughput.sh` and
`build/run-snes-throughput.py` in fresh Linux scratch directories. The
same-process arm uses `build/run-snes-throughput-pair.py`. The exact vendor
test uses `build/qualify-vendor-pcm-fill.py`; the isolated real controller
uses `build/qualify-snes-cold-raster.py`. These require existing private
qualified inputs. No ROM, save, vendor binary, or card image is published.
The 94 qualification windows each replay 1,200 calls with the declared
video and PCM coverage. Four timing jobs and the first controller run were
interrupted by SIGBUS during a concurrent ELF inspection. The exact core hash
remained unchanged. Interrupted logs are retained privately; only clean
retries enter the results. The report now reads `.text` from ELF bytes.

[Aggregate results and input hashes](../evidence/2026-11-10/snes-throughput/analysis.json) ·
[Actual offline controller check](../evidence/2026-11-10/snes-throughput/cold-raster-runner.json).
