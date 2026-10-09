# FAT repair need verified — 2026-10-09

Subsequently approved and completed: [FAT recovery](fat-recovery-2026-10-09.md).
This document preserves the read-only pre-repair verification.

At 10:22 America/Chicago, a new read-only check of the connected D: confirms
label `DIIUM D-R35`, serial `11EB-1465`, and FAT32. **Filesystem repair/recovery
is needed before further installation or re-arming.** Approval remains pending.

`chkdsk.exe D:` ran with no repair flags and exited 3. It repeats the earlier
invalid first allocation units for `game-a27f1c7a-3145728.srm.bak` and
`last-session.txt.bak`, plus 1,472 KB in 14 recoverable lost-chain files. Its
initial `Access is denied` line does not prevent the subsequent full check.
The report explicitly says errors were not fixed because `/F` was absent.

Independent `System.IO.File.ReadAllBytes` calls on both backup paths also
fail with Windows error 1392, "The file or directory is corrupted and
unreadable." Current SRAM reads successfully but is zero bytes. Stock
`retro/showlogo` still matches SHA256
`436d8018808b150c926274575a195f664e61db646f44713371019e9ae10caf3b`;
game and lab one-shots are unarmed.

[Microsoft's CHKDSK documentation](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/chkdsk)
warns that an unlocked active-volume check can report spurious errors.
Here, the repeated specific metadata findings are corroborated by separate
file-read failures on exactly the same entries. The conclusion does not rely
on a dirty flag, generic repair prompt, zero-length files alone, or a single
lost-chain report. This is an OS/filesystem-level verification, not a raw-sector
FAT audit or a physical flash-health test.

No repair, restoration, splash installation, or re-arm was performed. The
verification commands made no intentional card writes. Read-only CHKDSK does
not recover lost chains even when its output describes recoverable files.
The earlier private readable-file backup remains the preservation baseline;
it is not a raw image or proof that all lost data is recoverable.

The audio descriptor failure remains unresolved. These results do not show
that FAT damage caused it, that the card hardware is defective, or that repair
will restore the latest SRAM or missing PCM records. The feathered Vesper
splash remains qualified offline and uninstalled.

Resume at the [existing recovery approval gate](handoff-2026-10-09.md): after
explicit approval, preserve lost chains during narrow FAT repair, inspect
recovery before restoring older progress, and require a clean read-only report
and complete strict archive before installing or arming anything.

Selected metadata-only evidence:
[CHKDSK report](../evidence/2026-10-09/fat-verification/chkdsk-read-only.txt),
[independent reads](../evidence/2026-10-09/fat-verification/file-read-results.json),
[markers](../evidence/2026-10-09/fat-verification/markers.json).
Private originals: `device-evidence/fat-verification-20261009T152254Z/`.
