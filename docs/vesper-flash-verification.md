# Vesper post-update flash verification

The later [first static-screen update](vesper-static-firmware-update.md) is now
staged and awaits its own physical/full-image acceptance. This document records
the completed earlier second-animation verification.

The original second-animation replacement is complete: physical boot accepted
static D-R35 -> Vesper -> default launcher, and both full8MiB flash reads match
the intended installed image exactly. Normal SD init is restored, Code.bkp is
absent, no test is armed and the final FAT check is clean. Ready for normal use.

## Verified return and restoration - 2026-10-10

Run `c4a59205933b4459a9d88ed6aafe5dd2` completed in103.776166 seconds with
two full8MiB passes,4,111 operations, CRC32 `3454f3d8` each. Both compare
byte-for-byte with the private expected vendor-mutated image, SHA256
`d20301be923288e6ace49b43dd8cce306855ded8cd961643e5ee14854d9e6f03`.
Consumed run identity, wrapper exit0, repeated IDs/status/settings, bundle length
and CRCs verify. No errors, timeout, unreaped child or flash/configuration writes.

First return archive `device-evidence/snes-mvp-return-20261010T052014Z`.
Restore archives again to `snes-mvp-return-20261010T052230Z`, checks fresh FAT
and exact run/init/rollback identity, then restores original normal init.
Independent direct card reads verify both full captures against the expected
image, normal init against the rollback, reader/wrapper and archived results,
all five stock/runtime hashes and51 protected MVP/progress files against the
pre-update baseline,49 lab files and all9 retained prior-reader files. No armed
markers or Code.bkp; final read-only CHKDSK passes. No FAT repair needed.

The completed init/readback run happened after Code.bkp removal and establishes
boot/rootfs execution without the update trigger. Visual animation/launcher
acceptance remains the user's earlier physical report; this reconnect supplied
no additional visual observation. The first static D-R35 screen is preserved.
External write recovery remains unqualified; the MVP1.18 audio failure unresolved.

[Full-image comparison metadata](../evidence/2026-10-10/vesper-flash-verification-return/verification.json),
[independent restored-card checks](../evidence/2026-10-10/vesper-flash-verification-return/restoration.json).
Raw flash, update packages and private progress are retained locally only.
The installation/procedure below records the completed run, not a new instruction
to re-arm or flash.

## Returned card and cleanup

Initial read-only archive `device-evidence/snes-mvp-return-20261010T050003Z` and
pre-removal archive `snes-mvp-return-20261010T050039Z` preserve51 MVP/progress,
49 lab files, prior probe profiles, root/display logs and the exact package.
All five stock runtime/core hashes match the pre-update archive; all51 protected
MVP/progress files match too. The448-byte boot.log contains no update-specific
records, so visual acceptance remains the user's observation. Fresh FAT checks
before/after removal pass. Only the exact hash-bound `retro/update/Code.bkp` was
removed; cleanup does not revert internal flash or alter normal init.

## Verification installation

Run `c4a59205933b4459a9d88ed6aafe5dd2`, unchanged release
`releases/spi-readback-1`. Private preservation/rearm archive:
`device-evidence/snes-mvp-return-20261010T050947Z`.
Private fresh installation archive:
`device-evidence/snes-mvp-return-20261010T050951Z`.

All9 old reader-profile files were hash-archived and retained intact on the card
as `retro/spi-readback.pre-vesper-e773f6fee1e94fd6b48ac326550280ec`.
No recursive deletion. The guarded helper checks resolved directory-move targets,
old consumed/completed run, init/splash/updater identity, unchanged source/release
qualification and no competing test/update trigger. A fresh legacy install then
recreates the active reader namespace and arms last. Failed installation retains
partial files, restores the original init and puts the prior profile back.

Only status05, ID9f and memory03 reads exist in this unchanged ARM reader;
no erase/program/write-enable/reset/configuration-write commands. It runs
synchronously before stock vrtemu owns SPI0.0. Same qualified wrapper and reader,
new run ID and results. The marker is consumed/synced before capture; the next
boot skips the reader. [Reader/ownership contract](spi-readback.md).

Independent installed readback verifies reader/wrapper/manifest, marker/run,
rollback init, retained9-file profile,51 MVP/49 lab protected files, absence of
the update trigger and only this reader armed. Post-install FAT check passes.

| Artifact | SHA256 |
|---|---|
| Reader | `b0f47d8742b0ef0c1624fd1d25ae3cb8af7474d5c16f2b941c46ced370749a0b` |
| Wrapper | `7efcf6c081dc03b4904ba88d7c22130349a5e477020838dc55c1ae5607fc46b3` |
| Installed init | `012b13133b4a0a76ff4f0939931b67f82dae07405bc72f140e88f4f44085cc02` |
| Normal init / rollback | `b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7` |
| Expected full programmed image | `d20301be923288e6ace49b43dd8cce306855ded8cd961643e5ee14854d9e6f03` |

`build/manage-vesper-flash-verification.py` reuses the original manager without
changing its qualification hashes.8 host checks cover exact expected image,
archive-retaining rearm, failure after arming/rollback, update-trigger refusal,
out-of-parent move refusal and full-byte match/difference/incomplete comparisons.
Those host checks did not establish physical readback; the completed device
return above supplies that separate evidence.

## Historical physical step and return procedure

Safely eject D:, insert while off and cold boot. Vesper may remain animated for
about two minutes while both reads finish; the previous identical reader took
103.771059 seconds. Allow five minutes. Once the stock launcher is stable, use
the normal power button and reconnect D:. If still at the animation after five
minutes, report that state and return the card normally for incomplete-run review.
The240-second child deadline is not a guarantee against a kernel-blocked child.

On return, run `python build/manage-vesper-flash-verification.py collect` before
changes. It archives all progress/results, validates consumed run/completion/
CRC/length/settings/wrapper independently, and compares both full8MiB passes
against private staging `expected-after-vendor.bin`. A mismatch is reported with
differing64KiB blocks and preserved raw bytes; never automatically rewrite flash.
Then `restore` archives again, requires fresh healthy FAT and exact run/init/
rollback identities, and restores normal init. No image or raw capture is published.

Correct expectation includes vendor metadata at0x100/104; unmutated candidate
SHA is not the expected installed image. The completed return above confirms
full-byte equality and init/readback execution without Code.bkp. External write
recovery remains unqualified; MVP/audio unchanged and Bio Blast unresolved.
