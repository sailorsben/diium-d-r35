# Matched five-game physical test — 2026-10-16

**Returned, unarmed:** three blocking windows complete; user abort during Star Fox
replay. No matched candidate pairs or Ranger result. See the
[physical return](fivegame-physical-return.md). The installation details below
are historical; do not boot expecting this one-shot to rerun.

**Installed and armed once on I:** source `8ccb0a3`, independently verified
2026-10-16. All 10,758 protected prior files, 27 payload files, two markers,
persistent UART/init and clean FAT pass. Saves and existing evidence are
unchanged; no full backup was created. Physical results are pending.
[Installation receipt](../evidence/2026-10-16/fivegame/installation.json) ·
[Independent readback](../evidence/2026-10-16/fivegame/live-verification.json).

This separately installed **measurement experiment** compares presentation
policies across all five inspected gameplay scenes. It does not promote the
rebuilt core as a generally fixed or physically performance-qualified emulator.

The corrected core is identical in both arms:
`d7988b2861500eb923b827ad412c14ae841c03dd44e4099f2616a637bf88f62a`.
Ranger's scoped APU rule, HDMA correction and SuperFX full-layout guard are
common to both policies; the test isolates presentation scheduling.

## Exact test

20 automatic epochs,1200 measured gameplay calls each. For each game the
policies are blocking/candidate/candidate/blocking (ABBA). Game order reverses
on alternate passes, so early/late position is also balanced. There are no
artificial CPU burns in this first five-game hardware comparison.

| Game | Scene | Initial state | Native period |
| --- | --- | --- | ---: |
| Super Mario World, PAL backup | Yoshi's Island2 | Qualified private gameplay checkpoint | 19,872,917 ns |
| Super Metroid, translation-labeled backup | Ceres station | Qualified private gameplay checkpoint | 16,688,155 ns |
| F-Zero | Starting grid into racing | Qualified private gameplay checkpoint | 16,688,155 ns |
| Star Fox | Corneria mission | Qualified8656-call cold replay before each measured window | 16,688,155 ns |
| Rendering Ranger R2 | Stage1 | Qualified private gameplay checkpoint | 16,688,155 ns |

The four checkpoints are wrapped with the exact ROM/core identity and payload
CRC; their original private states are untouched. Star Fox deliberately avoids
GSU snapshot continuation. Its unpaced replay generates every emulated frame
and audio sample, but discards callbacks **before native PCM opens**. The
screen may remain still and silent during that replay. Warmup wall/thread CPU
is logged separately and is not counted as a measured gameplay window.

The suite executes24,000 measured calls plus34,624 cold-replay calls. Within
each matched block, core, ROM, starting state, scripted buttons, audio,
frequency policy and diagnostics are identical. Scripted deaths/respawns are
ordinary input outcomes, not proof of a stall or failed comparison.

Policy0 waits for display credit. Policy1 renders into private scratch storage
when credit is unavailable and skips only that presentation. Every emulated
refresh, render and audio quantum is retained. SuperFX uses full-layout core
output and callback copying in both arms. Neither arm replaces queued display
jobs or writes scaler-owned buffers.

## Installation/performance gate

**Measured A7 saving of this rebuilt core: MISSING.** No sustained saving or
20% margin is assigned. The older FFVI physical return establishes a scheduling
mechanism, not the A7 costs of these five games or this binary. The user has
authorized installing this matched measurement test to obtain those costs.

Added costs: the scoped Ranger port-write branch and instruction completion,
the SuperFX callback copy (typically256×224×2 =114,688 bytes per presented
frame), scripted-input observation, frame-boundary CPU/frequency counters,
full bounded native PCM history and end-state serialization after cleanup.
The last operation occurs after audio join/display idle. No per-frame SD log
write or pixel/PCM CRC scan runs in physical callbacks. The exact offline
rehearsal enables CRCs explicitly, and that flag is absent from the boot wrapper.

Break-even requires the measured main/audio/video CPU and nonoverlapped device
service to fit the game's native period; a conservative20% service target is
0.8×period. Audio production must keep pace with consumption, with cumulative
reserve `prime + transferred - hardware_consumed` remaining valid and positive.
Presentation wait is not CPU saving. The expected remaining audio deficit is
**MISSING until this return**; it must be derived from accepted samples,
hardware progress and the complete valid reserve history, not work counts.

Falsifiable result: each successful epoch must complete1200 core calls,
`rendered = submitted + intentional_skips`, scaled/flipped=submitted, exact
final PCM accounting with no remaining/cleared/error, complete trace retention,
valid pointer identities and joined audio/idle display. Blocking controls must
have zero presentation skips. A failed or censored prefix cannot pass a window.
If both arms pass, no performance advantage is inferred from success alone.
If candidate audio fails or its presentation behavior is visibly unacceptable,
do not promote it. Optical cadence, speaker and live input still require human
observation; scripts do not qualify interactive controls.

## Preservation and boot

The owned target is `retro/snes-fivegame1`. The only existing file changed is
`retro/snes-mvp/launch.sh`; two one-shot markers select the experiment and are consumed at startup.
Normal init/UART, stock adapter/core, all original ROMs and saves, prior test
packages and returned evidence are protected by complete hash inventories.
Results and any final state stay under the new package's unique results path.
No firmware update is staged. No new full rollback backup is created.

The pre-install sparse archive is
`a7-pair-before-20261016T185326967290Z`:10,759 existing files hashed, zero new
content bytes stored, FAT clean. The installer rechecks the live card against
that inventory before staging and checks protected/payload hashes and healthy
FAT before staging, after payload readback and after arming. Independent
post-install readback verifies the complete expected file set and both markers.
The previous dispatcher is reconstructible from its existing frozen source;
failed transactions restore its bytes and remove only the new owned markers.

After installation, safely eject I:, insert it with the handheld powered off,
and cold boot once. Allow roughly15–25 minutes; the supervisor's hard deadline
is35 minutes. The game sequence repeats automatically and includes quiet
Star Fox replay intervals. Do not load or overwrite normal saves.

Select+Start aborts. After a normal completion/abort, wait until the stock
launcher is visible, power off, then return the card. An unsafe/forced child
exit holds the wrapper and requires a reboot; its markers are already consumed,
so the following boot takes stock with permanent UART correction retained.
The wrapper waits for active showlogo processes to exit before display ownership
and captures UART/IRQ state before/after.

## Qualification and return

`qualify-fivegame-physical.py` runs the actual controller with an offline-only
pixel/PCM/sample-count oracle from the inspected original gameplay frames,
tests both native consuming-provider policies including forced busy credit,
fault/retry/drain and deficit rejection, checks glibc≤2.30, and exercises firmware
wrapper UART/splash/replay/failure/forced-supervisor boundaries. The exact
installer transaction is checked with success plus six injected rollback/FAT
failures. These are installation prerequisites, not physical acceptance.

The initial native deficit fixture used a19.8805 ms NTSC delay. At Mario's
19.872917 ms PAL period it did not create the intended deficit; that negative
fixture result is retained. The final fixture uses native-period +3.192345 ms
and correctly rejects sustained deficit under both policies. No emulator
behavior was changed to make that fixture pass. The fake-card transaction
also caught a marker-list sorting assumption before any card write; both
installer and independent readback now sort their expected marker sets.

On return, use the sparse collectors before changing or rearming anything.
`report-fivegame.py <archive> --installation <published installation.json>`
binds the installed payload hashes, rejects mock telemetry as hardware proof,
censors invalid native/CPU tails and records bounded results. Keep reserve,
thread CPU, wall waits, intentional skips and user observation separate.

Published receipts are under `evidence/2026-10-16/fivegame/`. ROMs, private
states, binaries and raw device logs remain excluded from publication.
