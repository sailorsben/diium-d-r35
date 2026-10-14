# Research reset after the PPU regression

2026-10-14. Read-only review of existing source, assembly and physical evidence;
no new emulator build, card access, install or rearm. A failed local optimization
bundle does not establish the device's emulation limit. The missing work is
attribution and architectural comparison, rather than another collection of
small kernels selected by work counts.

## What “2005” means here

The upstream label denotes lineage: its README lists Snes9x1.43, NDSSFC,
BAGSFC and CATSFC, not an untouched2005 implementation.
[Upstream lineage](https://github.com/libretro/snes9x2005/blob/master/README.md).
Our current baseline already builds with Cortex-A7/NEON, O3, LTO4, hidden
visibility and no semantic interposition. It has decoded-index caching,
small palette tables, band-local palette reuse, constant-mode background
producers, source-geometry sharing, hidden/sparse rejection, strict DMA
bookkeeping reduction, exact DSP dead-work elimination, exact frontend
resampling and owned direct display output. These are already-paid gains.

Its concrete earlier physical1.09–1.10ms Meteor improvement disproves the
claim that software changes cannot help. It does not prove sufficient headroom
exists. Code age supplies neither a speedup forecast nor a hardware-limit proof.

## Fresh finding: PPU source isolation did not isolate generated code

The exact source hashes for apu_blargg.c, cpuexec.c, cpuops.c and cpuops.h are
identical across the qualified baseline, OBJ, shapes, bulk and combined cores.
Emulated CPU/APU behavior remains exactly qualified. Nevertheless:

| Existing binary | .text bytes | Named SPC interpreter bytes |
| --- | ---: | ---: |
| demand-v3 |657196|21260|
| OBJ |658676|10212|
| Shapes |659172|10212|
| Bulk |658020|21260|
| Combined v5 |679764|10212|

Combined executable code grows22568 bytes (~3.43 percent). The static SPC
read/write/DSP/timer call-site populations are exactly halved in OBJ/shapes/
combined versus baseline/bulk, while the named interpreter approximately halves
in size. DSP helper sizes/symbols also differ. This establishes different
compiler-generated structure across unchanged sources. It does not mean half
the runtime work, twice the speed, more cache misses, or proof of a specific
optimization pass. Smaller SPC code could help or hurt.

GCC documents whole-program optimization, function cloning and loop unswitching;
unswitching can duplicate loops to move invariant tests outside them.
[GCC optimization options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html).
These are mechanisms to inspect using optimization reports/disassembly, not
an identified cause of this return's regression. Static calls are not dynamic
frequencies, and code size is not a measured cache miss rate.

The “isolated family” physical numbers remain valid for their complete binaries,
including compiler effects. They cannot be attributed solely to the changed
PPU kernels. Before another candidate, establish reproducible codegen boundaries
for the SPC/DSP and65C816 engines or explicitly measure their changing costs.
Function-specific optimization, splitting hot translation units or selective
LTO boundaries are research options, not an automatic blanket no-LTO change.

[Reproducible source/ELF audit](../evidence/2026-10-14/core-codegen-review/analysis.json),
`build/audit-core-codegen.py`. It only reads existing binaries and source hashes.
Initial audit setup selected nonexistent getset.h; corrected to actual cpuops.h
before producing evidence. Prior source and binary bytes remain intact.

## Architectural candidates and what the code actually supports

1. **Resolve winning pixels before expensive color production.** Current
   gfx.c RenderScreen renders OBJ, then enabled BGs; tile priorities interleave
   between layers. Its depth checks reject work hidden by an earlier producer,
   but cannot reject a successful RGB write overwritten by a later layer.
   The earlier exact observer recorded33.37 percent overwritten main RGB writes
   in Meteor, versus9.71 percent Quasar; only5.55/5.88 percent of tile-math writes
   were discarded. These counts belong to the older combined1 baseline, before
   demand-v3, so they must be refreshed on current v3 before being priced.
   A priority/source/index representation or priority-ordered producers could
   address plain overdraw as well as math. Simply defer math has a much smaller
   removable population and a costly metadata/readback pass.
2. **Share source production between main/sub consumers.** bsnes fast PPU's
   background.cpp performs one background traversal and offers source pixels
   to both above/below planes; line.cpp chooses final math from surviving source
   metadata in its output pass.
   [Background source](https://github.com/bsnes-emu/bsnes/blob/master/bsnes/sfc/ppu-fast/background.cpp),
   [line composition](https://github.com/bsnes-emu/bsnes/blob/master/bsnes/sfc/ppu-fast/line.cpp).
   It still computes source color before priority insertion; it is not evidence
   of a winner-before-palette architecture. Our v3 already shares one eligible
   BG's geometry. Any proposal must price additional source reuse beyond that,
   preserving distinct windows, depth, math and redraw lifetime. The restricted
   old BG0 experiment had zero positive-path hits; the separate RGB-span cache
   has exact outputs but remains A7-unpriced and was absent from this return.
3. **Measure and then specialize CPU/SPC dispatch and exact DSP.** Current
   65C816 uses opcode function pointers; SPC uses a large switch with cached
   registers. Port reads/writes run SPC to current emulated CPU time outside the
   broad APU timer. Gaussian DSP uses four scalar products with a required
   intermediate16-bit truncation before the fourth and final clamp/even mask.
   Direct-threaded dispatch, exact coefficient layout/vectorization and register
   locality are concrete research areas; a four-product sum with one final shift
   would change audio. Current no-SA1/no-SFX loops and dead interpolation skips
   already exist.2010 retains a comparable SPC switch: newer lineage is not a
   drop-in dispatch improvement or assured faster core.

Source comparison is about mechanisms. Supafaust's README recommends dual-core
hardware and exposes a single-thread renderer option; that recommendation cannot
establish performance on our single A7. Its detailed PPU source could not be
fetched through browsing in this pass; no fresh claim about those internals is
made. [Supafaust requirements/options](https://github.com/libretro/supafaust).
No whole-core swap is recommended from README claims alone.

## The next evidence that earns implementation

Use the current demand-v3 failed-state/recovery workload and a small control set
to answer who owns time: BG/OBJ traversal, palette expansion, clipping/depth,
math/stores,65C816 and port-driven SPC/DSP. Historical sparse broad profiling
attributes~87 percent of effect growth to PPU, but predates v3. Its~4.2ms
APU-inclusive and~4.5ms residual pools are observer-inclusive; residual is not
pure65C816 time. Do not transplant those absolute prices to this baseline.

Use bounded low-perturbation attribution, with matched uninstrumented controls,
instead of scanline clock pairs that previously added~1.3ms to sampled calls.
Where target perf/PMU support exists, sampling may distinguish execution/cache
stalls with less code interference; availability on this kernel is unverified.
Opcode/row counts can establish mechanisms offline but do not replace A7 prices.

Then choose one large, disjoint saving with an explicit added-cost model,
independent positive-path output/state/PCM tests and complete effect/recovery
reserve qualification. Priority selection must preserve transparent holes,
strict equal-depth ties, sprite evaluation/order/limits, main/sub windows,
OBJ palette math eligibility, fixed/sub operands, HDMA/raster boundaries and
unsupported-mode fallback. A general indexed mode1 first implementation can
be useful, but eligibility must be state-based and common across games.

The current decision is research first, implementation after ownership and
compiler interactions are bounded. Hardware capability remains unresolved;
full-screen coverage is an opportunity for work rejection only when the actual
priority/transparency/state proves it. No ability prediction or omitted frame/
sample is needed to pursue these mechanisms.
