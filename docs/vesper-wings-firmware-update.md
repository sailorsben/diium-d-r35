# Wings2 firmware animation update

Ben explicitly requested flashing the new animation before the next UART test.
This update retains the accepted first static Vesper screen and replaces the
second screen's three dots with the [feather-light animation](vesper-wings-animation.md).

## Exact image and qualification

The starting image is the last physically verified installed firmware,
SHA256 `509cdc305deca2654fbf48184eb16d523b4b6cae0effffc4a3cba6845622d9fd`.
Both retained complete8-MiB reads and their run identity are required at staging.
That verification was on October10; staging does not perform a new live SPI read.
No intervening firmware update is recorded in this investigation.

Only the embedded showlogo ZIP changes inside the decompressed rootfs. Every
other cpio byte, including metadata, startup scripts, binaries and duplicate
directory records, stays exact. Recompression produces3,382,648 bytes inside
the existing3,406,558-byte rootfs slot, leaving23,910 bytes. The section length
changes and unused slot bytes are FF-filled. All flash bytes outside that slot
and length field stay exact before the vendor's CRC/time metadata mutation.
The static bitmap, kernel, device tree and compatibility word are preserved.

Candidate SHA256:
`7fda151c788d256c9bacbadeddc76d342b631459c5dea072edd6c0885dce8414`.
Expected full programmed image after vendor metadata:
`5c2f34e6b4451b27fa5e6782f1396d8e6a3bf485e24c0fe209b44854f77660c3`.
Update package SHA256:
`2b78853155c087cfaf3dab730cabbb2dabc757982626da53ddb04cb9dc7bc389`.
Package size5,797,906 bytes. Vendor images/packages remain private.

Twelve checks pass: independent GNU gzip expansion and libarchive extraction;
actual Thumb static-pointer and section-loader execution for baseline/candidate;
actual ARM vendor updater acceptance, incompatible-family/bad-CRC/missing-prefix/
repeated-CRC refusal; original ZIP decoder and all18 ShowSprite frames.
The unmodified vendor programming algorithm performs52 erases/13,312 page writes
against RAM and produces the complete expected image, including CRC/time stores.
Block0 contains vendor metadata and is rewritten by the updater. The baseline
static pixels remain exact even where an erase block must be rewritten.

Six host staging checks cover exact artifacts, wrong-card refusal, actual file
write/rename/readback, filesystem-failure rollback, existing-trigger preservation
and acceptance of the retained full image versus refusal of a different image.
These establish offline contracts; physical flashing/appearance/cadence and
external write recovery remain unqualified for this candidate.

## Staging and next boot

The new installer targets only the designated I: card and requires clean exact
source already pushed, fresh strict archive/FAT verification, normal init,
stock binaries, FFVI ROM, no armed markers, no existing update trigger and the
matching retained installed-image capture. It archives outer-card files too,
retains the baseline/package/expected image privately, hashes all card files
and verifies that only `retro/update/Code.bkp` is added. Windows-owned System
Volume Information is excluded. It changes no init/launcher/progress file.

The device's existing updater performs the actual flash on the next normal
boot. With sufficient battery, safely eject I:, insert it while powered off
and boot normally. Let the update finish without interrupting the progress
screen. If it powers off at completion, turn it on once more. Confirm static
Vesper -> feather-light animation -> stock launcher, then use the normal power
button and return I:. A host staging receipt is not physical flash acceptance.

On return, archive first, collect updater artifacts and confirm the appearance
report. Remove only the exact known trigger after healthy-FAT/hash checks;
do not automatically retry a failed update. A subsequent read-only full-image
capture can verify both passes against the expected programmed hash above.
The earlier UART results remain archived; no UART correction is armed here.

[Preparation](../evidence/2026-10-15/vesper-wings-firmware/preparation.json),
[offline qualification](../evidence/2026-10-15/vesper-wings-firmware/qualification.json),
[staging checks](../evidence/2026-10-15/vesper-wings-firmware/staging-checks.json).

## Staged and independently read back - 2026-10-15

I: now contains the authorized update trigger. Exact source e12c531 was pushed
before staging. Fresh archive a7-pair-before-20261015T054338Z preserves all7,821
retro files plus outer-card contents and baseline/package/expected firmware.
All8,455 existing card files remain exact, normal init stays stock, no armed
markers exist and FAT is clean before/after staging. Only retro/update/Code.bkp
was added. Independent readback verifies its complete ZIP/CRC, all8MiB of the
candidate and unchanged init. Physical update and appearance remain pending.

[Staging receipt](../evidence/2026-10-15/vesper-wings-firmware/staging.json),
[independent readback](../evidence/2026-10-15/vesper-wings-firmware/independent-staging.json).

## Returned update and cleanup - 2026-10-15

Ben reports "Flash worked." Fresh private archive
vesper-wings-return-20261015T055425Z retains7,822 files/1,942,963,405 bytes,
including the exact update trigger. All8,455 pre-stage card paths are present;
only stock swapfile differs. ROM/private progress and normal init verify.
Clean FAT checks pass before/after removal of only the exact archived Code.bkp.
No armed markers or IRQ correction are installed. Post-update full SPI image
readback remains pending; user acceptance is not byte-for-byte verification.
[Return and cleanup receipt](../evidence/2026-10-15/vesper-wings-firmware/return-cleanup.json).
