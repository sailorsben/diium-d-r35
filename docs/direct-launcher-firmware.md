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
before delegating poweroff to BusyBox.

The ARM fixture checks the confirmation, cancel, failed preparation and
request order. The shell fixture checks the card and swap path, remount
command, read-only verification and error handling.
[Shutdown installation receipt](../evidence/2026-11-13/vesper-shutdown-arming.json).

On the handheld, the Vesper preview completed all 14 frames, consumed its
marker, and reported no SPI use. The card log records the Settings shutdown
request before the sync and remount. The user confirmed the handheld turned
off by itself. On return, Windows reported a clear FAT32 dirty flag and
read-only CHKDSK found no problems. All five original FF6 slots and all five
direct-core copies match their pretest hashes.
[Physical return](../evidence/2026-11-13/vesper-shutdown-return.json).

The original card frontend and init are preserved by hash in the private
staging archive, along with the previous one-shot launcher. The verified
prior firmware and its update package remain available for a board rollback.

## Illustrated home grid

The English launcher uses the approved 12-tile artwork at 640×480. Start
opens Settings, Select opens Favorites, X opens Search, Y opens Last
Played, L opens All Games, and R opens the local file browser. The same
shortcuts are reachable with the D-pad. A short Power press on Home opens
the existing confirmed shutdown action. The vendor long-press path
remains available. Both English Settings themes place factory reset last.
Other locales and alternate display modes use the stock home path.

The grid delegates to the original menu dispatch. Platform tiles enter the
stock list for the selected platform. The SNES route still loads the pinned
direct core. The installer preserves other emulators, private saves, menu
sounds, splash assets, and the Vesper updater artwork. The vendor frontend
fallback is available if the grid asset is unavailable.

The board update changes `init.project.rc` and the compressed initrd length
in the loader table. The boot script logs `direct-launcher-grid-v2` and the
presence of the SD grid asset. The original Thumb loader and ARM updater
pass offline, with 20 changed blocks and 5,120 programmed pages in RAM.
The original BusyBox passes the splash handoff and no-card fallback cases.
ARM checks cover all grid platform IDs and shortcuts, Settings order,
shutdown confirmation, emulator dispatch and the direct save-slot path.

Boot the handheld with the card installed and charging power connected.
The Vesper progress bar reports the update. After completion, power on if
needed and check Home, the platform and shortcut routes, Settings, and
shutdown. Archive the boot log and progress before removing the consumed
update. A fresh boot tag verifies the handoff script executed, and full SPI
readback is needed for byte-for-byte physical verification.

### Launcher order and shutdown art

The first row starts with Nintendo Entertainment System and Super Nintendo.
The second row starts with Game Boy, Game Boy Color and Game Boy Advance.
The builder reuses the approved art and updates the tile labels. The ARM
fixture exercises the stock dispatch ID for each position. The revised grid
asset carries a version marker so the new frontend rejects a mismatched tile
order and falls back to the stock menu.

Home and Settings share six antialiased shutdown panels in each theme.
The launcher loads one theme when the dialog opens and releases it on
Cancel. The existing card flush, read-only check, retry, and Linux shutdown
sequence still run. The ARM fixture checks actual RGB565 pixels for the
confirmation, in-progress and secured frames alongside the input and
shutdown call sequence.

The stock display extension drew its battery icon over the selected
system. Home now reserves header space and draws the current ADC band
there. It bypasses only the stock battery paint while Home is active.
The ordinary display extension and low-battery warning path still run
outside that drawing scope. The indicator uses bars for the measured
bands. The existing ADC value cannot support a calibrated percentage.

Esc uses the dedicated physical pin and opens the Power Off dialog on
Home. In the stock launcher menus, it sends the same Back event as B.
The input hook checks the pin because the vendor mask is also shared with
Start plus Select. Movement on Home submits Leaf Brush directly to the
stock mixer, without relying on the presence of a vendor effect buffer.

The card update consists of both copies of `vrtemu`, the versioned
`home-grid.rgb565`, and `power-dialog.rgb565`. These changes require no
additional SPI flash. Preserve the status of the previously staged
`Code.bkp` until the handheld boot log has been collected.

### Single-row compact Home

The 640×480 Home keeps the 12 illustrated platforms, makes each tile
11 px taller, and reduces the footer from 78 to 45 px while increasing
the label font from 15 to 18 px. Start opens Settings, Select opens
Favorites, X opens Search, Y opens Recent, A opens the selected platform,
and Esc brings up the confirmed Power Off dialog. The D-pad stays on
the tiles. L and R still open All Games and Browse Files.

The D354 grid and both launcher copies replace the card frontend for
ordinary boots. The returned `direct-launcher-grid-v2` record establishes
that the board already runs this handoff. The installer archives the
returned logs, saves, and exact used `Code.bkp` before removing that
trigger, and verifies the full card inventory after updating. The
internal image, direct SNES core, Settings packs, and menu sounds are
unchanged. The ARM fixtures verify tile navigation, direct shortcuts,
both shutdown themes, audio cue routing, and existing emulator dispatch.
[Qualification](../evidence/2026-11-13/compact-home-qualification.json).

### Battery display and pause menu

Use **Settings → Battery display** to switch between **Bars** and **Est. %**.
Bars is the default. The Home header shows one of five approximate
levels, `~90%`, `~70%`, `~50%`, `~30%`, or `~10%`, from the existing ADC
bands. It uses the lightning icon when the stock charging flag is set.
The percentage is a display preference for the English launcher. See the
[ADC measurements](stock-battery-trace.md) for the limits of the readings.

Load State enters the first occupied slot in slot order. Release A after
opening the menu, then press it again to load. The top preview shows the
selected save's screenshot or a placeholder when the thumbnail is
missing or unreadable. The vendor file begins with a four-byte compressed
state length, followed by that many state bytes and then the thumbnail
stream. Five returned direct-core saves confirm the offset and contain
153,600 decompressed bytes, with the 190×142 preview at the start.

English Controls uses the right side of the pause menu for the player and
mapping selector. L2 + R2 has a text area below the A/B mappings. The
stock joystick editor still owns mapping changes and saving defaults.
[Qualification](../evidence/2026-11-13/launcher-pause-battery-qualification.json).
