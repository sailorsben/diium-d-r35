# Battery investigation: pre-kernel rollback — 2026-10-16

**Current card after authorized cleanup:** 1,601 files remain; obsolete tests
were removed only after host byte verification. The exact rollback trigger and
card UART boot files remain armed/unchanged, all save paths are intact, and
independent full remaining-file/ZIP/FAT checks pass. The larger staging counts
below describe the historical pre-cleanup inventory.
[Cleanup receipts](card-test-cleanup.md).

**Armed on I:** pushed source `481415f`. Independent final readback verifies all
11,003 protected files, exact 11,006-file set, complete package CRC/image/original
kernel, proven card UART payloads and clean FAT. No game test is armed. User authorizes preparing I: for a controlled rollback
after immediate low-power warning on unplugging despite extended plugged-in time.
This is a diagnostic rollback, not an established battery repair. No game suite
is armed. No full-card/retro backup or new rollback-copy collection is made.

## Exact rollback

Reuse the original, hash-verified Wings2 `fixture-compatible.bkp` byte-for-byte.
Its package SHA256 is
`2b78853155c087cfaf3dab730cabbb2dabc757982626da53ddb04cb9dc7bc389`,
and expected programmed image is
`5c2f34e6b4451b27fa5e6782f1396d8e6a3bf485e24c0fe209b44854f77660c3`.
This restores the original kernel SHA256
`21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321`,
removing all four direct-kernel UART changes. Both Vesper screens and the whole
rootfs are byte-identical to the currently verified flash. Only the kernel section
and vendor CRC/date differ between the expected programmed images. The original
Wings2 package was user-reported flashed successfully; exact current-to-rollback
programming is newly tested offline using the captured ARM updater.

Restore the exact proven persistent card UART init/wrapper, without rebuilding
or replacing the module/helper. Kernel bytes match all saved module code/ABI
guards. This restores the prior combination of vendor kernel plus card correction;
it does not claim module-free firmware correction. Before the rollback takes
effect, the module's exact-kernel guard safely refuses the current patched kernel.
The pre-existing helper's guard/refusal qualification is retained. After rollback,
the original kernel matches and the fix applies through the restored card hook.

Eleven qualification groups check original package/ZIP/CRC, expected byte identity,
screen/rootfs preservation, original kernel and module guards, actual ARM updater
acceptance from current kernel and full RAM result equality, incompatible/CRC/
prefix/repeated-update refusals, original static-splash/boot-loader execution,
and firmware-shell syntax. Seven staging cases cover success and hook/trigger/
health-gate rollback. These do not prove physical flash or charging behavior.

## Preservation and staging

Fresh sparse archive `uart-kernel-return-20261017T030857768581Z` hashes the whole
card and retains selected progress/logs by content-addressed hard links. Saves,
all returned five-game/UART evidence, stock binaries and old test packages stay
protected. Only existing `retro/init` and `retro/uart-fix1/launch.sh` change; add
only exact `retro/update/Code.bkp`, last. No emulator markers are armed. Failure
removes only the owned trigger and restores the prior hook bytes after a healthy
FAT gate. Existing module/helper and disabled-state checks are mandatory.

Check all prior hashes and clean FAT before writes, after restoring hooks and
after trigger arming. Independent final readback checks the entire exact card
file set, package CRC/image/original kernel, restored module payloads, absence
of game markers, sole expected firmware trigger and clean FAT.

## Physical procedure

Keep the handheld connected to reliable charging power throughout the update.
Safely eject I:, insert with power off, and cold boot. Let the vendor update
finish without interruption. It may power off on completion; if so, wait for it
to finish before turning it back on with power still connected. Confirm both
Vesper screens and stock launcher. No gameplay test runs.

After boot, shut down and charge while fully powered off using the same charger
and cable. Then boot stock and compare the unplugged warning/behavior. Report
whether only a warning appears or the device actually shuts down, plus charging
indicator behavior. Do not label the rollback a battery repair from boot alone.
Power off and reconnect I: for strict collection, exact trigger removal and UART
attachment/battery-outcome analysis. No automatic rearm or additional firmware
change. The trigger remains present until removed; avoid repeated update boots.

If the warning disappears, that implicates the kernel change but charge state
and elapsed charging remain confounders; isolate patches before reintroducing
any correction. If it persists, charging hardware, supply/cable and ADC reporting
remain open. Do not lower battery thresholds or infer charging from USB-powered
operation. Exact flashed rollback image will require readback if that claim is
needed; stock observation alone is not whole-image proof.

[Qualification](../evidence/2026-10-16/battery-rollback/qualification.json).

[Installation](../evidence/2026-10-16/battery-rollback/installation.json) and
[independent readback](../evidence/2026-10-16/battery-rollback/live-verification.json).

Return collector: `python build/collect-battery-rollback-return.py` accepts only
the exact rollback trigger or its absence, preserving all progress/evidence before
health checks or cleanup. It makes no full backup and writes nothing to the card.
