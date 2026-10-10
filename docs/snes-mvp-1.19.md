# MVP1.19: prepare only visible color rows

**Physical return2026-10-10: Bio Blast still fails with native EBADFD/SETUP.**
The one-shot is consumed; clean FAT, completed B/library exit, wrapper flush
and unchanged progress verify. Near-fault audio production remains about12%
below the sink. Offline color-work savings have not fixed sound. Keep this
release unarmed; attribute the actual expensive phase before another change.
[Returned evidence and limits](snes-mvp-1.19-return.md).

The recovered 1.18 Bio Blast return has a real production deficit: matched
large-batch anchors produce 38,512 accepted frames/sec against the 44,100 Hz
sink. Audio reserve erodes before the application pointer advances in three
unexplained 128-frame steps and the stream enters SETUP/EBADFD. Neither a larger
buffer nor a hidden restart fixes that deficit. The [recovered evidence](fat-recovery-2026-10-09.md)
supersedes the original missing-report boundary.

1.18 materializes all eight rows of an RGB tile before checking transparency
and depth. Its actual Magitek replay includes 532,405 empty/rejected NEON rows
across the 162 expensive effect frames. 1.19 tests index/depth visibility first,
then prepares only the requested color row. An eight-bit row-valid mask shares
the existing bit-depth tag; cache storage remains exactly 36,864 bytes. Actual
tile decode, palette mutation, brightness rebuild and epoch wrap invalidate
the same keys. Full drawing, color math, flips and native PCM remain exact.

The independently repeated 1.18 instrumented core reproduces all 1,200 prior
census rows. Its effect needs 1,003,928 palette lookup rows; the candidate needs
667,001, a **33.56% reduction**. All other 126 raster/tile/visibility/flush
counters and command-boundary pixel/PCM CRCs match. Row cache requests are
1,957,367 versus 1,889,529 earlier tile requests; per-row tag overhead can offset
some savings. These are work counts, not an A7 speedup or physical audio result.

The scene uses the same private Narshe-derived battle entry and real menu
inputs as 1.18. It includes the complete Terra MagiTek Bio Blast effect, but is
not the exact physical battle background. Shipping-core equivalence separately
checks every frame's visible pixels, native PCM, geometry and periodic logical
state against the clean pinned core. Cache demand tests cover untouched rows,
key changes/collisions and bounded footprint; extracted CGRAM seams check old
palette flushing and invalidation. Runner tests check snapshot loads, retries,
partial writes, consuming PCM, drain and retained fault evidence.

The native audio/controller policy, sampling frequency, wrapper isolation and
Vesper flash images are unchanged. The only runtime change outside the color
path identifies diagnostics as 1.19. A missing candidate snapshot during the
first local runner check was corrected by preparing a separate matching header;
the test then passes. No owner snapshot was overwritten.

The published Narshe capture log describes the earlier private1.16 scene
capture; it is historical fixture context, not a new1.19 visual or hardware
receipt. Unchanged raster-register and old-owner/wrapper regression artifacts
remain retained contract evidence. The shipping-core equivalence, lazy-row
census, cache invalidation and current runner checks are freshly executed.

The guarded installer accepts only exact unarmed 1.18 on the known FAT card,
archives before writes, retains stock binaries and every existing save/state,
lab file and SPI-reader profile, and creates a separate matched snapshot header.
Read-only CHKDSK must be clean before writes and after payload installation,
before arming. Independent readback is required before publication.

Installed2026-10-10 at06:46 UTC and independently read back. Pre-write archive
`snes-mvp-return-20261010T064615Z` retains51 MVP/progress and49 lab files;
installation archive `snes-mvp-1.19-install-20261010T064616Z` records the clean
FAT gates,29 preserved save/state files and27 unchanged reader files. Core
CRC`3d35ed49`,789,764 bytes. Only SNES armed; Code.bkp absent and the verified
Vesper SD artwork/normal init preserved. [Readback](../evidence/verification/snes-mvp-1.19/independent-readback.json),
[work counts](../evidence/verification/snes-mvp-1.19/lazy-row-work-counts.json),
[qualification](../releases/snes-mvp-1.19/manifest.json).

The original [device instructions](snes-mvp-1.19-test.txt) describe the intended
qualification sequence. The returned Bio Blast failure above supersedes its
pending acceptance: sound continuity failed. This build remains installed but
unarmed; do not run that historical sequence again unchanged.
