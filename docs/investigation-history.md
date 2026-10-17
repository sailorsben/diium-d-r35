# Investigation history and negative results

## Collect UART reflash and qualify fresh read-only verification - 2026-10-17

UART reflash boot accepted by user: both Vesper screens and stock launcher.
Fresh strict sparse return hashes 1,601 files, adds zero content bytes and passes
FAT. Saves/states/stock/prior evidence are unchanged; returned stock settings and
swapfile changes are preserved. No fresh flash/IRQ measurement exists on this
return. Remove only the exact used firmware trigger and stage the unchanged,
qualified read-only two-pass SPI/UART verification before stock ownership.
No firmware writes, UART module loads, emulator test or full backup. Exact
kernel bytes and idle IRQ acceptance for this reflash remain pending that boot.
[Return and verification procedure](uart-kernel-reflash-return.md).

## Rearm exact kernel UART firmware after charge recovery - 2026-10-17

Battery follow-up: user reports charging to the green indicator restored normal
battery behavior, then authorizes the UART firmware reflash. Actual depletion is
now the supported explanation; the stock ADC false-low mechanism was never
observed on this device. Reuse the exact previously physically verified kernel
UART image, preserving both Vesper screens/rootfs and battery configuration.
All original qualification/artifact hashes verify; fresh ARM driver/updater
checks and 11 unarmed-card staging fixtures pass. Sparse return adds zero content
bytes. Normal init is restored and exact Code.bkp is armed from pushed `ec128b3`.
Independent final file-set/1,599 protected hashes/full ZIP/CRC/init/FAT checks pass.
Both screens, saves/evidence and host rollback preserved; no full backup/game test.
Physical reflash pending.
[Reflash qualification and procedure](uart-kernel-reflash.md).

## Trace exact stock ADC false-low and shutdown paths - 2026-10-16

Stock battery trace: the exact SD frontend ignores ADC errors and masks the
ADC driver's timeout flag. Each sample opens a fresh client with saved value zero;
a semaphore timeout returns 0x8000, which becomes critical zero after masking.
Both GPIO checks can override this; a critical state blocks further heartbeat
sampling and can display the warning then request poweroff after five seconds.
49,152 exact ARM sampler cases and intercepted menu shutdown pass. Configuration
and SD frontend match the pre-kernel-flash archive. User reports rollback did not
clear the symptom; the actual runtime ADC/flags/GPIO cause remains unmeasured.
Sparse return retained; only the used rollback trigger was removed after full
preservation/FAT gates. All 1,600 remaining files, including every save and state,
verify unchanged. No update/test armed, flash or full backup.
[Trace and qualification](stock-battery-trace.md).

## Complete archive-verified retired card test cleanup - 2026-10-16

Obsolete card test cleanup complete: 9,405 files removed after host byte/hash
verification; 1.57 GiB of FAT space reclaimed, 1,601 files remain. Preserve all
683 save/state files and unique evidence, including 2,046 recovered text records.
One unmatched executable retained. Collector gap fixed/tests pass. Independent
remaining hashes/save paths/rollback ZIP/UART hooks/unarmed-game/FAT checks pass.
The current rollback remains armed.
No full backup. [Plan and preservation](card-test-cleanup.md).

## Qualify exact pre-kernel battery diagnostic rollback - 2026-10-16

Battery regression investigation: exact pre-kernel Wings2 rollback qualified,
with both Vesper screens/rootfs preserved and proven card UART hook restored.
Eleven firmware groups and seven staging cases pass. Armed from pushed `481415f`;
independent readback verifies 11,003 protected files, exact file set, full rollback
package/original kernel/UART payloads and clean FAT. No game test or full backup.
Physical rollback and battery outcome remain unproven.

## Collect kernel-UART five-game abort; retain battery regression - 2026-10-16

Five-game powered return: Mario, Metroid and F-Zero complete first blocking
windows; Star Fox cold replay is aborted after 102.97s while F-Zero remains
onscreen. Replay call count is missing: slow progress vs stall unresolved.
Ranger/candidate arms not started; zero matched pairs. UART idle IRQ windows
remain 85-86/s. Battery warning after extended plugged-in time is a reported
unresolved regression, not cleared by IRQ/readback success. Saves/evidence exact,
FAT clean, 6,049,004 sparse bytes; zero card writes, no full backup or rearm.

## Qualify matched five-game test for kernel UART - 2026-10-16

Exact measured five-game payloads retained; only wrapper/paths adapt to the verified
kernel fix. Nine firmware-shell and seven staging cases pass. Fresh sparse
archive: 10,906 hashes, zero new bytes, clean FAT. Armed from pushed `831d676`;
independent final readback verifies 10,905 protected files, 28 payloads, exact
markers/file set, original normal init and clean FAT. No full backup or reflash.

## Accept powered physical kernel UART verification - 2026-10-16

Powered verification passes on a fresh boot: both 8-MiB flash passes match the
exact corrected kernel image, with both Vesper screen payloads/rootfs preserved.
No runtime UART patch module or endpoint exists. IRQ19 is 85.36-86.36/s and
85.37-86.37/s, passing the declared idle flood threshold. User confirms stock
remained on while plugged in. Prior shutdown cause remains unproven; low battery
is plausible. Saves and all prior evidence unchanged; FAT clean. Sparse return
hashes 10,906 files and adds only 8,219 evidence bytes. No full backup.
Original normal init restored exactly; all 10,905 other files verify unchanged.
Independent init/file-set/unarmed/FAT checks pass. No tests or firmware update armed.

## Verify flashed kernel and preserve completed UART return - 2026-10-16

The first verification return is complete: both 8-MiB passes match the exact
expected flash, and its decompressed kernel is the corrected image. No runtime
UART module/proc patch exists. IRQ19 brackets are 88.49-89.62/s and 85.37-86.37/s,
passing the declared idle flood threshold. All saves and prior evidence remain
exact; FAT clean. Shutdown after successful probe exit is unresolved; user
suggests low battery. Identical plugged-in repeat armed from `a636eb0`; independent final readback
verifies all 10,868 prior files preserved, sole read-only marker, no firmware
trigger and clean FAT. No full backup.

## Collect kernel UART flash return; qualify read-only verification - 2026-10-16

User confirms both Vesper screens and stock launcher. Strict sparse return hashes
10,826 files, zero new bytes, clean FAT. Only expected init/update/swap differences;
saves, old evidence and all 636 outside-retro files exact. No fresh SPI or UART
sample: do not treat stale module logs as corrected-kernel proof. Qualify one
read-only two-pass/IRQ verification boot: ten groups and nine staging cases.
Known update trigger removed after archive/hash/FAT gates. Read-only verification
armed from pushed source `08e4b06`; all 10,824 protected files pass installation
readback. Independent final-card receipt linked below; physical image/IRQ result
still pending. No full backup.
[Return and next physical verification](uart-kernel-return.md).

## Arm final direct kernel UART firmware on I: - 2026-10-16

Final corrected kernel source `70b0b40` pushed before staging. Independent full
readback verifies 10,824 protected files, original normal init without a runtime
UART hook, complete update ZIP/CRC/image, exact file set and clean FAT. Only
init and the known prior update are replaced; saves, stock and evidence remain.
Both Vesper screens/rootfs exact. No full backup or emulator test armed.
Physical flash, kernel boot, IRQ behavior and wire acceptance remain pending.
[Verified package and boot instructions](uart-kernel-firmware.md).

## Qualify synchronous UART wakeup refill before deployment - 2026-10-16

Final call-path review finds a synchronous line-discipline wakeup callback.
Withdraw the first staged kernel candidate before physical boot, restoring the
exact previous package/init on clean FAT. The revised TX body re-reads head/tail
after wakeup before stop-TX; an independent refill test delivers the new byte.
All 26 groups, exact 64-KiB decompressor heap and eight staging cases pass.
Original metadata remains historical; v2 qualification governs deployment.
[Final kernel contract](uart-kernel-firmware.md).

## Qualify direct kernel UART driver correction - 2026-10-16

Replace the TX body in the exact kernel, correcting pending service, FIFO safety,
flow/urgent/queue/wakeup behavior and literal-zero PutChar. RX/IRQ registration,
rootfs and both Vesper screens stay exact. No runtime patch module. 25 groups
pass: 7,344 queue/FIFO cases, all 256 bytes, actual ARM decompressor, original
loader/splash/updater RAM checks and eight staging cases. Preserve negative
FEXTRA and caller-register findings. Restore original SD init; replace only the
known staged update. No full backup. Physical kernel boot/IRQ/wire pending.
[Kernel correction and evidence](uart-kernel-firmware.md).

## Arm verified internal UART firmware on I: - 2026-10-16

Stage the normal vendor update from pushed source `726f89c`. Independent full
readback verifies 10,824 protected existing files, authorized UART handoff hook,
complete ZIP/CRC/image, exact file set and clean FAT. Normal init, module/helper,
saves and evidence stay exact. No full backup or emulator rearm. Both Vesper
screens are preserved in the image; physical flash/boot/attachment pending.
[Installed update and boot instructions](uart-firmware.md).

## Qualify internal UART firmware - 2026-10-16

Build the exact card-proven UART module/helper into the latest Wings2 rootfs.
Preserve both Vesper screens, kernel, DT and boot instructions; only project
startup changes plus four new cpio entries. 18,089 compressed-slot bytes spare.
35 offline checks and eight staging cases pass, including original ARM
loader/updater RAM simulation and exact firmware-shell card/internal boot.
Card hook verifies firmware ownership without duplicate loading; safe fallback
and uncertainty barriers remain. Sparse preservation only, no full backup.
Qualified source awaits authorized staging; physical boot/attachment pending.
[Image, evidence boundaries and boot](uart-firmware.md).

## Collect five-game physical return - 2026-10-16

Three clean blocking windows: Mario, Metroid and F-Zero, 1,200 calls each.
User confirms Select+Start at retained F-Zero picture; Star Fox cold replay
records abort before measurement, normal exit 5 and safe teardown. No process
crash or forced timeout. Ranger and all candidate windows untested; zero pairs.
Exclude stale F-Zero PCM/input buffers from Star Fox. Reporter distinguishes
failed-before-measurement from not-started. Sparse collection: 6,065,591 new
bytes, clean FAT, UART/saves/evidence exact, no full backup, writes or rearm.
[Return, preservation and next test](fivegame-physical-return.md).

## Install matched five-game physical test — 2026-10-16

Install and arm `retro/snes-fivegame1` once on I: from pushed source `8ccb0a3`.
Independent complete readback verifies 10,758 protected existing files, all 27
payload files, exact two markers, persistent UART/init and clean FAT. Only the
owned dispatcher changes among existing files. Saves and evidence are unchanged;
sparse collection stored zero new content bytes and no full backup was created.
Published installation/readback receipts bind the exact qualified package.
Physical performance, audio and display acceptance remain pending the run.
[Installed test and boot instructions](fivegame-physical-test.md).

## Qualify matched five-game physical test — 2026-10-16

Prepare20 policy-only ABBA/reversed epochs across the five actual gameplay
scenes, exact corrected core and original backup ROMs.24,000 controller calls
match original pixel/PCM/sample oracles; Star Fox uses34,624 cold calls and no
GSU snapshot continuation. Both consuming native policies, busy/fault/drain,
firmware/reap and seven installer transaction cases pass. PAL-aware native
period/headroom and relative deficit fixture. Sparse inventory preserves all
10,759 prior files with zero new content bytes; no full backup. Measurement
experiment only: rebuilt-core A7 saving/remaining deficit explicitly missing.
[Qualification, gate and boot](fivegame-physical-test.md).

## Fix Ranger/Star Fox and qualify five gameplay scenes — 2026-10-16

Resolve Ranger's stalled SPC SYNC exchange with AVCJ-only instruction-complete
port writes. Remove redundant HDMA cached-pointer subtraction that leaks host
addresses into Star Fox's DMA register shadows. Strict tests then expose a
SuperFX direct-target pixel failure; retain the established full-layout path.
All five reach actual gameplay:14,656 pixel/PCM/geometry comparisons and489
strict state checks pass. All18 FFVI scenes and ten unchanged-frontend mock
boot/audio cells pass. No card changes, new full backup or physical promotion.
[Fixes and acceptance limits](five-gameplay-fixes.md).

## Five-game backup-ROM evaluation — 2026-10-16

Test Super Mario World, Super Metroid, F-Zero, Star Fox and Rendering Ranger
against the exact returned FFVI candidate. Four6000-call pixel/PCM/state
windows complete, but Ranger output is black; Star Fox stops at state frame150,
also reproduced with identical candidate libraries. Ten actual-runner mock
boot cells pass software PCM accounting. Inspect actual scene coverage, retain
failures and prohibit a whole-emulator-fixed claim. No emulator/card changes,
full backups or private ROM/image publication.
[Results and next acceptance gates](multigame-evaluation.md).

## Matched FFVI physical return — 2026-10-16

78/80 clean bounded windows. Both48 ms candidates complete all1200 renders and
seven burns; both blocking controls fail. All72 ordinary and four24 ms cells
pass.28 total presentation skips; candidate minimum sampled reserve5.374 ms.
User reports no obvious issues. Bind exact payload, preservation, full native
PCM and matched effect/input evidence; censor failed control tails. Preserve
UART/init/saves and all prior evidence. Sparse collection only, no card writes,
rearm or new full backup. Repair original-proof reconstruction in reporter and
add regression checks. [Return and limits](presentation-ffvi-return.md).

## Stop full-card copies on routine attempts — 2026-10-16

User requested removal of repeated attempt backups and prohibited repeating the
whole-I: backup per attempt. Both retro and supplemental collectors now retain
only progress/log content, sharing unchanged content by hash, with static files
hash-only. Keep FAT/identity/protected-file checks. Update the current FFVI
installer/reporter/publisher for explicit sparse manifests. No device writes.
See [policy and validation](attempt-evidence-policy.md).

## Matched FFVI test installed; one-backup limit — 2026-10-16

From pushed `a3b8d68`, install/arm only a separate test directory and owned
dispatcher after clean FAT/protected-file gates. Independent readback checks
all10,092 protected prior files,95 declared payload files, exact markers and
UART/init/ROM/saves; final FAT clean. Hardware return remains pending.
User explicitly rejects accumulating backups: at most one current full
rollback, unique evidence/saves plus compact inventories separately. Concurrent
archive-retention changes are preserved; the installed test remains bound to
its frozen pushed source and independent readback. No replacement bulk copies
made. [Installed test](presentation-ffvi-test.md).

## Matched actual-core presentation test prepared — 2026-10-16

Prepare80 policy-only ABBA/reversed epochs:18 unchanged1200-frame effect/input
windows four times plus seven executed24/48 ms bursts in each of eight matched
HOLY cells.96,000 real-core rehearsal calls, all effect properties and56 burns
pass. Keep full RAM native/frame histories through joined cleanup, separate
render/present/skip/load accounting and failure censoring. Both consuming-native
policies pass with the established O2 fixture after a preserved O3/LTO fixture
admission timeout; no causal compiler/hardware claim. The deployable controller
remains O3/LTO. Firmware UART/splash/replay/error/reap guards and six installer
success/rollback cases pass. Archive every10,093 existing file/FAT clean before
any write. Physical result remains pending. [Test contract](presentation-ffvi-test.md).

## Real-runner presentation integration qualified offline — 2026-10-15

Use a fresh candidate tree to apply the proven atomic reservation to the actual
owned-output runner. Busy credit selects aligned heap scratch, fully executes
the core/render/PCM path and intentionally omits only presentation. Production
PCM is retained: importing pressure3's diagnostic collector first failed the
durable-fault assertion; that attempt is preserved rather than hiding the
support mismatch. Final O3/LTO ARM executable and byte-identical core pass192
board states, real worker teardown/queue checks,21,600 raw pixel/PCM/normalized
state comparisons across18 original FFVI contexts, real-runner native failure/
retry/resume and forced40-of120 skip checks. Blocking/error controls pass.
Physical A7 costs, visible cadence/input/audio and matched gameplay remain
pending; no card access/install/rearm or production promotion.
[Implementation, proof and physical gate](presentation-runtime.md).

## Pressure3 demonstrates48 ms recovery with five presentation skips — 2026-10-15

Candidate48 ms passes180 quanta/six burns with valid running pointers, exact
PCM accounting, oracle and drain;175 drawings/five explicitly skipped. Same-boot
matched blocking control fails at59 completed during second burst. First five
candidate events regain prime in19.5–20.0 ms after observed minima; last has no
production recovery window. Post-event reservation0.004 versus11.480 ms supports
the proposed catch-up mechanism.24 ms passes both/no skips;80 ms fails both;
sustained CPU threshold does not change. All77 cells complete,62 accepted.
Publish418 input hashes with failure-tail censoring, preserve prior evidence,
clean FAT/stock/ROM/init/progress and UART72.37/sec. No code/install/rearm on
return; full-core/visual qualification remains next. [Results](render-pressure3-return.md).

## Presentation-independent recovery candidate — 2026-10-15

Address pressure2's clean48 ms recovery stall with an atomic try-reservation:
without display credit, render the same frame to scratch, retain load/audio,
skip only presentation. Never replace READY or touch SCALER ownership.77 phases
retain original work plus seven matching blocking controls.192 actual board
states, controller/audio busy-credit/cleanup/burst fixtures, oracle/mock and
wrapper/source/ABI checks pass. Physical benefit and skipped-frame cost remain
pending; recorded gate distinguishes11.452 ms observed wall opportunity from
unmeasured A7 saving. Install/arm separate pressure3 from pushed `678643a`
after fresh archive, clean FAT and exact prior/payload/marker gates; UART
correction and earlier tests remain intact. [Details](render-pressure3.md).

## Physical budget and reserve recovery from pressure2 — 2026-10-15

All70 cells finish;58 pass. Corrected audio-only/light cells now drain normally.
Added8 ms/frame passes180 quanta at12.036 ms warm main CPU;12 ms fails at57
completed.24 ms bursts execute6/pass;48 ms executes3/fails, but pointer history
already becomes invalid around second event;80 ms executes1/fails. First five
24 ms events restore primed lead after observed minima; last has no recovery
window. After first48 ms event, clean rows have11.452 ms reservation waits,
4.385 ms main CPU and inadequate lead recovery. Preserve the distinction between
CPU capacity and presentation-gated recovery; no speculative driver attribution.
Hash-bound376 raw files, full PCM histories and censoring gates;9,035-file clean
archive, prior payloads/progress/ROM/init verify. I: unarmed, UART retained,
no new build/install/rearm. [Results and next focus](render-pressure2-return.md).

## Qualify corrected pressure2 before physical repeat — 2026-10-15

Remove the new controller's extra drain without changing the frozen audio owner;
place steady/burst sweeps on the previously successful light static route.
Record load events and check the real controller plus real threaded owner with
a fake device: normal single finish, finish failure propagation, six actual burns
and a negative control restoring the original bug. All70 mock/oracle/wrapper/ABI
checks pass. Preserve pressure1 and matching-kernel audit; no speed claim or
device threshold from fake timing. Install and arm separate pressure2 from
pushed `fa3005d` after fresh archive/FAT/hash gates; independent readback
verifies prior files and exact markers/payloads. UART correction retained,
physical results pending. [Details](render-pressure2.md).

## First independent pressure return separates rendering and shutdown — 2026-10-15

All 70 cells finish normally; 50 non-audio pass. Audio-only and four light
render cells complete production with valid pointers/reserve, then the new
controller calls finish after the audio worker has already drained, causing
errno77. Fifteen dense/loaded cells fail during production; all three burst
cells fail before frame29. No burst limit or audio end-to-end pass is claimed.
NEON synthetic dense rows cost20.317 ms main CPU versus16.688 ms audio quantum;
queued/direct display helps but does not close that budget. Tested cached colors
show no win. Prebuilt output achieves about60fps at all three dimensions.
IRQ19 remains72.39/sec with correction attached. Strict archive/input hashes,
clean FAT, ROM/init/stock/progress verify; markers consumed, no card mutation.
Record the harness defect and next bounded diagnostic without changing the
frozen workload or installing another candidate. [Analysis](render-pressure-return.md).

## Arm independent pressure lab — 2026-10-15

Install the qualified ROM-free 70-phase lab from pushed `26e9d3d` in its own
directory, preserving persistent UART correction and prior logs/private progress.
Fresh strict archive, three clean FAT installation gates, protected-file hashes,
payload readbacks and both one-shot markers verify. No production core or driver
change; physical acceptance and timing remain pending.
[Installation and collection route](render-pressure-installation.md).

## ROM-free pressure lab and actual scaler wait contract — 2026-10-15

Respond to the hardware-ceiling challenge with a70-phase independent harness,
not another game-specific inference. Compose exact row math, cache-friendly/
churning/depth/window workloads, heap/chunk traffic, prebuilt display, audio and
controlled CPU loads. No ROM/core DLL; frozen physically used board/audio support.
Oracle60 full-frame guards/equality cases and70 short mock cells pass, with
supervisor/replay/forced termination/UART failures checked in actual firmware
shell. Physical timing and combined native-driver acceptance remain pending.

The matching kernel is now available, unlike the original lab2 review. Pin11
functions and verify ioctl jump-table dispatch for0x80045004, scalar arg in r2,
5000ms clamp and __msecs_to_jiffies / waitqueue / schedule_timeout helpers.
Vendor3000 is a3-second maximum, not mandatory work or demonstrated busy-spin.
Queue/retrigger presence does not qualify persistent-FD/DMA changes. Do not
promote reconstructed module-build HZ/HIGH_RES/PREEMPT settings to board facts.
All prior evidence retained; no I: access, install/rearm, kernel/driver/game
mutation or QEMU-derived speed claim. [Test and review](render-pressure-lab.md).

## UART-corrected FFVI return: resilience improves, CPU margin remains — 2026-10-15

Strict8,275-file/2,026,867,632-byte archive, clean FAT and exact payload/stock/
ROM/progress. Only swapfile changes among7,827 protected prior files. All48
epochs finish;46 clean versus44 before. Raw Meteor controls now both qualify;
APU-only controls still fail, later at521 calls with first invalid frames496.
Candidate40/40 remains clean with36 reserve improvements/four equal. Quasar
pricing minimums gain129 frames each, but candidate still costs raw v3 another
0.545/0.562ms warm thread CPU. No broad CPU saving or20% headroom claim.
UART stays attached, no fault/bypass;70,633 calls reconcile internally. Wrapper
rate71.63/sec versus prior6,920.94 (98.965% reduction over16.4minutes).54RX/break
events, no frame/parity/overrun/full-FIFO event. No serial-wire/general traffic
qualification inferred. Quasar's planned repetitions complete normally.
Reporter reproduces all frozen prior statuses/hashes and rejects mock/unsafe
status/incomplete fixed-window speed claims. No card writes, core changes or
rearm. I: unarmed, persistent correction retained. [Analysis](snes-uart-retest-return.md).

## Install persistent UART fix and arm unchanged FFVI suite — 2026-10-15

Fresh strict archive `a7-pair-before-20261015T065323Z` retains7,829 files before
any card mutation. Install from clean pushed46ddf9a: normal init automatically
attaches `uart-fix1`, then the one-shot dispatcher selects `snes-draw-uart1`.
All7,827 previous files except those two authorized scripts verify, along with
ROM/progress, all new payloads and the sole marker. FAT clean before/after fix,
after retest payload and after arm. Preserve all previous evidence and original
init. No firmware update, emulator/APU rebuild or claimed gameplay gain.
[Installation receipt and procedure](snes-uart-retest.md).

## Persistent UART correction and identical FFVI repeat — 2026-10-15

The physically causal TX1 correction becomes an automatic card-boot package,
without SPI changes, a resident process or diagnostic cutoff. Preserve the
hash-frozen original test and all guards/service semantics; change only cutoff,
cap report and description in the module source. Targeted compiled checks cross
the old200,000 threshold and unsigned wrap after a bulk new-path RAM replay
timeout.18 module groups,16 helper cases and exact firmware startup/failure
barriers pass. Five temporary-card transactions verify activation-last and
rollback/preservation.

For the user's requested FFVI measurement, retain the previous48-run plan,
controller/cores/states/inputs byte-for-byte (82 unchanged payloads). New wrapper
destination and pre/post UART checks are outside the child. Reuse full48-epoch
qualification by hashes and execute a one-epoch retarget seam; a redundant bulk
mock replay timed out after partial progress and remains private. Both offline
timeouts are qualification execution limits, not hardware/performance findings.
No A7 CPU saving, audio deficit closure or persistent physical acceptance is
claimed. [Fix](uart-persistent-fix.md), [retest](snes-uart-retest.md).

## UART pending-versus-empty source contract — 2026-10-15

Locate/pin/hash GP32/GPM4 definitions matching the actual register layout:
TX pending0x4000 differs from empty0x80. All31,345 physical statuses have pending,
144 empty; shipped ISR tests empty. Original ARM comparison reproduces ignored
pending with queued/enabled TX and service with changed test, but also shows no
clear in the already-disabled context. Qualify actual GIC pending/active/masked
leaf reads for8 combinations and ordinary IRQ69 EOI in RAM. Reject differently
mapped GPL32900/SPMP8050 sources; matching4.19 GPA7 source still absent. Shared
IP inference is not a causal board result; next correlation must pair status,
control and controller state in the same call. Preserve939 proofs; no card
access/rearm/new kernel probe or fix. [Research](uart-source-contract.md).

The subsequent board-focused pasted note is checked against the VT569B photo
record, retained DT and actual UART clock helper. Serial0 deliberately selects
hardware UART1 and its matching clocks; no alias/clock mismatch is found. Three
okay nodes do not prove three active IRQ producers. UART DT nodes specify no
pad/pull/bias state; RX trace/pull remains unknown. Error status is a different
register from captured0x531f. Six static board-contract checks preserve this
boundary without speculative GPIO changes or a polarity flip.

## UART status1 identifies dominant unrecognized-status path — 2026-10-14

Archive7,813 files/1,937,139,157 bytes, clean FAT and exact payload/stock/ROM/
progress; only stock swapfile changes among protected prior files. All31,345
captured calls equal IRQ19 counter growth.31,201 (99.54%) yield0x531f, selecting
neither RX nor TX;144 TX-only, zero RX. All return IRQ_HANDLED, no overflow or
bypass. Restore/frozen capture/non-forced unload/exit0 pass. Original ARM ISR
with captured0x531f reproduces1000 no-service/no-RAM-write handled returns.
Identify the live software path; do not invent electrical cause, undocumented
bit names, register clearing semantics or CPU saving. Sequential rates7,369/
6,262/5,786 per second are not a treatment effect. Preserve937 prior proofs;
no card write/rearm/UART fix. See [return](uart-status-return.md).

## Build original UART status and branch probe — 2026-10-14

User explicitly requests implementation/validation/arm. Use the actual ISR
entry getter return instead of another snapshot hypothesis: verified frame
bridge, RAM aggregate callback, resume original tests/body, no extra status read
or executable text patch. Temporarily replace only the guarded IRQ19 action
handler; pin until restoration/drain and withhold stock on cleanup failure.
Actual ARM relocation and40 original/intercepted cases qualify side effects,
status-read counts, return and preserved registers; histogram bounds/lifecycle
faults pass. Catch a Thumb host-memcpy fixture mismatch and use a typed ARM
fixture for the kernel import.17 owner/actual-firmware-shell checks qualify
detach failures/cancellation/consumed reboot. Physical cause/cost still pending.
See [probe](uart-status-probe.md); no UART fix or emulator/APU change.

Subsequent authorized deployment uses clean pushed0b90c2d, strict7,805-file
archive and clean FAT before/after payload/after arm. All7,804 protected prior
files/stock/ROM/progress and new payloads/dispatcher/marker verify. I: is armed
for one idle original-status capture; existing state1 logs remain exact.
Interception safety/status/branch conclusions require the physical return.

## UART state1 physical return rejects persistent TX mismatch — 2026-10-14

Archive7,805 files before analysis; clean FAT, exact deployed payloads/dispatcher,
consumed marker and stock/ROM/progress verification. Module loads,100 snapshots
succeed, unloads and wrapper returns0. All samples show TX hardware/software
disabled, empty queue, no mismatch, flat RX and~83.55 TX bytes/s. IRQ rates are
7,291.55 before/6,755.75 loaded/7,323.38 after: unexplained phase difference,
not a measured performance saving. Reject persistent TX divergence for this idle
capture; retain transient/emulation-only possibilities. Original status/branch
capture and handler-cost controls remain next. No card writes/rearm or speculative
UART fix. See [return](uart-state-return.md).

## UART snapshot observer reconstructed from existing artifacts — 2026-10-14

User directs continued investigation without supplying vendor contacts. Bounded
public search still lacks the matching tree; reconstruct the small observer's
ABI against actual module relocation offsets, loader field accesses and4,394
verified kernel text exports. Correct old-kernel/new-GCC architecture fallback
and userspace time/file/libc interfaces.27 checks include actual ARM module
relocator, compiled snapshot module, owner failure/cancellation/cleanup paths,
firmware BusyBox execution and consumed reboot. A generated-script CRLF failure
is caught and corrected with explicit LF bytes. No live cause or IRQ-duration
claim; snapshot-only idle preflight avoids changing UART settings or handler.
See [preflight](uart-state-preflight.md) for exact scope and evidence boundaries.

## Exact UART kernel follow-up — 2026-10-14

Revisit the unresolved IRQ19 after the draw-order return. Verified existing SPI
backup yields the exact kernel and17,533 decoded symbols; all242 retained built-in
runtime triples match. Six archived-code ARM/QEMU fixtures reproduce divergent
TX-enable state surviving1000 empty handler calls, unconditional IRQ_HANDLED for
unrecognized status and literal-zero PutChar output. These are code properties,
not proof of the live IRQ source. Latest suite endpoints retain6.73million IRQ19
events/~972s,92.32% of interrupt counts; no CPU-time claim. Actual dispatch and
accounting plus absent tracing symbols narrow the observer options. Matching
kernel build interface is still missing; specify qualification/cost/restoration
requirements before any observer installation. No card access, rearm, module,
core/APU or firmware change. [Research and next measurement](uart-kernel-investigation.md).

## Draw order succeeds on remaining contexts, exposes Quasar cost — 2026-10-14

18/18 contexts pass twice for the first complete clean physical regression suite;
all4 extra candidate price windows clean too. Meteor/Rage032 now retain valid
pointers/full frames/PCM/recovery. Raw/fixed-APU Meteor controls fail, including
one nominal1200-call raw completion with drift.44/48 clean overall. Net earlier
Meteor saving0.54–0.62ms vs raw; warm Quasar regresses0.45–0.56ms, despite audio
continuity. User's middle-run observation is consistent but not assigned to an
exact epoch. Fixed APU object prevents compiler drift but whole boundary-control
build costs0.18–0.215ms warm. All-common and fixed intervals expose early/Quasar
overheads; no complete late Meteor price. Preserve candidate, no promotion until
regression/headroom addressed. Strict archive/FAT/payload/protected/ROM verify;
I: unarmed, no recoding/card writes/rearm. See snes-draw-order-return.md.

## Authorized draw-order physical candidate installed — 2026-10-14

After full validation and clean source push9ba664f, install85 payloads in
separate draw-order1 directory, verify7,358 prior files/stock/ROM/progress and
clean FAT at all three stages. Strict7,359-file archive matches evaluated return.
One-shot armed for48 automatic epochs; next reboot stock. Fixed APU compiler
object and priority candidate are paired with boundary-only/raw-v3 controls.
No measured net A7 gain or full effect/recovery acceptance until return. Prior
proofs/frozen readiness exact. See snes-draw-order-installation.md.

## Ordinary draw-order candidate and APU compiler boundary — 2026-10-14

Implement state-based Mode1 top-BG3 priority pass from frozen v3 without research
arrays. Preserve original lower order/depth/math/windows/OBJ/fallback. Same
unchanged APU unit compiled once non-LTO and reused by hash;21 linked SPC/DSP
sizes identical.43,200 ordinary original-input calls/all18,2,560 actual original
renderer pixel/depth/OBJ oracle fixtures,8,400 resolution/state calls pass.
New48-epoch controller57,600 calls plus native direct/failure/retry/state,
wrapper/ABI and mock-rejecting reporter pass. User explicitly authorizes putting
qualified result on I:; separate measurement suite includes raw v3, boundary
and candidate in both orders. A7 net saving/boundary cost/remaining deficit
unknown; falsifiable acceptance and added costs written before installation.
Frozen and prior evidence exact. See snes-draw-order.md.

## PC diagnostic physical owner census — 2026-10-14

All four unchanged-v3 epochs return; clean Quasar twice, Meteor pointer failure
even in completed control. Sampled Meteor drift488/error509 vs control drift532.
Sampler supports A7 CPU-targeted delivery but coalesces requested1ms to about10ms;
613/1,333 active samples,583/1,333 selected before drift, zero sampler errors/
dropped records. Heavy384–487 named PPU53.0%/46.5%, DSP/APU17.7%/26.8%; short
fixed windows sparse, late Meteor unavailable. No estimated per-owner ms.
Warm sampled-minus-control thread CPU+0.159/+0.105ms includes order/variation.
Full retained PCM transactions and pre-drift cumulative identities verify;
Meteor loses2,076/2,075 reserve frames, Quasar gains193. Strict archive/FAT/
payload/protected/ROM checks pass; marker consumed, I: unarmed. General priority
and hidden-color avoidance remains strongest lead; exact net gain missing.
No emulator/card writes/rearm. See snes-pc-profile-return.md and published counts.

## Authorized unchanged-core PC diagnostic — 2026-10-14

Explicit "Arm I" installs1.19-pc-profile1 from clean pushed6123047. Fresh strict
archive preserves7,226 files/1,827,485,639 bytes, all identical to prior return.
88 payloads read back;7,225 protected files/stock/ROM/progress exact, three FAT
checks clean. Four Meteor/Quasar off/on sampling epochs share byte-identical
ordinary demand-v3 core. Existing dispatcher and one-shot marker select test;
marker consumed before startup, following reboot stock. Physical support,
quality, owners and disturbance pending.
No optimized prototype installed or A7 speed claim. Published receipt and prior
evidence/frozen artifacts verify. See snes-pc-profile-installation.md.

## Compiler cause and priority-scheduling research — 2026-10-14

Exact report rebuilds identify SPC loop unswitch loss across LTO partitions;
one-partition/fixed-APU controls restore it, flag snapshot alone does not. Fixed
APU object identical across PPU variants.14,400 compiler comparisons pass.
Fresh current census7,200 calls finds27,600 late-Meteor RGB pixels overwritten
by BG3. State-based unique top-BG3-first counterfactual passes21,600 calls/all18,
main RGB writes-32.5% with extra traversal/guards unpriced. Current A7 budget is
core~15.5ms plus~1.5ms other recorded CPU, inner ownership unmeasured. Unchanged-
core PC/control diagnostic qualifies4,800 calls plus native lifecycle/reporter;
timer overruns retained, no1ms delivery claim. No card access/rearm or optimized
installation. See snes-deep-efficiency-research.md for proofs and limits.

## Deeper efficiency research / codegen interaction — 2026-10-14

Source-identical CPU/APU modules produce different SPC/DSP codegen when PPU
variants are rebuilt under LTO; .text combined+22,568 bytes. Static call-site
populations are not runtime counts. No causality/speedup claimed. Architectural
priority is current inward ownership, then winning-source/color production,
main/sub sharing beyond installed geometry, exact interpreter/DSP mechanisms.
Historical counts are not current v3 prices. Primary upstream code comparison
and reproducible ELF audit preserved; no emulator/card changes. See
snes-efficiency-research-reset.md.

## PPU physical combination rejected — 2026-10-14

56 epochs return, same16/18 final contexts clean; Meteor/Rage032 still fail.
Combined Meteor common-warm CPU slower0.071–0.120ms and pointer drift earlier
480/484 vs496/505 controls. Control-heavy selector alone reports0.055ms saving;
all-common windows/fixed intervals expose the regression and must accompany
that number. Bulk isolated helps heavy intervals but nominally complete1200
calls drift; no acceptance. Shapes helps Quasar, OBJ broader prices weak/mixed;
savings do not add. Cause of combination loss remains unproven. Strict archive,
FAT/protected identities verify; no emulator/card writes/rearm. See
snes-ppu-test-return.md and the bounded published analysis.

## Authorized PPU measurement test — 2026-10-14

Fresh56-epoch controller qualifies67,200 calls before user-authorized rearm;
18-context final regression and Meteor/Quasar baseline/isolated family blocks.
Native/wrapper/ABI and mock-rejecting reporter pass. Preserve6,721 returned
files and private progress; clean FAT. No row-cache experiment. Missing new A7
prices remain explicitly unknown; authorization allows measurement installation,
not production acceptance. See snes-ppu-test.md and its installation receipt.

## General PPU refinements qualified offline — 2026-10-14

Implement state-based OBJ initial-window reuse, opaque depth, clipped
normalization, sparse plain/math and contiguous depth fills. Final v5 inlines
math and corrects legacy counter labeling.18 contexts/variants pass259,200 raw
graphics/PCM calls with normalized state every30, independent stock/scalar/NEON
oracles, native fault/retry and resolution seams. Synthetic239 uses shared
test-only HDMA host-pointer reset for existing baseline defect. Separate1KiB
row cache exact but excluded pending positive A7 price. Prior cores/proofs and
setup failures preserved. No card writes/rearm or new physical speed claim;
remaining deficit unknown. See snes-ppu-refinements.md for added-cost accounting.

## Physical spell return narrows remaining work to Meteor — 2026-10-14

Evaluate before recoding:32/36 v3 windows clean,16/18 contexts pass twice. The
remaining Meteor/Rage032 contexts both exercise effect19. Quasar2/2 clean vs
0/2 reference;1.436–1.466ms matched recorded CPU saving. Meteor1.088–1.102ms
saving, later reserve collapse/pointer drift, but still0.231–0.270ms recorded
CPU above nominal quota in its worst valid intervals. This excludes uncounted
costs and is not a promised sufficient fix. Conservative service proxy can
double-count overlap; full20% margin remains unmet.

Three candidate windows complete1200 with empty errors yet pointer drift;
do not pass them on nominal completion/software totals. All32 accepted bounded
windows have full frames/exact PCM/valid untruncated trace and1200 actual direct
submissions/zero copied bytes. Archive6,721 files, clean FAT and protected
payload/stock/ROM/progress verify; I: unarmed. No recoding or device writes.
[Evaluation and trustworthy prefix limits](snes-demand-spells-return.md).

## Install and arm the prepared spell suite — 2026-10-14

Explicit “Arm I” authorizes guarded separate demand-spells1 installation.
Fresh strict6,340-file archive, known clean FAT, exact qualified packet and
pushed source verify before writes.82 payloads read back,6,339 prior retro
files/stock/adapter/boot/ROM/progress preserved; only dispatcher and one marker
route the automatic40-epoch test. Clean FAT after payload/arm and final protected
readback. Frozen preparation receipts remain exact. Physical results pending.
[Installation receipt and boot sequence](snes-demand-spells-installation.md).

## Prepare bounded automatic late-game effect coverage — 2026-10-14

User cannot manually access late-game spells and requests a test for unfixed
effects. New demand-spells1 drives all18 preserved original state/input/property
contexts twice, with Meteor/Quasar reference controls in opposite orders. Fresh
controller preserves qualified ordinary cores, every frame/PCM and original
state payloads, joins workers before trace flush and uses owned chunk output.
Add direct/copy metrics missing from the manual runner; disable nested phase
clocks and ambient frequency pinning.40 epochs/48,000 actual ARM mock calls,
18 expected property fixtures, native149 direct callbacks with fault/retry/drain/
deficit, actual wrapper/ABI and reporter mock-rejection checks pass. QEMU timings
do not price A7 work; headroom/conditional-branch/output boundaries remain. Test
prepared locally, not installed or armed; no card access. [Scope](snes-demand-spells.md).

## Demand-v3 opening-scene physical return — 2026-10-14

Strict6,340-file return archive and clean FAT verify exact candidate/stock/ROM/
original progress; consumed marker leaves I: unarmed. Only prior stock swapfile
changes.3,952 submitted frames,59.995 active calls/s, no logged PCM faults/
underruns, exact2,908,357 accepted nonpriming audio frames. Ben reports Confuser
worked fine; opening-scene coverage only, no Ultima/Holy/late-game play.

Core wall11.266ms average,25.076ms maximum. Histogram retains9–18 nominal-quota
overruns without logged starvation; reported running reserve minimum2,028 frames.
Do not claim every call met its deadline from late_calls=0: its admission test
uses a different boundary. Distinct recorded CPU-region mean11.660ms is partial
system cost and whole-session average, not20% worst-effect acceptance. Tail and
sparse samples have no spell identity; no matched incremental savings. Small
copy timer is consistent with owned output, but direct counts/bytes are not
persisted. Normal display-worker teardown proves lifecycle, not broad visual
coherency. No new card writes/rearm or production promotion.
[Return and reproducible evidence](snes-demand-gameplay-return.md).

## Implement shared work elimination; measure intersections — 2026-10-14

Fresh isolated and combined candidates pass302400 raw original-command frame/
PCM/geometry comparisons, with periodic normalized state. Replace zero-hit BG0
restriction with eligible-layer,8/16-tile and window-aware geometry. Reuse frozen
fusion/alignment; strict DMA spans and exact local cleanup preserve simulation.
Own direct output with reserved FIFO credit, coupled layouts, auxiliary migration,
completed-draw source release and joined teardown. No device/card work or A7 gain.

Counted combination reveals all570 Quasar shared BG1 main cells are hidden,
intersecting4410 fused rows. New clip rejection removes setup/descriptor reads;
aggregate depth-vector count stays5319 and index rows unchanged. Meteor adds one
failed coverage probe before veto; sparse opportunities retained. Ring modulo
was a needless added price and is removed in a fresh revision. Appearance dirty
writes avoided are not actual removed schedule rebuilds; retain zero peak credit.

Synthetic239-line state mismatch at frame240 reproduces between identical
baseline binaries. HDMA current pointer reset leaves stale base; null-minus-base
termination contaminates emulated registers with host-address bits. Never mask
those fields. Test-only common null/null initialization isolates resolution/state
seams; final core remains unchanged at HDMA. Setup/ABI fixture errors and failed
boundary/control receipts retained. Full added-cost ledger and subsequent72-epoch
A7 plan documented; no deadline/headroom guarantee or production promotion.
[Changes, negative result and missing prices](snes-demand-optimization.md).

## Count proposed architectural shortcuts, not hypothetical traversal — 2026-10-13

Source review plus28800 exact replay calls in three observer-only iterations.
NEON backdrop and small palette cache already installed. Whole invisible layers
and full-width clipped OBJ calls have zero peak hits; discard those explanations.
Only~5.6/5.9% of Meteor/Quasar tile math later overwritten, despite greater plain
RGB overdraw. Defer-only math is not first without a guard/metadata/traffic price.
Strict contiguous DMA eligibility covers1344/839.5 bytes per heavy call; once-per-
tile invalidation reduces logical store requests. Recipient-aware guard covers8
rows, brightness0 allows exact zero fills, and real ring fragmentation is small
on average. Preserve current renderer/timing and conditional cost equations;
no new A7 test/card writes. [Counts and limits](snes-architecture-populations.md).

## Measure the core split before further PPU changes — 2026-10-13

Quick profile1 return confirms PPU~87% of effect CPU growth for Meteor/Quasar.
Early3.32ms becomes7.91/7.04ms; APU-inclusive grows only~0.4/0.34ms. Kernel-clock
sampling itself adds~1.3ms on sampled calls, with nearly unchanged unsampled
costs; retain costs and use unprofiled controls for budget. All four runs fail
native PCM, with pointer drift and incomplete effects. Video callback outside
PPU/APU consumes~0.85ms, exposing compact chunk-buffer copying as a common
secondary target. Residual after video remains~4.5ms, includes port-driven SPC
and cannot be labelled pure65C816. No new core, test build, card writes or rearm.
[Measurements and conditional savings](snes-quick-profile-return.md).

## Derive scalar/NEON selection from state and work shape — 2026-10-13

Design only: keep geometry/state decisions outside pixel loops and reuse the
visibility mask across scalar sparse or NEON dense payloads. Separate plain,
math-operand, clip/layout and palette-reuse classes; measure guard misses and
integrated ABI/cache costs before choosing thresholds. Existing source/binary
inspection exposes full-width scalar clip routing and opaque OBJ depth merging.
Preserve separate sprite test/write depths and order. Zero empty sole-layer hits
deny a tempting source-only credit; more n3 candidates do not prove speed.
Use existing native peaks/logs for required saving thresholds, never inclusive
CPU/count quotients. No recoding/build/replay/card access. [Policy and evidence](snes-ppu-scalar-neon-selection.md).

## Find a shared full-tile boundary instead of eight effect patches — 2026-10-13

Trace CPU/WaitAddress, APU interpolation/envelopes/clocks, PPU flush/captured state,
background/OBJ/Mode7/mosaic/clipped rendering, cache/math/store helpers and runner
resampling/publication ownership. Thousands of tile entry boundaries recur in
every failure; only0–21.75 decodes do. Existing exact resampler and mandatory CPU
state are not free removals. Preserve clock/quota/frame fidelity.

Generic batch v1 is exact but introduces outlined blend calls per math row.
Constant-mode band v2 keeps math inline; v3 hoists palette lookup to tile scope and
retains eight tables only for the owning background call. Quasar's prototype
materializations256 to10 are not the staged core's cache count. All three pass
18 original-command contexts; final independent tile and repeated-palette seams
pass. Case counts support one common candidate, not universal positive A7 saving.
No price from prologue bytes/QEMU/inclusive time and no new hardware test. See
[common C analysis and conditional gate](snes-common-renderer.md).

## Follow Pearl's C path before assigning new milliseconds — 2026-10-13

An aligned layer/plane census distinguishes mostly hidden main BG3 tile setup
from opaque sole-layer subscreen production. Early rejection removes 4,763
preambles; a separate inline producer accelerates 4,569 subscreen calls. Both
preserve output in the bounded original replay and independent tile fixtures.
Reject shared BG1/BG2 production (zero eligible rows) and constant-color bands
(actual BG3 uses16x16 tiles and no uniform rows). No speed credit for dormant
code. Correct a generated dangling else caught by the original-output oracle.

Legacy 406-overlay runner stops at missing diagnostic ABI symbols, so it supplies
no new overlay coverage. Initial hidden census export/sysroot issues are build
failures, not game failures. Research upstream A7/ARM renderers, SPC assembly,
exact versus approximate Gaussian arithmetic and headless optimization targets;
separate transferable mechanisms from incompatible representations and timings.
The conditional3.310ms target now has a concrete unit-price inequality, but no
new measured A7 price. Already armed fullpaths1/card remain untouched. See
[full evidence and next measurement boundary](snes-pearl-workback.md).

## Measure each full-frame path and interaction on the A7 — 2026-10-13

Stage a measurement-only five-core crossover under explicit new authority.
Standalone binaries/proofs remain exact; the new combination passes 18 original
contexts. The actual 100-run controller, native faults/retries/deficit and wrapper
ownership pass offline. Distinguish full frame submissions in mock from actual
hardware flips; never label mock costs physical. Independent accounting rejects
pointer drift, missing frames and clock/wait faults. Synthetic analyzer fixtures
catch missing flips and incomplete heavy-state overlap instead of calling them
zero-cost savings. These checks do not price the paths.

Only fresh-observation, capacity-available, surplus-lead condition waits count as
intentional pacing. Other admission work stays in the budget. Included observers
and worker CPU produce a conservative service proxy, with remaining complete-
effect/recovery/final-worker boundaries explicit. Two reversed orders reveal
variation and interaction; they do not establish worst-case or universal proof.

Archive/hash/FAT guards protect all 5,020 old files except the authorized dispatch
after a 5,021-file collection. New 91-file payload and marker verify; I: armed.
Generator expected an obsolete optional-profile guard; retained assertion failure
corrected by asserting existing disabled clocks. New parser avoids unsupported
C23 strtoul ABI; independent fixture bounds its path to satisfy Werror. A return
parser correction uses real display_flipped instead of a nonexistent drawings
field. No A7 saving inferred from these corrections. [Design](snes-fullpaths-measurement.md).

## Full frames, removable work and a missed clipping boundary — 2026-10-13

New isolated fixed-row/subscreen/DSP paths pass 129,600 original-command
comparisons; fixed rows pass another 243,600 bounded overlay comparisons.
Do not equate those counts with universal coverage or physical speed. Genuine
fixed-color fragmentation removes much more setup in Siren/Carbunkl/Lullaby than
in Meteor. New full-add shortcuts mostly target Holy/Meltdown/Quasar/Bahamut;
zero-envelope DSP work is shared but unpriced. Added predicates/capture/cache
traffic need direct A7 measurement before combining or promoting anything.

An earlier clipped lookup used a negative-X tile base to select a row. Source
reasoning found the counterexample after ordinary battle/overlay replays passed.
Original scalar tile functions independently reject that version and match the
corrected first-visible-pixel lookup across 16,128 fixtures. No affected build
was installed. Corrected helper setup/green-bit assumptions are fixture errors,
not device failures. Preserve these negative results and bounded proof receipts.

Proposed 20% capacity margin means 13.351 ms unpaced service, requiring up to
5.354 ms saving in matched expensive tails. Healthy pacing is not spare-capacity
measurement. Frameskip is unauthorized; neither these tests nor repeated failed
optimizations prove hardware impossibility. Native SETUP/errno77/pointer excess
remains a separate unresolved protocol seam. No card writes or rearm.
[Mechanisms and remaining proof](snes-full-fidelity-paths.md).

## Fixed-math cache does not close physical deficits — 2026-10-13

Ability3 returns the same six passes/twelve native failures as ability2.
Carbunkl/Lullaby save~96/98us in matched overlap, controls50–102us; Siren has
no net gain, several cases regress. Retain measured negative result; do not
rearm unchanged or price row operations by dividing whole-core time. Source
classification now runs before original blend classification; optimized ARM
half-add stack grows76→148 bytes. Added predicate/palette/stack overhead is a
supported explanation to investigate, not a measured cost or exclusive cause.

Generalized analysis preserves identity/hash/FAT/progress gates and matches
original Rage IDs. Missing old failure tails no longer become zero savings;
explicit common-frame overlap retains earlier Bahamut/Quasar/Siren/Rage stops.
Next targets remain genuine fixed-color fragmentation and mode-specific row/
subscreen work; direct warm/sparse A7 prices are missing.0 card writes, I: unarmed.
[Return and missing evidence](snes-ability3-return.md).

## Ability2 measured partial improvement and fixed-math hypothesis — 2026-10-13

Same-frame A7 CPU savings establish useful Window2 batching without a universal
fix: Ultima/GrandTrain complete, Holy/Meteor remain short.12/18 native failures
remain; no signal/C crash retained. Whole-call savings are not e/r/b unit prices.
Slow2 improves in one context with unchanged work but fails in Rage; variance
and context prevent crediting that improvement to window deferral. Included
observer costs are not subtracted and frequency remains unexposed.

New fixed-operand math palettes target repeated RGB arithmetic; eligible rows
are most numerous in Carbunkl/Siren/Lullaby. Preserve real register flushes and
all mixed/depth-dependent fallback. Exact scalar/memory/cache oracle and18
normal cast replays pass. Initial hidden census export was detected before
claiming work counts, preserved and corrected; mandatory counter presence
prevents absent observations becoming zero. Conditional thresholds remain
unpriced; only the next separately versioned A7 test can measure real saving.
[Return](snes-ability2-return.md), [candidate](snes-ability3.md).

## Aligned common renderer patterns and short regression — 2026-10-13

Generalized Window2 batching removes tile/entry preambles in four of the eleven
failed-effect tails, while preserving row attempts/decode/palette counts and
exact original output. Seven effects have no removed work; do not claim their
failures fixed. Siren/Carbunkl/Lullaby have~158–164 real fixed-color flushes and
~162–168 renderer entries in matched tails. Remaining28-entry cases retain
heavy row work. Captured per-row color/all-consumer correctness is a future
design, not permission to ignore genuine color writes. Existing unused-color
shortcut remains a zero-saving negative result.

18 actual fixtures with a new counter-free core plus22 aligned census runs pass
48,000 exact calls; the actual runner's18 full windows and native/wrapper seams
pass. Initial disabled-counter guard, owned include paths and empty mock base
errors were caught offline and preserved/corrected before staging. Correctly
label $2126/$2127 as Window1; those zeros do not measure Window2 deferrals.
Rage subset uses five confirmed failed contexts; control summon is Terrato.

Conditional dispatch/setup prices still do not close the measured deficits and
are not new A7 measurements. Explicitly requested experimental18-case one-shot
staged on archived healthy I:,79 payloads verified and4,604 prior files preserved.
No production installation acceptance or physical fix claim.
[Predictions, sources and staging](snes-ability-regression.md).

## Ability1 hardware failure replication — 2026-10-13

400-case return identifies24 native PCM failures grouped into11 observed
effects. Holy repeats across six Magic/Rage contexts, Meteor four, Meltdown
and Slow2 three each, Lullaby two; Ultima/Siren/Bahamut/Carbunkl/Quasar/GrandTrain
one each. All use SETUP/errno77;23 SYNC_OBSERVE and one WRITEI_FRAMES. No C/signal
crash is retained. Heavy call tails exceed16.688ms; pooled59.985FPS hides these
local failures. Native quota100.000058% and full software accounting refute a
quota explanation in this sweep. Pointer bias makes late reported reserve
inexact; completed Ifrit has transient128-frame bias, so discrepancy alone is
not a fatality criterion.

Existing generalized Window2 renderer completes11 exact archived failing
contexts offline against original1.19,13,200 graphics/PCM/state comparisons with
animation init/table/deinit observations. No new core build/card writes. This
strengthens correctness coverage but does not price its A7 saving; old work
counts/sensitivity assumptions must not be mixed with new unmatched tail costs.
[Measured tails and missing evidence](snes-ability-suite-return.md).

## Ability targeting and observer identity corrections — 2026-10-12

Before the authorized automated I: exercise, test real command inputs against
separate fixtures. Raise/Arise initially animate toward living Terra and leave
Wedge dead; explicit Down after opening the target cursor revives him. Keep both
negative and corrected receipts. Blitz/Bushido/Tools load command-local attack
numbers with an animation-table base; global-index matching wrongly reports
absent animations. Reinterpret preserved frames using the actual LoadAnimProp
contract; all16 Blitz/Bushido and8 Tool identities are observed. Quadra Slam/Quadra Slice
share properties; Chainsaw naturally takes alternate record336. Late Rage menu
checks select252–254 rather than repeating the first entry.

400 independent contexts now staged on unchanged successful core;149 contexts
exercised offline, without A7 performance inference. Frame-boundary observation
is not animation-completion proof. Full-target/reset/logging plan, measured-cost
limits and pending hardware qualification are in [ability1](snes-ability-suite.md).

## Successful physical return and systematic effect screen — 2026-10-12

Confuser gameplay1 returns cleanly: 7,119 calls/drawings, zero audio errors,
59.994 active calls/sec, minimum reported running reserve1,313 frames and normal
B/display/wrapper exit. Strict577-file archive, clean FAT, consumed marker and
552 unchanged prior files/progress verify; only runtime swap differs. Card stays
unarmed,0 writes. Ben reports two beautiful fights. See
[return](snes-confuser-gameplay-return.md).

At Ben’s request, screen all406 AttackAnimProp records on current and generalized
renderers, plus23 inward trace pairs,19 negative-hypothesis cases and eight
normal completed Magitek casts:567,000 exact graphics/PCM/state comparisons and
2,097,152 original clipping oracle states pass. Generalize Mode1 Window2 to
multiple BG targets and irrelevant-edge writes, removing major Holy/Meteor/
Ultima/Snare/GrandTrain preambles. Reject unused fixed-color shortcut: zero work
saved in19 cases. El Nino/glow/Mode7 remain workload leads, not confirmed A7
crashes. No new hardware build/stage or speed claim; incremental A7 prices and
broader command/state coverage remain missing. See
[coverage, fix, calculations and next evidence](ff6-effect-safety-screen.md).

## Offline hypotheses reveal omitted tile-call overhead - 2026-10-11

[Creative renderer report](bio-blast-clever-renderer.md) tests six isolated ARM
variants. Full-row sums concealed8,341 plain tile calls removed by window batching;
the earlier partial price model omitted this cost. Tiny palette tables/direct
NEON eliminate RGB-row cache storage/work while adding gathers on former hits.
Prefix summaries replace ordered validity scans, with original fallback retained.
12,000 output-comparison frames and clip/range oracles pass; no measured A7 saving.
Revised partial dispatch thresholds0.1855/0.2961us target late/PCM floors.
Retain original negative component accounting, but do not reject the entire
mechanism from it. No production source/card change or installation.

## C-path inverse model and held-out failure - 2026-10-11

[Backward analysis](bio-blast-backward-model.md) finds increasing NEON row
visits and scalar clipped operations, nearly flat tile decoding, and only17us
of added warm materialization payload. Source confirms full-tile NEON versus
scalar clipped fallback and row sums' inability to expose dispatch fragmentation.
Single-count regression on archived controls fails seven-call held-out timing
by at least0.84ms mean absolute error. Do not treat fitted entry slopes as costs.
Rank mechanisms, record inverse thresholds and exact missing populations/prices
before another diagnostic. Analysis only; unchanged card and executables.

## Physical A7 prices reject the current batching prediction - 2026-10-10

[Cost1 return](snes-a7-cost-return.md) archives all13 physical passes. Each
reproduces SETUP/77 before the dense frame320. Small warm setup blocks are
fractions of a microsecond; weighted baseline fixed setup gives2.179us/entry.
The conditional mean model credits231.5us, debits149.8us for added rows and
114.6us for short-span helpers:32.9us loss. Zero helper cost still leaves only
81.7us saving versus the1,514.3us floor. Whole-candidate cache/removed path mix
and longer pending spans remain unpriced, so this is a negative model verdict,
not measured whole-candidate performance. No production build or install.

Deep phase clocks add9.294ms CPU in the complete sampled frame and advance
failure six calls; using the raw29us setup/entry quotient would credit observer
cost. Later passes have a different color-cache split from frame0 before active
timing, despite exact total requests and entries. Full unwrapped PCM histories
show quota consistency and reserve erosion, then the recurring384-frame pointer
discrepancy. Dense pixel/color attribution and full recovery remain absent.
Archive/hash/FAT checks pass with0 card writes; all141 protected hashes survive.

## Byte-matched ROM -> circular-window renderer work - 2026-10-10

User asks to reconstruct ROM code and follow functions through hardware behavior
to an emulator change. Full owner ROM rebuild is byte-exact; static native
instructions receive a private C map, with readable focused script/wave code.
178 real wave-copy executions match the model. Direct register/flush trace
exonerates immediate BG1 scroll redraws in the tested frame and identifies123
pending-render flushes from the circle's Window2 edges. A separate per-line clip
patch preserves the actual effect and batches other background work.

The independent original clip oracle covers524,288 states;3,600 actual ARM
comparison frames pass visible/PCM checksums, geometry, sample counts and periodic
serialized-byte comparison. The effect interval has78.97% fewer PPU entries but
34.58% more color-row materialization; a net A7 win cannot be inferred. Initial
patch preparation crossed a function boundary into Mode7, failed compilation,
and was narrowed before successful qualification. That was a preparation defect,
not a hardware result. No new production core or card candidate installed.
Preserve all private inputs and six bounded public evidence files. The armed
focus1 result remains the next physical input. [Cause map](ff6-bio-blast-cause-map.md).

## Bounded focus1 diagnostics installed on unchanged1.19 - 2026-10-10

Final24 physical failing calls lacked phase samples. The diagnostic runner keeps
64 calls, adaptively samples real phase/callback CPU under ordinary-call load and
prevents sampled cost from extending capture. It does not change pacing, pixels,
core or audio admission. Actual ARM contract checks and analyzer rejection cases
pass. Archive58 MVP/progress and49 lab files before writes; clean FAT and138
protected hashes independently verify. Only focus1 SNES armed, Code.bkp absent.
Physical cost/overlap and instrumentation overhead remain explicit limits.
[Qualification and next test](snes-focus-1.md).

## SNES1.19 Bio Blast failure and completed exit - 2026-10-10

Ben reports another Bio Blast failure and exit with B. Archive58 MVP/progress
and49 lab files read-only; fresh FAT is clean. Exact1.19 release, all prior files,
nine CRC-valid snapshots and three nonempty SRAM generations verify. Current
stock/Vesper SD artwork and normal init match; all markers and Code.bkp absent.
No card changes. Native session502-9771840000 runs1,713 calls, loads a snapshot,
then reports SYNC_OBSERVE errno77/SETUP; its audio error returns to our library.
B leaves that library, display worker joins and wrapper final copies complete.
Status255 is rc=-1 from the game failure, not a recorded signal crash.

Final23 ordinary calls average18.287 ms wall /16.935 ms CPU. Matched227.816 ms
audio interval supplies38,764 accepted frames/sec to a44,100 Hz sink; reserve
erosion precedes an unexplained+128/+256 pointer difference, total384 frames.
The offline lookup savings did not fix physical sound. Similar1.18 costs are
historical context, not controlled cache-speed proof. No phase sample covers
the final24 calls; next work is bounded RAM-only phase attribution of the actual
expensive interval, retaining instrumentation-cost limits. Keep1.19 unarmed.
Publish text/metadata only, preserving all637 previous evidence hashes.
[Physical result and reproducible analysis](snes-mvp-1.19-return.md).

## Explicit1.19 rearm for proper exit - 2026-10-10

Ben requests rearming the same installed release to exit properly. Archive56
returned MVP/progress files and49 lab files before mutation; FAT is clean.
Exact1.19 payload, current stock/Vesper boot baseline, private progress and27
reader files verify across138 protected hashes. Only the one-shot marker is
recreated. This is an authorized lifecycle retry, not new audio/performance
acceptance or a changed candidate. Select+Start opens the game menu; choose
Exit game and wait for the stored-save status before power off.

## SNES1.19 demand-driven color rows - 2026-10-10

Return to the recovered1.18 Bio Blast deficit after completing both boot
screens. Inspection finds eager eight-row RGB materialization before the
actual transparency/depth rejection. Prepare only visible requested rows,
retaining the36 KiB cache and existing invalidation, PCM and frame policies.
Repeated1.18 scene census matches its historical1,200 rows;162 expensive effect
frames reduce palette lookup rows1,003,928 ->667,001 (33.56%). All other126
work counters and command-boundary pixels/PCM CRCs match. Row-level requests
rise slightly, so this does not prove a CPU speedup. Shipping core passes14,400
clean-core equivalent frames and ARM runner/lifecycle/invalidation checks.

Initial runner integration lacked a separately prepared new-core snapshot;
prepare its matching header without altering owner input, then pass. The first
installer guard rejects current SD showlogo before writes because the historical
lab guard predates Vesper artwork. Current bytes match the independently verified
Vesper release exactly; pin that hash instead of restoring or weakening the guard.

Archive51 MVP/progress files and49 lab files before installation. Retain29
private save/state files,49 lab files,27 SPI-reader files and exact current boot
hashes; create a separate state header with original payload. Fresh FAT before
writes and after payload is clean; independent readback passes. Only SNES1.19
is armed; no firmware update trigger or new flash write. Physical first launch,
complete repeated MagiTek Bio Blast, sound and movement are the next acceptance
test. [Candidate and receipts](snes-mvp-1.19.md).

## Both Vesper screens verified; normal startup restored - 2026-10-10

Returned run `db7079b5f61b4ee5b7d36d22e58472fd` completes two 8 MiB SPI reads
in 103.790618 seconds. Both match the expected programmed image byte for byte,
SHA256 `509cdc305deca2654fbf48184eb16d523b4b6cae0effffc4a3cba6845622d9fd`,
CRC32 `cdf3f0aa`. Marker/run, wrapper exit, ID/status/counts and CRC checks pass.
Archive twice before fresh FAT/run/init gates and original startup restoration.
Independent reread verifies normal init, no Code.bkp/armed markers, five stock
hashes, 51 protected MVP/progress files, 49 lab files, both nine-file prior reader
profiles and all returned captures. Final FAT clean; no flash/config writes.
The user's earlier Vesper static -> Vesper animation -> stock launcher report
and complete installed equality finish both requested replacements. Ready for
normal use with no verification delay. External recovery unqualified; audio
unresolved. [Verified result](vesper-static-firmware-update.md).

## Both Vesper boot screens accepted; read-only verification armed - 2026-10-10

User explicitly confirms Vesper static -> Vesper animation -> stock launcher.
Archived 51 MVP/progress files, 49 lab files, profiles/root/display logs and the
exact package before removing Code.bkp through fresh FAT checks. Stock/progress
hashes remain exact. Retained all nine second-animation capture files and nine
older factory-reader files; reused the unchanged qualified reader/wrapper with
fresh run `db7079b5f61b4ee5b7d36d22e58472fd`.
Independent marker/no-stale-results/init/rollback/reader/manifest/protected/
retained-profile checks and post-arm FAT pass. Only read-only reader armed,
targeting the new expected full image, SHA256
`509cdc305deca2654fbf48184eb16d523b4b6cae0effffc4a3cba6845622d9fd`.
Full 8 MiB equality and the next boot without the trigger are pending. First/second
appearance acceptance is the user's report. External recovery unqualified;
audio unchanged. [Current physical verification/return](vesper-static-firmware-update.md).

## First static Vesper update qualified and staged - 2026-10-10

Replace the exact640 x480 RGB565 bitmap using the accepted animation background.
Start from the physically verified Vesper-installed image; preserve every byte
outside bitmap0x8854/614400, including boot instructions/header and second
animation/rootfs/kernel/tables. Ten offline checks execute the actual Thumb
bitmap stores/loader and captured updater with RAM-only flash, including refusal
fixtures. Valid simulation erases ten64KiB blocks/2560 pages; metadata
17e40b24/5d4a6000. Seven host stage/rollback/card/baseline/refusal checks pass.
Archive current progress/profile/logs and verified full backup before staging.
All1,006 original readable card files exact; only qualified Code.bkp added.
Independent package/init/protected/profile reads and fresh FAT pass. Normal
init exact and no test armed; user SD update/first-screen boot/full new-image
verification remain pending. External recovery unqualified, audio unresolved.
[Exact staged image and next physical/return steps](vesper-static-firmware-update.md).

## Installed Vesper image verified; normal startup restored - 2026-10-10

Run c4a59205933b4459a9d88ed6aafe5dd2 returns two complete8MiB SPI reads in
103.776166 seconds, each exactly equal to the expected vendor-mutated image.
Archive twice before restoring original SD init through fresh FAT/run/hash gates.
Independent card reread confirms full captures, original init, absent Code.bkp/
armed markers, five pre-update stock/runtime hashes,51 protected MVP/progress,
49 lab and9 retained prior-reader files. Final FAT clean. This establishes
installed bytes and init execution without the update trigger, supplementing
the user's earlier static D-R35 -> Vesper -> default launcher acceptance.
No additional visual report supplied on this return. Ready for normal use;
first static screen preserved, external write recovery unqualified, audio
unresolved. Publish metadata only; raw flash and private progress stay local.
[Verified return](vesper-flash-verification.md).

## Original second-animation replacement physically accepted — 2026-10-09

After SD update progress100% and power-off, normal manual power-on shows the
static D-R35 screen, Vesper replacing the regular D-R35 animation, then default
launcher. The user's physical observation accepts the requested replacement
and boot path. The earlier added third SD-stage splash stays consumed/unarmed.
Card-return logs/package, exact flash bytes, trigger removal/repeat cold boot
and external recovery remain pending; no new device/card access on this report.
First static screen preserved and audio unresolved. [Result and next return](vesper-sd-firmware-update.md).

## Current authorization and SD firmware staging — 2026-10-09

The user explicitly chooses the SD update now, accepting programmer purchase
if boot fails. That supersedes waiting for external recovery equipment; it does
not establish recovery or remove the vendor's boot-code-block erase. The exact
previously qualified package is staged as retro/update/Code.bkp after archiving
current logs/private progress and another full original SPI backup. Fresh pre/
post FAT checks,997 unchanged readable card-file hashes and independent package/
init/updater readback pass. Normal init remains exact; other tests stay unarmed.
6 host staging/refusal/rollback checks pass. Expected full programmed image
includes the vendor metadata, and has its own SHA distinct from the candidate.
Physical update, Vesper replacement/cold boot and full flash readback await the
next device run. First static screen stays; audio remains unresolved.
[Staging evidence and exact physical/return instructions](vesper-sd-firmware-update.md).

This history preserves what changed, what was observed, and the inference boundary. It does not retroactively turn proposals into device results. Deeper dated reviews and selected raw returns are published under `docs/reference` and `evidence`.

## 2026-10-09: install animated Vesper stock-splash replacement

After approved FAT recovery and fresh healthy checks, install the qualified
feathered cyan V/heart with loading dots. Exact patched hash and stock code
outside the ZIP verify; fresh protected save/runtime/lab files and recovered
chains match. Both tests stay unarmed and post-install CHKDSK passes. Older
swapfile differs without an immediate pre-install baseline; record the limit
and preserve its current contents privately. Physical appearance/stock handoff
acceptance remains pending. [Installation evidence](vesper-boot.md).

## 2026-10-09: verify whether FAT repair is warranted

Subsequently approved repair/recovery succeeds:14 chains preserved, fresh checks
healthy and all412 readable files unchanged. Recover actual1.18 session/PCM text;
restore only known pre-test SRAM into its empty path. No audio fix, splash install
or re-arm. [Recovery evidence](fat-recovery-2026-10-09.md).

Fresh read-only CHKDSK repeats both invalid backup entries and 1,472 KB in14
lost-chain files on serial11EB-1465. Separate byte reads fail with Windows1392
on both paths. Although unlocked CHKDSK can have false positives, the matching
read failures corroborate actual filesystem damage. Repair/recovery is needed
before card updates; approval remains pending. No repair, installation or
re-arm occurs, and no audio-cause or physical card-health conclusion follows.
[Evidence and resume gate](fat-verification-2026-10-09.md).

## SNES host/adapter investigation

| Stage | Observation and resulting decision |
|---|---|
| Factory path | FF3/VI audio warbled. A core substitution alone did not establish correct native/host timing. |
| Plus direct rename | Putting Plus directly at `emu_sfc.so` bypassed the adapter and garbled live video. Correct baseline keeps adapter and core as separate files. |
| Chunk-buffer ownership | Heap buffers were unsuitable for the scaler. Chunk-backed compact RGB565 and completion-aware reuse fixed corruption. Clean menu preview alone had not proved the game path. |
| ROM/audio comparisons | Known-clean v1.0/Rev1 ROMs and matching music data did not identify corruption as the clicking cause. A 2010 trial still clicked before host timing was repaired; it is not a final 2010 verdict. |
| Analog path | Speakers, headphones and ground-loop-isolator combinations still exhibited the issue. Captured concatenated PCM sounded clean, but did not preserve gaps between writes. |
| Map/menu control | FF6 map clicked; party menu with the same music stopped it; map restored it. Workload affected deadlines. Other games/scenes were cleaner. |
| Write audits | Nonblocking behavior and accepted batches were measured. Simple lost-partial-write guesses were not established as the explanation. The new transport nevertheless owns/preserves partial/EAGAIN data. |
| v8/v9 drawing controls | Removing expensive internal drawing reduced core-call wall time sharply while audio/emulation continued. Omitting only presentation is a different experiment. |
| v9 measured runs | Normal average call19.958ms vs render-disabled6.752ms; native budget16.688ms. Wall includes callbacks/preemption. The deficit cannot all be assigned to SNES graphics CPU. |
| v10 adaptive policy | Mixed run23,604 steps,1,183 held drawings (5.012%); intro/Narshe/wind listening clean with no obvious dropped pictures. Held percentage is not CPU shortfall. |
| v11 production | Retained adaptive internal drawing and continuous resampling; removed automatic diagnostic overhead, retained opt-in observation and rollback. This is the playable reference. |

## Platform inventory and UART control

Hardware v1 identified the single A7/Linux platform, memory arrangement, driver resources, DT and profiling limitations. v2 added runtime CPU/FD/IRQ data and recovered bounded logs/symbols. Driver DWARF/assembly established private ABIs and existing asynchronous display work.

Hardware v3 redirected stdout/stderr to `/dev/null`. IRQ19 remained around7k/s (v2 6968.24; v3 6953.20), comparable high-load CPU phases stayed essentially the same, and the same map/menu/map sequence felt the same. The negative result demotes ordinary console redirection. Other console descriptors and actual IRQ handler cost remain unresolved.

The kcore recovery branch stopped at ENOENT. No MMIO/flash fallback occurred. Tracefs IRQ timing and separately pricing scaler setup/wait/producer blocking were proposed; they have not been reported as completed measurements.

## Launcher MVP bring-up

| Version | Physical result | Lesson/fix |
|---|---|---|
| 1.0 | Stuck on loading animation; no persistent exit log | An unbounded all-buttons-released gate existed before first paint; RAM-only evidence could be lost at power-off |
| 1.1 | READY in about200ms, UI briefly appeared then splash replaced it | A genuine input-gate fix did not explain this failure; independently running showlogo still owned display cleanup |
| 1.2 | Splash exited with acknowledgment; READY reached, controls failed/fallback reported | The recovered handoff worked; readiness did not prove polling/liveness |
| 1.3 | No buttons; main thread in identical absolute sleep six seconds apart | A clock/timer seam stalled the UI. Heartbeat restoration was not shown to fix it. Native direction masks were also incorrectly relabeled |
| 1.4 | Launcher worked, FF6 started, private state loaded; 2465 frames, two pauses, no write errors | Direct kernel clock/relative waits repair the input loop. Same probe showed kernel8.361s vs libc447.327s. Directions still incorrect |
| 1.5 | All four directions confirmed; launcher/game/state work; 23,872 calls, 11.838% held drawings; occasional lag and rare random crackles in story/map | Stock-derived input repair is physically validated. Performance/audio are not fully qualified; mixed held-frame means cannot establish full-render throughput |
| 1.6 | Very choppy sound, slow movement, clean-looking graphics, then whole-device power-off | Output equivalence did not prove faster A7 execution or physical stability. Startup worked; no fresh session report/exit record survived. Do not attribute stale 1.5 totals to this run or re-arm unchanged |
| 1.7 | No crash; Save Point/save/normal exit; lag remains, partly relieved in FF6 party menu | Fresh 7,068 calls, zero holds, ~54.63 calls/sec active loop; 31.08% definitely over budget. Audio queue sampled empty despite complete PCM acceptance. Missing head leaves system diagnostic gaps; source regression now reproduces sparse firmware PATH. New progress archived; card unarmed |
| 1.8 | Played okay, clicking returned, whole device powered off | Fresh previous checkpoint:1,648 calls, zero holds, ~57.93 calls/sec;13.33ms mean core wall plus3.00ms lead wait. Latest/tails empty, final report stale1.7. Both head and sed absent; source fix now tests both missing. Shutdown cause unknown; progress intact, card unarmed. Exact returned core passes10,000 output frames |

The user reported Rightâ†’Down, Leftâ†’Right, Upâ†’Up, Downâ†’Right and repeated the duplicate-Right observation before1.5. The unlabelled raw traces cannot attribute each physical press independently. The stock callback establishes four distinct canonical directions; the1.5 physical return confirms all four. Do not silently edit the historical report to fit a neat permutation.

## Corrections that must survive future work

Ben next authorizes a standalone hardware lab and custom software exploration.
[Lab1](platform-lab.md) isolates A7 tile-work reuse, OSS negotiation/service and
display/CPU overlap in bounded phases. Its [physical return](platform-lab-1-return.md)
completes all phases and stock handoff. NEON wins, this cache loses, CPU slicing
gives no clear benefit, and5ms deadlines average5.48ms late. Negative free-space
reports are retained; an audio scheduling clock/timer quantum remains unqualified.
The card is archived/unarmed. No hardware ceiling or whole-game speedup is inferred.

- The1.8 return disproves the claimed firmware sed availability. Test actual
  capture with both head and sed absent. Current shell-builtin repair is source
  only; retain historical releases. Empty latest/tails and a previous running
  checkpoint do not identify shutdown time or cause. See [return review](snes-mvp-1.8-return.md).
- MVP1.8 proceeds with a forward A7 renderer build at Ben's direction, replacing
  the proposed paired device comparison. Mode specialization must be verified
  in emitted code. Clamp empty/reversed clipping before unsigned vector counts;
  the actual FF6 intro exposed this seam before release. See [1.8](snes-mvp-1.8.md).
- Native0x40/0x80/0x20 mean Down/Left/Right in the **final stock callback**, not the names assigned in the earlier review.
- A green first-frame/QEMU check did not prove sustained physical UI input.
- A ~85% host thread includes core, adapter and frontend; it is not Snes9x-only CPU.
- 240 scaler log messages/s is not established four messages per60Hz frame.
- Scaler IRQ counts are not panel refresh; static NEON counts are not executed hot-path cost.
- Clean concatenated PCM is not absence of wall-clock delivery gaps.
- 5% held drawings is not a proven5% CPU deficit.
- Stock `sound_driver_playframe` returns void; a tailcalled write register is not a public result API.
- A DT GPU node is not an operational GPU; a symbol/struct field is not a demonstrated queue contract.
- The old timestamp regex parsed `[247]` source-line text as time. Corrected v3 analysis anchors at line start. Older v2 derived spans must not be trusted without reanalysis.

The user requested a concrete full-speed proposal before another run, then
authorized implementation. [MVP1.6](snes-mvp-1.6.md) implements ordinary NEON
tile/color kernels, completion-aware display queuing, independent audio-first
delivery and full rendering with one kernel-monotonic clock.8.4million color
checks,280k rows,1200 real-core equivalence frames and migrated-state runner
resume pass locally. Raw snapshots were found to embed host pointers; the state
oracle normalizes only named pointer fields and compares resumed output too.
The isolated core and separate qualified state copy were installed for the
physical test, which failed. The return is archived and unarmed; stock and all
original progress are intact. Read the [failure review](snes-mvp-1.6-failure.md)
for the surviving evidence, telemetry gap and controlled qualification needed.

After stock boot was confirmed, the user requested logging and another run.
[MVP1.7](snes-mvp-1.7.md) therefore retains the exact failing core and pipeline
while adding crash-surviving progress and bounded platform evidence. Real ARM
SIGKILL and wrapper live-persistence checks pass. Installation preserves stock,
hook and 19 pre-install private files; the one-shot was armed for this retry.
This updates the test sequence without claiming speed or a shutdown cause.

The [1.7 return](snes-mvp-1.7-return.md) supplies fresh final totals and completed
main/display cleanup. Archive 38 files read-only, including new SRAM/backup;
the card remains consumed/unarmed. Party-menu relief is game workload evidence,
not a host-pause reset. Active-loop throughput is below native speed; worker
wall overlaps and legitimate audio throttling must not be added/subtracted as
automatic performance gains. Correct missing-head diagnostics in source,
test the actual wrapper with a sparse PATH, retain the shipped release and
record empty kernel/stderr and missing final wrapper line as evidence gaps.

## 2026-10-05: infrastructure contracts before the next game build

Ben asks for an aggressive investigation of the infrastructure rather than
another emulator guess. [Lab2](platform-lab2.md) prices independent waits and
slack, actual native-rate OSS transport, readiness/drain/reset, chunk/heap costs
and coherent production with occasional28ms CPU bursts. It retains every
synthetic drawing and PCM byte. Readable labels and ramped tones address lab1's
physical feedback. Physical results were pending at installation; the subsequent
return is recorded below.

Offline extraction recovers exact scaler/display calls. Read-direction
0x80045004 receives scalar3000; its units remain unknown. Status tests bit2, with
ten fallback sleeps and no further status query. dispFlip submits a44-byte bitmap,
calls update/wait candidates and then toggles its index. A/B status names and
queue fields remain leads, not established continuous ownership. The lab observes
the existing calls and their real arguments in RAM; it adds no hardware command.

Actual ARM checks execute the concurrent owner against odd-byte shorts/EAGAIN/
misleading readiness and compare all nine accepted streams against independent
Python bytes. A RTLD_LOCAL shared-driver fixture verifies pointer/scalar/status
and metadata interception. Timer restoration, sparse shell handoff and whole-run
TERM/KILL/reap pass. Distinguish these exactness/lifecycle checks from device speed.
The guarded updater archives every old lab/private file before changing owned
payload and arms last; the game runner/core and stock paths remain unchanged.

Lab2 is now installed and armed after a fresh41-MVP/17-lab archive. Independent
readback confirms released bytes, both markers,13 retained lab files and20
protected private entries. Stock, hook, dispatcher and original game paths match
their prior hashes. Physical results were pending at that checkpoint.

## 2026-10-05: lab2 return and researched interface correction

Ben returns the card and reports clicks between tests and some clicking during
tests. Wrapper status0 permits stock handoff; the final stock screen is not
separately confirmed. Archive 41 MVP/49 lab files read-only, verify all 20
protected private entries and exact payload/stock/game hashes. Both one-shots
are consumed. No update or re-arm occurs. The [return review](platform-lab-2-return.md)
retains raw batches and qualified analysis.

All 1152 timer observations survive. Libc/direct syscall/poll timeout/timerfd
1/2/5ms requests average about 10ms under both load and slack settings. Neither
direct syscall nor reduced slack repairs coarse wakeups. Device-driven audio
readiness can wake around 2.77ms in a transport. All nine PCM targets are
accepted and all four 240-drawing phases complete, but occasional 28ms CPU
bursts exceed nominal playable lead and take longer than four logical seconds.
These are concrete scheduling/reserve findings, not hardware limits or clean
sound/full-speed acceptance. All 973 scaler statuses include FRAME_DONE; its
ten-sleep fallback never runs. Nonwait syscall brackets total about 0.37ms per
256Ã—224 job; worker wait wall overlaps core work rather than adding serial CPU.

Ben challenges using physical runs to rediscover documented interfaces. The
[source review](platform-interface-research.md) reads Linux 4.19 OSS/native PCM
and a pinned TinyALSA client. OSS accepts partial fragments into staging outside
GETODELAY; POST starts without flushing, SYNC flushes/drains, RESET discards.
Lab2's zero-delay reset leaves accepted/pointer accounting residue, so its
claimed faded drain was not qualified. This was discoverable from source before
the test. Boundary clicks have a software candidate; during-test clicks remain
unresolved. Do not promote nominal queue-gap indicators to exact xruns.

Native ALSA playback/control/timer nodes exist and its source defines constrained
parameter negotiation, priming, meaningful poll wakes, stream state and drain.
Current game source splits lead accounting across queues and several gates.
Its `ring_count` includes the worker queue through `pump_audio`; the defect is
separately sampled queue/device delay plus uncounted OSS staging, not omission
of the entire worker queue. Preserve that correction to the initial review.
The next implementation should use one coherent native PCM owner, a playable
reserve for long calls and valid in-frame publication of already-emulated PCM.
Matching Generalplus kernel/SDK sources remain unlocated; current module-map
metadata does not supply the matching display/audio implementations. Remaining
physical work should qualify vendor behavior and the repaired real game path.
The analyzer's drain/reserve/scaler extensions pass independent calculated
fixtures. No new executable is installed by this return/research work.

## 2026-10-05: implement the researched native game path

Ben authorizes building and explicitly retains the wider goal: understand and
exploit the hardware, not stop at a smooth emulator. [MVP1.9](snes-mvp-1.9.md)
implements native PCM, one coherent owner,64ms playable priming, event-driven
consumption admission and earlier already-mixed core audio. Native rate avoids
conversion when accepted. Full drawing and prior UI/display/input contracts
remain. The [capability roadmap](hardware-capability-roadmap.md) records measured
costs, useful concurrency and remaining interface/ownership opportunities.

1200 exact-output frames pass;1196 publish identical PCM in earlier batches.
Independent actual ARM client/owner fixtures cover constrained settings,
partial/EAGAIN, START failure after acceptance, asynchronous drain, visible XRUN,
30ms bursts, false readiness, fixed deadlines and blocked cancellation/flush.
Final runtime checks pass180/30 mock frames and snapshot/SRAM/menu/splash/display
ownership. Neither QEMU nor those fixtures qualifies vendor PCM settings,
physical sound/full speed or fixes prior poweroffs. The exact-baseline updater
archives all returned logs/private progress before changing owned files and
arming; independent readback and source/check hashes gate selected publication.

Installation archives41 MVP/49 lab files before writes, retains20 existing
private entries and49 lab files, verifies stock/hook/original game-wrapper
hashes and creates only the separate qualified snapshot. Independent readback
passes; game one-shot armed, lab unarmed. Physical results remain pending.

## 2026-10-05: native startup failure and state-aware repair

Ben returns1.9 with Audio Failure before the game launches. Read-only collection
archives43 MVP/49 lab files; exact released payload and18 previously protected
game-progress files are unchanged. Both final and first-attempt reports record
zero emulation,44100Hz/128-period/3712-buffer and2823 accepted priming frames,
then EBADFD. State2/queue0 is prewrite, not the failed after-write state.
Runtime/kernel byte tails are empty; exact failure operation is missing.
See [return](snes-mvp-1.9-return.md).

Linux4.19 WRITEI can start playback at the software threshold; START requires
PREPARED.1.9 calls START on queued count alone, a concrete client defect. The
retained logs do not establish the exact vendor cause.1.10 uses the priming
threshold, observes write-driven RUNNING, STARTs only from PREPARED and checks
RUNNING afterward. EBADFD succeeds only with fresh RUNNING evidence. Preserve
operation/errno/state/pointers on failures and running-stream minima. Bounded
runtime/kernel capture now works without tail/head/sed.

Independent actual ARM fixtures exercise the observed fallback, automatic and
healthy explicit start, verified EBADFD race, rejected early/nonrunning states
and parameter mismatch. Owner/runtime/input/splash/display/save checks and
1200 exact core-output frames pass. The exact early-audio A7 core is unchanged;
this is not another performance/core experiment. See [repair](snes-mvp-1.10.md).
Physical startup, consumption, sound/full speed and prior poweroffs remain
unqualified; the next test first needs successful FF6 startup.

Installation completes after a fresh 43-MVP/49-lab archive. Independent readback
verifies the exact 1.10 payload, all 22 current private files, 49 lab files and
unchanged core/stock/hook/original-wrapper hashes. No snapshot migration or core
replacement occurs. Game one-shot is armed; lab remains unarmed. Physical
startup, playback, speed and stability are pending.

## 2026-10-05: native playback fails during play/resume

The 1.10 return preserves two controlled fatal reports: 72 and 605 calls, one
WRITEI/EBADFD per attempt, software high 2823/8192 and 705 frames remaining. The
UI's overflow label incorrectly hides worker errors. Second report proves one
pause/re-priming, but lacks explicit snapshot success. No intentional holds;
fatal callback omits one final drawing. Short second interval reaches 59.70
active calls/sec. Do not promote that interval to sustained speed/audio proof.
Archive 43 MVP/49 lab files read-only; 19 prior progress files/snapshots unchanged,
updated FF6 SRAM retained, exact payload and stock hashes verified. dmesg is
absent. Stock fallback follows recorded library B exit and joined cleanup.

The source's requested admission refresh is not awaited. A deterministic
actual-device-lead change reproduces stale admission against the immutable
shipped owner and passes the repair. 1.11 reads post-HWSYNC state/control with
GET flags, uses negotiated-boundary pointers, restores period readiness after
DRAIN and retains fresh post-write-fault state. Pause drain failure stops before
snapshot work; error labels distinguish transport from capacity. Count loads,
rejections and native epochs with fresh phase checkpoints.

The real FF6/native-client/owner consuming fixture passes injected WRITEI
failure, clean retry, two snapshot loads/re-primes, 25ms producer stalls, 120
full drawings and complete successful PCM accounting. Existing ARM contracts
remain. Core and PCM candidates are unchanged. Exact vendor failure cause,
sustained physical continuity and earlier poweroffs remain open. See
[return](snes-mvp-1.10-return.md) and [repair](snes-mvp-1.11.md).

Installation completes at 19:09 UTC after a fresh 43-MVP/49-lab archive.
Independent readback verifies the qualified 1.11 payload, all 22 current private
files including updated FF6 SRAM, all 49 lab files, original snapshots and
unchanged core/stock/hook/older-wrapper hashes. Game one-shot is armed; lab is
unarmed. Physical playback, snapshot resume, speed and stability are pending.

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

Installation/readback complete at 2026-10-06 04:13 UTC (October 5 locally).
Archive 43 MVP/49 lab files before writes; retain and verify all 22 current
private files, 49 lab files, original snapshots and core/stock/hook/older
wrapper. Game one-shot is armed; lab remains unarmed. Physical capture pending.

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

## 1.14 follows the execution-budget review

[1.14](snes-mvp-1.14.md) owns the whole-program A7 compilation, adds custom
NEON planar decoding, exact reduced-ratio frontend conversion and removes a
duplicate locked PCM observation. Clean-core output equivalence and independent
oracles pass. Sampled APU/PPU regions and24 recent per-call costs travel with the
same gameplay build. A sustained19.8805ms provider fixture now proves the
controller exposes starvation rather than masking it with an initial buffer.
This is not proof of native device speed or a complete vendor-driver diagnosis.

Before delivery,1.14's marker was archived and retired unconsumed.1.15 keeps
the exact core and retains eight sampled calls separately so phase costs
cannot immediately age out of the recent24-call history. The complete runtime
qualification is rerun; no extra physical experiment is requested. Both
intermediate and final release/evidence bytes remain immutable.

## 1.15 return exposes redundant raster invalidation;1.16 repairs it

[1.15](snes-mvp-1.15-return.md) has three audio-failed attempts. Two retained
reports show successful snapshot loads followed by19/18 calls; ordinary main
CPU about18ms, wall19.3–19.5ms, sampled PPU about10ms. Exact payload and21
game-progress files match. No new poweroff independently established. The
first detailed history is lost across retries.

Exact-state local census finds214 pending $2132 flushes per frame with no
effective fixed-color change. Raw channel-tag changes fragment render work.
[1.16](snes-mvp-1.16.md) flushes only on changed selected components, preserving
assignments/latch and flush-before-change.217–223 PPU jobs become4–10; every
tile row/frame/native sample remains.16.8million extracted register cases and
1200 exact-core frames pass. Removed jobs do not prove physical cycle savings.

Failed-session report/trace pairs now survive retries; native lifecycle fixture
verifies first-failure preservation. Final install/readback at06:23 UTC keeps
all23 original private files and49 lab files exact; game armed, lab unarmed.
Next physical acceptance is sustained saved-scene play, party menu, pause/resume
and save/exit with full sound and rendering. First-launch stability remains
unresolved until that run.

## 1.16 provides sustained margin;1.17 removes an observer workload

[1.16 return](snes-mvp-1.16-return.md): successful retry runs31,601 complete
video callbacks near59.99 calls/sec, zero intentional holds, duplicates or
audio-write errors. Snapshot load, game save, combat and menu work. The exact
first70-call failure now survives retries. It shows9ms CPU stretching to
18–39ms wall time during the wrapper11.27–11.57s discovery/card-copy window.
This separates a short scheduling stall from the earlier sustained core deficit.

[1.17](snes-mvp-1.17.md) removes live routine diagnostics rather than shifting
the same workload to another arbitrary gameplay time. Old wrapper fails the
actual lifetime/write fixture; repaired wrapper, ARM runtime contracts and
12,000-frame output equivalence pass. Core remains byte-identical. Independent
install/readback preserves all26 private and49 lab files; game armed, lab
unarmed. Physical cold-start reliability is pending; whole poweroff can lose
RAM-only progress. Wind/snow reported missing in outdoor Narshe remains a
separate effect/phase/baseline correctness question.

## 2026-10-08: first-launch success and Magitek Bio Blast

Archive1.17 before writes:50 MVP/49 lab files verify, stock/release match,
all snapshots intact, changed SRAM retained. User confirms first attempt worked
and identifies the failure as Terra's armor Bio Blast -> audio error/library.
Native report retains35,763 calls; effect calls overrun, reserve erodes before
vendor pointer steps/SETUP. Wrapper run log/backup remain1.16 historical data.
User corrects expected driving snow; no demonstrated snow regression remains.

Derive an offline private Magitek replay, distinct from Edgar's Tools attack.
157 renderer updates/frame expose repeated tile-color work.1.18 adds bounded
NEON materialization with explicit mutation/load invalidation.1,200 effect and
12,000 intro/Narshe frames match clean output; matched work counts show93.36%
reuse/48.71% fewer lookup rows. Prior losing Lab1 cache is explicitly retained;
physical benefit remains pending. [Return](snes-mvp-1.17-return.md),
[implementation](snes-mvp-1.18.md).

## 2026-10-09: repeated Magitek exit, filesystem damage, Vesper loading art

1.18 again returns to our library with an audio descriptor failure reported
at Magitek Bio Blast. Archive51 readable MVP/progress files and49 lab files
before writes, explicitly recording two unreadable backup entries. Preserve
412 readable card files in a private full backup. Exact release and stock
hashes match; snapshots survive. Fresh fault/session files and current SRAM
are zero bytes, while wrapper stderr is stale1.16. No new timing/PCM attribution
is possible. Read-only FAT32 check confirms invalid allocation units/lost
chains; repair/recovery consent is pending. [Return](snes-mvp-1.18-return.md).

Build the requested feathered cyan wing-V/heart boot screen from the user's
preferred reference. Recover the stock embedded ZIP/sprite contract, alter
only artwork data, and qualify decoding plus all18 draws through the exact
original ARM functions. Publish owned artwork/source; preserve vendor ELF
privately. Installation waits for a healthy card; SNES remains unchanged and
unarmed. [Boot workflow](vesper-boot.md).

## Physical boot return: Vesper unchanged — 2026-10-09

Ben saw unchanged solid boot and stock animation, then stock launcher. Returned
patched showlogo still has SHA ab56a67ae629e816a5752b1ad7cec2c335b46c82df84856f8a41376d2f919ebe.
FAT is healthy; strict archive snes-mvp-return-20261009T160157Z preserves51 MVP
and49 lab files. SD init does not launch showlogo. Actual early-boot owner is
unverified; offline sprite qualification did not establish executable ownership.
A passive consumed-once probe captures startup scripts, mountinfo and any active
showlogo executable privately. It never launches a splash, signals processes,
controls display or writes firmware. Offline capture fixture and archived device
BusyBox syntax checks pass. SNES/lab remain unarmed; audio remains unresolved.
On next return archive retro/vesper-boot-probe/results first, then restore exact
init.before-probe from the installation receipt. Physical acceptance has failed.

## Actual animation owner captured — 2026-10-09

Second physical test remains stock. Passive capture proves PID447 executes
`/showlogo` from internal root: captured198408-byte executable SHA
436d8018808b150c926274575a195f664e61db646f44713371019e9ae10caf3b
matches stock, not patched SD copy. Source-script capture failed because firmware
PATH lacks tr. Correct filename mapping uses shell case only; capture fixture
passes. Strict51-MVP/49-lab archive and all probe files preserved privately in
`device-evidence/snes-mvp-return-20261009T161740Z`; original init restored exactly
before corrected capture installation. No firmware mutation or audio changes.
Next capture must recover init.rc/init.project.rc and mountinfo to identify a
reversible startup seam. Internal solid-logo owner remains unproven.

## Captured boot route and SD-stage animation test — 2026-10-09

Corrected capture succeeds: init.project.rc launches /showlogo before sleep2,
mounts card /retro at /usr/retro, then launches SD init. Internal rootfs is RAM
rootfs; no firmware replacement is attempted. Captured stock owner and boot
scripts are archived privately in snes-mvp-return-20261009T162604Z. Diagnostic
init was restored exactly. New one-shot launch-vesper-boot.sh signals stock via
/tmp/vrtemu.log, waits for all non-zombie showlogo owners to exit, removes only
the RAM stop marker, launches qualified SD showlogo for3 seconds, signals it,
then waits/reaps its owned child before stock launcher. A release timeout refuses
replacement; an owned-child stall waits rather than starting a competing display.
Device BusyBox syntax and independent dummy-executable one-shot/reap/no-op checks
pass; physical display remains pending. Early solid firmware logo remains stock.
Installer checks healthy FAT, exact init/splash, archives progress and arms last.
No SNES/lab arming or audio change. This is a userspace animation handoff test,
not replacement of the earlier internal boot interval.

## Physical success is an added SD-stage animation — 2026-10-09

Ben observed: static D-R35, animated D-R35, then Vesper. Vesper is physically
accepted as an added SD-stage animation, not a replacement of either stock screen.
Returned startup log reports stock_released=1, owned child484 exit0 and reaped
before launcher. Strict51-MVP/49-lab archive plus complete animation files are
preserved in device-evidence/snes-mvp-return-20261009T163638Z. Marker consumed;
no rearming. The next boot follows stock. Audio remains unresolved.

Captured /init.project.rc starts internal /showlogo before sleep2 and SD init.
The internal executable matches the qualified stock ZIP owner. Replacing that
original animation requires an earlier boot hook or modifying the embedded root
filesystem image; SD init alone cannot change already displayed frames. Rootfs
is RAM-backed at runtime; editing its live copy would not establish persistence.
The static screen asset/owner remains unknown: bootloader or kernel is a hypothesis.
Prior investigation found no registered /proc/mtd partitions. No verified firmware
image/repack/flashing/recovery route is established. Do not flash or claim both
screens can be replaced yet. Next engineering scope is read-only firmware/boot
image inventory and recovery-method verification, not another SD display test.

## Firmware route return and USB dispatch correction — 2026-10-09

Complete passive capture archived privately in snes-mvp-return-20261009T165057Z
with strict51-MVP/49-lab progress preservation. Original init restored exactly;
no test armed. Only SD and RAM block devices; empty /proc/mtd and sys/class/mtd.
Vendor /bin/nand_part_info and /bin/nandsync exist; /dev/spidev0.0 exists but
its attached peripheral is unidentified. This does not establish flash access.

Offline exact sysinit disassembly: main at0x11540 dispatches only argument core;
other arguments, including usb_gadget, are ignored. sysInit at0x1151c initializes
PPU/DLA/audio/ADC only. Unreached usb_gadget_init at0x11260 loads usb-common only.
The script command /sysinit usb_gadget is therefore not evidence of active USB
gadget support; earlier suggestion overstated it. No button recovery sequence
found in this dispatch. This does not rule out boot-ROM/bootloader recovery.
Next work: inspect vendor NAND tools and identify SPI peripheral/boot storage
without raw writes; a persistent splash replacement remains unimplemented.

## Reusable passive device survey and test catalog — 2026-10-09

Build native Cortex-A7 inventory collector, exact firmware BusyBox one-shot
wrapper, guarded install/rearm/collect/restore commands, SHA-mapped analyzer and
private offline ELF review. Prioritize NAND helpers/module candidates, SPI/USB
identity and device tree; also capture platform/process/memory/power/input/audio
metadata and runtime/module inventories. Bound reads, bytes/jobs and scheduling;
explicitly retain errors, missing paths, truncation, caps and stale-run rejection.
16 independent native/ARM/timeout/sparse-shell/analyzer checks pass; physical
capture pending. Archive progress and restore exact init before repeats. No raw
hardware reads, vendor utility execution, flash writes or active lab rearming.
Catalog19 investigation questions and reuse existing active labs with their
ownership/contracts. NAND tools already preserved privately contain driver-load
and storage-operation code; inspect copies before invoking anything on-device.
[Suite coverage and next run](docs/device-survey.md).

## Survey1 storage failure and exact updater recovery - 2026-10-09

Survey1 returned329 of901 captures.521 missing nonempty captures occupy exactly
17,856 KB at32 KiB allocation granularity, matching521 recovered chains. All789
readable files survive approved repair; saves/runtime/lab hashes match baseline.
Old ROM deletion preceded the clean install check. Directory-growth/persistence
is plausible; exact media/driver/shutdown cause remains unproved. Survey2 uses
one indexed CRC32 bundle/report and a fresh-health restoration gate.21 software
checks pass; healthy-card rearm completed, physical return pending.

SPI0.0 DT node names NOR flash; UDC/gadget paths absent despite an enabled USB
controller declaration. Exact vrtemu main calls the Code.bkp updater; WQW/ZIP/CRC
checks precede flash programming. SPI_ROM.bin is a string, not a proven trigger.
No raw SPI transaction or recovery path qualified. See device-survey-1-return.md
and firmware-update-contract.md for evidence and next test.

## Survey2 intact return and SPI owner — 2026-10-09

Survey2 returns all905 capture ranges with verified CRC/length/completion and
matching run identity; wrapper exit0, no failed/truncated reads or caps. Fresh
CHKDSK is clean. Strict51-MVP/49-lab archives match baseline except the intended
hook, then exact init is restored after another fresh health check. One clean
return qualifies this run, not every storage workload or shutdown sequence.

Process metadata proves stock vrtemu PID521 owns SPI0.0 through FD8. Prepare a
synchronous early-init identification profile rather than a background hardware
probe beside that owner. Fixed05/9f transactions, ownership/response/settings
guards and child deadline/reap pass11 software checks. Only identification is
armed, independently read back with healthy postinstall FAT. Physical chip ID,
full readback, recovery and persistent second-splash replacement remain pending;
audio is unresolved. [Return](device-survey-2-return.md), [profile](spi-identify.md).

## Physical SPI ID and pending full readback — 2026-10-09

Archive the successful read-only ID run: three c84017c84017 replies, status00,
five messages, no competing owner/error/timeout, matching marker and wrapper0.
Returned FAT clean,51-MVP/49-lab hashes preserved; exact init restored after fresh
health check. Match C8 40 17 to GigaDevice64-Mbit NOR/nominal8MiB using primary
manufacturer/kernel references. Do not assign an exact suffix/package from this ID.

Build fixed05/9f/03 two-pass reader using the unchanged physically qualified
ownership/ID source. Hold two4KiB buffers; store a16MiB bundle plus report,
compare fresh passes byte-for-byte, retain CRC/checkpoints and refuse busy/wrong
ID/settings changes/short reads/mismatches. Nine checks exercise independent
native/ARM packets, actual supervised capture, timeout/reap, damaged/stale returns,
health-gated restoration, release owner refusal and firmware BusyBox/ABI.
Independent installed payload/init/marker and protected progress/prior-result
hashes pass; FAT clean, only readback armed. Physical readback remains pending;
raw flash stays private. No write/recovery/splash/audio qualification.
Offline exact `/wdt` main sleeps500ms and loops watchdog ioctls independently,
with no userspace stock-main check; init starts it before the SD hook. This
supports the delayed placement but does not qualify extended startup physically.
[ID return](spi-identify-return.md), [reader](spi-readback.md).

## Full SPI backup and original animation located — 2026-10-09

Two physical8MiB passes match byte-for-byte, CRC32/SHA256, complete4,111
messages in103.771059s and matching consumed/wrapper identity. FAT is clean;
51-MVP/49-lab/43-prior-profile preservation passes. Exact normal init restored
after fresh health; postrestore readback/FAT healthy and nothing armed.

Exact image section table yields kernel, gzip-cpio rootfs and device tree.
Rootfs original showlogo/init/power/watchdog hashes match prior runtime captures;
the second animation's persistent location is established. Private rootfs-only
Vesper replacement changes just the qualified ZIP span and fits with108,732
compressed bytes spare. Six checks pass including independent libarchive/GNU
gzip. Duplicate directory records are preserved in order; repeated file bodies
are refused. Matching static bitmap located visually; its code reference unknown.
Kernel built-in cpio has no rescue init. No full flash candidate/update staged;
boot validation, recovery, original-screen replacement and audio unresolved.
[Return/layout/candidate and next work](spi-readback-return.md).

## Exact boot loader/updater acceptance and failure boundary — 2026-10-09

Follow the verified flash backup with exact-code offline checks. Thumb boot-main
pointer stores bind the static bitmap to the boot display setup; first screen
owner is now supported by code, and remains unchanged. Prepare a private full
candidate that changes only compressed rootfs and its table length; all other
flash bytes exact. Actual captured parser/getter/GPAP copy selector/section loader
and DT initrd-bound mutation pass for original and candidate under QEMU.

Actual vrtemu UpdateROM/bundled ZIP/UpdateROMProc accepts our WQW+ZIP full image
and fully matches simulated RAM flash after55 erases/14,080 page programs.
Metadata CRC/DOS time at0x100/104 and compatibility word0x108 are recovered;
compatibility compares unsigned words divided by10. Vendor metadata forces an
erase of boot-code block0; table and rootfs boundaries also share kernel blocks.
Four rejected/repeat fixtures do not program. Inconsistent ZIP CRC declarations
instead trigger a captured NULL-image fault at0x13920 before programming.
Nine outcomes include that fault; it is not described as safe rejection.

No physical flash/configuration write or SD staging. Programmer unavailable
by Ben's direct answer. Exact marking/package/access and recovery equipment are
next; do not confuse a verified dump with demonstrated write recovery. Current
normal init, protected progress/results and prior clean FAT state remain untouched.
Vendor-containing candidates stay ignored/private; three interpreted reports
join the evidence manifest with all583 prior published hashes unchanged.
[Qualification, limitations and exact physical sequence](firmware-offline-qualification.md).


## Focus1 return and quantitative prediction contract - 2026-10-10

Archive60 runtime/progress and49 lab files read-only; exact payload/consumed
marker/clean FAT, all58 prior files,12 unchanged progress files and9 snapshot
CRCs verify. Six retained samples show growing PPU CPU5.741 ->8.904ms while
APU-inclusive stays4.529..4.898ms. Emulated clocks predict534.688 native /735.948
sink frames per call; session average534.650 is consistent. Actual late accepted
production38,480.644/sec is insufficient for44.1kHz. This is a host cost lead,
not an identified vendor stop mechanism or measured window-entry price.

Cumulative reserve is reconstructable only over the retained partial trace;
onset/recovery are absent, and pointer divergence disqualifies later reported
queue as certified reserve. Previous18.287ms was a failing interval, not a
pre-effect baseline. Enforce measured saving/added costs/break-even/remaining
deficit/falsifiable prediction before any candidate install. Window gate fails
because unit costs remain unmeasured. No card writes/rearm/new core. See
[snes-focus-1-return.md](snes-focus-1-return.md) for calculations and limits.

## A7 cost1 suite and measurement-only handoff - 2026-10-10

User requests measured costs and a diagnostic suite that accounts for logging.
Separate baseline core retains every renderer decision while timing setup,
window/clip regions, sampled rows/cache and actual warm source blocks. Dense
per-row clocks can themselves exhaust the budget, so sparse1/64 row timing and
one dense cross-check are labeled separately. Full bounded PCM RAM history and
per-call accepted/pointer/frequency/worker data preserve more than a fault tail.
Post-pass flushing and sync keep SD writeback outside the next live pass.

Exact outputs/state and consuming-client contracts pass;13 automatic mock
passes verify replay/lifecycle/log separation. No QEMU duration is A7 evidence.
Stage measurement after fresh archive/FAT/hash/readback checks; retain old
production binaries and private progress. The current PCM cadence needs more
saving than the partial late-call account alone. Do not manufacture e/r/b or a
passing scorecard from warm payloads that omit longer candidate spans and cache
interaction. A7 capture is pending. [Procedure and limits](snes-a7-cost-suite.md).

## Paired UART source capture - 2026-10-15

UART pair1 qualifies same-handler status/control/software queue/GIC correlation.
Sixteen exact-image guards, original handler retained,64 bounded tuples, explicit
query errors and restore/drain/unload.14 compiled groups include52 original-vs-
intercepted cases and all8 GIC combinations;18 owner/firmware-shell checks.
Diagnostic only: physical result and added A7 cost pending; no UART settings or
core/APU change. [Procedure and limits](uart-pair-probe.md).

## Paired UART installation - 2026-10-15

UART pair1 is armed once on I: from pushed source ec8ec39. Fresh7,813-file
archive,7,812 protected prior hashes, stock/ROM/progress and three clean FAT
checks pass. Four new payloads and sole marker/dispatcher verify. Physical
capture pending; boot once, wait for stock startup, power off and return card.
[Verified installation and procedure](uart-pair-probe.md).

## Vesper feather animation candidate - 2026-10-15

Vesper Wings2 replaces the loading dots with a rising cyan feather-light sweep.
All18 frames pass the original ARM decoder/drawing seam;133,088-byte content
fits the141,940-byte ZIP span. Authored GIF/native assets are ready for review;
physical cadence/appearance pending. No card or firmware staging; UART pair1
remains armed. [Preview, format and verification](vesper-wings-animation.md).

## UART pair1 physical return - 2026-10-15

UART pair1 returned: all12,340 captured calls have both TX enables set and
GIC pending/active/unmasked.12,202 (98.88%) select neither service, including
1,324 with an empty software queue. Original FIFO-empty predicate ignores the
pending condition. Restore/unload and counter conservation pass; observer
strongly disturbs rate, so no CPU saving or causal correction claimed. Archive/
FAT/stock/ROM/progress verify; I: unarmed, no card writes or rearm.
[Paired evidence and next causal check](uart-pair-return.md).

## Wings2 firmware update qualification - 2026-10-15

Wings2 firmware update qualified:12 independent/original-ARM checks plus6 host
staging checks. Only the rootfs showlogo ZIP changes; accepted static screen,
other filesystem bytes, kernel and DT remain exact. Original updater RAM model
matches all8MiB after52 erases/13,312 pages. Authorized I: staging follows fresh
archive/FAT/hash/source checks; physical update still pending.
[Image contract and boot procedure](vesper-wings-firmware-update.md).

## Wings2 firmware staged - 2026-10-15

Wings2 firmware is staged on I: from pushed source e12c531. All8,455 prior
card files remain exact; fresh archive, clean FAT and independent full-package/
image readback pass. Only Code.bkp added; normal init unchanged, no UART test
armed. Physical flashing occurs on next normal boot and remains pending.
[Verified staging and boot instructions](vesper-wings-firmware-update.md).

## Wings2 flash return and UART next step - 2026-10-15

Wings2 flash user-reported successful. Return archive7,822 files; clean FAT,
stock/ROM/progress hashes verify. Exact completed Code.bkp removed; no other
host card changes and no IRQ test armed. Full post-update SPI readback remains
pending. Next UART correction must qualify the live FIFO-size/room contract:
probe initializes8 and TX sends half-size batches, then use a light original/
corrected/restored comparison. [Next test contract](uart-correction-plan.md).

## Reversible UART TX correction qualification - 2026-10-15

UART TX1 correction test qualified: guarded one-byte pending service with
TX_FULL/FIFO8 bounds, unchanged vendor RX/empty-FIFO paths and repeated exact
restoration.17 compiled groups include153 occupancy cases and100-byte draining
retry;21 owner/firmware-shell groups cover five phases and failure cleanup.
Physical result, silicon full-flag behavior and A7 saving pending. Separate
one-shot package; no firmware/core/APU change. [Test and boot procedure](uart-tx-correction-test.md).

## UART TX1 installation - 2026-10-15

UART TX1 is armed once on I: from pushed source a173f82. Fresh archive,
three clean FAT checks, all7,820 protected prior files/stock/ROM/progress and
four payloads/dispatcher/sole marker verify. Five5-second original/corrected/
restored phases, then unload/stock startup; physical FIFO/IRQ/CPU result pending.
[Installation and boot procedure](uart-tx-correction-test.md).

## UART TX1 physical causal return - 2026-10-15

UART TX1 physical causal test passes: original/restored6,951-7,060 IRQ19/sec,
corrected68.87/71.86, weighted98.994% reduction. Both restorations reproduce the
flood; TX counters/queues progress, RX/errors stay flat, no faults/bypass.
Restore/unload/exit0 and archive/FAT/stock/ROM/progress verify; I: unarmed.
CPU savings, wire/full-FIFO/mixed-RX and SNES benefit remain unmeasured.
[Physical result and limits](uart-tx-return.md).
