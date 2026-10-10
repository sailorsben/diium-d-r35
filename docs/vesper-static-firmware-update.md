# First static Vesper screen - 2026-10-10

**Both screens physically accepted:** the user reports "Reconnected, flash
worked" and explicitly confirms Vesper static -> Vesper animation -> stock
launcher. First-screen and normal startup acceptance pass. Exact full installed
SPI equality remains pending; appearance is the user's report, not a photo/video.

## Current return and read-only verification

Initial archive `device-evidence/snes-mvp-return-20261010T054957Z` and cleanup
archive `snes-mvp-return-20261010T055009Z` preserve 51 MVP/progress files, 49 lab files,
all prior profiles/root/display logs and the exact package before removal.
Fresh pre/post-removal FAT checks pass. Only the known Code.bkp is removed;
stock/protected progress remain exact. This does not undo internal flash.

Reader run `db7079b5f61b4ee5b7d36d22e58472fd`, preservation/rearm archive
`snes-mvp-return-20261010T055025Z`, installation `snes-mvp-return-20261010T055030Z`.
Reuse unchanged spi-readback-1 with fixed 05/9f/03 operations only. Retain all nine
second-animation-reader files under
`retro/spi-readback.pre-vesper-2ef5b65b19664fbc934a7460000e8eee`; all nine factory
reader files in the earlier parked profile also stay exact. No capture deleted.

Independent direct card reads verify reader/wrapper/manifest, new marker/run and
no stale results, patched init and original rollback, 51 protected MVP/49 lab/
18 retained reader files, pre-update stock/progress hashes, absence of Code.bkp
and only the reader armed. Fresh final FAT passes. No flash or global config
writes. Target SHA is the new expected `509cdc...622d9fd` listed below.

[Physical startup report](../evidence/2026-10-10/vesper-static-verification-install/physical-boot.json),
[archived cleanup](../evidence/2026-10-10/vesper-static-verification-install/cleanup.json),
[reader installation](../evidence/2026-10-10/vesper-static-verification-install/installation.json),
[independent installed checks](../evidence/2026-10-10/vesper-static-verification-install/independent-install.json).

## Next physical verification step

Safely eject D:, insert while handheld off and cold boot. Allow up to five
minutes for the stock launcher; the identical reader previously finished in
103.776166 seconds, so Vesper may animate about two minutes. Once the launcher
is stable, use the physical power button and reconnect D:. If still at splash
after five minutes, report it and return normally for incomplete-run review.
The 240-second child deadline cannot guarantee recovery from a kernel-blocked child.

On that return, run `python build/manage-vesper-static.py verify-collect` before
changes, then healthy `verify-restore`. Both complete 8 MiB passes must match the
new expected image including vendor metadata. Preserve any mismatch, never
automatically reflash. Boot without the update trigger/full equality remain
pending; external write recovery is unqualified and MVP1.18 audio unresolved.
The staging/update instructions below record the completed earlier steps.

## Exact change and qualification

The first screen is a 614,400-byte, little-endian RGB565 bitmap at flash
`0x8854..0x9e854`, 640 x 480 pixels. Decoding the exact slice reproduces the
stock D-R35 Plus screen. Thumb boot code loads RAM pointer `0x02608654` into
display register `0xd05001e0` and dimensions `0x01e00280` into `0xd05002e4`.

The candidate uses the exact background pixels from the accepted Vesper
animation's `ui.raw`, with no loading dots on the first static screen. Every
candidate byte outside that bitmap stays identical to the verified installed
image, including all boot instructions/header, kernel, section tables, rootfs
and second animation. The updater subsequently changes CRC/time words at
`0x100/0x104`, as in the preceding successful update.

| Artifact | SHA256 |
|---|---|
| Verified installed baseline | `d20301be923288e6ace49b43dd8cce306855ded8cd961643e5ee14854d9e6f03` |
| Static-screen candidate | `9f99ec3984f19b38d216cef2cad38eacb2bad9792046900d8fa91262a6e772b9` |
| Expected programmed image, including metadata | `509cdc305deca2654fbf48184eb16d523b4b6cae0effffc4a3cba6845622d9fd` |
| Exact staged package, 5,713,655 bytes | `0012b1016df784ff92d92691d1740b3215bfda005a58b6382aaabffaf5c18b4c` |
| Replacement RGB565 pixels | `82616f0a09e5cb91633dc5eacf2eb1a36216de0f70e0af2375d2681482c91946` |

Ten offline checks pass: the exact Thumb bitmap-pointer/dimension stores and
section loader execute for baseline and candidate; the captured vendor updater
accepts the new WQW/ZIP package and programs RAM to the expected bytes; wrong
family, wrong consistent ZIP CRC, missing prefix and already-recorded CRC are
refused without erase/program; public vendor-image output is refused.
The valid simulation erases blocks `0x0..0x90000`, ten 64-KiB blocks and 2,560
pages, preserving all non-bitmap contents. It writes metadata `17e40b24/5d4a6000`.

The bitmap harness substitutes anonymous RAM for MMIO and stops each instruction
fragment immediately after the target store. It does not execute boot ROM,
GPIO/display initialization or the physical panel. No exact public primary
boot-ROM integrity documentation was identified; its contract remains unknown.
The unchanged header/code and these offline results do not establish physical
acceptance. The existing external recovery limit remains: no programmer or
external write/restore procedure is qualified. The user requested this next SD
update with the earlier no-programmer risk acceptance still in force.

## Card staging and preservation

Run `9cb16d1fda284bdab17d18bc641d7211`, staged `2026-10-10T05:41:55Z`.
Private archive `device-evidence/snes-mvp-return-20261010T054138Z` preserves
51 MVP/progress files, 49 lab files, profiles/root/display logs, all nine retained
prior-reader files, the verified current full SPI backup, package and expected
programmed image before card writes.

The stage guard requires the original normal SD init, exact vendor updater,
consumed complete reader run `c4a59205933b4459a9d88ed6aafe5dd2` with both
passes equal to the installed baseline, no competing test and no existing
Code.bkp. Fresh FAT checks pass before/after staging. All 1,006 original readable
card files stay byte-identical; only `retro/update/Code.bkp` is added. Windows-owned
`System Volume Information` is excluded from that inventory.

Seven host checks cover exact qualified artifacts, wrong-card refusal, actual
staging file operations, poststage health-failure rollback, preexisting update
refusal, a complete-but-different flash baseline, and a competing armed runtime.
Independent direct card reads confirm the entire staged package, current backup,
normal init, pre-update stock/progress hashes, lab/prior-profile hashes, no armed
test markers and another clean FAT report. The update file itself is the vendor
trigger; it is not a one-shot `armed` marker. No host tool wrote physical SPI flash.

Authored [static preview](../releases/vesper-static-1/preview.png).
Curated [preparation](../evidence/2026-10-10/vesper-static-firmware/preparation.json),
[offline qualification](../evidence/2026-10-10/vesper-static-firmware/qualification.json),
[host staging checks](../evidence/2026-10-10/vesper-static-firmware/staging-checks.json),
[staging receipt](../evidence/2026-10-10/vesper-static-firmware/staging.json),
[independent installed checks](../evidence/2026-10-10/vesper-static-firmware/installation.json).
Full images, updater packages/vendor binaries and private progress remain local.

## Historical physical update procedure

1. With sufficient battery charge, safely eject D:, insert the card while the
   handheld is off, and turn it on normally.
2. Let the update finish; do not interrupt an active progress screen. The previous
   update reached 100% and powered off. If it powers off again, turn it on normally
   once; there is no reason to wait ten minutes in an actually powered-off state.
3. Confirm Vesper static -> Vesper animation -> default launcher. Report a different
   order, failed boot or incomplete update rather than retrying the update repeatedly.
4. Once the launcher is stable, use the normal physical power button, then reconnect
   the SD card as D: for archive/trigger removal and full flash verification.

## Exact return procedure

Archive before changing the card. These commands are for the next return, not
another update now:

```powershell
python build/manage-vesper-static.py collect
python build/manage-vesper-static.py unstage
python build/manage-vesper-static.py verify-arm
```

`unstage` archives again, requires clean FAT/protected init and removes only the
exact known package. `verify-arm` archives and retains the consumed prior profile,
then reuses the unchanged qualified read-only reader synchronously before stock
main. It compares both full 8-MiB reads against the new expected image SHA above;
the earlier animation-only expected hash is no longer the target for this run.

After that verification boot and card return:

```powershell
python build/manage-vesper-static.py verify-collect
python build/manage-vesper-static.py verify-restore
```

These wrappers bind the established verification helper to the new expected
image without changing its ARM reader, source qualification or fixed 05/9f/03
commands. Preserve any mismatch/incomplete return; never reflash automatically.
Restoration archives first and checks fresh FAT/run/init/rollback identity.
Physical appearance is accepted by the user's report above; full installed
equality remains pending. MVP1.18 audio unresolved and no SNES test armed.
