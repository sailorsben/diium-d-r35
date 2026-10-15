# UART state1 physical return — 2026-10-14

The snapshot preflight completed on the device: ordinary module loading,
100 valid snapshots, non-forced unloading, no cancellation, no remaining owned
module/proc entry reported, and wrapper exit0 returning to stock startup.
The interrupt flood persists with **no persistent TX-enable mismatch observed**.
This eliminates that proposed state as the explanation for this idle capture;
it does not exclude brief transitions between samples or emulation-only states.

| Phase | IRQ19 increase | Kernel-clock interval | IRQ/s |
| --- | ---: | ---: | ---: |
| Before load | 7,332 | 1.0055475s | 7,291.55 |
| Observer loaded | 33,816 | 5.005513s | 6,755.75 |
| After unload | 7,392 | 1.009370s | 7,323.38 |

Intervals use midpoints of bracketed counter reads. The published result retains
endpoint-time bounds; sequential procfs enumeration introduces additional timing
uncertainty. These are short startup phases, not matched stationary workloads.
The loaded phase is about7.55% below the mean of the surrounding rates. Its cause
is unestablished: observer disturbance and changing startup activity remain
possibilities. No recovered CPU budget or performance improvement is claimed.

Every snapshot has control`0x0000b070`, software flags`0x05`, hardware TX-enable
bit`0x4000` clear, software TX flag`0x02` clear, and equal queue head/tail.
There are zero mismatch samples and100 empty-queue samples. TX rises1848→2262:
414 reported bytes over4.955229s, about83.55/s. RX remains63 throughout. Thus the
flood is present while the sampled state shows an empty transmit queue and both
TX enables clear; the suspected persistent divergent-TX state is absent.

Snapshot scopes total636 microseconds, min4/max9 microseconds. That measures only
the observer's bracketed snapshot body, excluding procfs/read/owner/scheduling
costs; it is **not the original IRQ handler duration** or total probe overhead.
No interrupt status/FIFO was read and no UART setting or IRQ handler was changed.
Control bits alone do not identify which status condition is generating IRQ19.

## Preservation and provenance

Strict private archive`a7-pair-before-20261015T023156Z` preserves and verifies
7,805 files/1,937,114,927 bytes before analysis. FAT32 serial11EB-1465 is clean.
All four deployed payloads and dispatcher match the installation receipt for
pushed source`3892f2a42da9950d6da81ec762fa8500d45b48b6`. The exact one-shot
marker is consumed into`last-launch`; no armed marker remains. The durable
pre-load record, ordered100 reads, successful load/unload, final cleanup and
wrapper result agree; owner stderr is empty.

Of7,796 protected preinstall files,7,795 are identical and only the stock
swapfile changes. Live read-only verification also matches all six protected
stock binaries, existing init and FFVI ROM hashes. Original progress is intact.
No card writes, rearm, core changes, firmware changes or production promotion.
The wrapper's successful return is not independent visual proof of stock startup;
the pre-existing boot log is not used as fresh confirmation.

The [interpreted result](../evidence/2026-10-14/uart-state/return.json) retains
input hashes, rates and limits without publishing private card/vendor contents.
The earlier installation and offline proof files remain immutable. Reproduce:

```text
python build/analyze-uart-state-return.py device-evidence/a7-pair-before-20261015T023156Z
```

## What this changes

The reconstructed small-module interface now has physical load/read/unload
evidence for this exact package/kernel. That does not qualify arbitrary modules,
live handler instrumentation or a kernel replacement. The conditional stop-TX
code defect remains a demonstrated offline property but lacks the live triggering
state in this capture. Do not deploy its speculative fix as the UART solution.

Next, qualify a bounded observer of the **status value already read by the
original handler**, with branch aggregates, preserving original behavior and
avoiding extra potentially destructive status reads. That can distinguish receive,
TX and unrecognized-status paths. Separately measure original handler scope with
observer-cost controls before assigning any CPU saving. The earlier specification
in [kernel investigation](uart-kernel-investigation.md) remains a design target;
that richer observer is not implemented or armed by this return analysis.
