# UART TX1: reversible pending-service correction

Ben authorized building, validating and arming this test after the paired
capture found12,202/12,340 ignored entries with TX enabled and GIC pending.
This is a bounded diagnostic correction, not a persistent driver replacement.

## Correction and FIFO contract

The module loads with the original IRQ19 action untouched. An explicit control
read attaches the guarded correction and pins the module; restoration puts the
original action back, drains IRQ19, then drops that reference. Kernel text and
firmware stay exact. Attachment requires the observed module ABI,14 exact-image
CRC guards, IRQ19/hwirq69, original handler/dev_id, port type/state and FIFO8.

Each corrected call reads the original status once. RX-priority cases, original
FIFO-empty TX cases and statuses without TX-pending resume the original ARM ISR
body at`c01177f8` with the same entry value/frame. No fabricated status bit or
extra status read is passed into that body. Original empty-FIFO batches retain
the initialized size8/half-size4 behavior.

Only the previously ignored TX-pending, nonempty-FIFO case adds service, and
only when hardware/software TX enables agree and are set. It checks urgent
characters first, empty/stopped queues, then TX_FULL0x20. A full FIFO gets no
write. Otherwise it writes **at most one byte**, preserves the original PutChar
function, advances the ring tail/counter once, retains the original wakeup
threshold and calls original stop-TX when the queue empties. An urgent character
does not dequeue the ordinary ring. Flow-control stops use original stop-TX.

The initial full indication suffices for the one-byte bound under the existing
single-A7, IRQ-disabled serial-ownership contract: no normal producer can add a
byte concurrently, and the transmitter can only drain while this handler runs.
The module does not assume four free slots from a pending indication. Runtime
FIFO-size or invalid-ring drift refuses added service and records a fault;
restoration still succeeds if IRQ action ownership matches. An actual action/
port ownership conflict refuses restoration and keeps the module pinned.

Three hash-pinned matching UART-IP headers define TX_FULL0x20. Their definitions
are checked in preparation. The exact GPA7 silicon manual is still unavailable;
the FIFO proof is conditional on that shared-IP flag contract. The occupancy
model does not prove physical full-flag semantics or wire contents. The original
literal-zero PutChar behavior remains unchanged and separately unresolved.

## Run order and measurements

Before stock startup, five5-second phases run in this order:

1. Original0: original action, no interception.
2. Corrected0: temporary one-byte pending service.
3. Restored0: original action restored/drained.
4. Corrected1: second temporary correction.
5. Restored1: original action restored/drained again.

The owner also takes one-second unloaded bookends, making about27 seconds plus
snapshot/loader overhead. The wrapper allows45 seconds, then TERM and2 seconds
for cleanup before its owned-child KILL fallback. Uncertain teardown withholds
stock startup; the consumed marker makes a later reboot stock.

Snapshots record kernel-syscall clock brackets, IRQ19 counts, aggregate CPU
jiffies, FIFO/queue/enable state, TX/RX/error counters and correction aggregates.
There are no per-IRQ GIC calls, clocks, histogram scans, allocations or SD writes.
The hot path has bounded counters and the actual service work. Results remain
in RAM until restoration/unload, then flush durably. Cancel/read/CPU/attach/
detach/unload failures all attempt final restoration and retain failure logs.

## Offline qualification and physical acceptance

Seventeen compiled groups include byte-for-byte agreement with the actual ARM
module relocator;40 original-vs-bridge cases;153 FIFO occupancy/queue cases;
full-to-draining retries delivering100 queued bytes; one-slot/wrap, urgent,
TTY/hardware stop and wakeup tests; runtime drift; ownership conflicts; repeated
attach/restore; proc/pin failures and the200,000-call cap. Actual vendor status,
PutChar, stop-TX, ISR tails and IRQ lookup execute against RAM. FIFO status and
capacity, radix/TTY/module/proc APIs are fixtures, not a physical board model.

Twenty-one owner/actual-firmware-shell groups verify phase order, two enables,
three successful disable acknowledgments, ordinary unload, cancellation,
missing/failed CPU reads, service faults, attach/stop/read/unload failures,
consumed reboot and withholding stock on uncertain cleanup. User-space ABI
requires only the existing GLIBC_2.4/GCC_3.5 versions. Emulator/APU code and
compiler output are untouched. All previous proof bytes are preserved.

The physical pass must show lower IRQ rates in both corrected phases, continued
queue/TX progress without added UART errors, and return of the flood in both
restored phases. It must also establish exact payload/marker identity, FIFO8,
zero faults/bypass, final restore/frozen report/unload/exit0 and healthy returned
storage. A missing flood restoration or poor TX progress falsifies acceptance.

Measured A7 saving and added handler cost are unknown. Coarse CPU jiffies do not
measure interrupt duration, especially with kernel IRQ-time accounting disabled.
Remaining SNES audio deficit/reserve is unmeasured here; no numerical audio
benefit or production promotion is predicted from IRQ counts alone. This
diagnostic establishes a causal result before any performance claim.

Fresh strict archive/FAT/stock/ROM/progress checks, exact source pushed first,
separate`uart-tx1` payloads, sole dispatcher/marker and readback verification are
required to arm I:. Boot once and wait for stock startup (normally roughly30
seconds for this test), then power off normally and return I:. If startup has
not appeared after60 seconds, power off and return the card for the preserved
failure evidence. No firmware flash is needed for this run.

[Preparation](../evidence/2026-10-15/uart-tx/prepared.json),
[compiled qualification](../evidence/2026-10-15/uart-tx/qualification.json),
[owner/package qualification](../evidence/2026-10-15/uart-tx/package-qualification.json).
Physical result **PENDING**; production gate **false**.

## Armed installation - 2026-10-15

Exact source a173f82da398a3a205bb3188a2d1ccfdc60a853a was pushed before
installation. Private archive a7-pair-before-20261015T060116Z preserves the
unarmed baseline. All7,820 protected prior files, stock/init/ROM/private progress,
four new payloads, dispatcher and sole marker verify unchanged/exact as applicable.
FAT checks pass before installation, after payload and after arming. Independent
readback confirms all payloads, dispatcher and marker; no firmware trigger exists.
All956 earlier published proofs retain their hashes. Physical result pending.
[Installation receipt](../evidence/2026-10-15/uart-tx/installation.json).

## Physical return - 2026-10-15

Both corrected intervals suppress the idle flood by about99%; both restorations
reproduce it with queue/TX progress and no added observed errors. Restore/unload
pass; I: unarmed. [Results and boundaries](uart-tx-return.md).
