# UART TX1 return: the correction suppresses the idle IRQ flood

**The reversible test passes.** Both corrected intervals reduce IRQ19 by about
99%, TX queue/counter progress continues, and both restorations reproduce the
flood. This establishes a causal idle-startup result for the bounded TX service
correction. It is not measured CPU recovery or sustained SNES qualification.

| Phase | IRQ19 calls | Kernel-clock seconds | IRQ19/sec | Reported TX bytes |
| --- | ---: | ---: | ---: | ---: |
| Original0 | 35,338 | 5.005504 | 7,059.83 | 432 |
| Corrected0 | 345 | 5.009468 | 68.87 | 414 |
| Restored0 | 34,964 | 5.009456 | 6,979.60 | 432 |
| Corrected1 | 360 | 5.009509 | 71.86 | 432 |
| Restored1 | 34,822 | 5.009465 | 6,951.24 | 432 |

The time-weighted original/restored rate is6,996.87/sec; corrected rate70.37/sec,
a98.9943% reduction. Against their immediate bracketing controls, the two
corrected reductions are99.0189% and98.9683%. The second corrected phase reports
the same432 TX bytes as adjacent controls. First corrected phase reports414;
counter throughput across all windows is82.64–86.31 bytes/sec. Queue head equals
tail at every boundary. Counts do not verify physical transmitted content.

## Service and restoration evidence

The two corrected IRQ deltas345+360 exactly equal the module's705 calls.
Of these,658 added pending-path services each enqueue one byte and47 calls
fall back to original vendor paths. Per corrected phase the reported TX delta
is exactly the added writes plus four bytes per fallback call (322+23*4=414;
336+24*4=432). This is consistent with the original empty-FIFO batch and added
one-byte service; it does not instrument each fallback's internal branch.

Full-FIFO refusals, empty/stopped/urgent added-path counts, faults and bypasses
are all zero. Live FIFO-size field is8 at all snapshots. RX remains63 and break
count63 throughout; frame/parity/overrun remain zero. These are unchanged
RX/error counters, not independent proof of TX wire integrity or FIFO capacity.
No full-FIFO condition was encountered physically. The matching-IP full-flag
contract and original literal-zero PutChar limitation remain as documented in
the [test specification](uart-tx-correction-test.md).

Both attaches succeed. The original IRQ action is restored/drained after each
corrected interval, with the final idempotent stop also succeeding. Frozen
counts match the last restored snapshot; ordinary unload succeeds, no module
remains, owner exits0, and the wrapper returns to stock startup. No visual-menu
claim is inferred from that log alone. The consumed marker leaves I: unarmed.

## Meaning and limits

The new service handles the TX-pending condition that the original ISR skips
until FIFO-empty. No GIC mask/clear, firmware/kernel text or emulator/APU code
changes are involved. The repeated corrected/restored result isolates this TX
service change as the cause of the flood suppression in this workload. This is
stronger evidence than status correlation or a slower observer's lower rate.

It does not establish a99% CPU saving. The accounting ticks are mostly idle in
all phases, IRQ-time accounting is disabled, and five-second CPU jiffies cannot
resolve precise handler cost or emulator headroom. Correction overhead, full/
mixed-RX behavior, serial wire contents and sustained audio benefit remain
unmeasured physically. Production gate stays false. The next useful comparison
is bounded gameplay with/without this correction and matched timing/audio
evidence, while retaining guarded restoration and pricing measurement cost.

## Collection and reproducibility

Private archive `a7-pair-before-20261015T062141Z` preserves7,829 files /
1,937,195,273 bytes. Source `a173f82da398a3a205bb3188a2d1ccfdc60a853a`, four
payloads, dispatcher and consumed marker match the installation. Clean FAT
serial11EB-1465 and independent live-to-archive log/payload checks pass.7,819 of
7,820 protected prior files remain exact; only the normal runtime swapfile
changed. Stock boot files/init, FFVI ROM and private progress verify unchanged.
No card writes or rearm occurred during collection.

The strict parser checks five-phase ordering, both attaches, all restorations,
counter conservation, FIFO8, corrected-call/IRQ equality, TX progress, flat
errors, frozen counters and ordinary unload/exit. Negative mutations of attach,
FIFO size, restoration, unload, fault and conservation values are rejected.
[Interpreted return metadata](../evidence/2026-10-15/uart-tx/return.json) preserves
hashes of all private inputs; all957 previous published proofs remain exact.
Raw vendor dependencies, ROM and progress remain private.
