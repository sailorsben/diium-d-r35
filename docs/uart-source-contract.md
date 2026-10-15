# UART source contract follow-up — 2026-10-15

**The leading source is now the transmit-side interrupt condition, with a
specific pending-versus-empty mismatch in the driver.** This is a source-backed
inference from matching UART-family definitions and the actual captured values;
it is not yet a physically isolated cause on this GPA7 board. I: is untouched
and remains unarmed. No replacement core, UART fix, probe install or flash.

## What the new sources establish

Three independently located GP32/GPM4 headers agree on control/data/status/FIFO
layout and distinguish these status bits:

| Status bit | Shared UART definition | Captured entries with bit set |
| --- | --- | ---: |
| `0x4000` | TX interrupt pending | 31,345 /31,345 |
| `0x80` | TX FIFO empty | 144 /31,345 |
| `0x10` | RX FIFO empty | 31,345 /31,345 |

The Generalplus-authored [GPM4 header](https://github.com/daviskung/GPM4_MLX_0528/blob/7ae0d2f0eed5420e6b29ebb557ff1c54939d01b0/driver_l1/common/inc/drv_l1_uart.h)
and its [register structure](https://github.com/daviskung/GPM4_MLX_0528/blob/7ae0d2f0eed5420e6b29ebb557ff1c54939d01b0/driver_l1/common/src/drv_l1_uart.c)
place data/RX-status/control/baud/status/FIFO at0/4/8/12/16/20 bytes, matching the
archived kernel's actual loads/stores. The independent
[GP32 header](https://github.com/davidgiven/gp32-sdk/blob/a7e4f98275a1438898b03f150cc339a313ba9dfa/src/gp32/uart_hw.h)
and [older vendor header](https://github.com/freexyz/gpl32/blob/91e466ec9502d308cfec10a1bdcefd0ad2de63e5/driver_l1/common/inc/drv_l1_uart.h)
agree. Downloads are pinned to commits and verified by SHA256 and Git blob SHA1;
source bytes remain private research dependencies, not publication copies.

The older Generalplus [GPL16925XA programming guide, pp118–121](https://ic.onidev.sdelang.fr/static/datasheet/GPL169256A.pdf#page=118)
also distinguishes TX interrupt from FIFO empty. It describes interrupt service
through FIFO operations rather than an invented status-clear write. It is a
different chip, with conflicting/reserved fields relative to this device; its
threshold sizes, gating details and acknowledgment semantics are not certified
GPA7 contracts. The captured0x1300 and low reserved-looking bits remain unnamed.

The exact shipped ISR at`c0117804` instead executes `TST r5,#0x80`. Its RX mask
is0xa000. Consequently the actual0x531f has the shared-IP TX-pending bit but
passes neither service test.0x5397/0x539f have the same pending bit plus the
FIFO-empty bit, so they reach TX service. This explains the captured selection
pattern exactly; it does not establish how this board gates that pending flag.

## Exact-code checks and the important negative result

`python build/check-uart-source-contract.py` verifies source hashes/definitions,
the original instruction word and physical histogram, then executes six ARM
check groups against the original kernel mapped into anonymous RAM:

1. Original0x80 test ignores0x531f even with TX enabled and one queued byte.
2. Change only that test to0x4000 **in the RAM fixture**: the original TX body
   sends/dequeues, reaches stop-TX and clears the enabled flag/control bit.
3. With software/hardware TX already disabled, the same comparison leaves
   control unchanged. It therefore cannot be promoted as a standalone flood fix.
4. Original GIC getter reads hardware IRQ69's pending/active/masked states for
   all eight combinations without changing register RAM.
5. Unsupported GIC state returns EINVAL without a result write.
6. Original ordinary GIC EOI routine writes hardware IRQ69 to CPU-interface EOI.

These are actual archived instructions; peripheral/controller registers and tty
delivery are fixtures. They do not simulate undocumented hardware assertion,
status-read side effects or A7 duration. The comparison preserves the existing
literal-zero PutChar behavior; it is not an output-corrected candidate.

The state1 capture showed control0xb070/software flags05, with TX interrupt
enable clear. It occurred on an earlier boot and was sampled at50ms spacing.
The status1 capture did not record simultaneous control. A pending flag alone
therefore cannot prove which enabled source asserted the wire, or distinguish
transient TX enables from a raw/latching condition or controller re-pending.
Do not quietly equate the status bit with the control-enable bit, or stitch
different boots into a simultaneous observation.

## Controller and source qualification

The archived device tree assigns UART atC0070000 SPI37, level-high; the GIC
translates that to hardware IRQ69, observed as Linux IRQ19. The exact ordinary
EOI function atc03033a0 writes IRQ69 to CPU-interface+0x10. Normal fast-EOI flow
contains its EOI callback; this is not evidence that the live callback was
invoked correctly on every interrupt. There is no demonstrated missing-EOI bug.

The exact GIC state getter atc0303d5c uses distributor read-only pending+0x200,
active+0x300 and enable+0x100 banks; IRQ69 selects word2/bit5. The exported
`irq_get_irqchip_state` provides the intended next interface, avoiding extra
reads of the destructive GIC acknowledge register. Its generic wrapper and the
combined live observer still need qualification; only the leaf getter is
executed in this check.

GPL32900/SPMP8050 Linux sources were located but rejected: their UARTs use an
incompatible16550-like layout. Shared function names do not make their register
contracts applicable. Public repositories named G-plus-6662118/kernel and
openplatform returned empty-tree HTTP409; no matching4.19 GPA7 source was recovered.

## The next discriminating observation

The supplied board-focused note was checked against the retained physical board
identification and exact initialization code. [VT569B is confirmed](board-identification.md);
the GPA7 family is the software platform, and GPA7740 remains a relative rather
than an identified replacement part. This is hardware interrupt delivery, not
an application polling rate or a proven intentional7kHz hardware clock.

The generic model label and three `okay` UART nodes are real, but availability
does not mean three active IRQ producers. The original driver registers the
interrupt in startup for an opened port. Also, the serial0 alias is intentional:
line0 selects C0070000 and the actual clock helper selects `uart1`/`uart1_reg`;
line1 selects C0060000 and `uart0`/`uart0_reg`. No alias/clock mismatch is found.

UART node properties contain no pad/pull/bias configuration. The decoded clock
helper only directly calls `gp_enable_clock`; it does not establish RX bias.
Existing photographs/DT do not identify an RX pad number, pull setting or actual
trace connection. Do not invent a GPIO or enable a pull based on sibling silicon.
RX noise remains possible, but zero captured RX selections and the shared-IP
RX-empty flag favor the TX-side lead in this capture. Earlier boot break counts
do not prove a currently noisy wire. The actual RX-error getter reads offset4,
whereas this status capture reads offset16: low bits of0x531f are not evidence
of framing/parity/overrun errors in the RX-error register.

Active-high level signaling is specified by the tree. The exact GIC SPI type
validator accepts rising-edge1 or level-high4; a speculative low-level polarity
flip is not a supported correction. Actual controller wiring/pending behavior
still needs observation. [Board/alias/clock inspection](../evidence/2026-10-15/uart-source-contract/board.json)
records six additional static check groups; these are not electrical measurements.

Extend the already physically qualified original-status bridge to record the
same invocation's verified control read, software TX flag/queue state and GIC
pending/active/masked state, with bounded tuples and explicit overflow/refusals.
Retain the original status read and handler, restore/drain/unload, and do not
write UART settings or clear GIC pending as part of observation.

If the dominant0x531f tuple has TX enabled and the line remains pending, it
supports an unserviced TX threshold condition. If TX is already disabled, a
redundant disable cannot establish causality: investigate raw/latched peripheral
state and source routing instead. GIC active while in its handler is expected;
it alone is not evidence of a broken EOI. Any later suppression must select the
identified source, be restored, and reproduce the flood after restoration before
claiming causality. No speculative pending-clear, FIFO reset or IRQ_NONE change.

[Interpreted source metadata and ARM checks](../evidence/2026-10-15/uart-source-contract/research.json).
All939 previous published hashes remain exact. No device access occurred in
this research; no measured CPU saving or production acceptance is claimed.

## Subsequent same-handler physical evidence - 2026-10-15

Pair1 now records both TX enables set and GIC pending/active/unmasked on all
12,340 captures, including12,202 ignored-status entries. This closes the earlier
status/control correlation gap; physical causal correction and CPU benefit are
still unmeasured. [Returned tuples and limits](uart-pair-return.md).

## Subsequent causal correction test - 2026-10-15

UART TX1 reduces the idle flood from about7k to70 IRQ19/sec in both corrected
intervals; both exact restorations reproduce it. This establishes the tested
TX service mechanism causally, while CPU/wire/full-FIFO/gameplay qualification
remains pending. [Physical result](uart-tx-return.md).
