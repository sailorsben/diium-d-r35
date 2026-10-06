# SNES MVP1.14: own the A7 execution budget

The [1.13 return](snes-mvp-1.13-return.md) showed sustained production near
37k samples/sec against a 44.1k sink. Its repeated 19.8805ms interval needs
about 3.192ms removed merely to reach the native 16.688ms period. This build
changes real execution paths while preserving every complete drawing and
the exact sound stream. Physical performance remains pending.

## What changed

The pinned Plus core now uses Cortex-A7 `-O3`, LTO, hidden internal symbols
and `-fno-semantic-interposition`. Its original `-fno-builtin` restriction is
removed, permitting known memory operations to optimize across modules.
Libretro entry points remain explicitly exported, alongside two owned
phase-accounting functions. The runner also uses O3/LTO. No blanket fast-math
or new permissive aliasing policy is introduced. Emitted ARM code and exports
are checked, rather than assuming the final flags took effect.

A custom NEON decoder expands 2/4/8bpp planar VRAM tiles directly into the
existing 64-byte index cache. It removes data-dependent per-plane table
lookups and branches. Existing VRAM invalidation still controls reuse; no
palette, raster state or completed drawing is cached across frames by this
change. Exact source lengths, blank classification and destination boundaries
are qualified against an independent bitplane oracle. Existing palette/color
math kernels remain. Clipped and Mode7 paths retain their prior behavior.

The frontend's 32,040-to-44,100 converter uses the reduced 178/245 ratio.
Smaller integer products and constant signed division preserve the old
truncation exactly. Phase and the previous stereo sample survive arbitrary
callback boundaries; other rates retain the generic converter. Blargg stays
at its native unity conversion, avoiding an additional Hermite pass.

The PCM owner reuses a successful post-write observation while it still holds
its ownership mutex. Every unlocked device/event wait invalidates that reuse.
Admission still requires a fresh observation after its request. This removes
the duplicate observation between consecutive writes without inventing queue
space or tolerating a stopped stream. Native settings, priming, fatal errors
and complete drain are unchanged.

## Accounting that can answer the next failure

The runner retains the last24 call costs in RAM: call/PCM epoch, sampled flag,
core wall and thread CPU, APU-inclusive and PPU thread CPU, audio/video
callback wall time and audio admission wall time. They accompany final/error
reports and existing once-per-second RAM checkpoints. Healthy PCM history
still performs no card I/O.

One call in64, starting at the fourth call after audio reset/resume, enables
kernel thread-CPU timing around `S9xAPUExecute` and `S9xUpdateScreen`. All other
calls retain the ordinary total/frontend measurements. Sampling prevents
hundreds of clock syscalls on every frame. Sampled calls include observer
overhead and are identified explicitly; they must not be mistaken for normal
worst-case execution. APU timing includes its audio callbacks; it is not an
exclusive SPC/DSP census. SPC execution driven by port reads/writes can remain
outside this region, so residual CPU cannot be called pure 65C816 work.
Audio callback wall time must not be subtracted from APU thread CPU as though
the two were disjoint measurements. Exact field order is in the report.

The phase ABI and sampling on/off behavior run inside output equivalence.
Per-frame records avoid claiming that cheap intro frames price an expensive
post-snapshot scene. The history is bounded; a sudden power loss can retain
only the latest copied checkpoint, while a controlled audio error gets a
fresh final report and durable PCM history.

## Qualification and acceptance

Local ARM/QEMU checks pass1,200 frames of clean-core equivalence across intro
and the returned private snapshot: exact visible pixels, native PCM, geometry
and periodic logical state, normalizing only known rebuilt host pointers.
The suite also checks60,000 planar tiles,8,388,608 color comparisons,
280,000 tile rows,60,000 backdrop/window spans and eight actual converter
cases against the original64-bit arithmetic oracle. Page guards, signed
extrema, arbitrary batch splits and short writes are covered.

Actual runner/owner/native-client checks cover an injected WRITEI failure,
clean retry, two snapshot resumes, complete drain,120 complete drawings and
isolated25ms stalls. A separate consuming44.1k provider replays repeated
19.8805ms production and must expose starvation without hidden re-priming,
frame suppression or accounting loss. This negative check prevents an
initial reserve from masquerading as sustainable throughput.

These establish correctness/lifecycle, not a device speedup. O3/LTO can
increase instruction-cache pressure; the candidate core is785,504 bytes
versus665,040 previously. Its ELF text is631,333 bytes, data22,700 and
BSS691,652. Compiler changes may recover meaningful time or worsen a hot
working set. The decoder helps cache misses, not already decoded tiles.
No claim is made that this bundle alone supplies the required3.2ms.

The physical acceptance is one meaningful gameplay run: sustained expensive
scene at native cadence with enough reserve to absorb jitter, every complete
drawing, uninterrupted sound, working controls, pause/load/resume and normal
save/exit. Provisionally aim for13–14ms main production with remaining
platform work and variation inside16.688ms. If it fails, compare recent
unsampled CPU/wall/admission costs and sampled inclusive regions from that
same run; do not disguise a throughput deficit with a larger initial silence.

## Installation and recovery

`build/package-snes-1.14.py` requires the exact consumed1.13 D: card and
current qualified sources/check artifacts. It archives all returned MVP/lab
logs and private progress before writes, verifies stock/hook/older wrapper,
replaces only owned payload, and adds a separately qualified older snapshot
copy with the new core identity. All original states and current SRAM remain
byte exact. Continue is the current-progress path. Arming is last; the next
boot consumes the one-shot and the following reboot takes stock.

`build/verify-snes-1.14-card.py` independently checks the payload, archives,
all original nonpayload files, protected progress, snapshot payload/CRC and
markers. `build/publish-snes-1.14.py` requires that proof, preserves historical
release/evidence bytes and excludes games, private progress and dependencies.
