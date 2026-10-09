# Device survey suite 2

Survey1 returned partial captures and new FAT directory damage. Its521 missing
nonempty files match all521 recovered chains and17,856 KB of lost allocation.
All789 readable files survived the approved repair unchanged. Do not rearm the
old release. [Return and exact next test](device-survey-1-return.md).

Survey2 replaces hundreds of capture files with one indexed CRC32 bundle and
one report. It checks returned range integrity and refuses init restoration on
unhealthy FAT.21 software checks pass; its physical durability remains pending.

Ben requested a broad reusable device investigation suite. The first deployed
profile is passive inventory, using the proven SD `/usr/retro/init` route. It
answers the firmware/splash question while collecting the wider platform map.
It does not execute copied NAND utilities, load/unload drivers, open raw device
nodes, issue ioctls, change USB modes, mount filesystems, change clocks, operate
display/audio, or modify firmware. It writes its own evidence to the card.

## Executable passive coverage

| Group | Captured evidence | What it can establish |
|---|---|---|
| Identity | Boot ID, kernel/version, CPU, boot arguments, RAM, interrupts, CPU counts, mounts/mountinfo, modules, partitions/MTD, devices, filesystems, iomem/ioports, swap/slab/buddy data | Actual runtime identity and exposed resource map |
| Boot tools | Init scripts, inittab, SD mount script, sysinit, power/watchdog/showlogo, BusyBox, NAND utilities | Exact startup/utility code for offline examination |
| Firmware storage | SPI modalias/uevent/DT identity, driver links, block sizes/major/minor/RO/removable state, MTD metadata; exact NAND module candidates | Exposed storage driver/peripheral identities; not a proven flash protocol |
| USB | UDC registration/state/speed, gadget directory metadata, USB VID/PID/product/uevent | Whether Linux exposes an actual controller/function; not boot-ROM recovery |
| Device tree | Raw binary properties and optional FDT | Declared peripherals, compatibility strings, register/memory regions |
| Devices/processes | Device-node metadata, process comm/status/maps/exe/fd links, ALSA/input/fb/TTY/RTC information | Owners and available interfaces; device metadata does not access the peripheral |
| Power/clocks | Available CPU-frequency/governor attributes, thermal temperatures/types, power-supply/hwmon measurements | Which measured values the running kernel offers |
| Module/runtime inventory | Bounded `/bin`, `/sbin`, library/runtime/module trees; `.ko` and module metadata copies | Offline ABI/import/driver examination; a file or DT declaration is not usable hardware proof |
| Final sample | Uptime, CPU counts, memory and interrupts again | Changes during the diagnostic, not an idle baseline or game-performance result |

The survey prioritizes boot/NAND tools, storage, USB and device tree before the
larger module census. It has a **30-second scheduling budget, 48 MiB aggregate
capture limit, 8 MiB per-file limit and 2,500-job limit**. Text/metadata captures
use smaller limits. Each regular-file read runs in an owned child with a maximum
two-second deadline using kernel `SYS_clock_gettime` and relative nanosleeps.
Only that child is killed on a timeout. An unreaped kernel-blocked child stops
further reads and is reported; it cannot be made safe by a stronger signal.
Directory enumeration/metadata and final sync are outside those per-read child
deadlines, so this is not an unconditional wall-clock guarantee against a wedged
filesystem. No conflicting display owner is started by this suite.

The collector refuses FIFO/symlink/device-leaf reads and `/proc/kcore`/`kmsg`.
It follows named sysfs class/bus directory aliases only to regular attribute
files. It does not recurse through mounted SD contents, ROMs, saves, or arbitrary
home/account files. Kernel metadata and vendor binaries are still private.
Proc process races and absent interfaces are recorded explicitly.

## Build and software qualification

```powershell
python build/check-device-survey.py
```

This builds against the exact device glibc 2.30 ABI and publishes owned release
files under `releases/device-survey-2`. The current21 checks cover native and
actual ARM capture of independent NAND/module/device-tree fixtures, byte and
source preservation, bounded truncation, denied raw-device/symlink/kcore/FIFO
reads, stalled-read deadline/reaping, exact firmware BusyBox with a sparse PATH,
marker consumption/second-boot no-op, byte-exact hook removal, stale/truncated/
failed-run analysis, and ELF version requirements no newer than glibc2.30.
Native/ARM600-property fixtures verify the two-file output layout; the analyzer
rejects missing old captures, corrupt/torn bundle ranges and extra bytes.

The fixtures exposed32-bit stat/readdir inode overflow under ARM/QEMU on NTFS;
the collector now uses explicit stat64/readdir64 and the device's exported
glibc2.30 compatibility entry points. Host tests are not hardware qualification.

## Install, collect, restore and repeat

The guarded manager accepts only the inspected D: volume, exact restored init
and qualified SD splash hashes. It checks current FAT health, verifies source/
release hashes, archives every MVP/save/state/lab file plus prior probe artifacts,
and checks protected hashes after changing only its directory and init hook.
The arm marker is written last. Any failed installation removes its marker and
restores exact init; partial owned files remain for inspection.

```powershell
python build/manage-device-survey.py install
# Safely eject, cold boot, leave the stock launcher alone for at least45 seconds,
# then use the physical power button and return the card to Windows.
python build/manage-device-survey.py collect
python build/manage-device-survey.py restore
```

The hook starts the survey in the background; stock launcher startup continues.
The marker consumes before work and syncs. A subsequent reboot is stock even
when the previous run was incomplete. `collect` is read-only and always preserves
partial evidence. `restore` archives again, requires healthy FAT, consumed/unarmed state and
the exact installed init hash, restores the saved original, and preserves results.
The installation receipt and each private return archive contain exact hashes.
Wait for completion before return; powering off during SD capture is not a
durability test. Collection verifies run-marker identity and wrapper completion.

For a deliberate repeat after collection and restoration:

```powershell
python build/manage-device-survey.py rearm
```

Rearm takes another strict archive and health check, hash-verifies all prior
owned captures, checks the resolved card directory before removing it, deploys
the qualified package and assigns a new run ID. It never reruns another test
marker or overwrites uncollected evidence.

## Offline interpretation

```powershell
python build/analyze-device-survey.py device-evidence/YOUR_RETURN/device-survey
python build/review-device-survey.py device-evidence/YOUR_RETURN/device-survey
python build/device-test-catalog.py
```

The analyzer creates a source-to-capture SHA256 map and groups missing, failed,
truncated and successful reads. A complete tail alone is insufficient: capped
or failed/truncated reads, stale marker identity or wrapper failure stay visible.
An interface missing from a supported path is a negative result at that path,
not proof that the physical device lacks the capability.

Offline review uses readelf/objdump and string extraction on up to32 private ELF
captures, prioritizing NAND and boot helpers. It never executes vendor binaries.
It records tool errors and capped disassembly. NAND utilities in our older root
copy reference `/dev/{app_nand,data_nand,hal_nand}` and vendor NAND module paths;
their code also contains module-loading and storage operations. Their names
are not sufficient grounds to run them, even with a seemingly harmless option.

## Active tests and remaining discovery

`device-test-catalog.py` indexes19 questions with execution status. The passive
suite is new; the following owned active programs already exist and have their
own physical results and guards. They are not automatically rearmed:

| Experiment | Existing implementation / contract | Next evidence needed |
|---|---|---|
| CPU/NEON/memory costs | [Lab1](platform-lab.md), [Lab2](platform-lab2.md) | A specific bounded workload and actual device measurement |
| Timers/readiness | Lab2 kernel-clock and PCM readiness comparisons | Account for observed libc-clock divergence and coarse relative waits |
| Display/scaler/scanout | Lab1/2 and [ownership contracts](boot-and-hardware-contracts.md) | Stop stock owner, retain chunk buffers, join workers; physical presentation remains separate |
| PCM continuity | MVP1.18 native PCM owner/fault history | Audio is unresolved; inventory is not an audio fix or proof of clean playback |
| Input | Stock-derived mask references and MVP physical controls | Deliberate physical button test; no guessed mask conventions |
| Persistence/shutdown | Current fsync/rename/save contracts and [FAT recovery](fat-recovery-2026-10-09.md) | Graceful exit/return and fresh identity; do not induce corruption |

USB recovery keys, flash readback/repacking/writes, unqualified GPIO/SPI/I2C
transactions, GPU/DMA jobs, suspend/power/watchdog experiments and clock changes
require first recovering the interface and owner. No speculative command or
unbounded stress test is bundled into the passive boot. These remain concrete
discovery entries in the catalog rather than fabricated working test modules.

Persistent replacement of the internal second splash remains the objective.
The qualified Vesper SD animation already works physically after both stock
screens; replacing internal `/showlogo` needs an earlier persistent image path.
This suite supplies the next evidence for that path. The static logo is separate
and its owner remains unknown.

## Installed second physical run

Private baseline: `device-evidence/snes-mvp-return-20261009T182253Z`.
51 MVP/progress files,49 lab files, stock binaries and splash are hash-preserved.
Independent readback and post-install read-only CHKDSK pass. Passive survey is
armed; SNES, hardware lab and Vesper markers are unarmed. See the public
[installation receipt](../evidence/2026-10-09/device-survey-return/installation-2.json).
Physical execution is pending. Return collection/restore is the next step.
Use `collect` and inspect filesystem health first; restoration now refuses writes
on a damaged card. Full private survey1/repair archives preserve recovered chains.
