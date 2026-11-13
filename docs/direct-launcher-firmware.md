# Permanent direct SNES launcher

I: has the direct launcher installed and `retro/update/Code.bkp` staged.
The complete card readback verifies 2,198 files, 2,194 protected prior
files, the sole firmware trigger and clean FAT32.
[Arming receipt](../evidence/2026-11-13/direct-launcher-firmware-arming.json).

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

Existing game progress is preserved. SNES states made through the direct
launcher continue to use their core-specific names. Older v11 states are
kept for rollback and require a separate compatibility check before use
with the direct core. [State behavior](stock-shell-prototype.md#what-the-prototype-changes).

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

After powering down normally, reconnect I: for archival and exact trigger
removal. A separate read-only SPI capture can verify the full internal image.
The card staging receipt establishes what was copied and armed. Physical
programming and launch behavior are pending the handheld boot.

The original card frontend and init are preserved by hash in the private
staging archive, along with the previous one-shot launcher. The verified
prior firmware and its update package remain available for a board rollback.
