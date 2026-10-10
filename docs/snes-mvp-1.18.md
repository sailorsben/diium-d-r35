# MVP1.18: reuse tile colors during fragmented raster effects

**Recovered physical return2026-10-09:** Magitek Bio Blast still causes an audio
error and library return. Approved FAT repair recovers the missing session/PCM
reports: reserve erosion and underproduction precede application-pointer
divergence and SETUP/EBADFD. Readable files, snapshots and earlier SRAM survive;
the empty current SRAM is restored from its verified pre-test copy. No controlled
cache-speed comparison exists. [Recovery](fat-recovery-2026-10-09.md),
[next targeted candidate](snes-mvp-1.19.md). The original [return report](snes-mvp-1.18-return.md)
preserves the evidence boundary before recovery.
The following describes the installed candidate and its offline qualification.

[The 1.17 return](snes-mvp-1.17-return.md) isolates a failure during Terra's
Magitek Bio Blast after otherwise sustained gameplay. The game's
[Bio Blast script](https://github.com/everything8215/ff6/blob/813013276c952fdd27edcf7b8b86f17291542cbf/src/btlgfx/attack_anim_script.asm)
moves a circular window, scrolls BG1 horizontally and vertically, and fades its
palette. Edgar's Bio Blaster instead uses BG3 and is a different replay target.

The actual offline Magitek effect reaches 157 renderer updates and 15,579 NEON
tile-row jobs in one frame. Changing window edges splits the work into many
small raster intervals, revisiting the same indexed tiles and palettes.

1.18 adds a 256-entry direct-mapped RGB565 tile cache: 32 KiB pixel data and
4 KiB tags. The key includes indexed-tile identity, palette identity, bit depth
and palette epoch. Materialization uses NEON; hits load prepared RGB colors.
Transparency still comes from the original index, and depth, flips, subscreen,
fixed color and all seven blending modes are evaluated for every drawn row.
Clipped/direct-color/other scalar paths retain their existing implementation.

The indexed VRAM cache's actual `ConvertTile` seam invalidates the corresponding
RGB bucket before decoding. Both actual CGRAM half-write paths flush the old
raster state, mutate its palette, then invalidate derived colors. Brightness
rebuilds invalidate too; state load already uses that rebuild. An epoch wrap
clears old tags. Cache contents are derived data outside serialized game state.

During the matched 162-frame effect window, 1,764,038 tile calls reuse colors and
125,491 materialize them: **93.36% reuse**. Actual palette-lookup row work drops
from 1,957,367 to 1,003,928, **48.71% fewer lookup rows**, including all eight rows
prepared on a cache miss. All 126 pre-existing raster/tile/flush counters remain
identical. These counts are neither a whole-core speedup nor A7 timings.

The [old Lab1 cache](platform-lab-1-return.md) lost to NEON and remains rejected.
It used scalar miss materialization, a separate opacity cache, 128 entries and
whole-tile synthetic workloads with 62.48%/0%/46.86% hit rates. This candidate
uses vector materialization, the original transparency indices, real raster
invalidation and measured effect reuse. That makes another physical test
justified; it does not erase the earlier negative result. Tag lookup, speculative
full-tile materialization and the additional 36 KiB working set can still lose
on the actual A7. The next physical trace must establish the benefit.

Qualification includes independent scalar pixel/depth/math checks, 40,000 cache
invalidation/collision/wrap cases, 131,072 extracted CGRAM half-write cases,
12,000 intro/Narshe frames and 1,200 complete Magitek Bio Blast frames matching
clean-core pixels/native PCM/geometry/periodic logical state. Native audio,
snapshot/retry/drain, FIFO ownership, input, splash and wrapper isolation checks
also pass. QEMU proves correctness/work counts, not hardware performance.

The [offline scene tool](../build/replay-snes-scene.c) uses owner-supplied private
inputs; commands, pictures, PCM and derived states stay local. It is never
installed on the handheld. The qualification scene forces only a private battle
entry, then uses real menu inputs; its background is not the failed encounter.

The installer accepts exact consumed 1.17, archives before writing, preserves
stock, saves, snapshots and all lab files, and creates a separate matched
snapshot header with the original state payload intact. The next test is
[one normal session with repeated Magitek Bio Blast](snes-mvp-1.18-test.txt).
Audio policy, rendering completeness and 1.17 diagnostic isolation remain.


Installed and independently read back2026-10-09 at02:45 UTC
(2026-10-08 America/Chicago). All28 prior private files and49 lab files verify;
stock and boot hook are unchanged. Original snapshot payload is preserved in a
separate core-matched header. Game armed, lab unarmed. Core CRC`1047d56f`,
785,704 bytes; runner SHA256`616755aa…`, wrapper`48b4db70…`, core`4ebbf5ce…`.
Release and checks: [`releases/snes-mvp-1.18/`](../releases/snes-mvp-1.18/manifest.json),
[independent readback](../evidence/verification/snes-mvp-1.18/independent-readback.json).

The retained `narshe-capture.log` describes the earlier private1.16 scene capture
and is historical scene context only. The1.18 effect, extended equivalence and
cache-seam logs are freshly generated for this candidate; no old capture is
used as new hardware or candidate visual acceptance.
