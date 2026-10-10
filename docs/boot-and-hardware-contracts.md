# Boot and hardware contracts

These contracts were recovered from the exact shipped binaries and checked against returned runs. They are the prerequisites for a replacement userspace runtime, not a complete hardware SDK.

## Splash handoff

1. `showlogo` runs independently and repeatedly draws/flips its sprites.
2. Its `joytest` checks for `/tmp/vrtemu.log`.
3. Once signaled, it clears/flips, releases allocations and returns.
4. Its main routine destroys its display, then creates `/tmp/displogo.log` and exits.
5. Only after active `showlogo` processes have exited may our runtime call InitVFB.

The wrapper creates the stop marker and waits up to five seconds, ignoring zombies that have already released resources. A marker acknowledgment alone does not justify racing a still-active display owner. A timeout refuses to start a competing owner. Returned v1.2+ logs show PID disappearance and acknowledgment. Do not substitute a blind sleep or unrelated-process kill for the recovered handoff.

## One-shot execution and recovery

The [survey1 return](device-survey-1-return.md) loses later capture directory
entries despite successful file fsyncs and wrapper completion. Count/allocation
match the recovered chains exactly. Keep evidence completeness and FAT health
separate. Survey2 uses one indexed CRC32 bundle plus report; its first physical
return verifies all905 ranges and clean FAT. This is not general media/shutdown
qualification. Archive before checking health, but require healthy FAT before any
restoration write. A consumed hook already selects stock on the next reboot.

SPI ownership is separate from display ownership. Survey2 finds stock vrtemu
holding SPI0.0; the [ID probe](spi-identify-return.md) succeeds synchronously
before stock starts. The [full reader](spi-readback.md) uses the same placement,
consumes/syncs its marker first and joins its owned child before permitting stock.
No speculative storage commands, global mode writes or concurrent stock SPI
owner. Its240-second deadline can require reboot if a child remains kernel-blocked.
Archive complete/partial flash contents privately before any rearm or restoration.

The [1.18 return](snes-mvp-1.18-return.md) adds a storage boundary: two FAT backup
entries are unreadable and fresh fault/current SRAM files are zero bytes.
Preserve readable files and report incomplete collection explicitly. A partial
salvage archive is never a healthy install baseline; keep strict collection as
the default. Back up before repair and inspect recovered chains before restoring
prior progress. Fsync/rename tests are not proof against physical FAT corruption.

The requested [Vesper artwork](vesper-boot.md) replaces the known embedded ZIP
only. Stock code and every byte outside that span stay exact; original ARM ZIP
decoding and all18 drawing cases qualify it offline. Install only on a healthy
card, retain the archived original for rollback, and still wait for showlogo's
actual exit before InitVFB. New art does not relax the ownership contract.

The current hook runs `/bin/sh /usr/retro/snes-mvp/launch.sh` synchronously before starting stock main, only when `armed` exists. The wrapper atomically consumes it into `last-launch`. Thus a following reboot takes the stock path without depending on the failed runtime to clean up.

First library draw/flip completes before initial held inputs are suppressed independently. A stuck pin cannot prevent first paint. Startup has a 20-second deadline (bounded configurable range); ready gameplay is not limited to 20 seconds. On a stall, capture thread state, retain logs, TERM/KILL only the owned child, and wait for it to exit before starting another hardware owner. A kernel-blocked process may require reboot.

Bring-up/input/exit/cleanup logs are bounded and durable. Game callbacks do not perform per-frame SD logging. Through 1.6, three post-ready snapshots retained runtime/thread/IPC state, then monitoring ended. [1.7](snes-mvp-1.7.md) adds atomic RAM progress outside core callbacks and persists the latest two records, three early snapshots and a bounded latest platform/kernel view. Its monitor captures after two seconds, then five-second waits for at most 63 iterations; capture time extends the nominal window. Capture/sync duration is logged. Cancellation reaps the owned sleeper. Verify current build/session/boot identity before treating a retained report as this run; normal-exit totals may remain stale after power-off.

The 1.7 physical return establishes that `head` is absent; the1.8 return also
establishes that `sed` is absent. The prior claim that sed already worked was
an unsupported assumption. Both releases have system CPU/memory/IRQ capture
gaps despite passing host checks. Current source uses shell builtins for line
limits and splash zombie parsing; test the actual wrapper with both utilities
absent and verify CPU/memory contents. This repair shipped in1.9. Do not
assume host utilities exist on the firmware.
The shipped 1.7 kernel/stderr tails are empty and its final wrapper exit line
is missing, despite fresh final runner totals and completed display cleanup.
Preserve these collection limits; see the [return review](snes-mvp-1.7-return.md).

The [1.8 return](snes-mvp-1.8-return.md) has an empty latest checkpoint and tails,
a fresh previous running checkpoint and a stale1.7 final report. Unfsynced
copies can lose writeback on power loss; the previous timestamp is not the
shutdown time. Preserve identities and archive private progress before updates.

## GPIO ABI and complete direction translation

The request has three 32-bit words: `pin`, `reserved`, `value` (12 bytes).

| Operation | ioctl |
|---|---|
| Write | `0x400c4700` |
| Read | `0x800c4701` |
| Configure attribute | `0x400c4702` |

Reads initialize reserved=0 and value=1. Successful value=0 is pressed. Failed reads behave released. The input attribute's third word is 1. Retain the known startup attributes; unknown GPIO roles do not authorize output experiments.

| GPIO | Factory native mask | Final libretro meaning/ID |
|---|---:|---|
| `0x200` | `0x10` | Up / 4 |
| `0x201` | `0x40` | Down / 5 |
| `0x202` | `0x80` | Left / 6 |
| `0x203` | `0x20` | Right / 7 |
| `0x204` | `0x2000` | A / 8 |
| `0x205` | `0x4000` | B / 0 |
| `0x30b` | `0x8000` | Y / 1 |
| `0x30d` | `0x1000` | X / 9 |
| `0x30f` | `0x1` | Select / 2 |
| `0x30c` | `0x8` | Start / 3 |
| `0x30a` | `0x400` | L / 10 |
| `0x208` | `0x800` | R / 11 |
| `0x207` | `0x100` | L2 / 12 |
| `0x30e` | `0x200` | R2 / 13 |
| `0x206` | `0x9` | MENU; stock Select+Start combination |
| `0x209` / `0x20a` | volume bits | Volume up / down |

`ReadJoystick` at 0x1599c proves pinâ†’native mask. `joystick_input` at 0xa2f0c and `joy_key_mask` at 0x16b254 prove libretro IDâ†’native mask. The analog branch independently uses 0x10/0x40 for vertical and 0x80/0x20 for horizontal. **Native numeric masks alone were previously mislabeled; the v1.3 direction diagnosis was wrong.**

`extract-vendor-input.py` verifies the stock ELF SHA256, maps the actual file-backed segment and extracts the callback mask fixture. The board check decodes raw GPIO fixtures against that independent table, including distinct Down+Left.

The runtime's low 16 bits use libretro IDs; bit16 is its private MENU flag. Start+Select also becomes MENU. The game callback passes the same bits without another direction remap. In the vertical library, Left/Right page the list; check physical directions with actual in-game character movement rather than interpreting short-list page jumps.

## Clocks

The working timing layer uses the ARM32 `SYS_clock_gettime` syscall for scheduling time. Libc monotonic and kernel monotonic were directly observed disagreeing by hundreds of seconds in the same startup probe. Kernel boottime agreed closely with kernel monotonic.

`timing_sleep_until` compares an owned kernel-clock deadline to a fresh owned kernel-clock read, sleeps only the relative remainder, and recalculates after EINTR. An expired deadline returns immediately. Initial game deadline, menu repeat timing, heartbeat and logger share the source. Display condition-variable timeout reads kernel realtime to match its wait clock.

Do not reintroduce libc-clock absolute nanosleep or mix the retained adapter timing helper into MVP deadlines. The regression injects a 26-second libc/kernel offset; a real ARM wait loop and actual launcher menu test also run. Those tests complement, not replace, the successful device return.

The [lab2 return](platform-lab-2-return.md) establishes another clock boundary:
correct timestamps do not imply precise timeout wakes. All four tested short
wait mechanisms average about 10ms for 1/2/5ms requests, even after timer-slack
reduction. The original slack is restored exactly. Intended 1ms polling/backoff
sleeps must not remain in a timing-sensitive controller; device readiness can
wake sooner. Kernel timer configuration remains unrecovered.

## Chunk/display ABI and ownership

`/dev/chunkmem` allocate ioctl `0xc00c4301`, free `0x400c4303`, request `{physical,mapped,bytes}` as three 32-bit words. Explicit freeing is necessary. Ordinary heap pointers are not interchangeable with chunk-backed addresses consumed by the vendor scaler.

Resolve the required vendor symbols rather than assuming generic framebuffer ABI: InitVFB, DrawVFB, FlipVFB, FreeVFB, video_driver_get_size, detect_hdmi, hDisp and USE_HDMI_OUT. Complete splash cleanup first; detect HDMI; initialize display; then enable handheld LCD backlight via GPIO0x108 (disable it for HDMI).

MVP1.6 owns one display worker, three compact source slots and a two-job ordered
FIFO. Reserve both a free slot and publication credit before entering the core;
copy/publish without waiting inside its callback. Release the source after
DrawVFB's stopped/completed scaler boundary, before FlipVFB, matching stock's
source release. The worker retains output ownership through flip and is the
sole draw/flip caller. A free source during flip does not imply FIFO credit.
Never replace READY jobs. Drain/join before FreeVFB/chunk free. The stock driver
worker loses its thread ID and lacks an adequate teardown join; ours owns it.

Recovered scaler structure: 228 bytes; output_addr[2] offset64, frame_queue_enable72, bypass_addr[2]76, bypass_frame_queue_enable84, drop-frame fields98/99, FRAME_DONE enum2. `PScaleRun` at driver0x14ac performs per-job open/setup/trigger/status/stop/close. These interfaces are leads for future optimization, not a proven continuous queue implementation.

[Lab2's exact command review](platform-lab2.md#exact-vendor-calling-contract-recovered-offline)
corrects the abstraction: the status caller tests bit2, and command0x80045004
receives scalar3000 despite its read-direction encoding. No units or kernel wait
semantics are recovered. The not-done fallback sleeps ten times without another
status query. dispFlip submits a44-byte bitmap, invokes0x6402 then0x6407, and only
then toggles its buffer index. Do not infer completion ownership from the presence
of two addresses. Lab2 observes these exact calls without enabling extra modes.
All 973 returned successful scaler statuses include FRAME_DONE, so the fallback
never executes in this workload. Preserve that negative result before spending
an implementation on removing its sleeps.

## Audio, geometry and state

Own open/configuration, negotiated rate, PCM queue and partial/EAGAIN preservation.
Through1.8 the game uses44,100Hz stereo S16_LE after continuous conversion from
the core's32,040Hz stream.1.9 negotiates native ALSA, preferring32040Hz/direct
PCM and retaining conversion for accepted44100/48000Hz. Lab2 establishes a
working32040Hz OSS client path; no requested/returned rate alone establishes
the physical DAC rate or absence of kernel conversion. Standard fragment hints
may be rounded/ignored; query actual queue data. Queue occupancy is not an
underrun counter.

MVP1.6's producer converts/enqueues while one audio worker owns writes and their
partial-byte tails. Stop/join before any pause/reset/close; only then clear the
software queue and reset OSS. Restart after priming a new stream. Do not share
writer-tail state with an unsynchronized queue observer. Full rendering uses
kernel-monotonic native timing and bounded total PCM lead; a reliable audio
cursor/physical full-speed result remains unqualified.

[Linux 4.19 OSS source](https://raw.githubusercontent.com/torvalds/linux/v4.19/sound/core/oss/pcm_oss.c)
accepts partial fragments into staging that GETODELAY does not include. POST
starts playback without flushing that tail; SYNC flushes/drains, while RESET
discards it. Lab2's POST/zero-delay/RESET stop does not establish that the faded
tail played. Upstream behavior guides interpretation, not a claim to possess
the vendor kernel text. See [the source review](platform-interface-research.md).

The device exposes native `/dev/snd/pcmC0D0p`. The1.9 replacement implements
documented ALSA parameter negotiation/readback, explicit priming, meaningful
device/event wakeups, state/XRUN observation and separate drain/drop paths.
Use ARM32-compatible structures; negotiate transfer mode and do not assume
mmap support. Upstream 4.19 on ARM requires a SYNC_PTR/HWSYNC path instead of
the usual mapped status/control pages; audio-data mapping is a separate contract.
One owner must account for its software queue and playable PCM
without sampling them through separate producer/worker gates. Reserve sufficient
playable sound for long core calls plus service margin.1.9 uses64ms explicit
playable priming and one consumption admission policy. Its return accepts
44100Hz/128-period/3712-buffer and2823 priming frames, then EBADFD before any
emulation. Those settings and one transfer are established; START, consumption
and audible continuity are not. Preserve
bounded flush/drain failure and visible XRUN instead of automatically dropping
and restarting the stream. See [1.9](snes-mvp-1.9.md).

WRITEI can start native playback when the priming threshold is reached. In1.10,
observe state after priming writes, acknowledge RUNNING only after the target
transfer, and issue START only from PREPARED with enough queued sound. Verify
RUNNING afterward; EBADFD is acceptable only with a fresh RUNNING observation.
Never infer state from transfer count alone. Preserve failure operation, errno,
state and pointers before cleanup. The1.9 logs do not prove the exact vendor
operation that failed. See [return](snes-mvp-1.9-return.md) and
[repair](snes-mvp-1.10.md). Runtime errors now use first192-line shell-builtin
capture; the compatible kernel-tail filename holds a labelled first128-line
snapshot. Fixtures exercise capture with tail/head/sed absent.

Vendor environment command37 (`SET_GEOMETRY`) writes a double 44100 at offset32 beyond a 20-byte geometry object. The adapter intercepts it; the direct MVP implements its own validated environment handling. Do not forward this callback blindly.

Private MVP SRAM/snapshots are qualified by ROM and exact core identity. Incompatible snapshots are rejected; failed loads roll back live state. v11 `D35PLUS1` states are not generally compatible with plain2005/2010. The importer requires the known Plus binary and explicit ROM selection because the old wrapper lacks ROM identity. Import a copy; preserve the original and newer progress.

Pinned Plus snapshots contain raw CPU/ICPU/SA1 process pointers; its loader
rebuilds active pointers. Cross-library comparison must normalize only named
host fields while retaining logical registers/memory/APU state checks and
resume/output validation.1.6 adds a separate FF6 snapshot with the new exact core
identity only after those checks; it never retags the original in place.

## Supervisor/watchdog

Stock main/vrtemu use SysV key1234, 460 bytes, IPC_CREAT|0666. Word0 is a soft-watchdog tick budget; `xintiao` publishes 60 and increments word1. The MVP preserves this layout but does not remove the segment when detaching.

Returned `/wdt` instead configures and autonomously feeds the hardware watchdog every 500 ms. It does not attach this shared heartbeat; the v1.3 IPC snapshot showed only the MVP attached. Omitted heartbeat was not demonstrated as the dead-input cause. Do not disable the hardware watchdog as a substitute for diagnosing a stalled runtime.

Read-only factory `power_key` disassembly identifies another shutdown path:
poll0xd0000068 bit0x08 every200ms; eleven consecutive asserted samples lead to
GPIO0x108 backlight-off and `poweroff`. The1.8 user confirms whole-device
power-off, but no retained late sample or shutdown message establishes that
this path fired. Recovered MMIO code is not a qualified live probing contract.

## PCM observation and resume correction in 1.11

Do not pace the next core call before its requested worker observation is
acknowledged. 1.10 can admit on cached lead; the changed-device fixture rejects
the exact shipped code. Linux 4.19 STATUS copies state before updating hw_ptr.
Use SYNC_PTR with HWSYNC and APPL|AVAIL_MIN GET flags for post-update state and
control. Never write application pointers or reset readiness during observation.
Derive queued frames with the returned boundary; test wrap. Read post-fault
state without another HWSYNC and preserve the original errno. EBADFD must not
be mislabeled as queue overflow or treated as successful consumption.

DRAIN sets full-buffer readiness; restore period readiness after PREPARE before
re-priming a resumed stream. Join/drain failures stop pause handling before
snapshot changes. Count successful/rejected snapshot loads and report native
epochs separately. The real-core/native-client fixture now consumes audio and
exercises failure/retry plus two snapshot/resume cycles. It complements actual
device qualification. The 1.10 return also proves dmesg is absent, so its kernel
snapshot contains no kernel-ring evidence. See [return](snes-mvp-1.10-return.md)
and [repair](snes-mvp-1.11.md).

## 1.11 physical failure and 1.12 diagnostic boundary

The 1.11 return reaches playback and explicitly succeeds at one snapshot load,
then stops in post-fault SETUP. Two final reports contain 2,195/253 calls, with
no intentional holds and no full software queue. An earlier stderr fault and
both reports have a 384-frame pointer/count difference; its origin is unproved.
Current SRAM/snapshots match; the changed SRAM backup is archived. User confirms
audio error/our library. See [return](snes-mvp-1.11-return.md).

1.12 keeps the core/settings/controller and adds a bounded RAM transaction
history plus nonclearing kernel READ_ALL on fault, before audio cleanup. Its
wrapper persists fresh history and clears stale files. Software checks qualify
bounded capture; device kernel access and timing remain pending. This is not a
claimed stop/underrun fix, or proof of a hardware limit. See
[capture contract](snes-mvp-1.12.md).

## 1.12 return and 1.13 durable fault capture

The [1.12 return](snes-mvp-1.12-return.md) fails after 1,106 calls and one
successful snapshot load, with post-fault SETUP and the same 384-frame
pointer/count discrepancy. No intentional holds or full software queue occur.
The fresh final report survives; PCM history is absent, stderr empty and later
periodic/final diagnostic copies missing. Their exact loss mechanism and the
native stop cause remain unresolved; the backup report is historical 1.11.

[1.13](snes-mvp-1.13.md) writes fault history directly to the card and fsyncs
file and directory before returning the error. Capture errno/sync status/bytes
are explicit; failed temporary evidence survives cleanup. Actual client,
runner and immediate-exit wrapper fixtures pass, including injected sync
failure without changing PCM errno. Core/settings/admission remain unchanged.
Independent install readback retains all 22 private and 49 lab files and
stock/hook/core hashes. Physical capture, native continuity and full speed
remain pending; this is not a hardware-limit conclusion or a playback fix.

## 1.13 return changes the working failure model

[1.13](snes-mvp-1.13-return.md) preserves the fault history and kernel READ_ALL.
It fails after 26/230 calls; the second attempt loads/resumes a snapshot. The
retained phase produces about 37k accepted frames/sec against negotiated44.1k,
then application pointer diverges by three128-frame increments and SETUP.
Reserve erosion precedes that divergence: starvation is the leading trigger,
but the exact vendor response and audio contents during it remain unknown.
Display reservation is only1.066ms over230 calls. All20 private progress files
and stock/hook/core hashes match. Card unarmed, zero writes or new build.

The [execution-budget review](execution-budget-review.md) supersedes a sequence
of further small diagnostic retries: attribute the expensive phase, qualify a
whole-program A7 build and optimize the actual core/frontend work. More initial
silence or automatic restart cannot repair sustained underproduction. Existing
fixtures establish lifecycle/correctness, not the device's repeated slow phase.

## Fixed-color raster invalidation

The pinned Plus $2132 register byte selects R/G/B components with bits5–7 and
a five-bit value. A changed raw channel tag can leave effective color unchanged.
The exact FF6 state replay has214 such redundant pending flushes per frame.
Flush before selected component values change; preserve component assignments
and last-written byte. Do not collapse changing raster colors. The1.16 guarded
patch and extracted stock-code fixture qualify this distinction; physical CPU
gain remains separate from the217–223 to4–10 raster-job census. See
[snes-mvp-1.16](snes-mvp-1.16.md).

## Diagnostics share the scheduling budget

The1.16 cold failure overlaps the wrapper first platform/card checkpoint,
11.27–11.57s uptime, while main CPU stays near9ms and wall stretches to38.7ms.
The retry runs31,601 complete frames near60 calls/sec. A removed global sync
does not make SD copies or repeated `/proc`/helper discovery free. The overlap
is a strong scheduling suspect, not an independently proved causal chain.

1.17 captures/flushes static inventory before the child and copies final RAM
progress after its exit. No routine live wrapper monitor exists. Actual shell
fixtures must watch writes through the child's lifetime and reject old behavior.
Keep native fault persistence and explicit state/SRAM save points. Whole-device
poweroff may lose routine RAM progress; do not read a wrapper-start marker as a
fresh gameplay checkpoint. See [return](snes-mvp-1.16-return.md) and
[implementation](snes-mvp-1.17.md).

## Derived renderer state contract (1.18)

RGB tile cache contents never own emulated VRAM/CGRAM, depth or blend state.
Invalidate the RGB bucket at the actual indexed ConvertTile seam; flush old
raster state before CGRAM mutation, then invalidate colors. Brightness and
state load's color rebuild invalidate too. Palette epoch wrap clears tags.
Keep direct-color/clipped fallback and serialization ABI intact. Cache entries
are bounded36KiB derived data; full effect/core equivalence is required before
installation. A cache hit count is not A7 speed proof; Lab1's rejected cache
remains a negative result. Exact Magitek Bio Blast scene coverage matters.

## Persistent firmware replacement boundary

The original second animation is `/showlogo` in internal gzip/cpio rootfs;
SD-stage animation changes cannot replace it. The first static bitmap is directly
referenced by Thumb boot code. Exact [offline loader/updater qualification](firmware-offline-qualification.md)
accepts the private Vesper image, but neither QEMU nor a flash dump qualifies
physical write recovery. GPAP primary/secondary headers are not proven full
firmware-bank redundancy. No USB boot-ROM or SD-only rescue is qualified.

Vendor UpdateROM changes CRC/time metadata and erases boot-code block0 even
for this animation change. Table/rootfs erase blocks share preserved kernel
bytes; retain whole-block contents, not just desired payload spans. Never stage
dummy or malformed Code.bkp files: a malformed ZIP fixture faults in the exact
offline updater. The user subsequently explicitly authorized the [SD update
before obtaining recovery equipment](vesper-sd-firmware-update.md); its exact
package was staged and the user's subsequent physical boot shows static D-R35
-> Vesper replacing the original second animation -> default launcher. Later
[two complete8MiB reads](vesper-flash-verification.md) match the expected
vendor-mutated image byte-for-byte after trigger removal. Boot/init/readback
execution without Code.bkp succeeds; original normal SD init restored, no test
armed, protected hashes intact and final FAT clean. External write recovery
remains unqualified. This completed write/readback establishes this installed
image, not general updater safety or recovery. Returned flash,
vendor executables, full candidates and packages remain private. Keep the
actual on-device readback, cold-boot animation/launcher and restore results
distinct from offline format/algorithm acceptance.

The subsequent [first static Vesper candidate](vesper-static-firmware-update.md)
changes only the640 x480 RGB565 bitmap at0x8854/614400 bytes in that verified
installed baseline. Boot instructions/header, kernel/rootfs and second animation
remain exact. The exact Thumb bitmap-pointer/dimension stores execute against
anonymous MMIO RAM, and captured updater simulation programs ten64KiB blocks.
Block0 still contains preserved boot code; boot-ROM integrity is untested.
Qualified package staged on clean FAT with full card preservation; new physical
first-screen acceptance and full-image comparison remain pending.
