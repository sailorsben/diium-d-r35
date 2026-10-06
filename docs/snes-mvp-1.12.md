# SNES MVP1.12: record the PCM stop before cleanup

The [1.11 return](snes-mvp-1.11-return.md) fails after native playback, including
one successful snapshot load/resume. Fresh post-fault state is SETUP and all
three captured failures have a 384-frame application-pointer/count difference.
Its cause is unresolved. This build gathers the missing causal record; it does
not claim to repair the vendor transition.

## Capture contract

- Store the last 96 PCM operations in RAM: kernel-clock time, operation,
  argument/result, state, queued count, pointers, epoch and accepted count.
- Healthy transfers perform no formatting, kernel-log reads or file writes.
  Recording does add a kernel-clock syscall and small memory writes; its
  physical timing impact remains unmeasured.
- On the first sticky PCM failure, freeze the history into an atomic RAM file
  before DROP/close. Successful WRITE records retain the preceding pointer
  observation; subsequent SYNC records carry fresh pointers. This distinction
  is printed in the capture header.
- Read up to 16KiB from the kernel ring with `SYS_syslog` READ_ALL (action 3),
  which does not clear it. Capture bytes or the exact failure errno. No firmware
  `dmesg` executable, `/dev/mem`, tracing configuration or kernel-text recovery
  is needed. Upstream [Linux 4.19 syslog](https://raw.githubusercontent.com/torvalds/linux/v4.19/kernel/printk/printk.c)
  defines this interface; availability/permissions on the device remain pending.
- The wrapper clears stale history, persists the fresh RAM file while alive
  and on exit, and cleans only its PID-owned temporary files. The retained
  `last-pcm-fault.txt` survives in the game folder for the next card collection.

## Qualification and deployment

The actual ARM native-client fixture fills the ring past capacity, proves no
healthy-transfer log file exists, injects a fault and verifies bounded history,
an explicit kernel-read result and capture before reset. Wrapper fixtures prove
stale-history removal and persistence before exit with firmware-style missing
tools. The real FF6 native consuming retry/two-snapshot test and existing
input/display/clock/save checks pass. The unchanged core retains exact-output
qualification. These checks do not qualify physical kernel capture or timing.

The guarded consumed-1.11 updater archives every returned log and private file
before changing runner/wrapper/test notes. Current SRAM, its changed backup,
snapshots, core, stock/hook and lab files are retained. Independent readback
must precede publication. The one-shot is consumed before launch; a following
reboot takes stock. [Test once](snes-mvp-1.12-test.txt); one audio failure is
enough to collect the diagnostic. The next decision depends on whether the
history shows ordinary lead erosion, an unexpected pointer/count change, or an
explicit driver stop reason. Full rendering and continuous sound remain goals.

Installation and independent readback complete at 2026-10-06 04:13 UTC
(October 5 in America/Chicago), after a fresh verified 43-MVP/49-lab archive.
All 22 current private files, including SRAM and its changed backup, original
snapshots, all 49 lab files and stock/hook/core/older wrapper match the protected
hashes. The game one-shot is armed and lab is unarmed. Physical capture and
stream behavior are pending; no new driver fix is claimed.

## Physical result supersedes pending capture

The [1.12 return](snes-mvp-1.12-return.md) fails during playback after a
successful snapshot load. Its final report survives, but the PCM history and
READ_ALL result are missing. The persistence contract above did not hold on
the device. [1.13](snes-mvp-1.13.md) repairs capture durability while retaining
playback behavior; neither release has resolved the native stop.
