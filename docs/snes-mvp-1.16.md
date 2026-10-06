# MVP1.16: flush the raster when the color changes

The [1.15 return](snes-mvp-1.15-return.md) prices ordinary main-thread work at
about18ms CPU and19.3â€“19.4ms wall time in the restored scene. Sampled PPU work
is about10ms. This build corrects a concrete source of repeated raster setup
found by replaying that exact state, rather than adding initial audio reserve.

The scene uses Mode1, with31,520 requested full tile rows per frame, no clipped
or Mode7 work and only0â€“8 planar tile decodes after its initial settling. The
prior decoder optimization therefore has little sustained coverage here.

Pinned Plus flushes on `$2132` whenever the raw last-written byte differs.
Bits5â€“7 select fixed-color components; bits0â€“4 contain their value. Changing
the component tag can leave every selected component unchanged. In the20
restored replay frames, all214 pending `$2132` flushes per frame do exactly
that. They force almost scanline-sized render jobs despite unchanged color.

The owned patch checks the effective selected component values before flushing.
It preserves the original component assignments and stored byte latch exactly.
Actual changes still flush before mutation. It does not defer a changing color,
change emulated time, cache a complete frame, suppress a drawing or alter sound.

| Exact local replay work |1.15|1.16|
|---|---:|---:|
| PPU updates, steady odd frames |217|4|
| PPU updates, steady even frames |223|10|
| Requested full tile rows/frame |31,520|31,520|
| Rendered layer-line totals/frame |423|423|

This removes roughly96â€“98% of PPU update calls in this workload, **not96â€“98% of
PPU CPU or total frame time**. Pixel processing still happens. Longer render
runs also amortize tile/palette setup across rows. Physical speedup remains
unmeasured; the returned device must establish enough sustained production
margin for complete native sound and every frame.

Qualification executes16,777,216 cases from extracted pinned and actual patched
register blocks. Expected effects come from running the original register code,
not a second copy of our predicate. Colors/latch match exactly; every effective
change retains flush-before-mutation. Full-core replay compares1,200 frames of
visible pixels, native PCM, geometry and periodic logical serialized state
against the clean core, including the exact returned snapshot and menu inputs.
The separate census checks40 exact-output frames; QEMU supplies work counts and
correctness, never handheld timing evidence. Native owner/PCM, sustained-deficit,
snapshot/boot/input/display/teardown contracts accompany the build.

Failed sessions now keep separate `failure-PID-KERNELNS-session.txt` and matching
`-pcm.txt` records in the private saves directory. Copies occur after failed
worker shutdown, with a limit of eight per process. PID and retained kernel
timestamps prevent an old latest trace from being attributed to a new session.
The existing latest report/trace remain available. This is fault retention,
not automatic PCM restart or a claim that the first-launch fault is explained.

The guarded installer accepts only consumed, exact1.15 on inspected D:. It
archives all logs/progress first, retains stock/hook/lab/original snapshots and
SRAM, and creates a separate qualified state header for the new core. Independent
readback and immutable release publication precede handoff. Follow the
[single gameplay qualification](snes-mvp-1.16-test.txt): load that snapshot,
play the scene, map/party/map, pause/resume, save and exit.

Installed and independently read back at2026-10-06 06:23 UTC, October6
America/Chicago. The pre-write archive retains45 MVP/49 lab files. All23
original private files, stock/hook, older wrapper and lab files match; the
separate new-core state has identical payload/CRC. Game armed, lab unarmed.
Owned release: `releases/snes-mvp-1.16/`. Qualification and independent
readback: `evidence/verification/snes-mvp-1.16/`. Work counts:
[raster census](../evidence/2026-10-06/raster-work-census/analysis.json).
