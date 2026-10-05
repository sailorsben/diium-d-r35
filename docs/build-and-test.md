# Build, test and recover

The source is published; device libraries, factory binaries, ROMs and personal
saves are supplied separately. The current1.11 installer requires the exact
consumed1.10 Windows D: card. Historical installers have different guarded
baselines; none is a universal factory-card installer.

## Dependencies and pinned inputs

Use Linux/WSL with `arm-linux-gnueabihf-gcc`, binutils, `qemu-arm`, Python3, make and git. The successful development builds used GCC13 with the device's glibc2.30 libraries. Compiler headers are newer than the target runtime, so ARM32 time/file ABI flags and the stat bridge are intentional.

```sh
git clone https://github.com/libretro/snes9x2005.git build/snes9x2005
git -C build/snes9x2005 checkout a79dfe9047e7fec58808aefe48ad2bf499c7af11
git -C build/snes9x2005 submodule update --init --recursive
mkdir -p build/sysroot/lib build/launcher-clock build/clean
```

Populate `build/sysroot/lib` from your ARM device/runtime export with:

```text
ld-2.30.so        libc-2.30.so      libm-2.30.so
libdl-2.30.so     libpthread-2.30.so librt-2.30.so
libz.so.1        libgcc_s.so.1
```

Provide standard loader/SONAME aliases (`ld-linux-armhf.so.3`, `libc.so.6`, `libm.so.6`, `libdl.so.2`, `libpthread.so.0`, `librt.so.1`). `build/build-plus.sh` creates those aliases when building the pinned core. Do not copy x86 host libraries into this ARM sysroot.

Copy your matching factory `retro/vrtemu` to `build/launcher-clock/vrtemu.original`. The input-reference extractor pins its hash to `8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72`. A different firmware needs its own recovered/qualified mask table, not a bypassed assertion.

The current real-core checks expect the exact tested Plus binary at `build/clean/emu_sfc_plus.so`:

```text
SHA256 1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657
CRC32  5ba71d2a
bytes  656816
```

Source builds can differ by compiler and library details; qualify a new binary rather than treating its state files as interchangeable. `build/build-plus.sh` records/builds the pinned source; preserve upstream notices.

The real-core fixture uses a user-supplied FF3/VI ZIP at `build/ff3.zip`, whose expanded ROM is 3,145,728 bytes with CRC32 `a27f1c7a` (not the Rev1 test ROM). No ROM is provided. The functional contract checks do not require redistributing a game.

## Build and checks

The current1.11 workflow retains the exact1.9 A7 renderer/early PCM core and
repairs native observations/resume; see [1.11](snes-mvp-1.11.md). Supply owner-only
output-equivalence inputs first. Do not migrate snapshots for this repair.
The pinned original remains an exact-output oracle. Historical releases and
evidence remain unchanged; no paired device performance experiment is required.

```sh
sh build/build-plus-a7.sh
python3 build/prepare-plus-inputs.py --rom build/ff3.zip --snapshot YOUR_ORIGINAL_5ba71d2a_STATE
sh build/build-snes-mvp.sh
sh build/check-plus-a7.sh
sh build/check-native-pcm.sh
sh build/check-snes-mvp.sh
sh build/check-native-runner.sh
python3 build/check-old-audio-admission.py
python3 build/verify-snes-mvp.py
```

Build flags target Cortex-A7, NEON-VFPv4, ARM hard float, ARM instruction mode, 32-bit time/file offsets and no dependency on a newer stack-protector runtime. Link against the copied device libraries and inspect `out/abi-versions.txt`; current maximum required GLIBC is 2.17, below device2.30.

`glibc230-stat-compat.c` bridges new header function names to ARM32 glibc2.30 versioned stat entry points (version3). NTFS large inode values under QEMU require `readdir64`; otherwise enumeration can silently fail with EOVERFLOW. These are cross-development issues, not proof the device uses NTFS.

The checks exercise:

- Exact Plus ZIP load, 180 unpaced frames and a bounded 30-frame paced run.
- PCM accounting, partial/EAGAIN preservation and independent startup priming.
- Independent ARM32 native PCM ioctl/provider contracts, constrained settings,
  write-driven and explicit startup, verified EBADFD/RUNNING races, rejected
  early/nonrunning starts and parameter mismatch, accepted START-failure
  accounting, asynchronous drain and visible XRUN.
- Actual consumption owner under30ms bursts, partial writes, false readiness,
  event cancellation, fixed admission deadlines and bounded blocked flush.
- SRAM/snapshot roundtrips, incompatible-state rejection and failed-load rollback.
- Library scan, invalid ROM rejection and UI render previews.
- First paint with stuck inputs, independent suppression and repeat.
- Actual main/menu navigation through real timed waits.
- GPIO backend against an extracted, hash-pinned stock callback table.
- Clock-skew/EINTR/expired deadlines and a real ARM relative-wait loop.
- Splash completion before launch, refusal on stuck splash, early error,
  startup timeout, ready-session lifetime and monitor cancellation.
- Real ARM runner killed before cleanup, fresh session/phase RAM checkpoint,
  live audio-worker CPU, and wrapper persistence while its child remains alive.

`verification.json` pins the checked executable SHA256. QEMU behavior does not measure device performance or prove physical audio/display/input. For previews, use the generated PPM images; PNG screenshots from earlier UI review are reference assets.

## Current release and deployment boundary

[MVP1.11](snes-mvp-1.11.md) repairs fresh observations and drain/resume after the
1.10 WRITEI failures. The exact1.9 core and PCM candidates remain. Run
`package-snes-1.11.py --card D:/` only on its exact consumed1.10 baseline.
Archive all returned logs/private progress before updating runner/wrapper/test
notes; retain newly updated SRAM and every existing snapshot/core/lab/stock/hook
file. Arm last. `verify-snes-1.11-card.py --card D:/ --archive LOCAL_INSTALL_ARCHIVE`
checks exact payload, all retained/archive files and one-shot read-only.
`publish-snes-1.11.py` gates immutable publication on matching source/check hashes
and independent readback, excluding all dependency binaries/private progress.
Use [1.11 test notes](snes-mvp-1.11-test.txt), including our snapshot load/resume.
The historical1.10 updater remains guarded to consumed1.9.

The historical1.9 updater requires the consumed Lab2/1.8 baseline, updates four
payloads and creates a separate qualified snapshot. Its publisher/readback
remain version-specific; do not run that updater on a returned1.9 card.

**The 1.6 physical run failed and its returned one-shot is consumed. Do not
re-arm it unchanged.** Read the [failure review](snes-mvp-1.6-failure.md).
The user subsequently requested a logging retry and confirmed stock boot.
[MVP1.7](snes-mvp-1.7.md) ran with the same core/pipeline, fresh checkpoints and
bounded persisted diagnostics. Its [return](snes-mvp-1.7-return.md) saved/exited
without a crash but remained laggy. That return was archived read-only with new
SRAM preserved. [1.8](snes-mvp-1.8.md) trims gameplay diagnostics and optimizes
the A7 renderer. Its [physical return](snes-mvp-1.8-return.md) has clicking and
whole-device power-off; card unarmed, shutdown cause unknown. Its sed-based
capture also failed because firmware lacks sed. Current source uses shell
builtins and passes with both head/sed absent; this repair is incorporated in1.9.
Historical1.7/1.8 bytes and evidence remain unchanged. A new runtime must be
qualified and published under a new version; do not re-arm unchanged1.8.
When analyzing a returned session, supply its actual core via
`analyze-snes-mvp.py --core ...`; stale reports from an earlier core are rejected.

[MVP1.11](../releases/snes-mvp-1.11/) contains our executable and wrapper, without
a ROM, snapshot, core dependency, driver or libc. Build its isolated A7 core
from pinned source; the wrapper selects `retro/snes-mvp/plus-a7.so`. It retains
`/usr/retro/driver.so` and existing `002`/`ROMs/SNES` scanning. The historical
[MVP1.5](../releases/snes-mvp-1.5/) uses the original tested Plus library.

The experiment puts files under `retro/snes-mvp` and runs its wrapper synchronously before stock main. It does not replace stock main, vrtemu, showlogo or driver. A `retro/snes-mvp/armed` marker requests one boot; it is consumed before execution. The following reboot takes stock automatically.

`build/package-snes-mvp.py` prepares a package only after exact-build verification. Its initial installer expects the known original init and current v11 binaries; its updater archives the existing MVP/private progress, writes only owned files atomically, verifies saves/stock/init, then arms. It intentionally targets D: and will reject unknown software. To use it in the original layout, supply your verified original init as `Hardware-Console-v3/init.before`; an already-hooked init is not the original.

That installer describes historical 1.5. Historical 1.6 uses
`build/package-snes-1.6.py`, with the existing hook and original binaries guarded
by hashes, an isolated core and a separately migrated, hash-qualified FF6 state.
It preserves every original private file and arms after verification.

Historical `build/package-snes-1.7.py --card D:/` requires the exact unarmed 1.6
card, verified 1.7 runner/wrapper and unchanged A7 core. It archives first,
updates only owned runner/wrapper/test notes, verifies stock/hook/private
progress and arms last. It deliberately rejects an already-updated/armed card.
`build/publish-snes-1.7.py` publishes selected verification and owned release;
historical publishers reject a mismatched version rather than overwrite releases.

Historical `build/package-snes-1.8.py --card D:/` requires exact returned/unarmed1.7
and qualified1.8 runner/core/wrapper bytes. It archives every private file,
preserves the newly earned SRAM and creates only a separate qualified older
snapshot before arming. Use FF6's **Continue** to play from the new Save Point.
`build/publish-snes-1.8.py` verifies actual qualified input bytes before writing
selected checks and the owned release. Changed source with stale verification
is rejected. `build/publish-snes-1.8-return.py` exports selected read-only return
evidence and source-fix checks while preserving historical hashes; no private
progress or core dependency is exported.

Before any deployment, retain a complete card backup, original init and original/private game progress. Preserve the supplied device's own backups rather than restoring another owner's files. These userspace tests have not changed internal flash/kernel.

## Physical test and collection

Boot the one-shot library. Check Up/Down selection, A/Start launch and B return. In FF6, check **all four directions through character movement**; Left/Right page the vertical launcher list and can be visually ambiguous. MENU or Start+Select opens Resume/Save/Load/Exit. Private progress is under `retro/snes-mvp/saves`.

On reconnect, archive startup/runtime logs, marker state, helper copies, session report and all private saves before updating. Keep new progress. `startup.log` now contains direct kernel/libc/boottime readings and bounded raw pin/error masks. `runtime-platform.txt` locates thread waits. `last-session.txt` reports actual run/audio accounting; it is not a sound recording or presentation counter.

The [1.8 test sequence](snes-mvp-1.8.md#physical-test) is historical; its returned
card was unarmed. Current testing uses [1.11](snes-mvp-1.11-test.txt).
After power-off, prefer fresh `last-progress.txt`/`last-progress.previous`
identity-qualified checkpoints over an older normal-exit report. Retain
`runtime-platform-latest.txt`, `kernel-tail.txt` and `diagnostic-flush.log` too.
The collector copies the whole MVP tree, so these files are automatically archived.

`python3 build/collect-snes-mvp.py --card D:/` performs read-only collection into
a new local archive with source/copy/source hashes. `build/analyze-snes-mvp.py`
analyzes its session histogram and accounting with explicit evidence limits.
These tools do not update or arm the card. `build/export-public-evidence.py`
publishes only selected reports, never the collected private progress.

For recovery, boot again after a consumed marker, or restore the unit's verified original init to remove the test hook. Do not overwrite core libraries or game saves to repair the launcher. A wedged kernel ioctl may require reboot; freeing DMA-owned memory early is not a recovery strategy.

## Historical tooling

Older `install-*`, `prepare-*` and comparison scripts preserve exact experiments and old hash/path guards. Read them as reproducible history first. Re-running an obsolete installer against a progressed card is not supported by their historical success. The maintained MVP sources are `build/snes-mvp/`, its build/check/verify/package scripts and the shared production rendering policy.
