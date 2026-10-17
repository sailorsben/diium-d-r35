# UART correction directly in the kernel — 2026-10-16

The user requested replacing the boot-time module approach with a driver
correction in the kernel itself, preserving both Vesper screens, saves and
evidence, and arming I: without a full backup. This candidate supersedes the
previously staged module-based firmware; that earlier image remains archived.

This is a source-defined **in-place binary correction of the exact vendor
kernel**, not a full rebuild from complete vendor kernel sources. The corrected
driver instructions are present when Linux decompresses. There is no module
load, IRQ-action replacement, code cave, extra executable allocation, or startup
patch. Original ISR entry/address/IRQ registration and RX instructions stay exact.

## Driver correction

The original ISR tests FIFO-empty (`0x80`) and ignores TX-pending (`0x4000`)
when the FIFO is nonempty. The replacement TX body tests pending, requires both
hardware and software TX enables, honors urgent characters and flow control,
checks TX_FULL and writes at most one byte per IRQ. It advances the queue/counter
once, wakes writers below the original threshold and stops TX when appropriate.
Original status is read once; RX service precedes TX on mixed interrupts.

The original `gpHalUartPutChar` independently substitutes literal zero for its
supplied character. Its corrected instruction passes the supplied byte. This is
a deliberate additional fix beyond the card-tested module, which preserved that
vendor defect. Actual serial wire contents, sustained throughput and A7 cost
remain physical acceptance boundaries. Shared-IP TX_FULL semantics retain the
prior hardware-documentation limitation; a FIFO model is not silicon proof.

Only four bounded regions change in the 7,476,028-byte decompressed kernel.
The 184-byte owned TX assembly and 12-byte stop tail fit existing TX regions;
the pending test and PutChar instruction are four bytes each. Register/state
addresses and every other kernel byte remain exact. Kernel symbols/module ABI
layouts retain their addresses, but old UART patch-module CRC guards will refuse
this corrected kernel. Normal SD init is therefore restored byte-for-byte to its
original hash, removing its UART-module hook. Old module files/evidence remain.

## Boot image and screens

Baseline is the expected programmed Wings2 image
`5c2f34e6b4451b27fa5e6782f1396d8e6a3bf485e24c0fe209b44854f77660c3`.
Wings2 was user-reported successful; a complete post-Wings2 SPI readback remains
pending. Earlier static-screen firmware had two matching complete physical reads.

Both static bitmap and showlogo/Wings2 payloads remain exact. The entire rootfs,
startup scripts, device tree, section table and all flash outside the kernel
section remain exact before the vendor CRC/time update. The candidate includes
none of the prior module-firmware rootfs additions. The captured updater also
accepts upgrading from that prior module candidate in RAM.

Recompression preserves the exact zImage length, wrapper, data addresses and
footer. A supported gzip filename field fills the gained space, keeping ISIZE
at its original address used by head.S. The **actual captured ARM decompressor**
produces every expected kernel byte for original and corrected images.

| Artifact | SHA256 |
| --- | --- |
| Candidate | `3b22fe71b6c502cbb921a2dc751cd8d210ddc25e586ece30c9f5bdb168066fb4` |
| Expected programmed image | `45ef4ea3fbe599bf7cc633c601e7033d6f3a27569b932a8d6697906c31b946ff` |
| Update package | `bc0bdb689361271d75c522da634006d214ffac4f274700e6e79239016566965f` |

## Qualification and negative results

25 groups pass: old-code controls reproduce both defects; 24 original/corrected
RX/no-TX state comparisons; all 256 PutChar values; 7,344 independent FIFO,
queue, enable, flow, urgent and ring-wrap combinations; 300-byte draining retry;
mixed RX/TX and callee-register checks. Actual kernel instructions execute
against RAM; peripheral/TTY callbacks remain independent fixtures.

Additional groups cover independent GNU gzip expansion; original ARM zImage
self-decompressor for both images; actual Thumb static-screen and section loader;
original ARM vendor updater acceptance from Wings2 and prior module firmware;
family/CRC/prefix/repeated-update refusal; exact splash ZIP decode and all 18
Wings2 frames; original normal SD init and firmware shell syntax. The Wings2
update simulation performs 38 erases and 9,728 page programs in RAM, including
metadata block 0, and produces the expected full image. It does not qualify
physical programming or external recovery.

Two negative findings are retained privately and in qualification metadata.
FEXTRA was valid to GNU gzip but rejected by the captured ARM decompressor;
FNAME passes both. An initial TX body relied on caller-clobbered r3 surviving
PutChar; the independent callback exposed a queue error. The final body reloads
the ring tail. No failed candidate was written to I:.

Eight staging fixtures cover success, interruptions after init/package writes,
both post-write filesystem failures, changed init/trigger and competing test.
Rollback restores the exact prior staged update and init after a healthy-FAT
gate. Private firmware, decompressed images and raw fixture bytes stay excluded
from publication. Qualification is offline; physical boot, UART IRQ behavior,
real wire output, normal launcher and full-image readback remain pending.

## Card and next boot

Fresh sparse archive: `uart-kernel-before-20261017T011353008133Z`. No new full
backup is made. Only the known `retro/update/Code.bkp` and `retro/init` may change.
All other card files, including saves, previous results, stock programs and old
UART payloads are protected. No emulator test is armed.

**Status: QUALIFIED; replacement staging/readback pending.**

After verified staging, safely eject I:, insert while powered off with sufficient
battery, and boot normally. Let the update complete without interrupting power.
If it powers off at completion, power on again. Confirm Vesper static -> Wings2
animation -> stock launcher, then power off normally and return I:. Collect
before mutation and remove only the exact known update trigger after FAT/hash
checks. No automatic retry. Kernel boot, IRQ/error behavior and complete SPI
readback must be verified from the physical return. External recovery remains
unqualified, as in the prior authorized firmware updates.

[Preparation](../evidence/2026-10-16/uart-kernel1/preparation.json) ·
[Qualification](../evidence/2026-10-16/uart-kernel1/qualification.json)
