# Permanent direct SNES launcher

The handheld booted the direct launcher firmware. The returned boot log
records `direct-launcher-v1` and `/usr/retro/vrtemu`. The card frontend
matches the staged executable. The consumed `retro/update/Code.bkp` was
archived and removed, and Windows reported clean FAT32 after the return.
[Arming receipt](../evidence/2026-11-13/direct-launcher-firmware-arming.json).
[Return receipt](../evidence/2026-11-13/direct-launcher-firmware-return.json).

The D-R35 boots Linux and the Vesper animation from internal SPI. It then
mounts the card's `retro` directory and starts `retro/init`. The normal
supervisor executes its sibling `vrtemu` and restarts it on a watchdog timeout.
The small internal fallback is a separate executable for boots without the card.

The replacement is installed at `retro/vrtemu`, the supervisor's real entry
point. Its SNES route opens `retro/d35-launcher1/libs/d35-snes.so` directly
for raw and decoded SNES content. The one-boot bind mount and v11 adapter
are outside the default path. New and Classic themes, menu music, search
and other emulator routes use the tested launcher package. The selected
core is `70d8851`. This package uses the established stock gameplay audio
writer. The interactive 150 ms trial stopped twice on tick 195 and remains
a separate experiment. [Audio return](starfox-launcher-audio-test.md#handheld-return).

SNES states made through the direct launcher use core-specific names.
The five existing Final Fantasy VI slots still had their original hashes
on return. They use the v11 adapter's 16-byte header and the vendor's zlib
container and thumbnail. Copies with that header removed and the original
thumbnails intact passed the production save-load path in the ARM fixture.
The old and direct paths matched video, PCM and final serialized state
over 120 ticks for each slot with the same ROM. The verified copies are on
I: alongside the five originals. Handheld resume remains to be checked.
[State behavior](stock-shell-prototype.md#what-the-prototype-changes).

## Internal flash change

The board's `init.project.rc` now signals the splash and waits for its display
owner to exit before starting the card init. The no-card path retains its
original internal fallback. The SD init can also wait on the initial boot,
while the previous firmware is still running the updater. This handoff
adds no emulation work. The boot script writes the firmware tag and Linux
boot ID to `retro/d35-launcher1/direct-boot.log` for return verification.

The updater takes a full 8 MiB image and erases only differing 64 KiB blocks.
The sole changed file inside the rootfs is `init.project.rc`. The loader
table holds the updated compressed length. The kernel and UART correction,
device tree, both Vesper screens, fallback executable and all other rootfs
files match the last verified firmware. The original ARM updater exercised
in RAM erases 20 blocks and programs 5,120 pages, including its metadata
in the boot-code block. Replaying the same package on the expected installed
image causes zero erases or page writes. The qualified Thumb loader reads the
exact new initrd length and leaves its load address and kernel entry intact.
[Qualification](../evidence/2026-11-13/direct-launcher-firmware-qualification.json).

## First physical boot

Safely eject I:, insert it while the handheld is off, connect charging power,
and boot. Let the update run to completion. If the handheld powers off at
completion, turn it on again. Check that both Vesper screens appear and
that the New/Classic launcher starts. Launch an SNES game, return to the
menu, and reboot once to confirm the launcher remains the default. The
firmware handoff log distinguishes a board that took the new image from
one that only ran the new card frontend.

On return, archive the card logs and progress before exact trigger removal.
A separate read-only SPI capture can verify the full internal image. The
returned firmware tag establishes that the new board boot script ran.

## Firmware progress display

The update interface runs from the card frontend. The original ARM updater
computes a percentage from the offset of each 64 KiB sector and presents
its 640×480 RGB565 buffer through `DispFrame`. The sector offset advances
after comparison confirms the sector matches the requested image. A
separate success frame precedes the sync and shutdown calls. The Vesper
launcher uses these events to drive its progress bar. It gives the screen
its own chunk allocation, waits for display completion before drawing
again, and shows a failure message if programming fails. The vendor
validation, compare, erase, write, retry, and shutdown paths still run.

The one-boot preview uses that same renderer and a simulated sector count
before the menu opens. It renames and syncs the preview marker before the
first frame. It runs only when the firmware package is absent and it never
calls the SPI updater. It shows 14 frames over about three seconds, then
continues into the launcher. The preview log is
`retro/d35-launcher1/vesper-preview.log`.

The selected menu sounds are M06 Start Line and S07 Leaf Brush. The
former loops through stock mixer channel 0. The latter replaces the two
stock navigation effects at frontend menu call sites on channel 1. Game
audio and the pause menu use their existing paths.

The ARM fixture runs the patched launcher preview entry and the vendor
sector loop against RAM. It checks the successful image, monotonic bar,
failure display and no false 100%, and the Leaf Brush mixer output. The
menu fixture compares Start Line PCM across the loop boundary and exercises
theme switching and save paths. Handheld display and listening remain
the acceptance tests. [Installation receipt](../evidence/2026-11-13/vesper-launcher-arming.json).

## Power off from Settings

Return to the launcher after exiting a game, open Settings, and press Start.
Press A to confirm or B to cancel. The launcher stops the card's active swap
file if present, logs the request, flushes writes and remounts the underlying
FAT filesystem read-only. It checks the actual media mount before requesting
the normal Linux poweroff. If card preparation fails before the remount, the
confirmation screen offers Retry or Cancel. If the remount cannot be verified,
it stops in a visible error state.

The factory button helper polls every 200 ms and requires 11 asserted samples
before asking for poweroff. The installed rootfs has an explicit BusyBox init
table with no shutdown entries. The shipped BusyBox includes unmount and
swapoff actions in its fallback table for a missing inittab. Those are absent
from this installed configuration. The Settings action handles the SD card
before delegating poweroff to BusyBox. The exact point at which the board
removes power remains to be verified on the handheld.

The ARM fixture checks the confirmation, cancel, failed preparation and
request order. The shell fixture checks the card and swap path, remount
command, read-only verification and error handling. After the physical test,
collect `power-off.log`, check the FAT dirty bit and read-only filesystem
scan separately, and confirm the save files still load.
[Shutdown installation receipt](../evidence/2026-11-13/vesper-shutdown-arming.json).

The original card frontend and init are preserved by hash in the private
staging archive, along with the previous one-shot launcher. The verified
prior firmware and its update package remain available for a board rollback.
