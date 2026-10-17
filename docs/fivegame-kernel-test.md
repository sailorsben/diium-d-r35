# Matched five-game test on the verified kernel UART — 2026-10-16

**Installed and armed on I:** pushed source `831d676`. Independent final readback
verifies 10,905 protected files, 28 payload files, exact card file set, both markers,
normal init and clean FAT. Saves/evidence and verified kernel UART preserved. This is a measurement-only test, not emulator
promotion. The firmware UART fix is already physically verified. No flash
package, kernel change, runtime correction module or full backup is needed.

## Matched experiment

Reuse the exact previously qualified `fivegame-suite`, corrected core
`d7988b2861500eb923b827ad412c14ae841c03dd44e4099f2616a637bf88f62a`,
plan, five ROMs, four gameplay checkpoints, Star Fox cold replay, scripted
inputs and expected output oracles. They are all byte-identical to the previous
five-game profile. Native PCM, frequency policy, instrumentation, paired order
and acceptance rules remain unchanged. Both policies use the same fixed core.

Twenty ABBA epochs alternate forward/reverse game order: Super Mario World
(PAL), Super Metroid, F-Zero, Star Fox and Rendering Ranger R2. Each has four
1,200-call gameplay windows, 24,000 measured calls total. Star Fox additionally
replays 8,656 cold calls before each window, avoiding unqualified GSU snapshots.
No artificial CPU bursts. The measured payloads retain the original twenty-epoch
ARM oracle rehearsal, native consuming-provider checks and supervisor proof.

Only boot integration changes: a separate `retro/snes-fivegame-kernel1` profile
uses a kernel-aware wrapper instead of requiring the obsolete module endpoint.
It refuses a present old endpoint/module and captures passive kernel-clock,
IRQ19, serial, modules and boot identity before/after with the same physically
used observer. No module load or kernel/configuration write occurs. These five-
second boundary samples are outside measured windows. The original normal init
and both Vesper screens stay protected. The existing SNES one-shot seam remains
synchronous, consume-first, splash-exit-before-InitVFB, with owned child reaping.

Nine exact firmware BusyBox checks cover syntax, normal/replay, old endpoint,
loaded module, observer before/after failure, active splash and child139/forced72.
Seven installer cases cover success and six write/health rollback boundaries.
This is reuse of a frozen measured binary, not a rebuilt performance candidate.
The original [performance gate and acceptance](fivegame-physical-test.md) still
apply: measured A7 saving and remaining audio deficit are missing; neither CPU
savings nor 20% headroom is claimed. Added SuperFX callback copying and Ranger
synchronization costs remain common to both arms. Break-even requires measured
CPU plus nonoverlapped service within the native period, positive valid cumulative
PCM reserve, exact render/presentation accounting and safe cleanup. Successful
bounded windows alone do not establish sustained playability or speaker/panel
acceptance. No per-frame physical CRC or SD logging is enabled.

## Preservation and installation

Fresh sparse archive `uart-kernel-return-20261017T024736712195Z` hashes 10,906
files, retains zero new content bytes and has clean FAT. No full backup. All prior
profiles/results, both UART verification runs, stock files, saves, original init
and card artwork remain protected. Only existing `retro/snes-mvp/launch.sh` is
changed to dispatch this separate profile. Both owned markers are armed last.
Failures remove owned markers and restore the prior dispatcher. All prior hashes,
payloads and clean FAT are checked before staging, after payload readback and
after arming; a separate checker verifies the final exact card file set.

## Physical procedure

Keep the handheld plugged in. Safely eject I:, insert it powered off, then cold
boot once. Let the sequence run automatically for roughly 15-25 minutes; its
hard supervisor deadline is 35 minutes. **Star Fox cold replay is silent and can
leave the preceding game picture onscreen for several minutes.** This is the
known replay phase, not by itself a crash. Keep waiting and avoid Select+Start
unless intentionally aborting. No new progress UI is added because the measured
controller remains byte-identical.

When stock returns, leave it up briefly, then power off and reconnect I:.
If it has not returned after 35 minutes, power off and return the card; do not
rearm or reflash. Select+Start is an intentional suite abort, not completion.
Report clicks/gaps, visual stalls and return-to-stock behavior separately from
the logs. Marker consumption means the following reboot is stock.

Collect before mutation with the strict sparse collector. Use
`python build/report-fivegame-kernel.py <archive>` for the exact staged profile.
Require all twenty complete windows, oracle-bound fixtures, valid full native
PCM history, no fatal errors, joined audio/idle display/reaped supervisor, exact
render/submission/intentional-skip identities and final reserve accounting.
A failed/censored epoch cannot pass. Compare matched policy pairs; do not infer
performance benefit from both passing. UART IRQ rates and CPU savings are separate.

[Qualification](../evidence/2026-10-16/fivegame-kernel/qualification.json).

[Installation receipt](../evidence/2026-10-16/fivegame-kernel/installation.json) and
[independent final readback](../evidence/2026-10-16/fivegame-kernel/live-verification.json).
