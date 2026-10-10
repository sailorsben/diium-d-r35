# Read-only SPI chip identification — 2026-10-09

Survey2 finds stock `vrtemu` PID521 holding `/dev/spidev0.0` on FD8. Its exact
binary also contains the recovered SPI self-update implementation. This probe
runs synchronously at the start of SD init, before stock main can start that
owner. It identifies the attached chip; it does not dump or modify its memory.

## Transactions and refusal conditions

`spi-identify.c` sends only status05, three repeated six-byte JEDEC IDs9f, and
status05 again: five messages on a successful run. Each message uses two
32-byte transfers under one chip select: command then response. Transfer fields
request eight bits, one data lane and at most 1MHz, within the currently reported
speed. The program reads mode/bits/speed before and after, and has no global
configuration-write ioctl. Opcode values and packet layout are grounded in the
primary Linux4.19 [SPI NOR definitions](https://raw.githubusercontent.com/torvalds/linux/v4.19/include/linux/mtd/spi-nor.h)
and [spidev ABI](https://raw.githubusercontent.com/torvalds/linux/v4.19/include/uapi/linux/spi/spidev.h),
alongside the exact vendor status/read transactions.

Before opening the node, and again before exchanging bytes, the program inspects
every numeric process's FD metadata. It refuses an existing owner, inaccessible
census, more than128 processes or more than2,048 descriptors. Disappearing
processes are tolerated. The node must be a non-symlink character device with
major153/minor0; the opened descriptor is checked again. An advisory flock is
additional protection, not a lock that an uncooperative vendor must respect.
The synchronous boot placement prevents our known stock-launcher race.

The probe refuses unsupported mode flags, base modes1/2, non-eight-bit settings,
zero speed, busy status, short/error transfers, empty/floating/unchanged-sentinel
IDs, disagreement among repeated IDs or changed global settings. It does not
load modules, invoke vendor storage utilities, kill an existing owner, alter
configuration, enable writes or send program/erase commands. Missing driver or
node is reported; there is no kernel-memory fallback.

An owned child has a three-second deadline measured through the kernel monotonic
syscall. The supervisor kills and allows250ms to reap it. If it remains blocked
inside the kernel, the supervisor saves a pending report and waits, preventing
stock from starting a competing owner. Thus the deadline cannot guarantee
recovery from a kernel wedge. The marker is consumed and synced before running,
so a subsequent power cycle skips the probe and follows stock.

## Qualification and installed state

Eleven software checks pass: independent native/ARM packet fixtures, refusals,
supervisor timeout/kill/reap, exact release owner refusal, actual firmware BusyBox
consume-first/next-boot no-op behavior, and GLIBC dependencies at or below2.30.
These checks simulate hardware responses. The [physical return](spi-identify-return.md)
now succeeds with three `c84017c84017` responses; full readback remains pending.
Release: `releases/spi-identify-1`. Source, wrapper and release hashes are bound
in its manifest.

Installed run: `42401fa0056c4cfda90da165e2ad851f`.
Private baseline: `device-evidence/snes-mvp-return-20261009T234340Z`.
Independent readback verifies release/init/marker, all51 MVP/progress files,
all49 lab files and retained survey2 hashes. Post-install read-only CHKDSK is
healthy. That identification is now consumed, its exact init restored, and the
[separate full reader](spi-readback.md) is armed. Historical [installation](../evidence/2026-10-09/spi-identify-install/installation.json),
[verification](../evidence/2026-10-09/spi-identify-install/verification.json).

```text
bash build/build-spi-identify.sh
python build/check-spi-identify.py
python build/manage-spi-identify.py install
python build/manage-spi-identify.py collect
python build/manage-spi-identify.py restore
```

The identification installation has completed; do not rerun install. Its original procedure was: safely eject,
put the SD back in the handheld and cold boot. Let the stock launcher sit for
at least45 seconds, use its physical power button and reconnect D:. Collect
before any change, inspect read-only FAT health, then restore only on a healthy
card. Restore archives results again and requires the test to be unarmed and exact
installed/rollback init identities. The analyzer checks consumed-marker identity
separately. A consumed hook is already a stock next boot.

A stable plausible ID establishes a completed exchange, not a recoverable image.
Matched manufacturer/kernel references now establish nominal8MiB capacity and
24-bit03 reads. Next obtain two independently matching full readbacks.
A dump is a backup; recovery still needs a verified way to write when internal
boot fails. Original splash replacement and audio are separate unresolved work.
