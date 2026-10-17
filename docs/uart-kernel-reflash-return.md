# UART reflash return and fresh verification — 2026-10-17

Ben confirms the reflash completed, both Vesper screens appeared and the stock
launcher started. This accepts the observed boot. It does not independently
measure the freshly programmed kernel or UART interrupts.

Strict sparse return `uart-kernel-return-20261017T100507473949Z` inventories
1,601 files, adds zero content bytes and passes clean FAT/serial 11EB-1465.
Every save/state, stock binary and prior evidence file matches the staged
inventory. Only `retro/setting.xml` and `retro/swapfile` differ from the exact
post-staging inventory; preserve these returned versions and their hashes.
The used update package and normal init remain exact. The old boot log is
unchanged, and there is no new SPI capture or UART measurement. Earlier physical
readbacks are retained as earlier evidence, not represented as this reflash.

[Boot and preservation receipt](../evidence/2026-10-17/uart-kernel-reflash/boot-return.json).

## Read-only verification boot

The user's request to verify the kernel UART fix requires a fresh device boot:
the offline SD card cannot read its internal SPI flash or current IRQ counters.
Reuse the exact qualified and previously physically used
`retro/uart-kernel-verify1` profile. Cleanup removed its old on-card profile;
all unique earlier evidence remains preserved on the host, so no output is
overwritten or moved for this installation. Ten existing qualification groups,
nine staging fixtures and all source/payload/init/marker hashes verify. The
fixed-reader release manifest, sources and binary hashes verify too.

Remove only the exact returned `Code.bkp`, SHA256
`b2f8b286095f189ad9d0cad30320212f88a1b59e761ee7120aa9d45bab44dfeb`,
after sparse preservation, complete card/progress hash and clean-FAT checks.
Install the existing consume-first synchronous hook in normal init, the four
unchanged payloads, qualification metadata and one-shot marker. Protect every
other returned file, including changed stock settings, by its return hash.
The independent final check verifies the exact full file set, all protected
hashes, payload/marker, absence of firmware triggers and clean FAT.

This probe runs before stock takes SPI ownership. It sends only the qualified
reader's fixed 05/9f/03 commands, reads two byte-compared 8-MiB passes and takes
five-second kernel-clock-bracketed UART/IRQ snapshots before and after the
readback. It never programs firmware, changes UART configuration, loads the
UART patch module, starts an emulator or owns the display. The 16-MiB readback
is verification evidence, not a full-card backup. Identical captures are
deduplicated by the existing sparse object store when collected.

The qualified marker/run ID is intentionally reused byte-for-byte. The complete
pre-install inventory proves the profile and output paths were absent. Return
acceptance must also verify a new boot ID against the earlier physical runs,
the consume marker, new outputs, exact expected flash/kernel hashes, no loaded
patch module and both measured IRQ windows. No previous output can count as
the new measurement.

The [verification installation](../evidence/2026-10-17/uart-kernel-reflash/verification-installation.json)
and [independent readback](../evidence/2026-10-17/uart-kernel-reflash/verification-live-check.json)
record trigger removal and arming completion. At staging, exact kernel/UART
acceptance for this reflash remains pending. No additional firmware flash,
full backup or game test.

**Staged and independently verified on I:** source `d72b89b` was pushed before
installation. The exact used firmware trigger is removed. All 1,599 protected
existing files, exact full file set, unchanged probe payloads/sole one-shot marker
and clean FAT pass independent readback. Only read-only verification is armed;
physical kernel/IRQ measurement remains pending. No full backup or game test.

## Next physical step and acceptance

Safely eject I:, insert with power off, keep charging power connected and cold
boot once. Allow about two minutes, up to five, for the stock launcher to
appear; the Vesper animation may remain visible during readback. No firmware
update should run. Once stock appears, shut down normally and reconnect I:.
If stock has not appeared after five minutes, power off and return the card
for partial-result collection rather than repeating or reflashing.

Collect before mutation. Validate fresh marker/output identity and all protected
return hashes. Both complete flash passes must equal
`ef69753afb56c84e4daaf78aa3fad5551d26b7438e49f4f1dbc7312b11e07321`,
with corrected decompressed kernel
`b1fe94004b84cbf8ee0ec3367466598bc9c8dd1cbfa9f55ae9373bbc6eefa459`.
Full image equality also checks both Vesper screens and rootfs preservation.
Require no runtime UART module/patch endpoint and both idle IRQ19 upper brackets
below the existing 500/s gate. Keep idle flood acceptance separate from wire
byte accuracy, throughput, CPU savings and emulator/gameplay results.

The older analyzer hardcodes the large original card inventory; do not run it
unchanged against this cleaned card and call its result current. Use this
installation's exact sparse inventory and payload receipt for return comparison.
After accepted collection restore exact normal init; the consumed marker already
makes the following boot stock. No automatic rearm.
