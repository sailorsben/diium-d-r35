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

## Powered repeat accepted

Powered verification passes on a fresh boot: both 8-MiB flash passes match the
exact corrected kernel image, with both Vesper screen payloads/rootfs preserved.
No runtime UART patch module or endpoint exists. IRQ19 is 85.36-86.36/s and
85.37-86.37/s, passing the declared idle flood threshold. User confirms stock
remained on while plugged in. Prior shutdown cause remains unproven; low battery
is plausible. Saves and all prior evidence unchanged; FAT clean. Sparse return
hashes 10,906 files and adds only 8,219 evidence bytes. No full backup.
Original normal init restored exactly; all 10,905 other files verify unchanged.
Independent init/file-set/unarmed/FAT checks pass. No tests or firmware update armed.

Both complete 8-MiB passes match SHA256
`ef69753afb56c84e4daaf78aa3fad5551d26b7438e49f4f1dbc7312b11e07321`;
decompressed kernel SHA256 is
`b1fe94004b84cbf8ee0ec3367466598bc9c8dd1cbfa9f55ae9373bbc6eefa459`.
Readback completes in 103.762641 seconds. The new boot ID differs from the first
run, and the previous run's retained files match the exact rearm inventory.
Each new observation window records 432 IRQ19 interrupts over at least five
kernel-clock seconds; no runtime patch module/proc endpoint is present. Serial
TX advances 414 then 432; RX/break stay 62 then 63 within the respective windows.
This accepts corrected image installation and the bounded idle IRQ-flood fix.
Electrical byte correctness, throughput, CPU savings and all-load behavior are
not established by this passive test. User observation separately accepts the
powered return to stock; it does not prove the previous shutdown's cause.

[Powered result](../evidence/2026-10-16/uart-kernel-verification/powered-return.json).

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
is recorded in the published verification receipt. This paragraph describes
staging only; the completed physical measurements are reported above.

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

## Powered repeat installation

The plugged-in repeat is armed from pushed source `a636eb0`, attempt
`fe41d3f8e9fe4172bb6f3f7f3256edb4`. Independent final readback verifies all
10,868 existing files preserved and the exact 10,869-file resulting set, sole
read-only marker, no firmware trigger and clean FAT. Previous output is retained
under `retro/uart-kernel-verify1/completed-fe41d3f8e9fe4172bb6f3f7f3256edb4`.
No full backup. Cold boot plugged in, allow about two minutes (up to five) for
stock, observe stock briefly, then power down and return I:. No reflash.

[Repeat installation](../evidence/2026-10-16/uart-kernel-verification/powered-repeat-installation.json) and [independent readback](../evidence/2026-10-16/uart-kernel-verification/powered-repeat-verification.json).

## Final card state after powered return

Only `retro/init` changes during restoration, back to original SHA256
`b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7`.
All 10,905 other files match the return inventory; both runs are retained.
Independent original-init, 10,906-file exact-set, unarmed/update-absent and FAT
checks pass. No additional test or firmware update is armed. Normal boot uses
the flashed corrected kernel and needs no card UART hook or runtime patch module.

[Restoration](../evidence/2026-10-16/uart-kernel-verification/restoration.json) and
[independent final check](../evidence/2026-10-16/uart-kernel-verification/restoration-independent.json).
