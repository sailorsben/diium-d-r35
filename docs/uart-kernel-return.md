# Direct kernel UART firmware return — 2026-10-16

Ben reports successful flashing, both Vesper screens and the stock launcher.
That accepts observed boot/display behavior. The card has no fresh internal
flash capture or IRQ-rate sample; it cannot yet prove exact programmed bytes or
UART behavior. Old UART-module logs are unchanged and must not be presented as
measurements of the newly corrected kernel.

## Collected preservation

Strict sparse return `uart-kernel-return-20261017T015801633471Z` hashes 10,826
files and stores zero new content bytes, with clean FAT/serial 11EB-1465 and no
card writes. All saves, previous results, stock programs and UART artifacts
remain exact. All 636 outside-retro files are identical. Compared with the
pre-install inventory, 10,823 files are unchanged; the only differences are
authorized normal init, authorized replacement Code.bkp and the stock swapfile.
There are no added paths or armed tests. The returned trigger matches the
exact final kernel package hash and can be reconstructed from its retained
private qualified source package; no extra backup is needed before removal.

[Boot/preservation receipt](../evidence/2026-10-16/uart-kernel1/boot-return.json).

## Completed first verification and requested plugged-in repeat

Strict return `uart-kernel-return-20261017T022201466502Z` preserves 10,868 files
by hashes, 16,787,372 new sparse evidence bytes and clean FAT. All earlier saves,
stock files and evidence are unchanged except the expected init/update/swap paths.
The wrapper completes successfully after 103.701112 seconds of two-pass readback
and both five-second observation windows. Both full flash passes match expected
`ef69753afb56c84e4daaf78aa3fad5551d26b7438e49f4f1dbc7312b11e07321`, and the
captured decompressed kernel matches corrected `b1fe94004b84cbf8ee0ec3367466598bc9c8dd1cbfa9f55ae9373bbc6eefa459`.
Entire flash equality also verifies both screen payloads and rootfs preservation.

IRQ19 increases 449 and 432 across the two windows: 88.49-89.62/s and
85.37-86.37/s using snapshot-time brackets. Both pass the prior <500/s criterion.
No runtime UART module or patch endpoint is present. TX increases 432 in each
window; RX/break stay 62 then 63 within the respective windows. These are idle
IRQ observations, not CPU savings, electrical byte accuracy or workload coverage.

User reports shutdown and later suggests low battery. The successful reader,
post-reader observer and wrapper exit establish completion before stock resumes.
They do not establish later stock stability or a poweroff cause. There is no
retained battery/shutdown telemetry to distinguish those causes. No shutdown
command exists in the probe; the watchdog was not disabled.

User requests the same test rearmed for a plugged-in repeat. Preserve outputs
by renaming logs/results/wrapper/consumed into a unique completed directory on
card, without copying or deleting them. Reuse the exact qualified helpers,
wrapper, installation and marker identity; a unique repeat receipt and fresh
output directories distinguish this repetition. Require a new boot ID on return.
Hash every existing file before rearm and verify all mapped paths after rename;
arm only after clean FAT and preservation readback. No reflash or full backup.

[First verification analysis](../evidence/2026-10-16/uart-kernel-verification/first-return.json).

## Necessary read-only verification boot

Use a separate `retro/uart-kernel-verify1` profile, preserving all older readers
and results. Remove only the exact known Code.bkp after strict collection and
healthy-FAT/hash gates. Temporarily prepend a consume-first, synchronous hook
to original normal init. It executes before stock takes SPI ownership. The
following boot is stock because the one-shot marker is already consumed.

The unchanged, physically used spi-readback-1 reader sends fixed read commands
05/9f/03 only. It takes two byte-compared 8-MiB passes, with the existing
240-second owned-child/reap contract. These are 16 MiB of verification evidence,
not a new full-card rollback backup. No flash programming or settings writes,
kernel patch, correction module, emulator or display owner is installed/run.

A small observer brackets passive IRQ19, serial, CPU-jiffy, module, version,
command-line and boot-ID snapshots with kernel-syscall monotonic time. It waits
five seconds using relative remaining-duration sleeps before and after the
reader. It records whether the old UART module/proc endpoint exists. Observation
failure, uncertain reader completion or missing helper withholds stock during
that boot; consumed marker permits a later stock boot.

Ten offline groups cover exact reader/source hashes and reused qualification,
firmware-compatible ARM ABI, actual ARM passive snapshot contents/kernel-clock
wait, existing-output refusal, missing-input failure, firmware BusyBox syntax,
consume-first order, failure barriers and replay refusal. Nine temporary-card
cases cover write/FAT failures and foreign trigger/init/profile refusal. No full
backup. Independently verify the complete card/payload/marker and clean FAT.

**Historical first staging: source `08e4b06`; completed successfully as above.**

The installer verifies all 10,824 protected existing files, exact probe payloads,
temporary init and sole one-shot marker with clean FAT. The known firmware update
trigger is removed. No firmware update is armed. Independent final-card readback
is recorded in the published verification receipt. Physical measurements remain
pending; installation checks do not establish the flashed kernel or IRQ result.

After verified staging, safely eject I:, cold boot once and allow about two
minutes, up to five, for stock to appear. Vesper may animate during readback.
Then power off normally and reconnect I:. If stock does not appear after five
minutes, power off and return the card for partial-result inspection; do not
repeat or reflash. The verification writes no firmware.

## Return acceptance and restoration

Collect sparsely before mutation. Require consumed marker/run identity, payload
hashes, successful wrapper/reader exit, complete untorn two-pass bundle, recorded
CRC/lengths, fixed command/read-only flags and both full pass hashes equal to
`ef69753afb56c84e4daaf78aa3fad5551d26b7438e49f4f1dbc7312b11e07321`.
Decode the captured zImage to confirm corrected kernel hash
`b1fe94004b84cbf8ee0ec3367466598bc9c8dd1cbfa9f55ae9373bbc6eefa459`.
Compare static bitmap/rootfs/logo and all bytes to the expected programmed image.

Require matching fresh boot IDs, both complete five-second observer windows,
no loaded d35_uart_tx module or proc patch endpoint, monotonic counters and
kernel-time brackets. Report IRQ rate as a bracket using snapshot start/end
times. Two idle windows below 500 IRQ19/s reject the prior approximately 7,000/s
flood in this bounded observation; they do not price CPU savings or prove all
loads. Retain serial TX/RX/error deltas separately. Wire bytes and sustained
serial throughput still need electrical observation if those claims are desired.
After successful collection/health/hash checks restore original normal init,
preserving all private captures and leaving everything unarmed.

[Probe qualification](../evidence/2026-10-16/uart-kernel-verification/qualification.json).

[Installation receipt](../evidence/2026-10-16/uart-kernel-verification/installation.json)
and [independent final-card verification](../evidence/2026-10-16/uart-kernel-verification/live-verification.json).
