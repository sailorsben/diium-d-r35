# D-R35 game loader on the current card

The I: copies of `retro/init`, `main`, `vrtemu`, `ldpath_launcher`
and all three SNES libraries match the archived binaries by SHA256.
The recent Star Fox test's markers have been consumed. Normal startup
takes the vendor menu path, whose SNES entry point is the project's
older v11 adapter.
[Card and execution evidence](../evidence/2026-11-10/snes-throughput/stock-loader-audit.json).

## Boot and game selection

```text
internal Linux
  -> SD retro/init
       -> ldpath_launcher checks ldpath_check.so and logs
       -> optional one-shot test when snes-mvp/armed exists
       -> main forks and execs its sibling vrtemu
            -> run_game chooses by extension or inspected ZIP contents
                 -> Snes_Load opens /usr/retro/libs/emu_sfc.so
                      -> v11 adapter opens emu_sfc_plus.so
```

The name `ldpath_launcher` refers to a library-path diagnostic. Its
source and binary open `/usr/retro/ldpath_check.so` and log success
or failure. `retro/init` exports the library search path and launches
`main` itself.

`main` at `0x106d4` derives the sibling path from `/proc/self/exe`,
creates a 460-byte SysV shared-memory region with key 1234, and forks
and calls `execl`. It checks the heartbeat at offset four, requests a
16,666 µs sleep between checks, and runs `killall vrtemu` and starts
another process when the counter stalls past the configured budget.

In `vrtemu`, `run_game` at `0xa5c68` uppercases the extension and
uses `GetCoreIndex` at `0xa5b28`. The exact table returns 2 for SMC,
3 for FIG, and 4 for SFC, with the same SNES bit. ZIP uses its own
route. The disassembly shows that route inspecting entries and
calling the archive extractor before dispatching. The host also has
a generic `Core_Load` route for table-specified libraries.

## SNES load and lifecycle

`Snes_Load` at `0xa4f54` builds the fixed `retro/libs/emu_sfc.so`
suffix under the SD runtime prefix and calls `Load_Proc1` at
`0xa3fb8`. The binary opens it with `RTLD_NOW` and resolves video
refresh, audio batch, input state, environment and input poll, then
calls `retro_init`. The shared load helper supplies path, data and
size to `retro_load_game`. Its raw file path rounds the size up to
a four-byte boundary. Its archive handoff uses already-decoded memory
and the decoded length.

`Load_Proc2` at `0xa426c` resolves `retro_get_region`, `retro_run`,
`SetDoubleBuffer` and `SetFrameSkip`. It selects nominal 50 or 60 Hz
from the region before calling `retro_run` in the gameplay loop.
The exact loader fixture intercepts entry to that loop and exercises
raw and predecoded archive inputs. A missing `retro_load_game` symbol
blocks entry. A present function returning false still reaches the
loop, because `run_process` checks symbol presence and ignores the
callback's return value.

The exact environment callback at `0xa2fc8` also writes the double
44,100 at byte offset 32 for `SET_GEOMETRY`, past the end of the
20-byte libretro geometry object. The fixture reproduces the write
inside an oversized guarded buffer. The installed adapter handles
that callback itself.

## Core selection under the existing menu

The installed `emu_sfc.so` is the 22,868-byte v11 adapter. It checks
`D35_PLUS_CORE`, then its sibling `emu_sfc_plus.so` and uses the
fixed device path when it cannot construct the sibling path.
`emu_sfc_orig.so` is present as a backup. The normal loader points to
the v11 adapter. The earlier native Star Fox one-shot used its own
runner and Plus ELF.

In ARM/QEMU, the exact installed adapter loads the installed Plus
core, the newer combined core and the profile-guided build. Each
completes 1,800 FFVI calls through the adapter's 44.1 kHz path.
The combined and profile-guided builds match all 1,324,600 captured
stereo PCM frames, the callback batches and the captured frame 1,799.
This uses the heap video fixture with adaptive drawing disabled.
The stock-menu override therefore has an offline loading seam.
Actual panel and audio timing and old save-state import remain open.
The v11 envelope carries a fixed `a79d` tag even when the override
selects another core, so a saved state's identity needs a separate
compatibility check.

Reproduce the vendor-side results with
`build/check-stock-snes-loader.sh <matching-vrtemu> <new-output-dir>`.
It executes selected instructions from the pinned ELF in a separate
ARM/QEMU process, intercepting core opens, symbol resolution, initial
device hooks, ROM I/O and gameplay entry. The separate SPI bootloader
has its own verified parser and section-loader analysis.
[Firmware loader analysis](firmware-offline-qualification.md).
