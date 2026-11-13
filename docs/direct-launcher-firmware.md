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
separate success frame precedes the sync and shutdown calls. These are the
display events for a Vesper progress bar. The Vesper design is a visual
prototype. The live updater still draws the original interface.

The original card frontend and init are preserved by hash in the private
staging archive, along with the previous one-shot launcher. The verified
prior firmware and its update package remain available for a board rollback.
