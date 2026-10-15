# UART pair1: catch the enabled source in the ignored interrupt

The previous physical capture identified the dominant driver path: status0x531f,
no RX/TX service, IRQ_HANDLED. This diagnostic correlates that **original status
read** with UART enable/control, software flags/queue and GIC state within the
same invocation. It is observation, not a performance candidate or UART fix.

## Capture and ownership

The separate `uart-pair1` package retains the physically qualified bridge shape:
original status getter once, register preservation, original ISR body in place.
No vendor kernel text, UART configuration, FIFO, interrupt mask, pending-clear,
acknowledge/IAR or emulator/APU code is changed. A temporary owned IRQ-action
pointer is restored and the IRQ drained before releasing the module reference.
Ordinary unload refuses a live hook; uncertain cleanup withholds stock startup.

Each pre-service tuple records, in order: status already read by the original
getter; control through original GetCtrl; software flag byte and head/tail queue
comparison; generic kernel GIC pending/active/masked queries; a second control
read. These are sequential reads inside the same IRQ, not an electrical atomic
snapshot. Control changes and getter errors are explicit. First/last raw queue
indices remain in the summary; histograms group only empty/nonempty queues.

`gic` low bits0/1/2 mean pending/active/masked. Bits8/9/10 indicate the matching
query failed, in which case its low bit is not evidence. `gic_errors` counts
failed queries, not affected interrupts. Active inside the ISR is expected.
A pending bit is a controller observation, not proof of a particular peripheral
source; a zero pending bit while active does not establish a correctly cleared
line after EOI. No claim of broken EOI follows from this capture alone.

Sixteen exact-image CRC guards cover the vendor ISR/status/control getters and
the generic GIC query, descriptor lock/unlock and GIC leaf. Attachment also
requires IRQ19/hwirq69, the exact chip getter and absent bus-lock callbacks.
Unknown mappings/configuration refuse rather than entering unqualified callbacks.
The single-A7/no-SMP ABI remains the observed448-byte module layout.

Aggregation is bounded to64 exact tuples and200,000 captures; unseen tuples
increment overflow, and the ceiling resumes original execution without further
capture. The report copy uses a bounded~1.9KiB stack frame, below the kernel's
8KiB thread stack but above its1KiB compiler warning threshold; this is not an
A7 stack high-water measurement. Two8KiB userspace sample buffers and a64KiB
RAM report hold results; SD flushing follows detach/unload. No per-event clocks,
allocation or SD work. Added A7 cost is unmeasured; capture-period IRQ rates
cannot establish a speed improvement.

## Qualification and publication

Offline compiled tests execute the original vendor ARM handler and its helpers,
plus the actual generic IRQ getter, descriptor lock/unlock, dispatch and GIC leaf
against RAM. Radix/TTY/module/proc APIs remain fixtures.52 original/intercepted
cases include0x531f/0x5397/0x539f, both software TX states and empty/nonempty queues.
They compare all UART/port/state/ring bytes, status read counts, TTY calls,
callee-saved registers and return. All8 GIC combinations preserve register RAM;
three getter failures are represented explicitly. Ownership conflict, wrong
mapping/bus callbacks, allocation/pin failures, overflow and cap paths are checked.
Actual ARM module relocation matches independent ELF relocation byte-for-byte.

Eighteen owner/actual-firmware-shell check groups cover clean completion,
cancellation, load/read/stop/unload failures, consumed reboot and withholding
stock on uncertain restoration. A report exceeding4KiB verifies the larger tuple read buffers. These do not prove physical load, capture or
A7 timing for this new build. All prior published proof hashes are preserved.

Build: `python build/prepare-uart-pair.py`, WSL
`sh build/build-uart-pair.sh`, then `python build/check-uart-pair-observer.py`
and `python build/check-uart-pair-package.py`. Interpreted proofs are under
[evidence](../evidence/2026-10-15/uart-pair/qualification.json); vendor images,
module payloads, ROM and progress stay private.

## Physical pass and falsifiers

Installation requires a fresh strict archive, clean FAT serial11EB-1465, all
protected stock/ROM/progress hashes and clean exact source pushed to GitHub.
Use only the guarded new-version installer with that archive. The sole marker
is consumed before module load; a later reboot is stock. The probe observes
idle startup for about7 seconds overall, with a5-second capture interval,
then restores/unloads and permits ordinary stock startup. Wrapper watchdog is
20 seconds plus2 seconds for cancellation. Return the card after stock starts;
if startup stalls, power off and return the card without rerunning it.

Required returned evidence: exact source/payload/marker identity; successful
load, nonoverflowing conserved tuples and branch counts; explicit getter validity;
IRQ growth consistent with captured calls within sample brackets; restore,
frozen report, ordinary unload and owner exit0. Archive before any rearm.

Dominant0x531f with TX enabled supports an unserviced TX condition. The same
status with both TX enables off rejects the simple persistent-enabled-TX model
and directs the next step toward raw/latched source state or routing. RX selection
would reopen the noise/error path. Neither enabled-source correlation nor an
IRQ count proves cycle savings: a later source-specific reversible intervention
must remove the flood and restoration must reproduce it before calling it causal.

Physical result: **PENDING**. Production gate: **false**.

## Installation verified - 2026-10-15

I: is armed once with source `ec8ec39f79200c1f6f7a00cc192b9e2aa132c84b`, pushed
before installation. Fresh private archive `a7-pair-before-20261015T051423Z`
preserves7,813 files/1,937,139,157 bytes. All7,812 protected prior files, stock
boot binaries/init, FFVI ROM and private progress verify unchanged; only the
owned dispatcher and sole one-shot marker change alongside the separate four
new payloads. Exact payload readback and FAT health pass before installation,
after payload and after arming. All944 previous published proof hashes remain
exact. [Installation receipt](../evidence/2026-10-15/uart-pair/installation.json).

Boot once, allow the probe to finish and stock menu to appear, then power off
and return I:. No gameplay is needed. If startup remains stalled after30 seconds,
power off and return the card. A consumed marker makes the next boot stock.
The actual source correlation and new module's physical result remain pending.

## Physical return - 2026-10-15

Captured paired enables and pending/active/unmasked GIC state in all12,340 calls.
Restore/unload pass; I: unarmed. [Complete result and boundaries](uart-pair-return.md).
