# Stock menu with an owned SNES loader

## Search and Settings test

The search worker reads the filename, display title and alternate names.
It matches ASCII letters without regard to case and ignores spaces and
punctuation. It keeps the localized initials behavior. The firmware
worker now terminates each full results page before parsing it. The
original code left the page unterminated and could read into old results.
The ARM fixture runs the vendor worker and its list parser against the
card index, including paging, clearing the query and zero matches.

The main Settings tile uses the matching beveled letter from Favorites.
The English settings heading also reads Settings. The artwork hook
changes the two labels in the loaded sprites. The stock assets on the
card supply the same backgrounds and the localized headings.

The installed Star Fox cartridge is the same revision as the successful
Corneria replay. Its SNES list row and global search row point to
`002/Star Fox.sfc`. A first boot should show the Settings tile and
heading, return Star Fox for `FOX` and `STARFOX`, and start the game
from either list. The one-boot test still uses the stock game audio path.

I: is armed for that test. The readback verified all 2,158 files, both
boot markers, the clean FAT32 volume and the existing saves.
[Installation receipt](../evidence/2026-11-10/snes-throughput/stock-shell-search-installation.json).

## Playable launcher preparation

The interactive build uses the same 16-entry core that completed the
handheld Corneria test. It keeps the vendor game list, menu artwork,
locale packs, volume and brightness settings, and the existing routes
for other systems. The stock supervisor opens the launcher at the
usual frontend path. The one-boot hook waits for the splash process to
exit and bind-mounts the candidate over that path for the current boot.
The mount vanishes on reboot.

Star Fox activates the renderer cache and the zoom only for the tested
cartridge revision. Before expanding a changed picture, the launcher
checks that every pixel outside the 226×190 viewport is black. It uses
the full frame when a scene draws into that border. The scaler receives
256×224 in either case. Duplicate detection includes the original
border, so a new HUD pixel triggers a display update. The SNES game
audio uses the stock mixer and output path. The earlier 150 ms native
PCM result came from the separate replay runner.

Offline checks cover five SNES replays, raw and predecoded ROM loading,
stock routes, locale selection, the frame-skip setting, the PCM menu
music loop, and pause-slot file isolation. The firmware shell fixture
executes the one-boot hook with the actual BusyBox mount applet in a
private Linux mount namespace. It covers an absent marker and a failed
mount as well as successful binding. Handheld menu startup, in-game
audio, live controls and returning to the menu remain to be exercised.

At the first preparation, the normal SNES list contained Final Fantasy
VI and Chrono Trigger. The Star Fox cartridge was available in the
replay fixtures.

The four payload files are staged on I: in `retro/d35-launcher1`.
The preparation verified all 2,155 expected files and cleared the FAT32
dirty flag after archiving the returned logs and saves. The initial
preparation left the one-boot markers unset.
[Preparation receipt](../evidence/2026-11-10/snes-throughput/stock-shell-live-preparation.json).

## First prototype

The prototype preserves the vendor's menu code and assets, and uses an owned
libretro launch path for SNES. The device menu, games list, artwork, language
packs, brightness, volume, controller mapping, and non-SNES launchers stay
with the same stock shell. This is a stock-derived prototype, not a source
reimplementation of the entire menu.

The builder accepts only the pinned stock ELF and the qualified profile-guided
SNES core. It adds one read/execute segment of owned ARM code and reserves
zero-filled session storage. It checks the original word at each of 24 patch
sites. No vendor binary or music is published with this repository. The local
prototype was assembled off the card; the card is untouched and unarmed.

## What the prototype changes

- Selecting SNES opens `retro/libs/d35-snes.so` directly. There is no v11
  proxy library between `vrtemu` and the core. The stock supervisor, watchdog
  and device driver are kept. The candidate doesn't remove the boot-time
  `ldpath_launcher` diagnostic or claim that removing it would save gameplay CPU.
- The owned launch path reads the exact raw ROM length or consumes the
  stock archive decoder's owned result. It checks the core's load result and
  rejects unsupported audio or pixel formats. Its environment callback
  avoids the stock `SET_GEOMETRY` out-of-bounds write.
- The 32,040 Hz core audio is converted to the stock 44,100 Hz sink using the
  same continuous interpolation as v11. Reducing the ratio to 178:245 keeps
  signed rounding exact. The stock output backend is still responsible for
  hardware playback. This work doesn't qualify native PCM recovery.
- An unchanged image stays on the screen after a full visible-byte comparison.
  A few byte samples only reject changed pictures early. Changed pictures
  still use ordered stock submission and two chunk-backed buffers. Reusing a
  buffer and freeing the pool fence the driver's display work.
- The language chooser retains all eleven locale packs. English is the default
  for missing or invalid language values; valid existing language preferences
  take priority. In Settings, **Select** toggles SNES **Frame Skip Off / Auto**.
  Off is the default. Auto uses the existing stock lateness signal and leaves
  at least two rendered ticks between skips. The core still runs CPU, input,
  and audio for every tick. The added footer is in English in this prototype.
- The original **Blue Circuit** loop is stereo, 16-bit, 44.1 kHz PCM. It
  replaces the menu's 22.05 kHz MP3 during menu playback, with no live MP3
  decode for the replacement. It uses the stock mixer/volume path and leaves
  menu sound effects alone. The PCM is 2,822,400 bytes in RAM; the stock MP3
  and its fallback remain available. No changes are made to game music.
- SNES state filenames have a core-specific suffix. The pause slot's preview
  and thumbnail append use that same private path. The normal autosnapshot
  thumbnail is suppressed for the prototype's SNES route. Older v11 states
  are not automatically imported. The previous stock state stays available
  on stock boot. Physical save/restore and stock return remain to be checked.

## Offline qualification

Run the patched ELF against the same profile-guided core behind the exact
installed v11 adapter, with simulated display/audio sinks. Each game contributes
1,200 checked ticks. With Auto off, visible RGB565, 44.1 kHz PCM, callback batch
boundaries and the final normalized state match. With forced periods of stock
lateness, Auto matches audio and the normalized state. Intentional render drops
can change the visible sequence, even when an identical image would have been
suppressed later by the display comparison.

| Game | Stock submits | Direct, Off | Direct, Auto |
| --- | ---: | ---: | ---: |
| Super Mario World (PAL) | 1,200 | 862 | 779 |
| Super Metroid | 1,200 | 699 | 677 |
| F-Zero | 1,200 | 1,200 | 1,084 |
| Star Fox | 1,200 | 398 | 398 |
| Rendering Ranger R2 | 1,200 | 1,200 | 1,084 |

The stock and patched dispatch fixtures match on NES, SNES, GBA, GB/GBC,
Mega Drive and PS1 formats, and on the stock arcade GMA and ZIP routes.
The archive dispatch fixture stubs archive I/O; the SNES playback fixture
also checks raw versus predecoded ZIP handoff and closes a core that rejects a
ROM without entering gameplay. These are loader checks, not full-system
compatibility runs for every other emulator.

The stock ARM mixer emits 735 frames per fill, exactly matching the new PCM
after its normal gain adjustment across the 16-second loop boundary. Its
offline mixer runs take less CPU with PCM than with the stock MP3. The
settings fixture verifies locale validation, held Select behavior, file
persistence, display submission, and the isolated state preview/append path.

In three 1,800-fill ARM/QEMU mixer runs per format, median thread CPU was
278.70 ms for the stock MP3 and 182.21 ms for the PCM replacement, a 34.6%
reduction in that fixture. There is no device output call in the timing sink.
The first stock/direct launch pairs saved 1.8–6.3 ms in four fixtures and
lost 7.1 ms in the fifth. Gameplay CPU changed sign in repeated pairs for
four titles. These measurements do not establish a general launch or game
CPU gain; the display work counts are the more useful result for the device
experiment.

Alternating calls within one ARM/QEMU process with two identical core
instances put the direct path 0.2–1.0% slower in the four shorter fixtures
with the display worker omitted. The adapter removal therefore has no
demonstrated steady-state CPU advantage by itself. The count of jobs saved
still tells us which real device work to measure.
[Qualification results](../evidence/2026-11-10/snes-throughput/stock-shell-prototype.json).

## Device measurement gate

The exact repeat check removes 802 of 1,200 Star Fox repacks and scaler jobs in
this replay. A prior physical return put a repack at 0.863 ms of wall time and
the display worker at 0.767 ms CPU per submitted picture in a short opening
window. These clocks overlap and cannot be added as a savings prediction. The
QEMU fixture omits that display worker and runs the exact same core on both
sides. Its launch/steady-state measurements cannot establish A7 savings.

At a repeat fraction `r`, the display change breaks even on CPU only if
`r × (repack CPU + scaler/flip worker CPU) > compare CPU + added fence CPU`.
Measured A7 comparison and fence cost, a candidate's total A7 saving, and the
remaining audio deficit are pending. The existing
[complete-window reserve model](snes-native-throughput-followup.md#audio-reserve-is-a-second-deadline)
defines the 16.688 ms Star Fox target and audio reserve constraint. The
prototype does not yet pass the device installation performance gate.

The next physical experiment should use the exact same PGO core and inputs
on both paths, Auto off. Record complete PCM quota/acceptance/reserve, board
fence and worker cost, launch time, visible image identity and progress hashes.
Check stock return and a non-SNES game. Only then repeat with Auto enabled and
compare the actual dropped pictures and reserve improvement. Boot must wait
for `showlogo` to exit before either path owns display.

## Reproduce locally

Run from the workspace under WSL. Supply the pinned original frontend,
the core from the corrected full-screen test and the local replay fixtures.
Use a fresh output directory.

```sh
python3 build/assemble-stock-shell.py <vrtemu> <16-entry-core> <new-out>
python3 build/make-stock-menu-music.py <new-music-out>
python3 build/check-stock-shell.py <out> <vrtemu> <v11-adapter> <fixture-root> --pairs 0
```

The additional ARM fixtures are `build/check-stock-shell-menu.c` and
`build/check-stock-shell-routes.c`. Compile both with the Cortex-A7 hard-float
GCC toolchain and run under QEMU; the menu fixture takes the patched ELF,
stock BGM, a scratch directory with `d35-menu.pcm`, and `pcm` or `mp3` mode.
The route fixture takes the stock or patched ELF. The local preview WAV is
generated from the same PCM bytes as the candidate music. The card payload
contains the assembled `vrtemu`, `libs/d35-snes.so`, `d35-menu.pcm`
and `build/launch-stock-shell-live.sh` as `launch.sh`. The package directory
on the card is `retro/d35-launcher1`.

## Launcher return and refresh

The November 11 return confirms the interactive frontend was bound for one
boot after a one-second splash wait. Both markers were consumed. Star Fox
was the first recent entry and the installed direct SNES core was
`70d885151b7d3cac05ae69fc9653974c420b49d5cb20f95b09af547f319a8936`.
That is the exact core from the corrected full-screen replay. The live
launcher resamples the core's stereo output and calls the stock writer
at `0xa2cc4`. The corrected replay used the native ALSA worker with a
150 ms reserve and recorded zero underruns. The launcher log has no
in-game PCM telemetry to attribute the reported clicks. Both the
`boot.log` and the `ldpath.err` diagnostic match the pre-test inventory.

The English refresh replaces 88 RGB565 sprites, including 18 illustrated
carousel panels and the library, search keyboard, Settings and in-game
pause screens. The artwork uses original scenes generated with ImageGen in
the stock launcher's dramatic game-cover style. Source-size review excluded
ambiguous hand poses, and the selected scenes were checked again at launcher
size. Both Settings headings have a straight underline. The sprite table,
coordinates, menu actions, language-picker glyphs and file-type badges use
the stock layout. Other locale packs use their stock artwork.

The alternate English pack is 6,195,096 bytes. The stock pack is 6,243,494
bytes. The one-shot hook binds the English pack before the frontend and
unmounts it if the frontend mount fails. The original pack stays at its
stock path on the card. The refreshed PCM is the original **Bonus Round**
loop at 144 BPM, 44.1 kHz stereo, signed 16-bit. It occupies 2,352,000
bytes and the exact stock ARM mixer matches the expected samples across the
loop boundary. Menu music and SNES gameplay use separate audio paths.

Under QEMU, the stock ARM ZIP code opened and decoded all eleven members of
both English packs. The search worker and both Settings load sites passed.
A shell fixture covered marker handling, bind order and rollback. The
stage readback on I: verified the payload and the stock pack, binaries and
private progress hashes. Both one-shot markers were absent when staged.
[Return and stage receipt](../evidence/2026-11-10/snes-throughput/stock-shell-refresh-stage.json).

To rebuild the artwork, use the pinned English pack, the locally saved
ImageGen sheets and their reviewed `scenes.json` manifest, and the local
Bahnschrift font. The manifest is a list of pairs containing the sheet
filename and the zero-based row-major cell index for each carousel entry.
The renderer requires Pillow and NumPy.

```sh
python build/make-stock-shell-art.py <stock-ui_en.bkp> <scenes.json> <font.ttf> <new-art-output>
python build/make-stock-menu-music.py <new-music-output>
```

### Handheld test

With the refreshed launcher armed, safely eject the card and start the
handheld from power-off. On the first boot, check the illustrated carousel,
open Settings and check its underline, listen to the new menu loop, and
search for `FOX` to launch Star Fox. Note any clicking during gameplay.
The interactive launcher uses the same stock game audio path as the
previous launcher test.

After shutdown, the returned log should report
`frontend_bound_for_this_boot=1` and `english_art_bound_for_this_boot=1`.
Both consumed markers should identify the refresh payload commit. A
subsequent boot uses the stock launcher.

The refresh was armed on I: from `ca9c0f2`. Readback verified both markers,
all 2,160 existing files and a clean FAT volume. The only card writes were
the one-shot markers.
[Arming receipt](../evidence/2026-11-10/snes-throughput/stock-shell-refresh-arming.json).

## Familiar platform art and pause screens

The first English refresh boot reported both mounts active and consumed
both markers. The returned inventory differs only in the three launcher
log and marker files and the swap file. The owner reported overlap on
the pause controls.

The replacement English pack keeps the original MAME, Mega Drive and
three Game Boy platform frames. New portraits depict Terra Branford
from Final Fantasy VI, Jin Kazama from Tekken, Chun-Li and Ryu from
Street Fighter, Guan Yu from Knights of Valour, and Terry Bogard from
Fatal Fury. Nintendo's original Super Mario Bros. 3 illustration
supplies Raccoon Mario for the NES frame. The SNES frame uses Nintendo's
North American Super Nintendo Entertainment System wordmark and a
photo of the North American console and controller. The other rebuilt
platform frames use the logos from the stock pack.
[Nintendo's Mario artwork](https://www.nintendo.com/jp/famicom/software/smb3/index.html),
[Nintendo's Super NES artwork](https://www.nintendo.com/us/store/products/super-nintendo-entertainment-system-nintendo-classics-switch/),
[Evan-Amos console photograph](https://commons.wikimedia.org/wiki/File:SNES-Mod1-Console-Set.png).

The pause screens have a plain backdrop. The firmware still paints
the current game preview and any saved thumbnails. The six slot
placeholders now follow the firmware's 86×60 thumbnail rectangles.
The firmware draws P1 and the six live mappings over reserved areas.
The two English help lines sit on baselines at y=452 and y=470, giving
them room at the stock font size. The exact ARM compositor fixture
exercises the controls text positions, all six selection rims and the
thumbnail interiors. The ARM ZIP, search, Settings, state path and
menu mixer checks also pass. The pause changes await handheld testing.

Use `--platform-portraits <reviewed-input-directory>` with
`make-stock-shell-art.py` to reproduce the character panels. Supply
the seven portrait PNGs and the Super Nintendo wordmark and console
PNG. Keep the external artwork and the assembled pack local.

## Settings and theme selection

Press Down past **Restore factory settings** to reach **Frame Skip** and
**Theme**. Press **A** to change the selected value. Frame Skip offers Off
and Auto for SNES. Theme offers New for the refreshed English artwork and
Classic for the stock artwork. Press **B** to apply the theme and return to
the carousel. The choice is saved for the next launcher boot. New and Off
are the defaults. The existing Select shortcut still changes Frame Skip.

The New artwork is available in English. Other language selections use their
original localized packs, and the selected theme takes effect when English
is selected again. A missing New pack falls back to Classic.

The settings hooks read the stock row index at both joystick poll sites.
The two launcher rows use their own selection state and keep the vendor's
row index within its four original rows. The launcher reads older one-byte
frame skip preferences and saves both preferences using a flushed temporary
file and rename. The saved preference changes only after the rename succeeds.

The firmware's locale artwork loader chooses the alternate English pack.
On return from Settings, the launcher waits for display work, then releases
the affected art buffers. The existing lazy-load paths fetch the new theme
as the carousel, lists, search, Settings and pause screens are needed. The
one-boot wrapper binds the frontend and leaves both artwork packs available.

The local package was checked against the exact ARM artwork loader, both
packs, both directions of theme selection, persisted settings, legacy config,
a failed save, held A, the missing-pack fallback and the locale fallback.
Search, pause controls, save-slot drawing, emulator routing and the one-shot
BusyBox wrapper also passed their fixtures. The Settings previews come from
the ARM fixture's actual RGB565 output. Physical display and controls are
pending. [Local qualification](../evidence/2026-11-12/stock-shell-settings-theme.json).

## Six-row Settings artwork

The New and Classic English Settings images each contain all six rows and
the controller guide on the 640×480 canvas. The pack includes selected and
unselected artwork for each Frame Skip and Theme value. The launcher picks
the matching sprite as the user moves or changes a value. The page fits
without scrolling. Older or localized packs use the compatibility drawing
path for the two added options.

Frame Skip uses double chevrons. Theme uses overlapping panels. The icons
align with the original rows and are included in each selected and unselected
sprite in both themes. [Icon qualification](../evidence/2026-11-12/stock-shell-settings-icons.json).

Classic retains the original settings background, first four rows, and
their highlight sprites. The extended panel uses the stock gradient and
bezel. The original yellow, blue, and red buttons sit in a separate footer
with labels beside them. [Classic artwork qualification](../evidence/2026-11-12/stock-shell-settings-classic.json).

The Classic panel, six rows, and controller guide sit 18 pixels higher under
the fixed title bar. The packed row rectangles move by the same amount, so
the firmware's live values and selection blits track the artwork. The New
pack is byte-identical. [Raised Classic qualification](../evidence/2026-11-12/stock-shell-settings-classic-raised.json).

`update-stock-shell-settings-art.py NEW_PACK STOCK_ENGLISH FONT OUTPUT`
builds the revised `ui_en.bkp` and a small `ui_classic.bkp` that contains
only `setting.raw`. The New pack's other members match the prior pack byte
for byte. Classic selects the supplemental artwork only for Settings, so
the other Classic screens continue to load from the original pack.

The pinned ARM launcher decoded both updated assets and drew the expected
row sprites byte for byte for focus changes, saved values and a failed save.
Search, pause layout, slot drawing and emulator routing passed their existing
fixtures. The images were also reviewed at 640×480. The local launcher build
includes both packs. Physical Settings verification is pending.
[Local qualification](../evidence/2026-11-12/stock-shell-settings-artwork.json).

## One-boot theme test

I: was armed with the launcher from `1c02c10`, including the raised Classic
Settings panel and the matching New theme. The card's language is English.
Safely eject the card and boot the handheld once. Open **Settings**, press
Down past **Restore factory settings**, and select **Theme**. Press **A** to
switch and **B** to apply it. Reopen Settings and switch back to check both
themes in the same boot. The following reboot takes the stock path.

The sparse archive retained the logs and private progress and hashed all
2,192 pre-test files. The read-only scan found no errors and FAT32 mark-clean
cleared the dirty flag. Independent readback verified all 2,195 card files,
including 2,188 unchanged prior files, both markers and clean FAT32.
[Arming receipt](../evidence/2026-11-12/stock-shell-settings-theme-arming.json).

### Theme test handheld return

Both one-shot markers were consumed with the expected source revision, and
the wrapper logged a successful frontend bind. A settings file absent before
the test now contains `0N`, meaning Frame Skip Off and Theme New. Settings
writes both values whenever either option changes, and the wrapper logs only
the boot. The file confirms a settings save and the final choice. The sequence
of theme choices and the artwork actually shown remain unobserved in the log.

Star Fox was already first in Recents, and the handheld rewrote that row.
The owner reports clicks during gameplay. The launcher payload opens the same
optimized SNES core, SHA256 prefix `70d8851`, as the successful full-screen
Corneria replay. It sends resampled game audio to the stock writer at
`0xa2cc4`, and its changed-picture path can wait for display completion.
It has neither the standalone runner's native PCM owner and 150 ms prime nor
the FFVI test's nonblocking display-credit policy. The FFVI test preserved
all renders and audio while skipping presentation when display credit ran out.
Both 48 ms burst candidates completed, while both blocking controls failed.
The Corneria replay ran 1,200 ticks with zero recorded underruns. The
interactive return contains no game audio telemetry to locate the clicks.
[FFVI return](presentation-ffvi-return.md),
[Corneria return](starfox-fullscreen.md#corrected-handheld-return).

The next physical audio comparison should hold the Star Fox core, content,
display geometry and Frame Skip Off fixed. Compare the existing interactive
writer against a port of the native PCM path and record accepted samples,
playable reserve and display waits through gameplay and pause/resume.

Read-only collection verified 2,194 files, including all previous saves.
Both markers remain consumed and FAT32 is clean.
[Return receipt](../evidence/2026-11-12/stock-shell-settings-theme-return.json).

The [next one-boot test](starfox-launcher-audio-test.md) ports the native PCM
owner and the FFVI presentation policy to the interactive Star Fox route.
