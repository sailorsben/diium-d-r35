# Persistent UART TX correction

`uart-fix1` applies the TX1 correction automatically on every normal boot from
this card, before an armed experiment or the stock frontend. It remains attached
through gameplay until explicit detach or power-off. The next boot loads it
again. This is a persistent card boot installation, with no SPI flash required.

The physical TX1 experiment reduced the idle UART interrupt rate from a weighted
6,996.87 to70.37/sec (98.994%), and twice reproduced the flood after restoration.
See [physical evidence and limits](uart-tx-return.md). That proves idle flood
suppression; it does not measure CPU time saved or FFVI improvement.

The production module is derived from hash-frozen TX1 source with exactly three
changes: remove the200,000-call cutoff, report cap0, and update the description.
All14 exact-image guards, single-byte !TX_FULL service, FIFO8 checks, original RX/
empty-FIFO bridge, flow control, queue/wakeup logic and restoration remain.
Unsigned diagnostic counters may wrap without affecting service. The existing
vendor PutChar behavior is preserved; serial wire data is not newly qualified.

The finite ARM boot helper loads with ordinary finit_module flags0, attaches,
checks active status/no faults/no bypass/no cap, then exits. The module's own
reference keeps IRQ code alive; no userspace daemon or periodic logger remains.
Missing payloads or a safely refused load retain original boot. A failure after
load restores/drains and ordinarily unloads before continuing. Ownership conflict
or uncertain teardown exits64 and prevents the patched init from starting stock.

The small package contains a6,812-byte module,7,016-byte helper, shell wrapper,
and revised normal init. These are file sizes, not a RAM footprint or A7 cost.
One bounded latest boot report is copied after attachment; no per-IRQ SD I/O.

Qualification executes18 compiled module groups,16 helper cases, the exact
firmware BusyBox shell and startup prefix, and five temporary-card transaction
cases. It includes40 original-vs-bridge cases,153 FIFO/queue combinations,
service across the former cutoff, counter wrap, RX/full/flow/urgent/wakeup,
guard refusal, live-module pin ownership, repeated detach/drain, boot failure
barriers, disabled/missing payloads and interrupted activation/rollback.
The bulk new-path RAM replay was stopped after an offline timeout; the targeted
cutoff/wrap checks passed. These are functional ARM models, not elapsed A7 prices
or sustained physical hardware acceptance.

Rebuild privately:

```text
python build/prepare-uart-fix.py
wsl --exec sh build/build-uart-fix.sh
python build/check-uart-fix.py
python build/check-uart-fix-install.py
```

The installer requires clean pushed source, fresh strict card archive, exact
stock/ROM/original-init hashes and clean FAT. It copies/verifies the separate
`retro/uart-fix1` package before atomically activating the normal init change.
All old logs, saves, ROMs, cores and one-shot packages remain protected.

Rollback on a powered-off, freshly archived healthy card:

```text
python build/install-uart-fix.py <fresh-archive> --rollback
```

That restores the exact original init and retains the correction package and
evidence. For immediate next-boot bypass, create `retro/uart-fix1/disabled` while
the card is connected to the PC. Remove that file to re-enable the installed
boot hook. On a live device an administrator can explicitly restore/drain/unload
using `uart-fix-boot stop ignored`; do not force unload a referenced module.

Persistent physical boot and sustained FFVI acceptance remain pending. The
[unchanged48-epoch retest](snes-uart-retest.md) is the next hardware measurement.
