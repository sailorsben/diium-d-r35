# Star Fox stack audit and raster reuse

The renderer now has a way to prove it can retain a span **before it
draws**. It remembers the tile-map and tile-data bytes read by the last
draw, along with the scroll, sprite, palette, window and color-math inputs
for those scanlines. It compares exact bytes. A VRAM upload elsewhere on
the chip does not invalidate a picture that never reads those bytes.

The guarded implementation retains spans on the core's own padded
surfaces. It draws normally on a miss, when another span overlaps, for
unsupported geometry and when a record exceeds the cache limits. Reset,
state load, game load, unload and feature toggles invalidate the cache.
The SNES CPU, Super FX, APU and PPU range/time status continue to advance
on every tick. A render hit needs no new buffer or framebuffer copy.
The current admission rule covers low-resolution Mode 2 on the
Super FX path, with safe fallback to the existing renderer.

## Audit across the stack

| Layer | Finding and experiment |
| --- | --- |
| Stock launcher | The returned problem starts in the gameplay loop. The stock-derived loader already opens the core directly. Music decode and startup raster are separate from steady-state Star Fox service. |
| Guest CPU and scheduler | This build's NTSC budget is 16.688155 ms per emulated tick. One Cortex-A7 runs the code. An additional thread can overlap device waits, but it cannot add compute capacity. Preserve scanline, interrupt, DMA and audio-port ordering. Earlier APU slice grouping produced PCM divergences. |
| Super FX | Keep the existing ROM fill and plot loop batching. A new instruction-pair fold recognizes register moves and operand selection in the live stream and consumes the original two instruction slots. Its Star Fox pair lost 1.3% mean and 3.9% at p95, so it stays off. |
| Tile decode | A NEON bit transpose reads eight rows as planar data and emits the same tile indices. Its initial Star Fox pair gained 2.8% mean and lost 0.3% at p95. Gains across the other games were mixed and close to run variation. |
| PPU composition | Broad state and whole-VRAM keys previously found zero matching Star Fox spans. The new census records actual renderer reads and compares candidate hits to real RGB565 output. The in-place bypass then removes the verified work from subsequent draws. |
| Display | The real LCD test already cut 801 scaler jobs and 0.852 ms wall per tick through byte-exact picture reuse. Keep that independent guard. The vendor scaler still needs owned chunk memory and the worker's draw/flip ordering. Leave the unsafe Super FX compact-target experiment out. |
| Audio producer | The complete Star Fox window generates 641,626 native stereo frames. The physical baseline consumes at 44.1 kHz and gets about 736 output frames per tick. Delayed delivery costs reserve even when the game has generated the right number of samples. |
| Audio transport | The direct ALSA path stopped in the vendor driver's repeat-period and DROP logic. The OSS interface uses the same ALSA subsystem and can choose different fragment and staging behavior. Switching interfaces alone offers no demonstrated throughput saving. |
| Kernel and hardware | The archived stock driver's PCM table advertises 512 KiB maximum, 16–16,384 bytes per period and up to 128 periods. The observed 3,712-frame ring was a userspace request. A larger ring is a diagnostic lever, with negotiated device support and audible latency still to measure. |

Prior work, the physical display comparison and the upstream ABI can be
checked in the [throughput architecture](snes-throughput-architecture.md),
[handheld return](stock-shell-display-test.md#handheld-return),
[hardware contract](boot-and-hardware-contracts.md) and
[Linux 4.19 PCM hardware structure](https://raw.githubusercontent.com/torvalds/linux/v4.19/include/sound/pcm.h).

## Exact output and measurement

The first paired in-place prototype reduced mean Star Fox gameplay CPU
time by **11.3%** and p95 by **10.4%** in ARM/QEMU. The four 300-tick
quarters improved 10.7–11.8% at the mean. The two arms were copies of the
same binary, with the feature toggled and call order alternating every
tick. An early counter sampled only work after the last internal frame
boundary in each call. The corrected counter counted **165,006 of 268,800
scanlines** reused across 1,200 Star Fox ticks, spanning 4,005 render calls.

| Memo variant | Star Fox mean CPU saved | p95 CPU saved | Rows reused |
| --- | ---: | ---: | ---: |
| 64 entries, compare 32-byte blocks | 11.0% | 12.0% | 165,006 |
| 64 entries, group contiguous reads | 10.1% | 10.0% | 165,006 |
| 64 entries, grouped reads with profile-guided compilation | 10.7% | 11.6% | 165,006 |
| 16 entries, 24 KiB per span | 0.0% | 1.2% | 30,446 |
| **16 entries, allow the full read set** | **10.2%** | **7.6%** | **165,006** |

The 16-entry full-read-set build has a fixed 1.31 MiB of renderer cache
storage, down from about 5 MiB in the larger prototype. It retains the same
rows as the larger caches. That makes it the candidate for the handheld's
43,120 KiB Linux memory budget. The four other frozen scenes show no
comparable savings. Its paired mean differences were −1.77% in Mario,
+0.08% in Metroid, +0.83% in F-Zero, and −1.43% in Rendering Ranger. The
mode gate took zero hits in each of those replays. These are same-binary
toggle pairs under ARM/QEMU, with each arm called first on alternate ticks.
The profile-guided check used the earlier 64-entry grouped build. Profile
training and a physical measurement of the 16-entry build are pending.

All five frozen game windows keep picture, source PCM and sample counts.
The four ordinary games fall through the feature gate. In a separate Star
Fox comparison the 16-entry build matched 41 normalized state
checkpoints and audio callback boundaries on the original input. It also
matched 1,200 picture/PCM/count observations and the same checkpoints with
held-out inputs, two state reloads and poisoned rotating offered buffers.
The comparison uses separate QEMU processes and the same library pathname
to avoid the previously observed two-instance DMA-state difference.
[Measurement and proof digests](../evidence/2026-11-10/snes-throughput/stack-audit.json).

## Audio reserve and the physical acceptance test

The physical reuse run averaged 16.511 ms over the whole silent window.
Its worst cumulative end-of-tick deficit was 12,279 frames. Its 2,823-frame
prime left 2,567 after the 256-frame guard. The valid opening of the matching
native reuse run adds 0.439 ms per tick on average, measured across 33 ticks.
The native window ends too soon to know its full-window cost, so use a
sensitivity range when pricing the remaining deficit.

| Prime | Approximate queued time at 44.1 kHz | Uniform net saving needed if native adds 0.5 ms/tick | If native adds 1.0 ms/tick |
| --- | ---: | ---: | ---: |
| 2,823 frames | 64 ms | 1.330 ms | 1.830 ms |
| 4,410 frames | 100 ms | 1.011 ms | 1.511 ms |
| 6,615 frames | 150 ms | 0.798 ms | 1.298 ms |
| 8,820 frames | 200 ms | 0.686 ms | 1.186 ms |

These break-even numbers require both cumulative drawdown within the prime
minus the guard and production keeping up over the full window. At 0.5 ms
added cost and zero further saving, the diagnostic 24,576-frame prime fits
the single replay model with 1,306 frames of margin at a two-period guard.
The model still ends 17,088 frames in deficit, so that diagnostic buffer
can mask a sustained throughput problem. Its roughly 557 ms of audio lead
is for measurement.

With the 150 ms prime, 1.0 ms of net saving per tick and 0.5 ms of native
cost leave a modeled margin of 2,148 frames. The same saving with 1.0 ms
of native cost leaves a 5,920-frame deficit. These scenarios treat the
saving as uniform. The device comparison must use its measured per-tick
curve and real audio acceptance.

The separate PCM experiment applies software parameters **after** the
vendor's PREPARE resets them, disables kernel-generated repeat periods, and
issues an explicit START after the whole requested prime has transferred.
Its ARM fixture imposes short writes and `EAGAIN`, reproduces the vendor
parameter reset and exercises a new PREPARE after DROP. The diagnostic
requests 512-frame periods and a 25,600-frame ring at the existing 44.1 kHz.
An intermediate probe requests 6,615 frames of lead with 128-frame periods.
The vendor's table lists 32 kHz but gives no 32.04 kHz native guarantee.
Changing rate would also change the sink PCM, so this probe keeps 44.1 kHz.

Use the same rebuilt core and runner in two real-LCD runs with the feature
off/on and identical-picture reuse on in both. Record full-window main,
audio and display CPU, wall time, process RSS, LCD flips, published pixel
and PCM identities, and the full per-tick arrival curve. The A7 saving is
the avoided draw time minus the new lookup, memory-compare and miss-recording
costs. That value is **unmeasured**. A saving at the mean is insufficient if
the first 452 ticks still exceed the native audio reserve. Next use native
PCM with explicit start at the ordinary or intermediate prime, and use the
long-reserve mode as a control if the shorter run stops. Require 1,200 audible
ticks, no application-pointer advance beyond accepted writes, no XRUN or
unexpected SETUP, and the original output identities. Check repeatability
and opening drawdown before setting an everyday reserve.

## Reproduce offline

Use `build/build-snes-stack-audit.sh` with the existing qualified Super FX
source as its first argument, an empty WSL output path as its second, and
`mode2-memo-bounded`, `mode2-memo-small`, `mode2-memo-ranges`, `mode2-memo`, `mode2-dependencies`,
`tile-transpose` or `fx-register-pairs` as its third. Run
`build/check-snes-stack-audit.sh OUT 003 000 001 002 004` for the frozen
output and timing pairs. Set `D35_CHECK_HELDOUT=1` to add the state and
held-out input checks. The optional third argument to
`build/build-snes-core-pgo.sh` enables the selected memo variant in the
normal instrument/train/relink workflow. `build/check-snes-pcm-audit.sh`
builds the separate runner and checks the PCM and display boundaries.
The runner opt-in is `D35_AUDIT_MODE2_MEMO=1`. Set
`D35_PCM_DIAGNOSTIC_RESERVE=150` for the intermediate prime or `1` for the
long diagnostic. See `build/report-snes-stack-audit.py`
for the offline PCM table and complete physical trace calculations.

The ARM tests run on a host under QEMU. No new handheld timing or audio
playback has been observed, and no card or firmware was changed.
