# Vesper post-update flash verification

The original second-animation replacement passes the user's physical boot test:
static D-R35 -> Vesper -> default launcher. The returned SD card is now archived,
the exact update trigger removed, and the unchanged read-only reader armed for
full-image verification. This does not stage or perform another update.

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
These new host checks do not establish the upcoming physical readback.

## Next physical step and return

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
SHA is not the expected installed image. Complete full-byte equality is pending,
as is this boot without Code.bkp. External write recovery remains unqualified;
MVP/audio unchanged and the Bio Blast failure unresolved.
