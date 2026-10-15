# General draw-order candidate with stable APU compilation

The physical test has returned: all18 contexts clean twice, with a measured
Quasar regression. I: is unarmed; see the [results](snes-draw-order-return.md).
The earlier
[actual installation record](snes-draw-order-installation.md) verifies all85
payloads, protected progress and clean FAT at deployment.

Ben explicitly requested implementation, stable APU compiler output, validation
and installation on I:. The candidate is separately owned at
`retro/snes-draw-order1`; production acceptance requires its returned hardware
evidence. The exact source must be clean and pushed before the guarded installer
runs. Original binaries, progress, prior tests and all frozen research artifacts
remain protected. Installation is recorded separately after readback.

The renderer draws the uniquely highest-priority BG3 tile class first in Mode1,
then retains the original order for OBJ, other backgrounds and low-priority BG3.
Existing depth rejection can then avoid coloring pixels hidden by that foreground.
Transparent holes, windows, main/sub distinctions, depth comparison/write rules,
color math, OBJ evaluation/order/limits and raster state remain with their original
consumers. Eligibility depends only on rendering state: BG3 enabled and priority
set, ordinary256-pixel pitch, no pseudo/half/double output, and no active BG3
mosaic. Unsupported states follow the original order. There are no spell IDs,
predicted frames or reused completed images. The priority filter is scoped to
the two BG3 calls and returns to zero before other consumers and after drawing.

The candidate starts from the ordinary qualified demand-v3 source, rather than
the research observer. `build/prepare-draw-order.py` makes fresh control/candidate
copies. `build/draw-order.h` and guarded changes to the original renderer and
scalar/batch/sole-source tile entry points implement the priority split. Work
arrays, test probes and PC sampling are absent from the ordinary cores.

The entire unchanged `apu_blargg.c` translation unit is compiled once outside
LTO. Its object is copied into both fixed-APU control and draw-order builds and
verified after linking, SHA256
`a3baec4aabbbb539858fb7fc59b5b96bddf7e7e6bb7a51c6e6fa394f8b542097`.
This is the identical object established by the prior compiler investigation.
All21 named SPC/DSP function sizes match the object and both final linked images.
This freezes compiler output for the APU unit while PPU sources change. Linked
addresses/relocations and cache layout can still move; it does not prove the
fixed-object boundary faster than raw v3. The hardware suite includes all three
cores so that boundary cost and draw-order benefit remain separately measurable.

| Ordinary core | Purpose | SHA256 |
| --- | --- | --- |
| Raw demand-v3 | Existing physical baseline | `1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8` |
| Fixed APU only | Compiler-boundary control | `24739a6e9d8d050175408e3d95ea1f24ec58c67616f652a8831bfc513dbb3516` |
| Draw order + same APU | Candidate | `48b49949a26ba0732ed70867deaa14816de52cc3bf08f171307e735fa6d0ff3a` |

Validation compares both ordinary new cores to raw v3 using every original
input command in all18 archived contexts:43,200 exact graphics/PCM/geometry calls,
with normalized state every30 calls. Test-only clones also compare against the
actual original `RenderScreen`, including both pixel planes, both depth planes
and OBJ limit flags:2,560 fixtures pass,1,024 taking the new path and1,536 the
fallback. They cover cold/warm tiles,8/16-pixel tiles, all flips, mixed priorities,
transparent holes, add/subtract/half/fixed math, empty/split/clipped/raster Window2,
OBJ rotation and32/34 limits, mosaic/pseudo/half/double/pitch guards. Seven real-core
mid-frame resolution/interlace/height/pseudo-hires and state-load-cycle tests pass
another8,400 calls. Their common test-only HDMA host-base reset is retained from
the independently characterized fixture issue; shipping HDMA is unchanged.

The new automatic suite has48 epochs:18 candidate contexts twice in opposite
fixture order, then Meteor/Quasar blocks with raw v3, boundary-only and candidate
in forward/reverse variant and effect order. Each epoch requests1,200 full calls.
The native consuming-PCM/direct-output/fault/retry/state fixture, real startup
wrapper, ABI ceiling and physical-mock rejection are required before readiness.
No nested phase clocks, PC sampler, work counters, frequency pinning, dropped
frames or dropped audio are enabled. Private state bodies remain exact; only
the existing identity header is migrated for each precise core.

Readiness is now verified: the actual ARM controller passes all57,600 calls,
all48 expected effect windows and lossless PCM accounting. The native fixture
passes142 acquired direct-output callbacks plus failure/retry/drain/state seams;
wrapper, ABI<=glibc2.30 and physical-mock rejection pass. No QEMU duration is used
as A7 performance evidence. The [frozen readiness receipt](../evidence/2026-10-14/draw-order/ready.json)
and its qualification/audit metadata preserve all prior published hashes.

The installation measurement contract explicitly retains missing prices:

| Gate item | Evidence before this installation |
| --- | --- |
| Measured new A7 draw-order saving | Unknown; no new candidate has returned |
| Fixed-APU boundary cost | Unknown; separate hardware control included |
| Added costs | Two extra BG calls per eligible main/sub pair, repeated BG3 traversal, priority guards, code and linked-layout/cache effects |
| Break-even | Avoided production time must exceed traversal, guards and layout cost; total candidate must also beat raw v3 after boundary cost |
| Predicted remaining audio deficit | Unknown; the latest raw Meteor recorded worst16 excess is0.266ms, before uncounted system/reserve costs |
| Falsifiable result | All18 contexts clean twice; valid full frames/PCM/pointers and effect/recovery reserve; positive matched candidate-vs-boundary and candidate-vs-raw savings in both orders, without unacceptable regression |

The earlier observed prototype removes32.5% of late Meteor main RGB writes and
about3,407 vector expansions/call, but those are work counts from the research
observer. They are not ordinary-candidate or A7 savings, and overlapping work
populations cannot be added. The recent physical census places related geometry,
band and tile producers in the hot path, supporting this general target. Explicit
installation authorization obtains the missing net hardware measurement; it
does not pass the production gate. Pointer drift, incomplete effects/recovery or
nonpositive net saving rejects promotion. Do not subtract synthetic observer cost.

After successful installation: safely eject I:, cold-boot with the handheld off
first, allow20–25 minutes, wait for the stock launcher, then power down and return
I:. Select+Start aborts; the one-shot marker is consumed before hardware startup
and the following reboot is stock. Archive on return before changing anything.
The [test instructions](snes-draw-order-test.txt) describe the same sequence.
