# UART pair1 return: enabled TX pending while the driver skips service

The same-handler capture closes the previous status/enable gap. All12,340
captured calls have hardware TX interrupt enable set (`ctrl=0xf070`), software
TX enabled (`flags=0x07`), and GIC pending/active/unmasked (`gic=3`). Control
is unchanged across the two reads in every call. All GIC queries succeed.

The original driver selects neither RX nor TX for12,202 calls (98.8817%),
despite the shared-IP TX-pending bit0x4000 being present in every entry status.
It selects TX only138 times, when FIFO-empty bit0x80 is also present. All calls
return IRQ_HANDLED. No RX selections, overflow, bypass or unexpected returns.

| Original status | Software queue | Calls | Original service selection |
| --- | --- | ---: | --- |
| 0x5397 | nonempty | 23 | TX |
| 0x531f | nonempty | 10,878 | neither |
| 0x539f | nonempty | 92 | TX |
| 0x531f | empty | 1,324 | neither |
| 0x539f | empty | 23 | TX |

Every row has the same enabled TX and pending/active/unmasked GIC state above.
The1,324 empty-software-queue calls still have FIFO-empty bit clear: empty
software queue and empty hardware FIFO are different observations.

## What this identifies

This is the live condition predicted by the [pending-versus-empty source
analysis](uart-source-contract.md): the shipped ISR tests0x80 at`c0117804`,
whereas matching UART-family definitions distinguish pending0x4000 from
FIFO-empty0x80. There is now direct within-handler evidence of both enable
bits being set while that pending status is ignored. The earlier theory of
hardware/software enable divergence is absent from these captured entries.

Earlier process-context state1 snapshots saw TX disabled, but did not sample
inside the interrupt. Between-burst sampling is a plausible explanation; it
has not been reconstructed as a complete chronology. Do not reinterpret
those snapshots as simultaneous with these calls or treat them as invalid.

The strongest inference is an unserviced transmit interrupt condition while
the driver waits for FIFO-empty. RX noise has no supporting RX selection in
this capture. The exact GPA7 register manual and undocumented bits remain
unrecovered. GIC active is normal inside this handler; it is not missing-EOI
proof. Sequential status/control/GIC reads are not an atomic electrical trace.

This identifies the live failure condition and a concrete driver predicate;
it does not yet prove that correcting that predicate removes the physical
flood. The next causal check should be a narrowly guarded, reversible TX-path
intervention with original/corrected/restored phases, successful serial queue
progress and teardown. Source-specific disable/restore could isolate the
source first; disabling the whole IRQ would not isolate TX from RX. Do not
patch persistent kernel/firmware or claim recovered emulator headroom yet.

## Timing and lifecycle

| Phase | Interrupts | Midpoint seconds | IRQ19/sec |
| --- | ---: | ---: | ---: |
| Before loading | 7,313 | 1.005693 | 7,271.60 |
| Observer attached | 12,340 | 5.002712 | 2,466.66 |
| After unloading | 7,422 | 1.009066 | 7,355.32 |

The lower attached rate is a substantial observation disturbance, not measured
savings. The heavier read path can change burst timing and the number of
redundant entries before a hardware transition. No handler duration, CPU share,
unobserved event distribution or A7 saving is measured.

Initial capture is zero; final attached and frozen totals are12,340. The count
exactly matches bracketed IRQ19 growth. Five tuples conserve all calls and
reproduce branch, bitwise status, control-change and query-error aggregates.
The guarded action restore/drain, frozen report, ordinary unload and owner
exit0 all pass. Startup log returns to stock; visual stock-menu appearance
requires the user's observation. The consumed marker leaves I: unarmed.

## Archive and checks

`device-evidence/a7-pair-before-20261015T052954Z` preserves7,821 files /
1,937,165,499 bytes. Clean FAT serial11EB-1465, exact deployed source
`ec8ec39f79200c1f6f7a00cc192b9e2aa132c84b`, four payloads, dispatcher and
consumed marker verify.7,811/7,812 protected prior files are exact; only the
stock runtime swapfile changed. All stock boot binaries/init, FFVI ROM and
private progress verify. No card writes, rearm, splash install or core change.

The strict evaluator verifies the entire private archive and input lifecycle,
tuple conservation, errors, status masks and monotonic snapshots. Checks reject
altered totals, error/control-change aggregates, unique count and branch count.
Interpretation is published in [return metadata](../evidence/2026-10-15/uart-pair/return.json);
all946 earlier published proofs retain their hashes. Vendor images/logs and
private progress stay in the private archive.

Production gate remains **false**; the new observer's physical load/capture/
restore/unload is qualified for this returned run, while causal correction
and CPU benefit remain unmeasured.
