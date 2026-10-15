# UART status1 physical return — 2026-10-14

**Source follow-up,2026-10-15:** matching GP32/GPM4 definitions identify a
TX-pending0x4000 versus FIFO-empty0x80 mismatch. This narrows the lead while
retaining the need for simultaneous enable/controller correlation; the full
GPA7 contract and causal suppression are still absent. [Research](uart-source-contract.md).

**The dominant live path is identified:**31,201 of31,345 intercepted IRQ19
entries (99.5406%) return status`0x0000531f`, which matches neither the shipped
ISR's RX mask`0xa000` nor its TX mask`0x80`. All31,345 handler calls return
`IRQ_HANDLED`. There are no RX selections;144 entries select TX only.

| Actual entry status | Count | Share | Selected path |
| --- | ---: | ---: | --- |
| `0x0000531f` | 31,201 | 99.5406% | Neither RX nor TX |
| `0x00005397` | 24 | 0.0766% | TX only |
| `0x0000539f` | 120 | 0.3828% | TX only |

No histogram overflow, capture-cap bypass, other handler return, RX-first or
RX-then-TX event occurs. Initial capture is zero; final attached and frozen
captures agree exactly. All conservation identities pass, including histogram
sum, branch sum, return sum and monotonic reports. The31,345 captured calls equal
the31,345 increase in the bracketed `/proc/interrupts` count, so the ignored
path is the measured flood's dominant path, not a sparse sampling artifact.

The exact archived ISR checks these bits, then takes its short return1 path
without RX/TX service or an explicit UART register write when neither matches.
A separate actual-ARM check with the physically observed`0x531f` reproduces
1,000 such returns without changing the anonymous RAM register/port/queue
fixture or calling tty delivery/wakeup. It executes the stock instructions,
not the observer callback. This check does not model hardware read side effects
or electrical behavior; its control/flags context comes from the earlier state1
run, not simultaneous status1 observations.

**This establishes the software path, not the original asserting condition.**
It does not establish whether a status read acknowledges anything implicitly,
which other status bits mean an active source, whether the IRQ controller is
re-pending it, or which clearing/masking change would be correct. Do not call
`0x531f` a proven RX error, TX fault, or a specifically named hardware interrupt
without a matching register contract. The earlier persistent TX-enable mismatch
was absent in state1 and is not resurrected as the explanation here.

## Timing and cleanup

| Phase | IRQ increase | Bracket midpoint interval | IRQ/s |
| --- | ---: | ---: | ---: |
| Before loading | 7,433 | 1.008747s | 7,368.55 |
| Hook attached | 31,345 | 5.0056495s | 6,261.92 |
| After unloading | 5,839 | 1.0091345s | 5,786.15 |

These are sequential startup windows with unpriced observer disturbance.
The rate also changes after unloading; the differences are not measured savings
or a treatment effect. No per-handler duration or recovered A7 budget is claimed.

Ordinary load succeeds. Stop reports restoration success/attached0; the frozen
report remains available, ordinary non-forced unload succeeds, module-remains0,
cancelled0 and wrapper exit0. Thus this exact physical probe now has interception,
capture, restore and unload evidence. Wrapper return does not independently prove
visual stock-launcher operation. I: is unarmed; its marker was consumed.

## Preservation and next step

Strict archive`a7-pair-before-20261015T044508Z` verifies7,813 files/
1,937,139,157 bytes and clean FAT32 serial11EB-1465. A separately hash-copied
early probe bundle matches the complete archive byte for byte. Four deployed
payloads and dispatcher match source`0b90c2d`'s installation receipt. Of7,804
protected preinstall files,7,803 remain exact; only the stock swapfile changes.
Stock boot binaries/init, FFVI ROM and original progress verify. Prior state1
logs remain intact. No card writes, rearm, core/APU change or UART fix.

[Physical interpretation and input hashes](../evidence/2026-10-14/uart-status/return.json)
and the separate [original-code check](../evidence/2026-10-14/uart-status/captured-status-path.json)
are published without private card/kernel contents. All937 prior proof hashes
remain exact. The evaluator rejects altered histogram counts, false restoration
and reordered sample IDs.

```text
python build/analyze-uart-status-return.py device-evidence/a7-pair-before-20261015T044508Z
python build/check-uart-status-path.py
```

Next, resolve the peripheral/interrupt-controller contract for the source that
asserts IRQ19 while the original entry read yields`0x531f`. Correlate the pending
source and enabled bits before designing a reversible corrective experiment.
The next work should explain this observed condition; another generic TX/RX
snapshot or speculative stop-TX patch would not resolve it. Physical CPU benefit
and unchanged emulation outputs must still be demonstrated for any later fix.
