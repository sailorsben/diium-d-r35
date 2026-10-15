# UART status1: original interrupt status and branch capture

**Installed and armed on I:** exact pushed source`0b90c2d` precedes deployment.
Fresh archive`a7-pair-before-20261015T031253Z` preserves7,805 files/
1,937,114,927 bytes. All7,804 protected prior files, stock binaries, ROM and
original progress match; four payloads and dispatcher/sole marker read back
exactly. FAT is clean before install, after payload and after arm. Existing
state1 logs stay intact. [Installation receipt](../evidence/2026-10-14/uart-status/installation.json).
Physical interception/status/branch results remain pending.

The state1 return leaves IRQ19 flooding with no persistent TX-enable mismatch.
This probe captures the **actual status value returned by the original ISR's
entry read**, then continues the original handler at its first status test.
The physical status/branch result is pending. This is a diagnostic, not a UART
fix or a performance candidate; no A7 saving or gameplay improvement is claimed.

## Interception and measurement scope

The exact archived kernel's ISR starts at`c01177dc`. Its six-instruction
prologue establishes a48-byte frame and saves r4-r8/fp/ip/lr/pc, then calls
`gpHalUartGetIntSts` at`c0117314`. The bridge reproduces that prologue, invokes
that same getter once, preserves r0-r3/ip/lr around a RAM-only callback, and
jumps to`c01177f8`. The original TST and subsequent ISR body execute in place.
The bridge's saved diagnostic PC points into the module; functional frame,
return and callee-save behavior are preserved. No kernel instruction is patched,
no vendor body is copied into generated executable memory, and there is no extra
status or FIFO read. The original RX loop still makes its own normal reads.

The callback counts full32-bit entry values in32 bounded histogram slots, with
explicit overflow, first/last, OR/AND, handler return counts and these branch
selections:

| Selection | Exact original test |
| --- | --- |
| RX first | `status & 0xa000` |
| TX only | No RX bits and `status & 0x80` |
| Neither recognized | Neither RX nor TX bits |
| RX followed by TX | RX selected and initial`status & 0x80` |

These are selections determined by the captured entry value and unchanged
original tests, not sampled PCs or a count of every internal RX/TX sub-branch.
The original RX path retains the entry value in r5 and tests its TX bit after
RX completion. Forty original-vs-intercepted ARM executions validate these
selections against receive delivery/transmit effects. Captures stop aggregating
at200,000 entries and bypass to the original ISR thereafter; bypass count is
explicit. There are no per-IRQ clocks, allocation, printk or SD writes. This
probe does not measure handler duration or total observer overhead.

The owner records one-second IRQ baselines before loading and after unloading,
an initial report, a report after five seconds, then a frozen report after
detachment. Histogram counts include the brief attached startup/stop margins;
they are not falsely assigned to exactly five seconds. The capture is idle,
before the stock launcher. A status-only capture avoids emulator variables.
Reported IRQ rates during interception may be disturbed by its added work.

## Ownership, lifetime and failure behavior

The exact single-core, non-preemptible kernel and physically tested448-byte
module ABI remain the prerequisite. Twelve complete function CRC guards include
the ISR, getter, dispatch, ownership lookup, synchronization and module reference
functions. Addresses, port type/IRQ/state, current action handler and dev_id are
checked before changing the handler pointer. CRC guards identify this build;
they are not cryptographic attestation against malicious root/kernel changes.

Only the verified IRQ19 action handler word is temporarily replaced, under local
IRQ exclusion. Its dev_id, chain, flags and all UART registers remain unchanged.
A live module reference pins the hook. Detach revalidates the same action and
owner, restores the exact original handler, synchronizes IRQ19, then drops that
reference. Ownership conflicts retain the reference and refuse restoration;
ordinary non-forced unloading must then fail rather than free live code.
Proc teardown drains reads before module code is freed. No forced module calls,
UART-source masking, global console changes, kernel/rootfs or flash changes.

The wrapper consumes the existing one-shot marker before loading. The owner
uses direct kernel-clock syscalls and relative waits, holds reports in RAM until
detachment/unload, and attempts stop even after read failure/cancellation. The
wrapper requests TERM after20s and later kills only its owned process. On any
owner failure it durably records the result and **withholds stock startup** until
power-cycle, rather than continuing with uncertain restoration. Kernel-blocked
syscalls are not claimed killable. The consumed marker makes the next boot stock.

## Qualification and physical result contract

Twelve compiled-module check groups pass, including the actual archived ARM
module relocator matching independent ELF relocation byte-for-byte,40 original
versus intercepted handlers, equal status-read counts, preserved return/r4-r11,
exact RAM/register/queue effects, RX/TX branch selections, full32-bit histogram,
ownership conflict, ref/drain/restore ordering, initialization failures,
idempotent cleanup, overflow and the200,000-entry bound. Kernel lifecycle APIs
are fixtures in these tests. They do not establish physical hook safety/timing.

Seventeen owner/firmware-shell checks pass: target GLIBC_2.4/GCC_3.5 ABI, normal
capture, wrong kernel/existing owner, load/unload/read/refused status, cancellation,
initial sync, existing logs, failed/refused detach, frozen-read failures, actual
firmware BusyBox syntax/execution/consumed reboot, and failed-detach withholding.
The ARM memcpy fixture is explicitly typed as ARM, matching the kernel import;
the independent relocator refuses unsuitable Thumb branch targets. The first
fixture run caught that host-library ABI seam before installation.

Reproduce from the existing verified kernel/toolchain cache:

```text
python build/prepare-uart-status.py
wsl --exec sh build/build-uart-status.sh
python build/check-uart-status-observer.py
python build/check-uart-status-package.py
```

Source and interpreted proof metadata are published; private kernel, payloads,
ROM, progress and raw card logs remain excluded from Git. All prior evidence
hashes must remain exact. A fresh strict archive/FAT/hash gate precedes a separate
`retro/uart-status1` install from clean pushed source. Only its package, existing
dispatcher and one-shot marker change; stock binaries/progress stay protected.

On return, require exact payloads, consumed marker, successful restoration,
non-forced unload, frozen attached=0, owner exit0 and no cancellation. Verify
`rx + tx_only + neither == total`, `rx_then_tx <= rx`, histogram sum plus overflow
equals total, handled/other returns sum equals total, and retained reports are
monotonic. Preserve and interpret failures rather than manufacturing a result.

Dominant neither-recognized status would identify a repeated source the ISR
does not handle in its RX/TX branches. Dominant RX or TX selects that specific
driver path instead. Preserve the actual full status values; assigning names
to undocumented bits or proving an electrical cause may need further evidence.
A reduced interrupt count alone is not a fix or proof of recovered CPU budget.

After the recorded arm: safely eject I:, boot once, wait for stock, leave it
about30 seconds, power down and return the card. If stock has not appeared after
a minute, power down and return the card without rearming. Expected normal
capture is about seven seconds plus module/sync/startup time.
