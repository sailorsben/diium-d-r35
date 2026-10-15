# IRQ19: exact kernel investigation — 2026-10-14

**Follow-up:** [UART state1 preflight](uart-state-preflight.md) reconstructs the
small observer's independently observed module ABI and passes27 offline checks,
including the actual kernel relocator. The snapshot-only first probe is now
built; physical load/read/unload and the live interrupt cause remain pending.
This supersedes the earlier unbuilt-observer prerequisite below, not its safety
or evidence boundaries. Full vendor source/configuration remains unlocated.

IRQ19 remains active in the latest physical run. The archived draw-order suite
starts at kernel uptime8.26s with150,669 UART interrupts and ends at980.69s with
6,880,798: **6,730,129 interrupts in972.43s, approximately6,921/s**. UART accounts
for92.32% of the increase in all interrupt counts. These whole-suite endpoints
include emulation, flushing and teardown; separately sampled uptime/IRQ reads
make the rate approximate. Count share is not CPU-time share.

The cause and A7 cost remain unproven. The investigation now has exact driver
code, reproducible failure-state fixtures and a more precise measurement gate.
No card access, rearm, register experiment, kernel/module installation or flash
change occurred. The SNES core and its APU compiler output are unchanged.

## Evidence and reproducibility

The previously authorized, two-pass matching SPI backup supplies the kernel;
this is offline inspection of an existing archive, not a new memory/flash read.
`build/inspect-uart-kernel.py` checks the exact8MiB flash SHA and kernel-section
SHA, decompresses the bounded embedded gzip and checks the7476028-byte image:

`21cc93e3f621c410ebe4174c0ab00aa4f0b21887c1698bbe974ffbeead2f0321`.

The Linux banner matches the runtime:4.19.128, Buildroot GCC9.3.0, build#56,
September5,2024. Decoding the base-relative kallsyms table recovers17,533 symbols;
**all242 retained built-in runtime symbol/address/type triples match**. Loadable
module symbols are deliberately excluded from that built-in comparison.
Private extracted bytes, complete symbols and disassembly stay under ignored
`device-evidence/uart-kernel-offline/`.

Run `python build/check-uart-kernel.py` from the repository root with the existing
private Capstone/pyelftools dependencies and WSL ARM compiler/QEMU installed.
The C harness executes the actual archived ARM instructions, uniformly relocated
into anonymous user RAM. Its UART registers, serial-port state and transmit ring
are RAM fixtures. Three external tty delivery/wakeup calls are intercepted.
The kernel is never booted and no hardware address is mapped. Six checks pass;
QEMU provides branch/side-effect evidence, never handheld timing.

[Published metadata and source/input hashes](../evidence/2026-10-14/uart-kernel/research.json).

## What the shipped UART code does

| Path | Exact code behavior | Implication |
|---|---|---|
| `gp_uart_start_tx` at`c011751c` | Sets software flag`port+0x108 &2` and control bit`0x4000`, but returns immediately when the software flag is already set | Software and hardware enable state are assumed coherent |
| `gp_uart_stop_tx` at`c011755c` | Returns immediately if that software flag is clear; otherwise clears both it and control bit`0x4000` | Hardware TX can remain enabled if the two states disagree |
| `gp_uart_isr` at`c01177dc` | Reads status; enters receive branch for`status &0xa000`, otherwise TX branch for`status &0x80` | A status capture can distinguish these branches |
| Empty TX queue | Calls the conditional `stop_tx` above |1000 fixture calls with status`0x80`, control`0x4000`, software flag0 leave control enabled and TX/RX counts unchanged |
| Unrecognized status | Returns1 (`IRQ_HANDLED`) without a control write | A repeatedly asserted condition outside the handled paths can be reported as handled without being cleared |
| `gpHalUartPutChar` at`c01172fc` | Ignores its character argument and stores literal zero to the data register | The software TX counter does not establish transmitted content; queued-byte and direct-call fixtures verify this oddity |
| Receive branch | Increments the RX counter when it reads a byte | The original flat RX counter argues against repeated execution of this exact receive branch in those samples |
| Console output | Calls the polling character path without updating the ordinary serial TX counter | Low reported TX count still does not establish low total serial output |

The consistent empty-TX fixture clears the hardware bit correctly. The divergent
state fixture is therefore a concrete conditional failure, **not proof that this
state occurs on the handheld or that hardware reasserts IRQ19 in that state**.
The RAM model deliberately does not simulate undocumented UART interrupt logic.
Likewise, literal-zero output is observed code behavior, not a proven cause of
the high interrupt rate or evidence about bytes on a physical wire.

Do not invent a console/ISR race to explain the divergence: the ordinary
`console_unlock` code at`c015bd20` disables local interrupts before calling the
console writer and restores them afterward. This agrees with upstream
[Linux4.19 printk](https://raw.githubusercontent.com/torvalds/linux/v4.19/kernel/printk/printk.c).
A proposed alternate interleaving must establish its actual caller/context.

## Why existing telemetry cannot price this

The October4 stdout/stderr experiment remains a valid negative result for that
specific redirection. It leaves inherited console descriptors and kernel console
activity outside its scope. The historical rates are reproduced; nearby coarse
kernel-uptime endpoints independently retain an approximately7k/s scale. Their
read endpoints differ, so this is a cross-check, not a correction to the rates.

The exact symbol table contains no ftrace/tracefs/tracing infrastructure or
`irqtime_account_irq`/scheduler IRQ-time functions. The actual
`__handle_irq_event_percpu` path directly calls the registered action without
IRQ tracepoint calls. The actual `account_process_tick` uses the tick-accounting
path. These observations support those facilities being omitted in this build;
they go beyond the earlier ENOENT observations. Debugfs itself is present, so
missing tracefs is not a reason to assert that all debugfs features are absent.
Upstream [IRQ dispatch](https://raw.githubusercontent.com/torvalds/linux/v4.19/kernel/irq/handle.c)
and [CPU accounting](https://raw.githubusercontent.com/torvalds/linux/v4.19/kernel/sched/cputime.c)
provide the comparison contracts, not the vendor implementation.

There is also no `hrtimer_interrupt`/high-resolution activation path in the
decoded symbols. The earlier10ms waits, actual low-resolution call paths and
upstream [hrtimer configuration branches](https://raw.githubusercontent.com/torvalds/linux/v4.19/kernel/time/hrtimer.c)
support a kernel built without high-resolution timers. The complete build
configuration is still unavailable. Fine clock reads do not imply fine sleeps.
Keep this separate from the UART cause; do not replace event readiness with
busy-waiting or propose an unqualified kernel upgrade.

Consequently, zero reported IRQ ticks is not zero IRQ cost, main-thread CPU
clocks are not an independent IRQ stopwatch, and a missing-time residual cannot
be assigned entirely to UART. Software perf task-clock opened successfully in
the old probe; tested hardware PMU events failed with ENOENT. Neither establishes
a supported per-IRQ duration interface. Interrupt count multiplied by an assumed
duration remains a sensitivity calculation, never measured recovered budget.

## Required next physical diagnostic

**Follow-up:** the smaller [state1 physical preflight](uart-state-return.md)
now qualifies this package's load/snapshot/unload lifecycle. The flood persists
without a persistent TX mismatch in100 idle snapshots. Original status/branch
and handler-duration observation below remain unimplemented; the missing vendor
tree was worked around only for the narrow reconstructed snapshot ABI.

The next useful test is an **ABI-qualified kernel observer**, not another
userspace redirection run. It must preserve the original handler and return
value and gather bounded RAM aggregates rather than print per interrupt:

1. Count original status values and actual handler branches. Observe the value
   already returned by the existing status read; avoid additional reads of
   potentially destructive hardware status/data registers.
2. Record software TX flag, queue-empty state and hardware TX-enable state at
   entry/exit through a verified non-destructive driver seam. This distinguishes
   coherent TX, divergent TX and unrecognized-source hypotheses. Do not disable
   an interrupt merely because one of these states looks suspicious.
3. Measure original handler entry/exit with the kernel clock, with count/sum/max
   and a bounded histogram. A handler wrapper excludes exception/GIC entry and
   exit cost; label that scope. Include the observer's own added costs and a
   pass-through/count-only comparison. No per-IRQ SD writes or printk.
4. Compare bounded idle and unchanged full-output emulation phases, retaining
   actual frame/PCM/pointer/deadline evidence. A lower IRQ count alone is not a
   gameplay acceptance result. Preserve RAM results after the measured phase.
5. Before deployment, qualify registration, exact ABI, concurrent ownership,
   bounded stop/unload, restoration and unexpected-state refusal offline.
   Archive/hash/FAT gates and a separate one-shot package still apply.

This richer observer is **specified, not built or installation-ready**. The exact
matching vendor kernel source/generated headers remain unlocated in the local
references and targeted public searches. The archived stock CRC module provides
useful metadata: vermagic`4.19.128 mod_unload ARMv7 p2v8 `,
448-byte `.gnu.linkonce.this_module`, no`__versions` section. This is not enough
to certify a custom module ABI. Do not force-load a generic4.19 module, transplant
a vendor module body, patch IRQ pointers blindly, or use raw MMIO/`/dev/mem` as
a substitute. The next engineering prerequisite is a matching build interface
or another independently qualified kernel observation seam.

Only after the live source state is identified should a reversible UART change
be designed. Require restoration of serial ownership/state and a measured
whole-device benefit with identical emulation outputs. Production promotion,
firmware flashing and any promised A7 saving remain outside this result.
