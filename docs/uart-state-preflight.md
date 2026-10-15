# UART state1: snapshot preflight — 2026-10-14

**Installed and armed on I:** exact pushed source`3892f2a` precedes the install.
Strict archive`a7-pair-before-20261015T021858Z` preserves7,797 files/
1,937,074,272 bytes. All7,796 protected prior files, ROM/progress and four installed
payloads verify; FAT is clean before/after payload/after arm. Only the existing
dispatcher, one-shot marker and separate`retro/uart-state1` package change.
[Installation receipt](../evidence/2026-10-14/uart-state/installation.json).
Safely eject, boot, wait for the stock launcher, leave it there about30 seconds,
then power down and reconnect I:. If stock has not appeared after a minute,
power down and return the card; do not repeatedly rearm it. Next boot after the
consumed marker is stock. Physical results remain pending.

The matching vendor source is still unlocated after targeted public code and
repository searches. We no longer depend on locating it to prepare the first
observation: an upstream-header reconstruction matches the independently
observed ABI used by this small module. This is not a recovered full vendor
configuration or a replacement kernel build.

## Current boundary

The module and owner pass27 offline checks:15 compiled-module/actual-relocator
checks and12 owner/firmware-shell checks. Physical module loading, snapshot
operation and unloading remain pending. No source-level UART fix or A7 saving
is claimed. This preflight observes idle boot before stock starts; it does not
alter or run the SNES spell suite. The card installation is recorded separately.

## How the build interface was reconstructed

The official upstream4.19.128 archive matches the checksum published over HTTPS
by kernel.org:
`29aba6849c972c0079ddee4aaf476a500ef52d937c7ba02ceec4c7cf4753613c`.
This checks the download against the published digest; no OpenPGP signature
verification is claimed. Source and private host-tool packages stay outside Git.

The shipped modules independently establish448-byte module objects,
init/cleanup relocations at`0xe8`/`0x1a0`, and vermagic
`4.19.128 mod_unload ARMv7 p2v8 `. Actual kernel code independently accesses
core/init layout at`0x100`/`0x130`, kallsyms at`0x174`, name at`0xc`,
and the refcount at`0x1a4`. The reconstruction matches those fields. PERF_EVENTS
selects the module address tree; unused-symbol fields, generic bug tables and
frame-pointer/non-unwind options resolve observed layout differences. No
configuration was installed on the handheld.

The observed UART header includes two console/sysrq words. The offline ABI
artifact selects that header shape explicitly, yielding264-byte uart_port with
membase4, IRQ72, state100, RX120, TX124, ops184 and line192, matching the actual
vendor instruction offsets. The live observer reads only pinned fields through
fault-aware kernel reads; it does not cast an assumed generic irq_desc layout.

The exact kernel supplies4,394 verified text-symbol export entries, including
all imported observer APIs. The module is GPL and modversions are absent. No
force-load flag, copied vendor module body, kernel-text patch or IRQ-pointer
replacement is used. The compiled refusal-only ABI artifact is never installed.

One compiler interaction required explicit correction: Linux4.19's architecture
capability probe fell back to`-march=armv5t` under GCC13, whose assembler target
then rejected CPSID despite ARMv7 kernel configuration. Explicit ARMv7 module
flags fix the emitted ISA. This does not touch the emulator or APU compilation.
The userspace owner is linked against the captured glibc2.30 with explicit
32-bit time/file settings and requires only GLIBC_2.4/GCC_3.5 symbols.

## What executes and what stays unchanged

The4760-byte module validates symbol addresses and CRCs of seven complete
functions before exposing its owned0400`/proc/d35_uart_state` entry. CRCs are
build-identity checks, not cryptographic live-kernel attestation. For each read
it briefly excludes local IRQs on this observed single-core non-preemptible
kernel, verifies IRQ19 still belongs to the original ISR and UART0, checks the
port and queue, then calls the exact driver's existing control-register getter.

It reports control bits, software flags, TX/RX counters, queue head/tail and
hardware/software TX-enable mismatch. It never reads interrupt status or FIFO
data, writes UART configuration, replaces a handler, creates a polling thread,
prints per IRQ, or adds work to each interrupt. This avoids introducing extra
reads of status whose side effects remain undocumented. Snapshot entry/exit
times measure snapshot scope, **not UART handler duration**.

The one-shot wrapper consumes the existing marker before any module syscall.
The owner refuses an existing module/proc entry or an existing result file;
uses`finit_module(...,flags=0)` and non-forced`delete_module(...,O_NONBLOCK)`;
retains a durable pre-load record; takes100 snapshots at nominal50ms spacing;
and records one-second IRQ baselines before loading and after unloading. Samples
stay in RAM until teardown. A refused snapshot stops sampling and still attempts
owned-module cleanup. Expected capture is about7 seconds plus load/sync/startup.

Normal completion unloads the module and returns to the existing stock startup.
The wrapper requests cancellation after20s and later kills only its owned
process. A kernel-blocked operation can still require a power cycle; it is not
claimed to be killable. Its consumed marker makes the subsequent boot stock.
No persistent kernel/rootfs/flash change is made. Existing init, ROM, saves,
cores and production executables remain protected by archive/hash/FAT gates.

## Verification and interpretation

The actual archived ARM`apply_relocate` routine accepts the compiled observer
and produces bytes identical to the independent ELF relocation fixture. The
compiled module executes against anonymous RAM, with the original GetCtrl and
irq_to_desc instructions and a fixture radix lookup. Fourteen additional checks
cover matching/mismatched TX states, wrong ownership/IRQ, unreadable state,
changed code, failed creation and cleanup. These do not boot the kernel or prove
its real module-loader lifecycle.

Ten native ARM owner fixtures cover normal capture, wrong kernel, existing
module, load/unload/read failures, refused snapshots, cancellation, sync failure
and preserved existing logs. Exact captured BusyBox checks syntax and executes
the wrapper with a fixture owner, including consumed-marker replay refusal.
That execution caught Windows CRLF generation in the fixture/dispatcher; both
generated scripts now explicitly write LF bytes. All publication metadata
labels mocks/offline evidence and pending physical results.

On return, require matching installed payloads/consumed marker, fresh result,
zero cancellation, successful load and unload,100 valid snapshots and a removed
module/proc entry before calling the preflight complete. Retain failures. If a
TX hardware/software mismatch persists while IRQ counts rise and RX is flat,
the conditional stop-TX lead gains direct state evidence. It still does not
identify the original interrupt status or prove what created the mismatch.
If the mismatch is absent, do not force that hypothesis: pursue original-status
observation next. A subsequent isolated reversible experiment can test causality
only after the source state is established. IRQ cost remains a separate question.

Reproduce offline with:

```text
python build/prepare-uart-state-observer.py
wsl --exec sh build/build-uart-state-observer.sh
python build/check-uart-state-observer.py
wsl --exec sh build/build-uart-state-owner.sh
python build/check-uart-state-package.py
```

The build script expects the verified source and private host-tool cache prepared
for this investigation; it refuses missing prerequisites. It builds modules only,
never a kernel image. Private package/metadata are under
`build/uart-kernel-private/`; interpreted proofs are published separately.
