# Two-pass SPI readback — 2026-10-09

**Returned successfully:** two complete8MiB reads match in103.771059 seconds;
FAT clean, protected progress/results preserved and normal init restored.
Nothing is armed. [Physical return and boot-image inspection](spi-readback-return.md)
supersede the historical install/pending procedure below.

The [physical identification](spi-identify-return.md) repeatedly reads
`C8 40 17`. Primary manufacturer/kernel references establish the nominal8MiB
family range and ordinary03 read with a three-byte address. This separate
profile captures that range twice before stock main starts. It uses the unchanged,
physically qualified identification/ownership source and its working1MHz limit.

Only05 status,9f ID and03 memory reads can be sent. No write-enable, erase,
program, reset, mode-change or global configuration-write operation is present.
The known SPI character node and competing FD owners are checked before opening
and before each identification phase. Mode/bits/speed must stay unchanged within
and between phases. Busy status, wrong full repeated ID, short/error reads or
another owner refuse the capture. No module loading or kernel-memory fallback.

Each read uses a four-byte03/address command followed by4,096 received bytes in
the vendor-compatible two-transfer ioctl. Single-lane eight-bit transfers run
at at most1MHz. Addresses are fixed from0 to0x7fffff; there is no CLI capacity,
address or command override. The second pass is freshly read from SPI and compared
byte-for-byte with the first stored pass. Blank00/ff or unchanged-a5 images are
refused. Both full passes must finish and match, then status/ID/settings are checked
again before completion is reported.

The device holds two4KiB buffers, not a full image in RAM. Output is one16MiB
`captures.bin` plus `report.jsonl`, with both directory entries synced before
growth. Each1MiB checkpoint syncs the bundle and reports progress. The return
analyzer checks run/marker/wrapper identity, completion/counts, exact bundle size,
per-pass CRC32, SHA256 and complete byte equality. Torn, changed or stale returns
stay incomplete. Raw contents remain in ignored private evidence only.

The owned child has a240-second kernel-clock deadline, followed by kill/reap.
An unreaped kernel-blocked child leaves a pending report and prevents stock from
starting a competing owner. The consumed/synced marker makes the following boot
stock. The timeout is not a guarantee against a kernel wedge.

The captured init starts `/wdt` independently before SD init. Offline inspection
of exact watchdog SHA256 `6a8d50aae684876074b54dc1b43acdc456a964d913aae6997b2f54fa5d97094a`
finds a500,000-microsecond sleep and watchdog-ioctl loop at0x10438–0x10460,
with no userspace stock-main process check. The reader does not change that helper.
This code inspection is not physical qualification of a four-minute startup.

## Physical procedure

Installed run `5250ec9cd87740ff9fba5ec82ae3a707`; release `releases/spi-readback-1`.
Private baseline `device-evidence/snes-mvp-return-20261010T001625Z`.
Nine software checks pass. Independent installed release/init/marker,51-MVP,
49-lab and43 prior-profile file hashes verify; post-install FAT is healthy.
Only this reader is armed. [Receipt](../evidence/2026-10-09/spi-readback-install/installation.json),
[verification](../evidence/2026-10-09/spi-readback-install/verification.json).

Use the installed run identity from [the current handoff](handoff-2026-10-09.md).
Safely eject D:, insert the card and cold boot. The boot animation may continue
for two to four minutes while both reads run. **Allow five minutes**, then use
the physical power button and reconnect. A still-running animation after that
window is a diagnostic failure, not a reason to stage an update file; a subsequent
boot skips the consumed probe. There are no flash writes in this test.

```text
python build/check-spi-readback.py
python build/manage-spi-readback.py install
python build/manage-spi-readback.py collect
python build/manage-spi-readback.py restore
```

Install requires healthy FAT, exact init/splash/vendor identities, the successful
measured ID result, source/release qualification hashes and no other armed test.
It archives all prior progress/results, changes only the owned profile/init and
arms last. On return collect before checking health or changing the card. Restore
archives again, requires healthy FAT, resolved consumed run identity and exact
init/rollback hashes. Never publish the bundle or a derived vendor image.

Software qualification covers independent native and ARM packets/address order,
the actual supervised capture, mismatch/blank/busy/wrong-ID/short/error/settings
refusals, timeout/reap, altered/torn/stale returns, unhealthy restoration, exact
release owner refusal, firmware BusyBox one-shot behavior and glibc2.30 ABI.
Physical full-range readback now passes for this run. Offline boot-image/layout
inspection locates the original showlogo in the SPI rootfs; a private replacement
fits and passes archive checks. Writes, recovery and original splash replacement
still need separate qualification. See the return linked above.
