# FAT recovery completed — 2026-10-09

Later continuation: [animated Vesper boot artwork installed](vesper-boot.md)
at10:54, with clean health and protected-file readback. This document retains
the recovery-completion checkpoint before that installation.

Ben explicitly approved the repair after asking whether it would wipe the
card. At 10:29 America/Chicago, administrator `chkdsk D: /F` repaired serial
`11EB-1465`, label `DIIUM D-R35`, FAT32. The lost-chain prompt was answered
**Y**; Windows preserved 1,472 KB in14 files under `FOUND.000` and exited1
(errors corrected). No format, orphan discard or broad cleanup was performed.
Read-only checks immediately afterward and after SRAM restoration exit0:
**no filesystem problems; no further action required**.

## Preservation and save restoration

Before repair, all412 private backup files (646,926,457 bytes) were rehashed
and compared with the card; all matched. After repair, a new complete private
426-file archive (648,433,785 bytes) verifies source/copy/source hashes, including
all14 recovered chains. **All412 previously readable files are unchanged by
repair.** The two invalid unreadable backup names are no longer in the readable
directory tree. Original archives and recovered allocation slack stay private.

Recovered FILE0008/FILE0010 each contain an8192-byte prefix exactly matching
the known pre-test FF6 SRAM, verified against its earlier collection manifest.
No newer SRAM was identified. The empty current SRAM was preserved privately,
then atomically replaced with that verified prior8192-byte copy, with fsync
and byte/hash readback. This restores the earlier save point; it does not
recover newer progress. Full post-restoration comparison finds **only this
intended SRAM change** among the426 archived files.

The final strict collector verifies51 MVP/progress files and49 lab files with
no read errors. Snapshots, stock/hook and exact1.18 runner/core/wrapper match.
The original showlogo hash remains exact. Game and lab one-shots are unarmed.
The feathered Vesper splash is still qualified offline and **not installed**.

Private recovery: `device-evidence/fat-recovery-20261009T152900Z/`.
Final strict archive: `device-evidence/snes-mvp-return-20261009T153241Z/`.
Healthy installation input: recovery archive's `chkdsk-final.txt`.

## Missing1.18 evidence recovered

FILE0011/FILE0012 contain two finished reports for `503-14018869000`, exact
coreCRC`1047d56f`/785704 bytes. Their counters match; only checkpoint/elapsed
timestamps differ. FILE0009/FILE0013 contain identical27,866-byte PCM text,
matching child503 and the report's fault pointers/capture length. The format
header `PCM fault history1.13` is the diagnostic schema, not the release number.
FILE0007 is historical1.17 and other chains include older diagnostics/WAV;
none are substituted for current-session evidence.

Fresh1.18:2238 calls,59.884 active calls/sec, successful snapshot load, no
intentional holds or duplicates. The fatal audio callback prevents the final
drawing (2237 submitted). Final23 ordinary calls average18.328ms wall and
17.001ms main CPU. Recovered96-operation PCM history reports SYNC_OBSERVE/
EBADFD, SETUP, and three128-frame application-pointer discrepancies. Its matched
large-batch interval produces38,512 accepted frames/sec against44,100Hz, with
reserve erosion before pointer divergence. Kernel READ_ALL returns16,335 bytes.

The audio failure remains unresolved. This recovery restores actual failure
evidence, not playback correctness. It supports the prior production-deficit
model without identifying the vendor pointer-change mechanism, proving FAT
damage caused the audio stop, establishing defective flash, or measuring a
controlled1.17/1.18 cache-speed comparison.

Resume: inspect the recovered actual audio seam before another runtime change.
Splash installation now has a healthy filesystem and complete strict baseline;
use the guarded installer when continuing that task. No SNES test is armed.

Subsequent user clarification: Ben powered down directly from our library after
the audio failure, rather than pressingB to exit to stock. The wrapper's final
card-wide sync waits for process exit; the returned startup record has no normal
library-exit marker. This makes the shutdown/persistence boundary a leading
investigation target, not proven causality: native capture reports checked file
and directory synchronization, and vendor shutdown behavior is not qualified.
The general save helper ignores directory-open/fsync failures. No persistence
fix is implemented, and no blame or physical card-defect conclusion follows.

[Verified analysis](../evidence/2026-10-09/fat-recovery/analysis.json),
[repair log](../evidence/2026-10-09/fat-recovery/chkdsk-repair.txt),
[final healthy report](../evidence/2026-10-09/fat-recovery/chkdsk-final.txt),
[recovered session](../evidence/2026-10-09/fat-recovery/recovered-1.18-session.txt),
[recovered PCM](../evidence/2026-10-09/fat-recovery/recovered-1.18-pcm.txt).
`build/publish-fat-recovery.py` verifies and publishes only identified text and
metadata; raw CHK/slack, SRAM, card contents and vendor binaries stay private.
