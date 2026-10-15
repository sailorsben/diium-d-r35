# Next UART test: qualify the TX correction, then original/corrected/restored

The [paired physical return](uart-pair-return.md) identifies the live enabled,
pending TX condition that the original FIFO-empty service predicate ignores.
The next experiment should test a correction, rather than repeat the same
heavy observation. No IRQ candidate is implemented or armed by this plan.

Before building the physical candidate, qualify the transmit capacity contract.
Exact `gp_uart_probe` instructions at`c0117b2c..c0117b30` initialize the FIFO-size
field to8. The TX body at`c0117918..c011791c` uses that field divided by2 as its
batch limit:4 at the initialized setting. Confirm the live field at attachment;
the earlier generic offline fixtures used16 and do not prove physical capacity.

Changing eligibility from FIFO-empty0x80 to TX-pending0x4000 can enter that body
with a partly occupied FIFO. Establish enough room for its batch, or bound
writes by a qualified space check. A one-byte RAM fixture alone cannot establish
safe multi-byte hardware service. Preserve urgent-character, empty-queue,
stopped-TX and mixed RX/TX behavior, and change no character-output semantics.
The existing literal-zero PutChar finding remains a separate unresolved issue.

Use an exact-image guarded, temporary module for the correction; preserve
original kernel/firmware bytes. Qualification must execute actual vendor ARM
paths across empty/nonempty/wrapping queues, partial FIFO occupancy/fullness,
RX/TX combinations, flow control and urgent characters. Retain ownership,
module pin, restore/drain/unload and fail-closed stock-startup behavior.

The physical experiment then uses comparable original, corrected and restored
phases in one boot, preferably repeated. Observe phase-boundary IRQ counters,
queue progress, software/hardware enables, TX/RX/error counts and CPU accounting.
Keep the three GIC queries and detailed per-entry histograms out of the hot path:
the last observer reduced the observed rate from about7.3k to2.47k IRQ/s.

Success requires a reproducible fall in the IRQ flood during corrected service,
healthy TX queue progress/error behavior, and return of the flood after exact
restoration. If that fails, preserve the result and reconsider the asserted-source
or service model. Do not equate fewer IRQ counts with recovered CPU cycles.
Measure CPU benefit with separately priced observation and matched workload;
only then test whether it improves sustained SNES audio headroom. No emulator,
PPU/APU compiler or firmware change belongs in this UART comparison.
