# Rearm the accepted kernel UART fix — 2026-10-17

The user reports charging until the indicator turned green, followed by normal
battery behavior, and explicitly requests flashing the UART fix again. This
supports a depleted battery as the explanation for the earlier symptom. The
stock ADC timeout/error-handling defect remains a demonstrated software path,
but it was never observed on the physical unit and is not established as the
cause. No ADC, charging or battery thresholds are changed by this reflash.

Reuse the exact final `uart-kernel1` image, already accepted by two full physical
SPI reads and powered idle IRQ checks before the diagnostic rollback. This is
the driver correction within the kernel; normal SD init invokes no UART patch
module. The retained kernel is a source-defined in-place binary correction of
the vendor kernel, not a full vendor-source rebuild. Both Vesper boot screens,
entire rootfs and all bytes outside the kernel section stay exact, apart from
the updater's known CRC/time metadata.

| Artifact | SHA256 |
|---|---|
| Update package | `b2f8b286095f189ad9d0cad30320212f88a1b59e761ee7120aa9d45bab44dfeb` |
| Candidate image | `eddd7444deb1cf0634ab409a595bcfceed3a8ce7072e2af69e71f9f7aa689ef7` |
| Expected programmed image | `ef69753afb56c84e4daaf78aa3fad5551d26b7438e49f4f1dbc7312b11e07321` |
| Normal card init | `b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7` |

## Qualification and staging

Existing 26-group firmware qualification, all source/artifact hashes, complete
WQW ZIP/CRC/candidate equality and the exact 64-KiB decompressor heap receipt
verify. Fresh execution of the exact ARM driver checks passes all 7,344 modeled
states and 256 PutChar values, including synchronous wakeup refill and RX-before-
TX service. Fresh captured-updater execution accepts upgrading the rollback
Wings2 baseline, performs 38 erases and 9,728 page programs in RAM and produces
the qualified image. These fresh checks do not themselves prove physical flash.

The historical installer requires another update already staged. The new rearm
path instead requires an unarmed card, either exact proven card-UART init or
normal init, the qualified package and complete sparse-return preservation.
Eleven success/refusal/interruption/FAT/readback fixtures pass without card
access. It restores exact normal init first, verifies protected content and FAT,
and adds `retro/update/Code.bkp` last. Failure removes only its owned trigger and
restores the previous init after a healthy-FAT gate. It never creates or flashes
a new firmware variant. The independent checker accepts either adding or
replacing the trigger and counts protected existing files accordingly.

Fresh sparse return `uart-kernel-return-20261017T095232136007Z` retains 1,600
existing files with zero new content bytes and clean FAT. The only authorized
existing-file change is `retro/init`; the only added file is the exact update
trigger. Every other file, including stock programs, ADC configuration, saves,
private states, earlier UART module/helper/wrapper and unique evidence, is
protected by complete hashes. The existing host rollback package is reused.
No full backup or game test.

Arming completion is recorded by the [installation receipt](../evidence/2026-10-17/uart-kernel-reflash/installation.json)
and [independent full card/ZIP/FAT check](../evidence/2026-10-17/uart-kernel-reflash/live-verification.json).
[Rearm fixture qualification](../evidence/2026-10-17/uart-kernel-reflash/staging-qualification.json).

## Physical procedure

After verified staging, safely eject I:, insert with the handheld off, connect
reliable charging power and boot. Leave power connected and let the update
finish without interruption. If it powers off at completion, turn it on again.
Confirm Vesper static screen → Vesper animation → stock launcher. No game test
runs. Shut down normally and reconnect I: for return collection before mutation,
exact used-trigger removal, and fresh kernel/UART verification. Arming I: is not
confirmation that this reflash has happened. No automatic rearm.

The previous battery/ADC observations remain in [the trace](stock-battery-trace.md);
the earlier kernel's physical acceptance remains in [the powered return](uart-kernel-return.md).
