# Vesper boot artwork

The user requested replacing the stock D-R35 loading visuals and supplied the
preferred cyan feathered wing-V with a heart negative space. The final screen
uses that reference: black background, full feathered cyan V, small spaced
`VESPER` lettering and three quiet loading dots inside the heart. The earlier
thin geometric V/green/tagline draft is discarded.

**Installed 2026-10-09 at10:54 America/Chicago** after the
[approved FAT recovery](fat-recovery-2026-10-09.md). The cyan feathered V/heart,
VESPER lettering and18-frame loading-dot animation replace stock showlogo art.
Physical appearance/handoff acceptance is pending. SNES runner/core/wrapper
remain1.18; game and lab one-shots remain unarmed.

Private original and pre-install baseline:
`device-evidence/snes-mvp-return-20261009T155414Z/`. Guarded installation and
independent readback verify patched SHA256
`ab56a67ae629e816a5752b1ad7cec2c335b46c82df84856f8a41376d2f919ebe`,
exact stock bytes outside the ZIP,51 unchanged MVP/progress files,49 unchanged
lab files, intact recovered chains and a clean post-install CHKDSK. An older
whole-card comparison differs in volatile `retro/swapfile`; no immediate
pre-install swapfile hash exists, so whole-card before/after immutability is
not claimed. Preserve its current bytes privately without restoring old swap.
[Installation receipt](../evidence/2026-10-09/vesper-boot-install/boot-installation.json),
[independent readback](../evidence/2026-10-09/vesper-boot-install/independent-boot-readback.json),
[healthy filesystem](../evidence/2026-10-09/vesper-boot-install/chkdsk-postinstall.txt).

## Recovered stock calling contract

Exact owner-supplied `retro/showlogo`: SHA256
`436d8018808b150c926274575a195f664e61db646f44713371019e9ae10caf3b`,198,408 bytes.
The executable contains a ZIP at file offsets `0x7180..0x29bf4`,141,940 bytes,
between `__LogoData`/`__LogoDataEnd` (`0x17180..0x39bf4` virtual addresses).
It loads ZIP entry0 (`ui.raw`) using its own OpenZipU/UnzipItem code.

The sprite table contains19 little-endian16-byte records:
`uint32 offset,resolution; uint16 x,y,x2,y2`. Record0 is the640x480 background.
ShowSprite paints it, then record`frame+1`; frame cycles0..17. Pixels are packed
little-endian RGB565. `joytest` allocates2,808,092 bytes for the uncompressed art.

The new table retains the640x480 background and uses18 small28x10 loading-dot
rectangles. This keeps the ornate feathers static and avoids repeating large
detail regions beyond the embedded ZIP capacity. The full raw payload is
624,784 bytes; the original was1,476,592. ZIP entry0 contains our artwork and
entry1 is inert stored padding that makes the ZIP exactly141,940 bytes.

Only that embedded ZIP span changes. Every instruction and byte outside it,
ELF structure, file size, allocation, display initialization, GPIO behavior,
18-frame loop, `/tmp/vrtemu.log` stop handling, display destruction and
`/tmp/displogo.log` acknowledgment remain exact. The error-screen ZIP and the
separate `retro/resource` are untouched. This replacement affects the stock
showlogo animation on ordinary and MVP boots; it cannot change any earlier
kernel/firmware picture that does not come from this executable.

## Qualification and publication

`check-stock-boot.c` maps the owner's ELF offline, resolves its libc imports,
and invokes the **actual original ARM** OpenZipU/UnzipItem/CloseZipU and
ShowSprite. It does not execute main, touch device nodes, initialize or flip a
display. The final ZIP decodes exactly; all18 sprite frames equal independent
raw-table composition and retain allocation/framebuffer canaries under QEMU.
This checks the real loader/drawing seam, not just our new packer's assumptions.
It is not physical boot appearance or HDMI acceptance.

Authored assets and [qualification manifest](../releases/vesper-boot-1/manifest.json)
are public under `releases/vesper-boot-1/`. The original and patched vendor
executables remain private; no vendor dependency binary is redistributed.

Built-in imagegen was used to adapt the user reference. Final prompt:

> Preserve the full cyan/teal feathered wing-V, sharp downward tip, symmetrical
> silhouette and heart negative space. Compose a4:3 black embedded-device boot
> screen with generous margins and only small spaced pale-cyan VESPER lettering
> below. Keep feather detail legible after RGB565 downsampling; no tagline,
> loading bar or geometric thin-line V.

The generated image is preserved as `artwork.png`; Pillow performs device-size
conversion and the loading dots are code-native overlays. No image/font decoder
or new process runs on the handheld.

## Build, install and rollback

On Windows with the current project Python/Pillow and WSL ARM toolchain:

```powershell
python build/qualify-vesper-boot.py --stock YOUR_PRIVATE_ARCHIVE/boot/showlogo
```

`install-vesper-boot.py` is narrowly guarded to this exact inspected D: and
stock SHA. It requires a saved read-only Windows CHKDSK report showing the
known volume serial `11EB-1465` is healthy, repeats that read-only check at
installation, checks qualification/source hashes,
and archives current MVP/progress/lab/hook plus showlogo before replacement.
It atomically installs the data-patched executable and verifies all protected
files. Init and the1.18 payload are unchanged; no one-shot is armed.

```powershell
python build/install-vesper-boot.py --health-log YOUR_CLEAN_CHECK.txt --stock YOUR_PRIVATE_ARCHIVE/boot/showlogo
```

Use the same command with `--restore` to restore the exact archived stock
artwork. It accepts only the matching installed Vesper hash for rollback.
Do not use the partial damaged-card salvage archive as a healthy install
baseline or bypass its filesystem check.

Next physical acceptance, after repair/install: eject safely, boot normally,
verify full feathers/heart/lettering/loading dots, then correct stock or MVP
handoff with no lingering overlay. Reconnect for hash/log collection. A SNES
audio retest needs its own deliberate arming and fresh failure evidence.

## Physical boot return: Vesper unchanged — 2026-10-09

Ben saw unchanged solid boot and stock animation, then stock launcher. Returned
patched showlogo still has SHA ab56a67ae629e816a5752b1ad7cec2c335b46c82df84856f8a41376d2f919ebe.
FAT is healthy; strict archive snes-mvp-return-20261009T160157Z preserves51 MVP
and49 lab files. SD init does not launch showlogo. Actual early-boot owner is
unverified; offline sprite qualification did not establish executable ownership.
A passive consumed-once probe captures startup scripts, mountinfo and any active
showlogo executable privately. It never launches a splash, signals processes,
controls display or writes firmware. Offline capture fixture and archived device
BusyBox syntax checks pass. SNES/lab remain unarmed; audio remains unresolved.
On next return archive retro/vesper-boot-probe/results first, then restore exact
init.before-probe from the installation receipt. Physical acceptance has failed.

## Actual animation owner captured — 2026-10-09

Second physical test remains stock. Passive capture proves PID447 executes
`/showlogo` from internal root: captured198408-byte executable SHA
436d8018808b150c926274575a195f664e61db646f44713371019e9ae10caf3b
matches stock, not patched SD copy. Source-script capture failed because firmware
PATH lacks tr. Correct filename mapping uses shell case only; capture fixture
passes. Strict51-MVP/49-lab archive and all probe files preserved privately in
`device-evidence/snes-mvp-return-20261009T161740Z`; original init restored exactly
before corrected capture installation. No firmware mutation or audio changes.
Next capture must recover init.rc/init.project.rc and mountinfo to identify a
reversible startup seam. Internal solid-logo owner remains unproven.

## Captured boot route and SD-stage animation test — 2026-10-09

Corrected capture succeeds: init.project.rc launches /showlogo before sleep2,
mounts card /retro at /usr/retro, then launches SD init. Internal rootfs is RAM
rootfs; no firmware replacement is attempted. Captured stock owner and boot
scripts are archived privately in snes-mvp-return-20261009T162604Z. Diagnostic
init was restored exactly. New one-shot launch-vesper-boot.sh signals stock via
/tmp/vrtemu.log, waits for all non-zombie showlogo owners to exit, removes only
the RAM stop marker, launches qualified SD showlogo for3 seconds, signals it,
then waits/reaps its owned child before stock launcher. A release timeout refuses
replacement; an owned-child stall waits rather than starting a competing display.
Device BusyBox syntax and independent dummy-executable one-shot/reap/no-op checks
pass; physical display remains pending. Early solid firmware logo remains stock.
Installer checks healthy FAT, exact init/splash, archives progress and arms last.
No SNES/lab arming or audio change. This is a userspace animation handoff test,
not replacement of the earlier internal boot interval.

## Physical success is an added SD-stage animation — 2026-10-09

Ben observed: static D-R35, animated D-R35, then Vesper. Vesper is physically
accepted as an added SD-stage animation, not a replacement of either stock screen.
Returned startup log reports stock_released=1, owned child484 exit0 and reaped
before launcher. Strict51-MVP/49-lab archive plus complete animation files are
preserved in device-evidence/snes-mvp-return-20261009T163638Z. Marker consumed;
no rearming. The next boot follows stock. Audio remains unresolved.

Captured /init.project.rc starts internal /showlogo before sleep2 and SD init.
The internal executable matches the qualified stock ZIP owner. Replacing that
original animation requires an earlier boot hook or modifying the embedded root
filesystem image; SD init alone cannot change already displayed frames. Rootfs
is RAM-backed at runtime; editing its live copy would not establish persistence.
The static screen asset/owner remains unknown: bootloader or kernel is a hypothesis.
Prior investigation found no registered /proc/mtd partitions. No verified firmware
image/repack/flashing/recovery route is established. Do not flash or claim both
screens can be replaced yet. Next engineering scope is read-only firmware/boot
image inventory and recovery-method verification, not another SD display test.

## Persistent second-splash replacement requested — 2026-10-09

Ben explicitly authorizes discarding/replacing the original second animation.
Preserving its appearance is not a requirement. Current obstacle is persistent
boot-image access: kernel cmdline rootfstype=ramfs; internal init starts /showlogo
before SD init; no registered MTD partitions or verified flash updater/image or
recovery route established. Online D-R35 Plus card-restoration reports do not
establish internal firmware flashing for this unit. No raw-device or flash writes.
Original SD init restored after archived successful animation test. A passive
firmware-route probe inventories proc partitions/mtd/cmdline and device/tool
names, and captures sysinit/BusyBox privately for offline updater inspection.
Device BusyBox syntax passes. It does not open raw devices or touch displays.
Next return: archive probe results, restore exact init, inspect storage/update
owner before deciding whether persistent replacement is achievable.
