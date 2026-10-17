# Changelog

## Verify flashed kernel and preserve completed UART return - 2026-10-16

The first verification return is complete: both 8-MiB passes match the exact
expected flash, and its decompressed kernel is the corrected image. No runtime
UART module/proc patch exists. IRQ19 brackets are 88.49-89.62/s and 85.37-86.37/s,
passing the declared idle flood threshold. All saves and prior evidence remain
exact; FAT clean. Shutdown after successful probe exit is unresolved; user
suggests low battery. An identical plugged-in repeat is requested. No full backup.

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
[Return and next physical verification](docs/uart-kernel-return.md).

## Arm final direct kernel UART firmware on I: - 2026-10-16

Final corrected kernel source `70b0b40` pushed before staging. Independent full
readback verifies 10,824 protected files, original normal init without a runtime
UART hook, complete update ZIP/CRC/image, exact file set and clean FAT. Only
init and the known prior update are replaced; saves, stock and evidence remain.
Both Vesper screens/rootfs exact. No full backup or emulator test armed.
Physical flash, kernel boot, IRQ behavior and wire acceptance remain pending.
[Verified package and boot instructions](docs/uart-kernel-firmware.md).

## Qualify synchronous UART wakeup refill before deployment - 2026-10-16

Final call-path review finds a synchronous line-discipline wakeup callback.
Withdraw the first staged kernel candidate before physical boot, restoring the
exact previous package/init on clean FAT. The revised TX body re-reads head/tail
after wakeup before stop-TX; an independent refill test delivers the new byte.
All 26 groups, exact 64-KiB decompressor heap and eight staging cases pass.
Original metadata remains historical; v2 qualification governs deployment.
[Final kernel contract](docs/uart-kernel-firmware.md).

## Qualify direct kernel UART driver correction - 2026-10-16

Replace the TX body in the exact kernel, correcting pending service, FIFO safety,
flow/urgent/queue/wakeup behavior and literal-zero PutChar. RX/IRQ registration,
rootfs and both Vesper screens stay exact. No runtime patch module. 25 groups
pass: 7,344 queue/FIFO cases, all 256 bytes, actual ARM decompressor, original
loader/splash/updater RAM checks and eight staging cases. Preserve negative
FEXTRA and caller-register findings. Restore original SD init; replace only the
known staged update. No full backup. Physical kernel boot/IRQ/wire pending.
[Kernel correction and evidence](docs/uart-kernel-firmware.md).

## Arm verified internal UART firmware on I: - 2026-10-16

Stage the normal vendor update from pushed source `726f89c`. Independent full
readback verifies 10,824 protected existing files, authorized UART handoff hook,
complete ZIP/CRC/image, exact file set and clean FAT. Normal init, module/helper,
saves and evidence stay exact. No full backup or emulator rearm. Both Vesper
screens are preserved in the image; physical flash/boot/attachment pending.
[Installed update and boot instructions](docs/uart-firmware.md).

## Qualify internal UART firmware - 2026-10-16

Build the exact card-proven UART module/helper into the latest Wings2 rootfs.
Preserve both Vesper screens, kernel, DT and boot instructions; only project
startup changes plus four new cpio entries. 18,089 compressed-slot bytes spare.
35 offline checks and eight staging cases pass, including original ARM
loader/updater RAM simulation and exact firmware-shell card/internal boot.
Card hook verifies firmware ownership without duplicate loading; safe fallback
and uncertainty barriers remain. Sparse preservation only, no full backup.
Qualified source awaits authorized staging; physical boot/attachment pending.
[Image, evidence boundaries and boot](docs/uart-firmware.md).

## Collect five-game physical return - 2026-10-16

Three clean blocking windows: Mario, Metroid and F-Zero, 1,200 calls each.
User confirms Select+Start at retained F-Zero picture; Star Fox cold replay
records abort before measurement, normal exit 5 and safe teardown. No process
crash or forced timeout. Ranger and all candidate windows untested; zero pairs.
Exclude stale F-Zero PCM/input buffers from Star Fox. Reporter distinguishes
failed-before-measurement from not-started. Sparse collection: 6,065,591 new
bytes, clean FAT, UART/saves/evidence exact, no full backup, writes or rearm.
[Return, preservation and next test](docs/fivegame-physical-return.md).

## Install matched five-game physical test — 2026-10-16

Install and arm `retro/snes-fivegame1` once on I: from pushed source `8ccb0a3`.
Independent complete readback verifies 10,758 protected existing files, all 27
payload files, exact two markers, persistent UART/init and clean FAT. Only the
owned dispatcher changes among existing files. Saves and evidence are unchanged;
sparse collection stored zero new content bytes and no full backup was created.
Published installation/readback receipts bind the exact qualified package.
Physical performance, audio and display acceptance remain pending the run.
[Installed test and boot instructions](docs/fivegame-physical-test.md).

## Qualify matched five-game physical test — 2026-10-16

Prepare20 policy-only ABBA/reversed epochs across the five actual gameplay
scenes, exact corrected core and original backup ROMs.24,000 controller calls
match original pixel/PCM/sample oracles; Star Fox uses34,624 cold calls and no
GSU snapshot continuation. Both consuming native policies, busy/fault/drain,
firmware/reap and seven installer transaction cases pass. PAL-aware native
period/headroom and relative deficit fixture. Sparse inventory preserves all
10,759 prior files with zero new content bytes; no full backup. Measurement
experiment only: rebuilt-core A7 saving/remaining deficit explicitly missing.
[Qualification, gate and boot](docs/fivegame-physical-test.md).

## Fix Ranger/Star Fox and qualify five gameplay scenes — 2026-10-16

Resolve Ranger's stalled SPC SYNC exchange with AVCJ-only instruction-complete
port writes. Remove redundant HDMA cached-pointer subtraction that leaks host
addresses into Star Fox's DMA register shadows. Strict tests then expose a
SuperFX direct-target pixel failure; retain the established full-layout path.
All five reach actual gameplay:14,656 pixel/PCM/geometry comparisons and489
strict state checks pass. All18 FFVI scenes and ten unchanged-frontend mock
boot/audio cells pass. No card changes, new full backup or physical promotion.
[Fixes and acceptance limits](docs/five-gameplay-fixes.md).

## Five-game backup-ROM evaluation — 2026-10-16

Test Super Mario World, Super Metroid, F-Zero, Star Fox and Rendering Ranger
against the exact returned FFVI candidate. Four6000-call pixel/PCM/state
windows complete, but Ranger output is black; Star Fox stops at state frame150,
also reproduced with identical candidate libraries. Ten actual-runner mock
boot cells pass software PCM accounting. Inspect actual scene coverage, retain
failures and prohibit a whole-emulator-fixed claim. No emulator/card changes,
full backups or private ROM/image publication.
[Results and next acceptance gates](docs/multigame-evaluation.md).

## Matched FFVI physical return — 2026-10-16

78/80 clean bounded windows. Both48 ms candidates complete all1200 renders and
seven burns; both blocking controls fail. All72 ordinary and four24 ms cells
pass.28 total presentation skips; candidate minimum sampled reserve5.374 ms.
User reports no obvious issues. Bind exact payload, preservation, full native
PCM and matched effect/input evidence; censor failed control tails. Preserve
UART/init/saves and all prior evidence. Sparse collection only, no card writes,
rearm or new full backup. Repair original-proof reconstruction in reporter and
add regression checks. [Return and limits](docs/presentation-ffvi-return.md).

## Replace routine I: full copies with sparse evidence — 2026-10-16

Save progress/log generations once per SHA256; record configuration and static
payload hashes without copying packages, ROMs or swapfiles. Apply to both retro
and outside-retro collectors, retaining FAT/identity/no-write gates. Update
current FFVI install/report/publication consumers and add fake-card regression
checks. Original recovery backups remain separate. No install or rearm.
[Policy](docs/attempt-evidence-policy.md).

## Install matched FFVI test and bound backup retention — 2026-10-16

Install/arm separate `snes-presentation-ffvi1` from pushed `a3b8d68` after
archive/hash/healthy-FAT gates. Independent readback verifies all10,092 prior
protected files, exact UART/init/ROM/saves,95 declared payload files and two
markers; final FAT clean. Only the owned dispatcher changes. Next boot runs
80 automatic matched epochs; later boot is stock/UART. Physical result pending.
User limits full rollback backups to at most one current try; retain unique
evidence and compact inventories, not expanding full-card copies.
[Run and verification](docs/presentation-ffvi-test.md).

## Qualify matched physical FFVI presentation test — 2026-10-16

Prepare separate80-epoch policy-only ABBA/reversed test:18 original1200-frame
contexts four times and eight24/48 ms burst cells. Retain exact core/state
payloads/inputs/effect criteria, per-frame render/presentation/load/CPU and full
PCM reserve histories. All96,000 controller calls/56 burns, native both-policy
busy/failure/drain checks, actual firmware guards/replay/forced-child/reap and
six installer transaction cases pass. Preserve the preliminary consuming-fixture
timeout; final fixture uses its established O2 flags, controller remains O3/LTO.
Archive all10,093 existing card files, clean FAT; no card mutation yet. Push
qualified exact source before authorized separate installation. Physical result
pending. [Test, evidence and falsifier](docs/presentation-ffvi-test.md).

## Integrate presentation policy into isolated real runner — 2026-10-15

Apply pressure3's try-reservation to the actual owned-output emulator runner.
Busy display credit uses aligned private scratch, retaining every render/core
call/audio sample and skipping only presentation. Keep production PCM/fault
persistence unchanged, matched blocking policy and explicit accounting. ARM
O3/LTO/glibc2.30 build,192 board states, real worker join/ownership,21,600 exact
pixel/PCM/state comparisons over18 contexts and actual-runner native fault/
retry/state/resume/skip/blocking/error controls pass. Preserve the failed
diagnostic-PCM assembly and preliminary O2 tree privately. No card access or
installation; A7 cost and physical cadence/input/audio remain pending.
[Integration, proofs and physical gate](docs/presentation-runtime.md).

## Confirm pressure3 burst recovery against blocking controls — 2026-10-15

Collect77 physical cells,62 accepted.48 ms candidate completes180 quanta/six
bursts with valid PCM recovery,175 presentations/five intentional skips; matched
blocking control fails during second burst. Post-event display-credit wait
0.004 versus11.480 ms; first five restore prime lead in19.5–20.0 ms.24 ms
passes both without skips;80 ms/sustained overload remain failures. Retain full
histories, censor invalid/error tails and final-frame recovery. Strict9,457-file
archive, clean FAT/hash gates; UART72.37/sec. I: unarmed, no writes/rearm or
claimed full-core/visual qualification. [Physical result](docs/render-pressure3-return.md).

## Qualify presentation-independent recovery candidate — 2026-10-15

Separate pressure3 adds atomic FREE-source/FIFO try-reservation. Busy credit
uses scratch render and explicitly skips presentation, retaining render/load/
audio work and source ownership.77 cells include identical blocking controls;
new produced/presented/skipped accounting and unchanged native audio. Actual
board192 ownership cases and actual-controller/threaded-owner busy fixture,
oracle/mock/firmware/ABI checks pass. Price the measured11.452 ms wall-wait
opportunity against added costs on return; no pre-install A7 saving claimed.
Install/arm from pushed `678643a` after fresh archive, three clean FAT gates
and independent protected-file/payload/marker readback. UART and prior evidence
preserved; physical recovery and presentation cost pending.
[Candidate, validation and physical falsifier](docs/render-pressure3.md).

## Measure frame budget and burst recovery from pressure2 — 2026-10-15

Collect/hash-verify70 physical cells:58 accepted. Light render+8 ms extra CPU
passes180 quanta at12.036 ms main CPU;12 ms fails. Six24 ms bursts pass;48/80 ms
sequences fail. Valid post48 ms rows wait11.452 ms for display credit despite
4.385 ms CPU, exposing presentation-gated recovery as a lead. Censor corrupted
PCM tails and final-frame recovery claims. Double-drain fixed physically;
UART72.29/sec. Strict9,035-file archive, clean FAT, frozen payloads/prior files
and ROM/init verify. I: unarmed; no new build/card writes/rearm.
[Measured limits and priorities](docs/render-pressure2-return.md).

## Correct pressure-test cleanup and load baseline — 2026-10-15

Prepare separate pressure2: remove controller's second finish, retain joined
audio-worker error handling, move phases59–65 to static cached/direct/queued
render+audio and record executed load events. Actual-controller/threaded-owner
fixture catches the original double-drain, propagates finish failure and executes
six bursts. All70 mock cells,60 image cases, firmware recovery/faults, ABI/source
pins pass. Original pressure1/evidence and production core/drivers preserved.
Install and arm from pushed `fa3005d` after a fresh strict archive, three clean
FAT gates and protected-file/payload/marker readback. UART correction and prior
evidence remain intact; physical results pending.
[Details](docs/render-pressure2.md).

## Collect first ROM-free pressure return — 2026-10-15

Archive and verify all 70 physical cells:50 non-audio passes, five completed
audio-production runs with a controller double-finish cleanup error,15 heavy
production failures. Publish source-bound metrics/376 input hashes; separate
production from shutdown and reject unexecuted burst-tolerance claims. Display
reaches about60fps; dense NEON rows cost20.317 ms main CPU; tested color cache
does not win. UART remains corrected at72.39 IRQ19/sec. I: unarmed, no writes,
rebuild/rearm or claimed hardware ceiling. [Results](docs/render-pressure-return.md).

## Arm ROM-free renderer/platform pressure lab — 2026-10-15

Install and arm the qualified 70-phase `render-pressure1` from pushed `26e9d3d`
on I:, after a fresh strict archive. Preserve all prior files except the owned
test dispatcher; retain permanent UART correction, stock/ROM/saves and logs.
Three clean FAT gates and independent payload/protected-file/marker readback
verify. Publish installation metadata separately from offline qualification.
Physical acceptance and timing pending. [Run instructions](docs/render-pressure-installation.md).

## Build independent renderer/platform pressure lab and inspect matching driver - 2026-10-15

ROM-free70-phase lab isolates row generation, memory routes, scaling/display,
audio, combined scheduling and steady/burst CPU load. Scalar-oracle/NEON/cache
equality passes60 full-frame cases; all70 short mock cells and actual firmware
recovery/guard checks pass. Bounded RAM telemetry, worker ownership, final-frame
oracle verification, pointer/accounting gates and mock-performance rejection.
Pin all local compile dependencies; retain physically used board/PCM source by
hash. Matching kernel ioctl evidence resolves scaler3000 as a capped millisecond
timeout with waitqueue completion. Module-build reconstruction is not recovered
device configuration. Diagnostic preparation only; no I: access, install/arm,
game/core/driver change or claimed A7 gain. [Lab and review](docs/render-pressure-lab.md).

## UART-corrected FFVI return improves reserve and raw Meteor - 2026-10-15

All48 epochs finish;46 valid versus44 previously. Both raw-v3 Meteor controls
now pass; fixed-APU-only Meteor still fails twice. Candidate40/40 remains clean;
reserve improves in36/equal in four, with Quasar pricing gaining129 frames each.
IRQ19 sustains71.63/sec (98.965% below prior suite) over16.4minutes, attached with
no faults/bypass. Thread CPU shows no broad gain; Quasar draw-order regression
and20% margin remain unresolved. Strict8,275-file archive, clean FAT, all payloads
and protected stock/ROM/progress verify. I: unarmed, permanent UART boot retained;
no card writes, core changes or rearm. [Analysis](docs/snes-uart-retest-return.md).

## Install persistent UART fix and arm identical FFVI48-epoch test - 2026-10-15

Install from clean pushed46ddf9a after fresh7,829-file strict archive. Four clean
FAT gates, exact payloads and all7,827 prior files except authorized init/
dispatcher verify; original init retained, previous logs/saves/ROM preserved.
`uart-fix1` loads every boot; `snes-draw-uart1` runs the unchanged48 epochs once.
No SPI update or emulator rebuild. Physical improvement remains pending.
[Deployment and procedure](docs/snes-uart-retest.md).

## Build persistent UART correction and identical FFVI retest - 2026-10-15

Automatic card-boot TX correction retains the physically proven guarded service,
removes the diagnostic cutoff, survives reboots by normal-init activation, and
keeps explicit detach/rollback.18 compiled groups,16 helper cases, exact firmware
shell/startup and five transaction cases pass. No SPI flash or emulator/APU
rebuild. Prepared48-epoch retest retains82 payloads exactly and checks UART only
outside the child. Physical persistent boot/gameplay and A7 savings pending.
[Implementation](docs/uart-persistent-fix.md), [retest](docs/snes-uart-retest.md).

## UART TX correction suppresses flood and restoration reproduces it - 2026-10-15

UART TX1 physical causal test passes: original/restored6,951-7,060 IRQ19/sec,
corrected68.87/71.86, weighted98.994% reduction. Both restorations reproduce the
flood; TX counters/queues progress, RX/errors stay flat, no faults/bypass.
Restore/unload/exit0 and archive/FAT/stock/ROM/progress verify; I: unarmed.
CPU savings, wire/full-FIFO/mixed-RX and SNES benefit remain unmeasured.
[Physical result and limits](docs/uart-tx-return.md).

## Arm reversible UART TX1 correction test on I: - 2026-10-15

UART TX1 is armed once on I: from pushed source a173f82. Fresh archive,
three clean FAT checks, all7,820 protected prior files/stock/ROM/progress and
four payloads/dispatcher/sole marker verify. Five5-second original/corrected/
restored phases, then unload/stock startup; physical FIFO/IRQ/CPU result pending.
[Installation and boot procedure](docs/uart-tx-correction-test.md).

## Qualify reversible UART TX pending correction - 2026-10-15

UART TX1 correction test qualified: guarded one-byte pending service with
TX_FULL/FIFO8 bounds, unchanged vendor RX/empty-FIFO paths and repeated exact
restoration.17 compiled groups include153 occupancy cases and100-byte draining
retry;21 owner/firmware-shell groups cover five phases and failure cleanup.
Physical result, silicon full-flag behavior and A7 saving pending. Separate
one-shot package; no firmware/core/APU change. [Test and boot procedure](docs/uart-tx-correction-test.md).

## Accept Wings2 flash report and clean completed trigger - 2026-10-15

Wings2 flash user-reported successful. Return archive7,822 files; clean FAT,
stock/ROM/progress hashes verify. Exact completed Code.bkp removed; no other
host card changes and no IRQ test armed. Full post-update SPI readback remains
pending. Next UART correction must qualify the live FIFO-size/room contract:
probe initializes8 and TX sends half-size batches, then use a light original/
corrected/restored comparison. [Next test contract](docs/uart-correction-plan.md).

## Stage verified Wings2 firmware update on I: - 2026-10-15

Wings2 firmware is staged on I: from pushed source e12c531. All8,455 prior
card files remain exact; fresh archive, clean FAT and independent full-package/
image readback pass. Only Code.bkp added; normal init unchanged, no UART test
armed. Physical flashing occurs on next normal boot and remains pending.
[Verified staging and boot instructions](docs/vesper-wings-firmware-update.md).

## Qualify Wings2 firmware animation update - 2026-10-15

Wings2 firmware update qualified:12 independent/original-ARM checks plus6 host
staging checks. Only the rootfs showlogo ZIP changes; accepted static screen,
other filesystem bytes, kernel and DT remain exact. Original updater RAM model
matches all8MiB after52 erases/13,312 pages. Authorized I: staging follows fresh
archive/FAT/hash/source checks; physical update still pending.
[Image contract and boot procedure](docs/vesper-wings-firmware-update.md).

## UART pair1 catches enabled ignored TX condition - 2026-10-15

UART pair1 returned: all12,340 captured calls have both TX enables set and
GIC pending/active/unmasked.12,202 (98.88%) select neither service, including
1,324 with an empty software queue. Original FIFO-empty predicate ignores the
pending condition. Restore/unload and counter conservation pass; observer
strongly disturbs rate, so no CPU saving or causal correction claimed. Archive/
FAT/stock/ROM/progress verify; I: unarmed, no card writes or rearm.
[Paired evidence and next causal check](docs/uart-pair-return.md).

## Animate the feathers in Vesper Wings2 - 2026-10-15

Vesper Wings2 replaces the loading dots with a rising cyan feather-light sweep.
All18 frames pass the original ARM decoder/drawing seam;133,088-byte content
fits the141,940-byte ZIP span. Authored GIF/native assets are ready for review;
physical cadence/appearance pending. No card or firmware staging; UART pair1
remains armed. [Preview, format and verification](docs/vesper-wings-animation.md).

## Arm paired UART capture on I: - 2026-10-15

UART pair1 is armed once on I: from pushed source ec8ec39. Fresh7,813-file
archive,7,812 protected prior hashes, stock/ROM/progress and three clean FAT
checks pass. Four new payloads and sole marker/dispatcher verify. Physical
capture pending; boot once, wait for stock startup, power off and return card.
[Verified installation and procedure](docs/uart-pair-probe.md).

## Qualify paired UART source capture - 2026-10-15

UART pair1 qualifies same-handler status/control/software queue/GIC correlation.
Sixteen exact-image guards, original handler retained,64 bounded tuples, explicit
query errors and restore/drain/unload.14 compiled groups include52 original-vs-
intercepted cases and all8 GIC combinations;18 owner/firmware-shell checks.
Diagnostic only: physical result and added A7 cost pending; no UART settings or
core/APU change. [Procedure and limits](docs/uart-pair-probe.md).

## Trace UART pending-versus-empty mismatch — 2026-10-15

Pin GP32/GPM4 source definitions: TX pending0x4000, FIFO empty0x80; all captured
statuses have pending but shipped ISR services empty. Six exact-ARM comparison/
GIC state/EOI groups pass; already-disabled fixture rejects a standalone mask
change as a proven fix. Reject incompatible vendor UART layouts. Preserve939
published proofs; shared-IP interpretation, not isolated GPA7 cause or A7 saving.
No device access, probe install, rearm or core/APU change. See docs/uart-source-contract.md.

## UART status1 physical return identifies ignored-status path — 2026-10-14

Capture31,345 IRQ19 calls matching counter growth:99.54% status0x531f selects
neither RX nor TX,144 TX-only, zero RX; all return IRQ_HANDLED. No overflow/
bypass, restore/frozen capture/unload/exit0 pass. Confirm captured status in
1000 original-ARM fixture calls; electrical/enable-bit origin and A7 cost remain
unknown. Archive7,813 files, clean FAT and exact protected stock/ROM/progress.
Preserve937 prior proofs, publish interpretation/check only; no card writes,
rearm or core/UART change. See docs/uart-status-return.md.

## Arm original UART status/branch capture on I: — 2026-10-14

Exact source0b90c2d pushed before deployment. Fresh7,805-file/1,937,114,927-byte
archive; all7,804 protected prior files/stock/ROM/progress and four new payloads
verify. FAT clean before install/after payload/after arm. Separate uart-status1
package, existing dispatcher and sole marker only; state1 logs remain intact.
Physical interception/status/branch result pending. See docs/uart-status-probe.md.

## Qualify original UART interrupt-status capture — 2026-10-14

Build exact-entry status bridge and32-value histogram/branch aggregates; resume
original ISR body, no extra status reads or kernel-text/UART register writes.
Guard temporary IRQ19 action ownership, module pin, restore/drain/unpin and
failure withholding.12 compiled groups include40 original/intercepted ARM cases;
17 owner/firmware-shell checks pass. Preserve933 prior evidence hashes and
publish interpreted metadata only. Physical hook/status/branch cause and added
A7 cost pending; no emulator/APU change. See docs/uart-status-probe.md.

## UART state1 physical snapshot return — 2026-10-14

Collect/hash7,805 files; clean FAT, exact payloads, consumed marker, stock/ROM/
progress verified. All100 snapshots and ordinary module load/non-forced unload
pass. IRQ19 persists6,756–7,323/s across phases with zero observed TX mismatch,
both TX enables clear, empty queue, flat RX and~83.55 TX bytes/s. Persistent TX
divergence is absent in this idle capture; status/cause/IRQ duration still unknown.
Publish interpreted metadata and strict evaluator, preserve all932 prior proofs.
No device writes, rearm or core/firmware change. See docs/uart-state-return.md.

## Arm separate UART snapshot preflight on I: — 2026-10-14

From clean pushed3892f2a, strict7,797-file/1,937,074,272-byte archive and clean FAT
precede the separate uart-state1 install. All7,796 protected prior files, ROM and
progress verify; payloads and sole marker/dispatcher read back exactly, FAT clean
after arm. No UART configuration/handler/core/firmware changes.100 idle snapshots
and non-forced module lifecycle are pending physical qualification. Boot once,
wait stock, leave30s, power down/return; next consumed-marker boot stock. See
docs/uart-state-preflight.md and the interpreted installation receipt.

## Reconstruct and qualify UART snapshot preflight — 2026-10-14

Match observed448-byte module ABI, init/exit/core/init-layout/kallsyms/refcount
offsets, UART offsets and vermagic from existing artifacts. Recover4,394 text
exports; build a4760-byte guarded snapshot module without vendor-body transplant,
forced loading, IRQ replacement, UART writes or status/FIFO reads. Actual kernel
ARM relocator matches independent ELF bytes;15 compiled-module checks and12
native owner/firmware-shell checks pass. Target-libc and LF dispatcher seams
qualify. Separate100-snapshot idle preflight retains ordinary kernel/emulator
behavior; physical module lifecycle, triggering state and A7 cost remain pending.
Preserve928 prior evidence records; source and interpreted proofs only published.
See docs/uart-state-preflight.md.

## Exact archived UART kernel investigation — 2026-10-14

Decode17,533 kernel symbols from the verified private SPI backup; all242 retained
built-in runtime triples match. Six actual ARM-code QEMU checks establish the
conditional TX-stop mismatch, unrecognized-status IRQ_HANDLED return and literal
zero PutChar store. Latest draw-order snapshots still show6,730,129 IRQ19 events
over972.43s (~6,921/s),92.32% of interrupt-count growth, not CPU time. Actual
dispatch/accounting and absent tracing symbols explain limits of existing
telemetry. Specify bounded ABI-qualified observation; matching vendor build
interface, live cause and A7 duration remain missing. Preserve all927 prior
published hashes. No device access, core/APU change, module load, rearm or flash.
See docs/uart-kernel-investigation.md.

## Draw-order physical return passes all18 contexts twice — 2026-10-14

Strict7,797-file/1,937,074,272-byte archive, clean FAT,85 exact payloads and
protected stock/ROM/progress; marker consumed, I: unarmed. All36 regression and
4 extra candidate windows clean, including Meteor/Rage032. Four invalid Meteor
control epochs leave44/48 clean overall. Complete retained PCM/cumulative reserve
identities verify. Earlier-heavy Meteor net saving0.54–0.62ms vs raw; Quasar warm
regression0.45–0.56ms. Fixed APU object retained, boundary-only build tax about
0.18–0.215ms. Preserve bounded success; reject production promotion with regression/
20% headroom unresolved. All-common/fixed prices, invalid completions and full
input hashes published; prior proofs exact. No core/card changes or rearm.
See docs/snes-draw-order-return.md.

## Install and arm validated draw-order candidate on I: — 2026-10-14

From clean pushed9ba664f, guarded separate draw-order1 install verifies85
payloads,7,358 prior files and original stock/adapter/boot/ROM/progress after
strict7,359-file/1,848,513,197-byte archive, identical to evaluated PC return.
FAT clean before installation/after payload/after arm. Existing dispatcher plus
one-shot marker selects48-epoch18-context regression and raw/fixed-APU/candidate
pricing. Production gate false; net A7 saving/boundary cost/effect recovery pending.
Frozen preparation and prior published hashes exact. Allow20–25min, wait stock,
power down/return; next reboot stock. See snes-draw-order-installation.md.

## Implement and qualify draw order with fixed APU compilation — 2026-10-14

Fresh ordinary Mode1 unique-top BG3-first core preserves original low BG3/OBJ/
window/math/fallback rules. Compile unchanged APU unit once outside LTO, reuse
byte-identical object in boundary/priority, verify21 linked SPC/DSP sizes.
43,200 exact frame/PCM/state calls/all18 contexts,2,560 independent original
renderer pixel/depth/OBJ-limit fixtures,8,400 resolution/state calls pass.
48-epoch raw/boundary/candidate hardware suite qualifies57,600 actual ARM calls,
142 native acquired-output callbacks and fault/retry/state/wrapper/ABI/mock
guards. No new A7 saving or boundary price; explicit cost/break-even/deficit/
physical prediction contract retained. User authorized separate installation
after validation; source/readiness committed before staging. Prior proofs exact.
See docs/snes-draw-order.md and evidence/2026-10-14/draw-order.

## Evaluate unchanged-core PC diagnostic return — 2026-10-14

Strict7,359-file/1,848,513,197-byte archive, FAT clean,88 exact payloads and
protected stock/ROM/progress; only stock swapfile changes, marker consumed.
All four epochs ran. Quasar clean twice; Meteor control drifts532 despite1200
calls, sampled drift488/error509. Sampler delivers613/1,333 active samples,
583/1,333 valid, about10ms CPU delivery with explicit overruns. Common heavy
prefix named PPU53.0%/46.5%, DSP/APU17.7%/26.8%; coarse statistical ownership,
no exact prices. Observed warm thread CPU disturbance+0.159/+0.105ms. Complete
pre-drift cumulative reserve identities verify; Meteor loses~2,075 frames,
Quasar gains193. Preserve frozen sampler/proofs and917 prior published hashes.
General draw priority/work avoidance remains first lead; no core/card changes
or rearm. See docs/snes-pc-profile-return.md and reproducible evaluation.

## Arm unchanged-core PC diagnostic on I: — 2026-10-14

From clean pushed6123047, explicitly authorized rearm installs88 separate
payloads after strict7,226-file/1,827,485,639-byte archive, all identical to prior
return.7,225 protected files/stock/ROM/original progress exact; FAT clean before,
after payload and after arm. Four Meteor/Quasar control/sample epochs use the
same exact ordinary demand-v3 core. Physical timer support, owner distribution
and sampling disturbance pending; no optimization or production promotion.
Publish verified installation receipt with prior evidence/frozen artifacts exact.
See docs/snes-pc-profile-installation.md; allow3–5min, wait stock, power down/return.

## Pin compiler interaction and verify priority-scheduling opportunity — 2026-10-14

Reproduce v3 byte-exact and combined .text-exact with GCC reports. SPC loop
unswitching disappears across changed LTO partitions; one-partition and fixed
non-LTO APU object controls restore it. APU object bytes identical across PPU
variants; local flag snapshot alone does not restore unswitching.14,400 compiler
control comparisons pass. Refresh current v3 work with7,200 exact calls; highest
mode1 BG3 causes27,600 overwritten late-Meteor pixels. State-based early top-BG3
counterfactual passes21,600 exact calls/all18 contexts and cuts main RGB writes
32.5%, with extra traversal/guard costs unpriced. Existing A7 logs measure core
~15.5ms plus~1.5ms other timed CPU, not an inner engine split. Prepare/qualify
unchanged-core4-epoch PC sampler:4,800 controller calls, host/ARM and native
lifecycle/mock rejection. Timer overruns explicit. No card access/install/rearm;
physical owner distribution and net candidate gain pending. See research report.

## Reset efficiency research; identify codegen confound — 2026-10-14

Read current source/build/ELF and earlier physical/profile evidence plus primary
upstream references. Unchanged selected CPU/APU source hashes produce different
SPC/DSP machine-code structure across PPU variants; final .text grows22,568 bytes.
This bounds family attribution, not a proven cause of regression or cache miss
rate. Research priority: stable codegen/current inward cost ownership, then
winner/source production architecture and exact interpreter/DSP work. Historical
overdraw/phase counts require refresh on v3; newer core labels do not price a
port. Publish reproducible read-only ELF audit. No emulator build/card access.
See docs/snes-efficiency-research-reset.md.

## Evaluate PPU return; reject combination — 2026-10-14

Strictly archive7,226 files/1,827,485,639 bytes, clean FAT,91 exact payloads,
protected stock/ROM/progress; only stock swapfile differs. Marker consumed.
All56 epochs ran:42 clean,14 invalid,12 reported runner errors. Final remains
32/36 clean windows/16 of18 contexts passing twice; Meteor/Rage032 unresolved.
Combined Meteor common-warm CPU regresses0.071–0.120ms and first pointer drift
480/484 vs496/505 controls. Isolated bulk saves0.181–0.215ms in matched control-
heavy intervals but both nominal1200-call Meteor completions drift and fail.
Add all-common-window/fixed-interval analysis to avoid selective peak claims.
Preserve qualified sources/cores/proofs; no recoding, card writes or rearm.
See docs/snes-ppu-test-return.md.

## Arm I: for authorized PPU measurement — 2026-10-14

From pushed514d359 install91 separately owned payloads after strict6,721-file
archive; all readback exact,6,720 prior files/stock/ROM/progress protected.
FAT clean before install/after payload/after arm. Existing dispatcher plus one
consumed marker starts56 epochs; following reboot stock. Physical result pending,
no production promotion. Publish installation receipt; frozen preparation exact.

## Prepare authorized PPU measurement rearm — 2026-10-14

On “Arm I,” strictly archive6,721 files/1,730,576,357 bytes with clean FAT;
only stock swapfile differs from evaluated return. Fresh56-epoch suite compares
final v5 across18 contexts twice and frozen v3/isolated OBJ/shapes/bulk on
Meteor/Quasar in opposite orders. Actual ARM controller passes67,200 calls,
native consuming PCM/direct output/fault/retry, wrapper/ABI and physical-mock
rejection pass. State payloads unchanged, prior evidence exact. Explicit
measurement-only exception obtains missing A7 prices; no production promotion.
See docs/snes-ppu-test.md; prepared receipt is not an installation claim.

## Implement general PPU refinements — 2026-10-14

Add state-based OBJ window reuse, opaque depth stores, full-width clipped
normalization, three-lane/half-row plain kernels, exact sparse color math and
contiguous depth clears. CPU/APU/DMA and owned-output runner unchanged.
Isolated/final variants and separate row-cache experiment pass259,200 raw
graphics/PCM comparisons across18 contexts, state every30 calls; independent
stock/scalar/NEON and native/resolution seams pass. Cache excluded from final
pending A7 net pricing. Prior evidence exact; no card writes/rearm or new A7
speed claim. See docs/snes-ppu-refinements.md for costs and acceptance limits.

## Evaluate automatic spell return before recoding — 2026-10-14

Strict archive6,721 files/1,730,576,357 bytes, clean FAT,82 exact payloads and
protected stock/ROM/progress; only prior swapfile changes, marker consumed.
All40 epochs ran.32/36 demand windows clean;16/18 contexts pass both orders.
Unresolved Meteor and Rage032 share observed Meteor branch19. Quasar passes
both versus two failing controls,1.436–1.466ms matched recorded CPU saving.
Meteor saves1.088–1.102ms and drifts later, but worst valid CPU still0.231–0.270ms
above quota across its two contexts; reserve falls to138–174 frames. Three
nominally complete candidate epochs have pointer drift despite empty errors,
and remain invalid. Publish bounded evaluation; keep all core/runtime/test
artifacts exact. No recoding, card writes/rearm or production promotion.

## Arm I: for authorized automatic spell coverage — 2026-10-14

On explicit “Arm I,” archive6,340 retro files before writes, verify prepared
source/payload/proofs and clean pushedba8e5f3. Install82 separately owned payloads,
read back all, preserve6,339 prior files/stock/adapter/boot/ROM/original progress,
and arm one consumed boot marker through the old dispatcher. FAT clean before
install, after payload and after arm. Publish installation receipt without
mutating frozen preparation artifacts.40-epoch physical run pending; no promotion.

## Prepare automatic demand-v3 tests for unqualified spells — 2026-10-14

New local40-epoch suite runs18 archived contexts twice and unchanged reference
controls for Meteor/Quasar in AB/BA order. No late-game manual progress needed;
all20 copied state payloads exact. Reuse ordinary qualified cores by hash, fresh
measurement runner with owned-output board/acquisition and persisted direct/copy
counts. Keep all frames/PCM, disable nested phase clocks/frequency pinning, flush
bounded complete histories after joined workers. Actual ARM controller passes
48,000 calls/all18 property fixtures; native149 direct callbacks, fault/retry/
drain/deficit, actual wrapper/ABI and mock-rejecting archive reporter pass. Preserve
all prior frozen/published artifacts; no card access, install, rearm or production
promotion. Ready packet and guarded future installer documented.

## Collect demand-v3 manual return and bound physical acceptance — 2026-10-14

Strictly archive6,340 files/1,658,860,825 bytes from I: read-only; clean FAT,
consumed marker and exact candidate/stock/ROM/progress verify. Only prior stock
swapfile changes. Opening-scene run completes3,952 full frames at59.995 calls/s,
zero logged PCM faults/underruns and exact nonpriming accounting. Ben reports
Confuser worked fine; no Ultima/Holy/late-game coverage. Core wall11.266ms mean,
25.076ms maximum; reported reserve minimum2,028 frames. Preserve transient
overrun, aggregate/partial telemetry, unmatched-price and visual-proof limits.
Publish analysis/telemetry with reproducible archive-only analyzer; frozen inputs
and prior evidence remain exact. No card writes/rearm or production promotion.

## Install authorized separate demand-v3 gameplay one-shot — 2026-10-14

Install from pushed9a0340f at I:/retro/snes-demand-gameplay1; all nine payloads
read back exactly. Protect6316 original retro files, stock/adapter/production
core/boot hook/ROM and all original progress. Read-only FAT checks clean before
install, after payload and after arm. One old launch dispatcher plus consumed
marker route the next cold boot into the separate manual test; following reboot
stock. Publish hash-only installation receipt and update handoff. Actual physical
gameplay/coherency/performance pending; production gate remains false.

## Qualify separately staged demand-v3 gameplay for I: — 2026-10-14

Following explicit “Push it to I:” authorization, strictly archive6317 retro
files and private progress; clean FAT/known serial and consumed marker verify.
Reuse exact qualified ordinary v3 core and owned-output runner in a new private
payload. Latest separate gameplay state changes only its core identity header;
2400 exact comparisons,180 actual runner mock calls, consuming native client
with149 direct callbacks/two loads and actual wrapper/ABI checks pass. Fresh
guarded installer protects production/adapter/ROM/all old progress, requires a
clean pushed source commit, and targets a separate experimental one-shot only.
New A7 prices/headroom/coherency and physical gameplay remain pending. The
72-epoch automatic plan is not staged. See docs/snes-demand-gameplay.md.

## Implement shared CPU-demand candidates and qualify their combination — 2026-10-14

Fresh isolated DMA, CPU/APU cleanup, shared geometry and owned-output candidates;
reuse qualified fusion/alignment in new combinations. Generic8/16-tile/window-aware
producer exercises Meteor BG0 and Quasar BG1. Counted overlap shows Quasar's570
shared main cells are hidden; final clip rejection removes their setup and2280
descriptor-read bytes without charging4410 already-removed index rows again.
Preserve every frame/native PCM/CPU/APU operation;302400 raw original-command
comparisons pass across18 contexts. Independent source/seam and native/FIFO tests
pass; retained synthetic239-line state divergence reproduces between identical
baseline cores, with separate deterministic test-only HDMA initialization for
layout qualification. Final core HDMA unchanged. Document costs, limits and72-epoch
A7 measurement plan. All A7 savings unmeasured; no card access/install/rearm or
production promotion. Existing measured and qualified artifact trees preserved.

## Qualify explicit A7 cache layout; locate shared source work — 2026-10-13

Review2010 allocation/framebuffer/span mechanisms and bsnes source sharing.
Exact current ELF puts half its32-byte palette tables across64-byte lines.
An isolated64-aligned tile/compact palette variant passes9600 original-input
calls across eight contexts, cache3840->3520 bytes; A7 saving unmeasured.
Reject a restricted BG0 geometry bypass:9600 exact fallback-only calls, zero
reused commands, with2400 guard-probe calls. A separate2400-call observer locates
Meteor's3094 shared BG rows on BG0 and Quasar's4410 on BG1, plus827.59/1220.71
eligible matching OBJ rows/call. Preserve separate visibility/cost boundaries.
Document direct-output ownership/fallback requirements, existing fill evidence
and optimistic copy-removal limits.2010's single-thread span path drains
immediately; do not import a queue as free throughput. Publish bounded receipts
and input identities, retain original production/core/card unchanged. No A7
test, card access, installation, frame omission or production promotion.

## Count architectural waste before changing rendering order — 2026-10-13

Audit current Plus C, not just upstream. Three owned observer iterations pass
28800 exact original-command calls across eight contexts. Measure successful
RGB/math writes, overwritten owners, shared source rows, palette behavior and
traversal populations. Heavy discarded tile math only5.55% Meteor/5.88% Quasar;
plain RGB overdraw33.37%/9.71%. Backdrop bulk and small palette cache already
installed. Fully clipped layers/full-width OBJ dispatch have zero peak hits;
no-recipient math entries cover8 rows. Strict DMA spans eliminate logical flag
store repetition; ring fixture passes230785 exact states. Preserve partial
memory-ledger limits and unmeasured A7 costs. No optimized renderer, card write
or rearm. Publish bounded counts and source identities, retain raw data privately.

## Archive and analyze quick A7 CPU profile — 2026-10-13

Archive6317 files/1,657,276,489 bytes; clean FAT,18 installed hashes, frozen local
proofs, boot/core/ROM and prior progress verify. Marker consumed; zero card writes.
All four epochs run and end with native PCM errno77,1866 calls/1862 drawings,
115 phase samples. PPU explains86.83%/87.26% of sampled Meteor/Quasar CPU growth.
Control worst16 nonterminal CPU17.997/17.491ms;20% target needs4.646/4.141ms saving.
Retain~1.3ms sampled-call disturbance, partial late coverage and invalid pointer
limits. Correct universal audio-nesting assumption from actual C; distinguish
video copy, display worker and CPU/SPC residual. Publish bounded measurements
and ranked general improvements. No emulator changes, new builds or rearm.

## Quick four-epoch A7 CPU profile — 2026-10-13

Build separately versioned1.19-profile1 for Meteor and Quasar with matched
profile-off/on controls. Reuse the exact combined1 core and snapshot payloads;
enable existing PPU/APU hooks and callback CPU clocks on one call in eight.
Retain every frame/audio and bounded per-call RAM records, flush after workers
stop. Qualify actual ARM controller:3200 calls,200 phase samples, unchanged
gameplay observations and exact PCM/frame accounting; reuse frozen core/native
proofs. Archive I: and stage only after clean FAT/hash guards. No renderer
changes, performance promotion or A7 timings from QEMU. Native result pending.

## Design scalar/NEON PPU selection rules without recoding — 2026-10-13

Map C paths to state/layout/operation kernels and sparse/dense payload decisions.
Define guard-inclusive break-even equations and realistic palette reuse. Reuse
native peaks and archived mask logs; Meteor sparse-only20% target requires
1.13-1.16us/hit before guards, Quasar needs broader work reduction. Preserve
negative cost scenarios and zero empty sole-layer hits. Inspect installed ARM
bodies for scalar clipped/full-tile coverage; identify eligible full-width clip
and opaque OBJ depth-store candidates without pricing unmeasured work.

Document exact Z1/Z2/order, math-lane, clipping, cache and scaled-layout contracts;
list missing A7 classes and observer-aware measurement plan. No C or diagnostic
source changes, build, replay, card access or rearm. Publish bounded calculations
and unchanged-source identities. [Selection design](docs/snes-ppu-scalar-neon-selection.md).

## Evaluate combined1 return and consider a general PPU backend — 2026-10-13

Archive6249 returned files read-only; clean FAT and exact57 payloads, boot/core/
ROM/progress verify. All48 runs attempted:21 complete,27 native PCM errno77;
latest completes six contexts twice, Meteor/Quasar still fail. Preserve actual
incremental gains and the small negative Carbunkl result. No code/build/rearm.

Separate conservative wall+worker proxy from distinct-thread CPU sum; inspect
worst sustained16-call windows before pointer divergence. Meteor17.85-17.97ms,
Quasar17.41-17.46ms versus16.69ms budget.20% target needs4.50-4.62 /4.06-4.11ms
more saving before other costs. Existing logs show later Quasar peak with roughly
doubled OBJ activity. Document state-driven BG+OBJ scalar/NEON backend design,
memory lifetime, exact arithmetic and unmeasured costs; no implementation.
[Return and design](docs/snes-combined-return-and-ppu-design.md).

## Fuse exact renderer tools and correct Window2 installation status — 2026-10-13

Verify generalized scanline Window2 already exists in all three staged combined1
cores; correct stale cause-map wording without promoting production or confusing
78.97% fewer renderer entries with total runtime saving. Keep card untouched.

Offline fusion shares band/palette decisions, reuses the first visible depth
result and combines sparse stores with selected4bpp hidden-tile rejection.
Negative Terrato probe behavior leads to a visible-result veto; preserve the
first prototype and its tradeoff. Quasar4410 fewer index rows/heavy call and
Meteor3978.5625 sparse opportunities compose without double-crediting work.
90000 original-output calls,396288 scalar cases per variant pass. Extra saved
registers, selector/cache costs and net A7 saving remain unpriced. Publish
bounded receipts and verify original staged/prior workback identities unchanged.
[Mechanisms and limits](docs/snes-fused-toolbox.md).

## Work backward through Meteor and Quasar partial merges — 2026-10-13

Keep running combined1 test untouched. Exact offline mask/plane census finds
8182 Meteor partial rows versus741 Quasar; most Meteor merges are plain, not
color arithmetic. Qualify scalar stores on one/two visible pixels, exact signed
mask widening and selective plain-state snapshots. Preserve broad snapshot
prototype as an unpriced register-pressure risk; refinement restores original
math save sets.3978.5625 sparse hits Meteor versus132 Quasar; all depth-skip and
unguarded full-depth-write shortcuts fail sampled legality. Quasar's hidden4bpp
background offers a separate preflight hypothesis; no blind generalized prepass.

18000 original-output calls,387072 scalar tile cases,32768 canonical masks pass.
Publish source/count/qualification identities and explicit conditional cost
model charging miss guards, cache, spills and interactions. No QEMU time used,
card access, installation, new A7 savings or production gate pass.
[Detailed workback](docs/snes-meteor-quasar-partial-workback.md).

## Archive fullpaths return and qualify combined A7 crossover — 2026-10-13

Archive5,834 files before writes, verify91 previous payloads and clean FAT.
All100 old epochs attempted;55 runtime failures. Previous combined completes
five/eight contexts both repeats; Holy/Meteor/Quasar still fail. Preserve actual
non-additive A7 gains and supersede old optimistic transfer assumptions.

Qualify48-run three-version/two-order test of all eight contexts, retaining
every frame. Reuse unchanged core proofs; verify actual new controller, native
provider faults/retry/drain/deficit, wrapper and ABI. Fourteen independent
accounting fixtures and synthetic archive rejection checks cover final worker
CPU, PCM, discarded/undrained data, missing frames and partial intervals.
Freeze source/payload/proofs; push9633be6 before guarded I: staging. All57
payloads independently read back,5,833 prior protected files unchanged and final
FAT clean. Separate combined1 one-shot armed, ROM/production unchanged.
No new A7 saving or production pass claimed. [Design](docs/snes-combined-measurement.md).

## Qualify common background bands across every failing context — 2026-10-13

Review the shared CPU/APU/PPU/render/cache/runner C paths. Target repeated full-tile
ABI/palette work and opaque depth merges rather than transplant Pearl's counts.
Final constant-mode band v3 handles2,058–10,055 former cells per heavy call with
103–378 band entries across all eight staged failures; Meteor8,208 to332. Eight
batch-local palettes and first-active-tile lookup avoid repeated row checks.

Final code passes43,200 original-command comparisons,129,024 independent scalar
tile cases and3,584 repeated-palette cases; three prototypes total129,600 replay
calls. Reject generic v1's extra per-row blend calls by assembly inspection,
retain v2's exactness and improve its one-slot Quasar palette churn256 to10 in v3.
Require real named final functions with inline color math. No time inferred from
assembly, counts or QEMU. Conditional Meteor deadline needs0.912–1.014ms more,
20% target4.250–4.352ms; new unit prices and all added costs remain missing.
All817 old evidence entries and staged160/90/25 identities preserved. No card
access, new install or production claim. [Analysis](docs/snes-common-renderer.md).

## Compare new renderer applicability across staged failing cases — 2026-10-13

Use already qualified per-case census logs; no new build/replay/card access.
Pearl has9,332 affected calls; most other staged failing tails have only488,
Carbunkl/Lullaby1,058. Publish an explicit conditional table combining historical
batching transfer, scaled Pearl subscreen/DSP judgments and illustrative0.30–0.40us
new-path net prices, b=0. Meteor still exceeds deadline in that model; Meltdown
and Quasar remain thin, Pearl/Carbunkl straddle the proposed20% target. No measured
new A7 prices or confidence interval. Preserve all816 prior evidence entries.
Exclude healthy paced controls from unsupported service subtraction. Current
I: version remains fullpaths1; newest two paths remain offline.
[Table and assumptions](docs/snes-pearl-workback.md#conditional-table-for-the-failed-contexts-actually-staged-on-i).

## Trace Pearl's redundant tile work and qualify exact replacements — 2026-10-13

Aligned source census identifies 4,275 wholly hidden main BG3 row visits and
4,569 opaque sole-BG3 subscreen rows per heavy call. Early depth rejection removes
4,763 preambles; inline sole-layer production retains pixels while avoiding
indirect calls and unnecessary depth competition. Shared BG1/BG2 and flat-band
hypotheses are rejected for Pearl; 16x16 opacity is not constant color. Preserve
an offline dangling-else failure and corrected block-scoped v2 integration.

Original-output replay and independent scalar tile/map fixtures qualify bounded
correctness, not A7 speed. Research Supafaust, 2010/2002, ARM SPC and quickerSnes9x
for applicable mechanisms; reject approximate audio and nontransferable timing.
Conditional remaining 3.310 ms requires `4763*h + 4569*s - b >= 3310.0389us` under
the earlier 1.0 ms staged forecast; equal net prices need 0.354698us before other
cost. No measured unit price or comfortable-headroom claim. No card access or
staged source/payload change. [Analysis](docs/snes-pearl-workback.md).

## State Pearl's combined forecast and its weak assumptions — 2026-10-13

Identify Pearl as HOLY/0x0e and record a 1.0 ms additional-saving planning point:
0.5 ms historically calibrated batching plus explicitly assumed 0.3 ms subscreen
and 0.2 ms DSP. Judgmental 0.7–1.4 ms band is not a confidence interval or measured
unit pricing. Conditional central tail becomes 16.661 ms, only 0.028 ms/0.17%
below the deadline, 3.310 ms short of the proposed 20% target. Predict borderline
completion, not reliable repeated-cast acceptance. No fullpaths return inspected,
no card/payload changes. [Forecast and assumptions](docs/snes-fullpaths-prior.md).

## Use historical A7 transitions as a conditional forecast — 2026-10-13

Correct the implication that unknown isolated prices prevent useful prediction.
Matched Window2 changes save 1.740–2.572 ms and move Ultima/GrandTrain to bounded
completion. Their net restart-plus-associated-work ratios support a conditional
transfer forecast: roughly 3.3–3.8 ms fixed-color batching in Siren/Carbunkl/
Lullaby, about 0.5 ms Holy/Meteor, before differences in new costs/work mix.
These are empirical priors, not isolated entry prices or confidence bounds.
Predict stronger deadline closure in the former, continued needs in the latter,
and no 20% margin from this path alone. No fullpaths return data used and no card
or frozen payload changes. [Calibration and limits](docs/snes-fullpaths-prior.md).

## Five-core A7 savings and headroom measurement staged — 2026-10-13

Explicit measurement-only authority stages 1.19-fullpaths1 in its own I: folder.
Five hash-pinned counter-free cores compare ability2 baseline, fixed-color rows,
true-subscreen shortcuts, DSP dead interpolation and their new combination.
Ten valid-target contexts repeat in two reversed case/variant orders: 100 runs,
1,200 calls each, nominal 33.4 minutes plus load/flush. Every frame/sample kept.

New combination passes 21,600 exact pixel/PCM/state comparisons. Reuse standalone
proof by hash; actual new controller passes all 100 runs/120,000 calls offline.
Native fault/retry/sustained-deficit and exact wrapper seams pass. Nine accounting
fixtures reject false headroom; synthetic model checks matched saving, negative
interaction, missing flips and missing heavy overlap. No QEMU timing is A7 data.

Kernel clocks and RAM-only per-frame records include observers and all new costs.
Distinguish pure intentional pacing from required admission; conservative service
proxy retains other waits and adds worker CPU. Log distributions, pointer validity,
full-frame completion and a conditional 20% headroom flag; complete recovery and
final worker service remain required on return. Source-generator guard/C23 parser
corrections and the retained failed construction are documented.

Archive 5,021 files before writing; preserve 5,020 old files and all production/
progress hashes. Verify 91 new payloads and clean FAT after payload/arming.
Only known one-shot dispatch changes; no production core or init replacement.
Eight public bounded receipts preserve 803 historical manifest entries. Hardware
saving/headroom pending, production gate false. [Design](docs/snes-fullpaths-measurement.md),
[test](docs/snes-fullpaths-test.txt).

## Full-frame mechanisms and independent boundary qualification — 2026-10-13

Keep every frame; no evidence proves full-frame execution impossible on the A7.
Build three separate offline hypotheses from ability2: raster fixed-color capture
and batching, true-subscreen compositor shortcuts, and pure DSP interpolation
whose result is unused for zero-envelope/noise voices. Preserve guest timing,
all samples and fallback behavior; no installation or rearm.

Each final core and counted variant passes 18 original-command contexts for
1,200 calls: 129,600 comparisons. Fixed rows additionally pass 406 bounded
animation overlays for 600 calls each. Those overlays do not establish natural
command coverage or completion. Independent original tile code checks 16,128
clipping fixtures; it rejects an earlier negative-X row-selection integration
missed by the replay suite. Correct first-visible-pixel lookup; affected local
candidate never installed. Row oracle passes 22,118,400 checks; subscreen oracle
also passes. Preserve corrected fixture/construction errors and counterexample.

Align work populations to archived ability2 physical tail frames. Up to 12,532
full/clipped calls disappear in Carbunkl; Meteor removes only 1,612 and has few
new full-add rows. Proposed 20% margin requires 3.032–5.354 ms saving across
these tails. Actual candidate A7 prices/net saving remain unknown; no universal
fix or gate pass claimed. Publish 10 bounded receipts while preserving all 793
prior manifest entries. [Analysis and missing evidence](docs/snes-full-fidelity-paths.md).

## Ability3 physical return rejects math cache as deficit fix — 2026-10-13

Archive5,021 returned files; verify79 installed payloads, consumed marker and
4,811 unchanged prior files, only swap differs. FAT clean,0 card writes/rearm.
The same6/18 cases complete; the same12 fail native SETUP/errno77 with384-frame
terminal pointer excess. All properties/Rage selections and PCM accounting verify.
Matched gains30–98us in several failed tails resemble50–102us control changes;
Meteor/Siren/Bahamut/Quasar and some Rages regress. Remaining tail deficits
range0.493–1.942ms. No C/signal crash retained; no deficit closure or unit price
inferred. Preserve ability3 as a negative result; ability2 remains source baseline.

Existing ARM half-add function grows stack76→148 bytes and adds predicate/table/
stack work before original classification. Record this as plausible overhead,
not A7 cycle pricing. Generalize read-only return analysis to exact suite IDs
and correct Rage mappings; report partial/missing old-tail overlap explicitly.
Four bounded receipts preserve all789 historical manifest entries. I: remains
unarmed and next boot stock. [Measured return](docs/snes-ability3-return.md).

## Ability2 measured return and fixed-math reuse experiment — 2026-10-13

Archive4,813 files, verify79 payloads and4,603 protected prior files; only swap
changes, FAT clean. Six of18 cases complete;12 fail native SETUP/errno77.
Same-frame CPU savings: Holy1.880ms, Meteor1.740ms, Ultima2.012ms,
GrandTrain2.572ms. Ultima/GrandTrain complete; Bio Blast/Confuser remain clean.
Requested properties/Rage selections and PCM accounting verify; no C crash
retained. Draw deficit12 is terminal audio-abort behavior, not frameskip.

Build separate1.19-ability3 exact fixed-operand palette cache with epoch/fixed/
mode/bit-depth keys, wrap invalidation and bounded2bpp reads. Mixed/subscreen/
clipped/direct-color fallback stays original.43,200 exact comparisons,2,097,152
scalar palette checks,18 actual-runner cases and native/wrapper seams pass.
Repair offline counter export; preserve invalid missing-counter receipts.
Matched work thresholds and conditional cadence precede installation; new A7
unit prices and net saving remain unknown, production gate false. Experimental
18-case staging uses a new folder and protected archive/FAT/hash gates.
Guarded I: installation completes:79 payloads read back,4,812 archived prior
files protected, production/progress exact, final FAT clean and one-shot armed.
[Return](docs/snes-ability2-return.md), [candidate](docs/snes-ability3.md).

## Generalized renderer and18-case physical regression staged — 2026-10-13

Build counter-free multi-background/irrelevant Window2 batching as separate
ability2. Replay the actual returned fixtures and align inward counters to the
final16 ordinary A7 calls: remove4,320 Holy tile calls,2,148.75 Meteor,
1,452.0625 full/clipped Ultima and2,895 GrandTrain per call. Row/decode counts
remain exact; seven failed effects show no removed work. Price sensitivity still
fails the production gate; document fixed-color fragmentation and remaining
row/compositor targets rather than claiming universal fixes.

18 new-core/22 census comparisons total48,000 exact calls; all18 actual-runner
windows, requested properties/five Rage selections, state-header payload
preservation, native fault/retry/drain/deficit and wrapper checks pass offline.
Record corrected owned mock base/header setup and Window1 counter labels;
negative receipts retained privately. QEMU timings excluded from A7 evidence.

Fresh4,605-file archive/FAT/serial checks precede all writes. Stage79 verified
payload files in retro/snes-ability2, preserve4,604 prior files and all original
progress/production binaries; consume-on-boot one-shot armed. About6–7 minutes,
no B press; physical performance and continuity pending. Four bounded public
proofs preserve778 earlier manifest entries. [Scope and predictions](docs/snes-ability-regression.md).

## Ability1 physical return and matched offline checks — 2026-10-13

Archive4,605 returned files; verify1,607 installed payload files,575 unchanged
prior files, consumed marker and clean FAT. Only runtime swapfile changes;
card stays unarmed,0 writes.400 cases attempted,376 complete1,200 calls;24 PCM
errno77 failures across11 observed effects. All summons fire,24/27 complete.
Bio Blast/Confuser and all Magitek/Tools/Blitz/Bushido/Dance cases complete.
255 Rage and8 Dance selections verify.32 completed Rage cases without requested
spell properties remain an observation/branch coverage gap, not proven failures.

460,615 calls maintain100.000058% native quota; complete software PCM accounting.
Holy/Meteor final16 ordinary calls measure19–20ms steps versus16.688ms budget,
requiring approximately2.5–3.0ms aligned saving before margin. Existing generalized
renderer completes11 archived failing contexts/13,200 exact original-output/state
comparisons with verified animation initialization/deinitialization; no new core
build or A7 speed inference. Record observer cost, frequency unavailability,
pointer-bias/reserve limits and missing incremental prices. Five bounded proofs
preserve773 existing entries. [Return and next evidence](docs/snes-ability-suite-return.md).

## Automated valid-target ability suite staged — 2026-10-12

Stage authorized experimental ability1 on healthy archived I:, separate from
production and gameplay saves.400 independent cases use the unchanged successful
Confuser core:54 Magic,27 Espers,8 Magitek,24 Lore,8 Tools,8 Blitz,8 Bushido,
8 Dance and255 Rage entries. Each runs up to1,200 calls with native audio/display;
full nominal duration133.505 minutes before between-case load/flush overhead.
Logs stay in RAM during casts; flush after audio join/display idle.

149 distinct contexts exercised offline,153 full-bound executions, plus one
preserved225-call intentional stop. Correct KO-ally cursor selection and observer
global-versus-command-local identities; verify all16 Blitz/Bushido and8 Tool
graphic identities and late Rage IDs252–254. Chainsaw's natural alternate
animation is retained. Native consuming/fault/drain/deficit and wrapper seams pass.
Property observations do not prove completion or physical speed.

Archive577 prior files; protect576 unchanged, verify1,607 payload files, clean
FAT before/after staging and one-shot arming. No ROM/production/core changes or
progress overwrite. A7 results pending; production gate remains false.
[Test and evidence limits](docs/snes-ability-suite.md).

## Isolated FF6 super-unit ability lab — 2026-10-12

Build three private playable profiles with9,999 HP/999 MP, full spell/Lore/
Magitek/Tools lists and unlocked Bushido/Blitz/Dance/Rage menus, plus27 named
summon checkpoints. Original ROM and actual gameplay progress remain untouched;
no card access or installation. Validate124 actual requested casts against
original1.19 through normal controls:151,200 exact graphics/PCM/state comparison
calls over126 cases. Soldier Rage's physical branch and Water Rondo's non-native
stumble remain unqualified for requested Fire/El Nino. Keep38 earlier receipts
and correct language-specific cursors, menu redraw, battle Tools inventory and
mechanics-versus-animation IDs. Six new-profile loads/360 drawings also pass the
actual runner/PCM-owner mock fixture. Four bounded proofs preserve764 earlier entries.
QEMU results do not establish A7 speed or universal ability coverage. See
[ability lab, remaining coverage and manual test](docs/ff6-ability-lab.md).

## Successful physical return and systematic effect screen — 2026-10-12

Confuser gameplay1 returns cleanly: 7,119 calls/drawings, zero audio errors,
59.994 active calls/sec, minimum reported running reserve1,313 frames and normal
B/display/wrapper exit. Strict577-file archive, clean FAT, consumed marker and
552 unchanged prior files/progress verify; only runtime swap differs. Card stays
unarmed,0 writes. Ben reports two beautiful fights. See
[return](docs/snes-confuser-gameplay-return.md).

At Ben’s request, screen all406 AttackAnimProp records on current and generalized
renderers, plus23 inward trace pairs,19 negative-hypothesis cases and eight
normal completed Magitek casts:567,000 exact graphics/PCM/state comparisons and
2,097,152 original clipping oracle states pass. Generalize Mode1 Window2 to
multiple BG targets and irrelevant-edge writes, removing major Holy/Meteor/
Ultima/Snare/GrandTrain preambles. Reject unused fixed-color shortcut: zero work
saved in19 cases. El Nino/glow/Mode7 remain workload leads, not confirmed A7
crashes. No new hardware build/stage or speed claim; incremental A7 prices and
broader command/state coverage remain missing. See
[coverage, fix, calculations and next evidence](docs/ff6-effect-safety-screen.md).

## Confuser candidate staged for authorized manual qualification — 2026-10-12

After explicit “Load it to I:” instruction, build the counter-free BG3 batching
and refined half-add candidate in a separate versioned one-shot. Preserve regular
1.19 runner/PCM/display/input/save/exit behavior, production files and all prior
progress. Copy latest combined-gameplay SRAM and migrate only snapshot identity.
Write conditional cost inequality, unmeasured prices and falsifiable physical
prediction before staging; production gate remains unmet, experiment pending.

Final4,800 output/state comparisons and180 actual-runner frames pass; consuming
native snapshot/fault/drain/deficit and wrapper checks pass. Fresh complete archive,
readonly FAT,553 protected prior-file hashes and payload/arm readback guard I:.
Publish seven bounded proofs and separate identity, excluding core/ROM/save bytes.
See [procedure](docs/snes-confuser-gameplay-test.txt) and
[setup](docs/snes-confuser-gameplay.md). Physical performance pending.

## Confuser offline cause map, work reductions and budget — 2026-10-12

Use the archived manual failure and byte-matched ROM/emulator C to identify BG3
window fallback plus growing half-add/depth work. Preserve the first incorrect
Heal Force replay as a negative control, then verify normal-input Confuser by
visual cursor and ROM initialization. Separate BG3 batching removes2,028 tile
calls/call; half-add experiments cover4,042 rows. Refine the guard after
counter-free ARM assembly reveals extra register saves in the first shortcut.

10,800 ARM output/state comparisons,1,048,576 original clipping states and
independent scalar/math/row oracles pass. Publish bounded counts/proofs and an
incremental cost inequality:0.803ms timing floor,1.020ms local accepted-rate
proxy, explicit added costs and transfer limits. A7 prices remain missing; no
card access, production changes, device suite or rearm. See
[investigation](docs/confuser-rendering-investigation.md).

## Manual combined gameplay return: Bio Blast works, Confuser stops — 2026-10-11

Archive and hash-verify the returned card without writes; FAT clean and unarmed.
User reports Bio Blast fine, Confuser crash. Retained225s session ends with PCM
errno77/SETUP and orderly library/display exit. Last23 complete calls imply
0.803ms local deadline gap; sparse PPU samples grow while APU stays near4ms.
Preserve pointer-bias uncertainty and missing effect-aligned replay/subphase
evidence. No new build, test, installation or rearm. See
[analysis](docs/snes-combined-gameplay-return.md).

## Combined renderer staged for manual longer gameplay - 2026-10-11

User authorizes manual Bio Blast casts. Reuse the exact physically measured
combined core and immutable regular1.19 runner in a separate gameplay folder;
remove automatic replay and retain normal library/input/pause/save/load/exit.
Copy current SRAM and qualify a separate header for the unchanged snapshot
payload; original progress and binaries remain intact. Write the measured
whole-path gate, conditional margins, cadence/reserve and falsifiable longer
gameplay prediction before staging. Sparse/recent normal telemetry stays light.

Additional2,400 snapshot output comparisons,180 actual-runner frames, consuming
native menu/load/resume/fault/drain/deficit checks and wrapper fixtures pass.
Archive/hash/healthy-FAT guards and payload/arm readback protect the I: card;
new test saves stay separate. Long gameplay remains pending. See
[instructions](docs/snes-combined-gameplay-test.txt) and
[qualification](docs/snes-combined-gameplay.md).

## A7 pair1 returned: combined renderer completes every pass - 2026-10-11

Strictly archive the physical return on I: and verify clean FAT/staged payloads.
All six combined passes complete; all six baseline passes stop with native
errno77/SETUP. Both combined full500-call replays preserve500 drawings and
complete effect/recovery with stable audio reserve. Matching RUNNING effect
calls save2.885–2.972ms CPU and3.125–3.250ms core wall; complete-effect core
wall means15.420/15.530ms, with observer-inclusive cadence near16.688ms.
Late baseline warmup never finishes, so no invented late paired price.
Frequency remains unavailable; extended gameplay and exact vendor stop semantics
remain unqualified. Preserve all raw evidence privately; no card writes/rearm.
See [return analysis](docs/snes-a7-pair-return.md).

## A7 pair1 measurement staged on reassigned I: card - 2026-10-11

Prepare a separate whole-path baseline/combined renderer comparison:12 ABBA
passes across the complete Bio Blast replay and two aligned later starts.
Disable nested phase/callback clocks and core counters; record bounded per-call
CPU/wall, admission, observer, frequency and worker/PCM state, flushing after
worker joins. Keep native audio/display active, all frames and original quotas.
Later snapshots are independent audio epochs, not playback recovery proof.

Qualify6,000 output comparisons,12 mock passes/2,704 calls, both cores through
consuming native fault/drain/deficit contracts and the actual one-shot/splash
wrapper. Archive457 retro files before writes; clean FAT and protected readback
guard I:, serial11EB-1465. Production binaries, adapter, init, prior diagnostics
and private progress stay exact; only owned diagnostic payload/dispatch/marker
are staged. Physical speedup and audio closure remain pending. See
[test instructions](docs/snes-a7-pair-test.txt) and [suite](docs/snes-a7-pair-suite.md).

## Offline Bio Blast hypotheses: dispatch, palette tables and prefix validity - 2026-10-11

Build isolated counted ARM/QEMU variants without changing production or accessing
the card. Window batching removes8,340.864 plain full-tile calls/effect frame;
row populations stay exact. Palette-table caching/direct NEON construction cuts
palette builds4,117 ->13 and entry storage36KiB ->3.75KiB; former RGB hits now
perform gathers, so net A7 cost remains unmeasured. Prefix validity replaces
ordered scans with two reads/comparison and preserves original fallback.

Six1,200-frame Bio Blast output comparisons plus two2,400-frame broader checks
pass; original clip524,288 states and independent validity38,400 queries pass.
Diagnose obsolete callback-batching assertion without weakening output checks.
Revised partial dispatch threshold0.1855us/call could close the late floor;
0.2961us could close the separate PCM proxy before other costs/headroom. These
are falsifiable prices to measure, not QEMU performance predictions. Publish11
count/proof files, preserving699 historical evidence entries. No install/rearm.
See [experiment and limits](docs/bio-blast-clever-renderer.md).

## Bio Blast inverse cost model - 2026-10-11

Inspect full NEON versus scalar clipped C paths and align three archived A7
controls with retained replay work counts. Quantify row/clip/cache/decode
population changes, inverse saving requirements and held-out prediction errors.
NEON visits grow38.66%; decodes stay flat; added palette payload predicts17.21us.
The best single-count model misses0.841..0.851ms on seven held-out calls, so
correlations are not installation prices. Preserve a reproducible offline
analysis with input/source hashes and exact missing call/branch/cache evidence,
observer budget and audio acceptance requirements. No executable/device changes.
See [backward model](docs/bio-blast-backward-model.md).

## A7 cost1 returned: priced batching model fails the budget - 2026-10-10

Archive60 runtime/progress,49 lab and67 separate measurement files before any
card writes. Clean FAT, exact payloads and all141 protected hashes verify;
all tests unarmed. Thirteen physical passes reproduce SETUP/EBADFD; controls
render291 calls, sparse285, benchmark287. Dense frame320 is never reached.

Retain CPU/wall individual and32-operation distributions, terminal exclusions,
full PCM histories and cache-alignment checks. The partial warm setup mix is
2.179us/entry; materialization payload0.1052us/row; short-span helper model114.6us.
The resulting setup231.5 minus rows149.8 minus helpers114.6 gives32.9us net
loss, leaving1.547ms of the late deadline gap. This is a conditional model,
not whole-candidate e/r/b or an installation prediction. Deep phase clocks add
9.294ms CPU at frame277; no calibration is subtracted. Later passes change the
cache miss/reuse split from frame0; total row work and entry counts remain exact.

Quota remains99.9994..100%; trusted reserve drawdowns2,823..2,988 frames precede
the repeated384-frame terminal pointer discrepancy. Complete effect/recovery
and vendor stop mechanism remain unqualified. Publish17 bounded timing/curve/
verification files, preserving all682 historical evidence hashes. No new
executable, candidate installation or re-arm. See [the return](docs/snes-a7-cost-return.md).

## A7 cost1 diagnostic suite staged; performance gate still pending - 2026-10-10

Build a separate baseline measurement core/owned ARM runner with exclusive
setup/window regions, sparse1/64 row/cache clocks, dense frame320 cross-check,
warm actual-path kernels, individual versus32-operation distributions, kernel
CPU/wall clocks, per-call frequency/worker/PCM observations and32,768-event RAM
PCM history. Flush after audio join/display drain and sync between independent
passes. No emulated quota, render decision or production core change.

600 exact comparison frames, four500-call captures, consuming native
fault/retry/drain/sustained-deficit checks and13 automatic mock passes qualify
contracts only. QEMU costs discarded; unpriced longer candidate spans and whole
cache interaction remain explicit. The1.514ms late-call account is distinct
from about2.436ms needed at the current PCM production-cadence proxy.

Archive60 runtime/progress and49 lab files before staging.141 protected hashes,
all new payloads/135 independently reread hashes and four fresh FAT checks pass.
Only measurement is armed; original normal init, production runner/core/adapter,
stock/current Vesper and private progress preserved. Publish owned runner and
six bounded verification files; preserve all676 historical evidence hashes.
No ROM/private state/diagnostic core/runtime dependencies published. See
[suite](docs/snes-a7-cost-suite.md). Physical A7 e/r/b and verdict remain pending.

## Focus1 return archived; cycle-derived effect budget and prediction gate - 2026-10-10

Strict read-only collection preserves60 runtime/progress and49 lab files;
all58 prior files,12 private progress files, nine snapshot CRCs, stock/current
Vesper init and27 reader files verify. Exact Focus1 runner/unchanged1.19 core
and wrapper match; FAT clean, marker consumed, no card writes or rearm.
Session1987 calls ends with SYNC_OBSERVE errno77/SETUP; B/cleanup/final copies
complete. Six retained phase samples show PPU5.741 ->8.904ms, APU-inclusive
4.529..4.898ms. Ordinary late calls17.991ms plus0.211ms admission exceed16.688ms.

Derive358,416 emulated master clocks/call ->534.688 native /735.948 sink frames.
Actual native average534.650 is consistent with the quota; accepted physical
production38,481/sec requires14.603% more throughput. Separate previous
18.287ms/13.766% context from this run; previous final cost was not pre-effect
baseline. Publish chronological partial reserve curve with pointer-validity
boundary; complete onset/recovery remains missing. Window scorecard fails the
five-condition prediction gate: per-entry/row/bookkeeping A7 costs unmeasured.
All665 historical evidence hashes verify before11 bounded files are appended;
raw progress/dependencies remain private. [Budget and limits](docs/snes-focus-1-return.md).

## ROM-derived Bio Blast cause map and isolated window patch - 2026-10-10

Rebuild the owner3 MiB FF6 ROM byte for byte from pinned annotated assembly;
lift103,538 native CPU instruction addresses into eight private C banks and
write a readable Bio Blast script/wave model.178 real wave-kernel executions
match all32 expected words. Frame320 scroll writes cause no pending-render
flushes; circular-window edges cause123. Patch a separate core to retain BG1
window bounds per scanline and defer eligible edge flushes.

Independent original clip code matches all524,288 edge/polarity/masking states;
3,600 actual ARM comparison frames match per-frame visible/PCM CRCs, sample
counts, geometry and periodic normalized serialized bytes. Effect PPU updates
drop78.97%, but color-row materialization rises34.58%; no hardware speed/audio
claim. Shipping1.19 core and card remain unchanged by this experiment. Publish
authored tools/models and six bounded evidence files, preserving659 prior hashes;
private ROM/assets/generated bank maps/states/dependency bytes remain local.
[Cause map and exact limits](docs/ff6-bio-blast-cause-map.md).

## Focus1 unchanged-core diagnostics qualified and armed - 2026-10-10

Retain64 recent frame records and sample phases/callback CPU one in eight under
ordinary-call load, with sampled-cost feedback excluded. Actual ARM runner,
resampler, failing-interval cadence, report-capacity and consuming native PCM
fault/retry/load/drain/deficit checks pass. Archive58 MVP/progress and49 lab
files before installing the owned runner/instructions. Independent readback
checks138 protected hashes, exact1.19 core/wrapper and clean FAT. Only SNES
armed, no firmware trigger. Physical attribution pending; no audio fix claimed.
Publish the runner-only release and14 curated files without dependencies,
preserving645 prior evidence hashes. [Test](docs/snes-focus-1.md).

## SNES1.19 Bio Blast still fails; clean exit preserved - 2026-10-10

Collect58 MVP/progress and49 lab files with verified hashes before any changes.
Exact1.19, all prior files, nine snapshots and three SRAM generations survive;
fresh FAT is clean.1,713 core calls end with native SYNC_OBSERVE errno77/SETUP.
Near failure, accepted audio is38,764 frames/sec against44,100 Hz; final ordinary
calls average18.287 ms wall /16.935 ms CPU. Offline color-work savings have not
fixed physical audio. No phase sample covers the final24-call window.

B exits our library after the game error; display join/close and wrapper final
copies complete. Fresh failure reports and stderr agree; recorded255 status
is the failed game's rc=-1, not a signal crash. Stock/current Vesper SD artwork,
normal init and58 archived files independently reread exact. No card writes,
repair or rearm; all tests and Code.bkp absent. Guarded return publisher keeps
private progress/binaries local and preserves637 prior evidence hashes. Next
engineering step is bounded phase attribution during the failing interval.
[Return](docs/snes-mvp-1.19-return.md).

## SNES1.19 rearmed for proper game exit - 2026-10-10

User explicitly requests rearming the unchanged build to exit properly.
Archive56 returned MVP/progress files and49 lab files before a clean read-only
FAT check. Verify exact1.19 payload and138 current protected file hashes,
including27 reader files and the current Vesper/stock boot baseline. Recreate
only the SNES one-shot marker; all archived bytes remain exact. No payload/save
or flash changes and no new audio acceptance inferred.
[Rearm receipt](evidence/2026-10-10/snes-mvp-1.19-rearm/rearm.json).

## SNES1.19 demand-driven colors qualified and armed - 2026-10-10

Resume SNES from the recovered1.18 Bio Blast production deficit. Test index/depth
visibility before RGB preparation and cache only demanded rows, retaining the
36 KiB footprint. Repeated1.18 baseline reproduces all1,200 census rows;
162 effect frames need667,001 palette lookup rows versus1,003,928, down33.56%.
All other126 counters and command-boundary pixel/PCM CRCs match. Row-tag
requests increase slightly; work reduction is not an A7 speedup claim.
Shipping core passes14,400 clean-core equivalent frames including the complete
Magitek effect, independent color/cache/CGRAM checks and actual ARM runner,
snapshot, native PCM, wrapper and display lifecycle checks.

Archive51 MVP/progress files and49 lab files before installing exact1.19.
Preserve29 private save/state files and27 SPI-reader files; stock/current Vesper
SD artwork and normal init retain their verified hashes. Create a separate
snapshot header with original payload. FAT clean before writes and after
payload; independent readback passes. Only SNES armed, no Code.bkp, no flash
write. The first historical showlogo guard refused before writes; pin the
already verified Vesper release hash for the current baseline. Physical audio
and speed remain pending. [Candidate and next test](docs/snes-mvp-1.19.md).

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
unresolved. [Verified result](docs/vesper-static-firmware-update.md).

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
audio unchanged. [Current physical verification/return](docs/vesper-static-firmware-update.md).

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
[Exact staged image and next physical/return steps](docs/vesper-static-firmware-update.md).

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
[Verified return](docs/vesper-flash-verification.md).

## Post-update return, trigger cleanup and read-only verification rearm

Archive51 MVP/progress,49 lab and all prior profiles/logs before card changes.
Stock runtime/core and protected progress match pre-update hashes; fresh FAT
passes before/after removing the exact Code.bkp trigger. Keep all9 prior reader
files intact via guarded archived rename; reuse unchanged qualified ARM reader/
wrapper and fresh run identity.8 host checks qualify manager rearm/rollback,
directory-move/update refusal and full-byte match/difference/incomplete analysis.
Independent installed reader/init/marker/retained-profile/protected hashes and
post-install FAT pass. Only read-only verification armed; full8MiB comparison
and boot without updater trigger pending. Physical splash acceptance retained;
no new flash program/erase, audio unchanged. [Run and physical procedure](docs/vesper-flash-verification.md).

## Original second-splash replacement physically accepted — 2026-10-09

User confirms normal manual power-on shows static D-R35, then Vesper replacing
the regular D-R35 animation, then default launcher. Requested physical boot/
animation acceptance passes; first static screen stays. Record outcome and exact
card-return resume without another write. Collect/archive before removing the
known update trigger; full SPI comparison and repeat cold boot without trigger
remain pending. External recovery unqualified and audio unresolved.
[Accepted result and return procedure](docs/vesper-sd-firmware-update.md).

## First SD update report:100% then power-off — 2026-10-09

User reports battery-only startup, progress100% and power-off without observed
automatic restart. Re-inspect the exact captured completion path: successful
programming return invokes sync then reboot(0x01234567). Correct the physical
instruction: normal manual power-on once with card inserted; no ten-minute wait
in an actually powered-off device. Boot/animation/full readback and recovery
remain unverified; no new card access or writes. Preserve exact current resume.

## Authorized SD firmware staging before external recovery — 2026-10-09

User explicitly chooses SD update now with programmer purchase if boot fails.
Stage only the exact privately qualified WQW package as retro/update/Code.bkp.
Archive current logs/progress and original SPI backup first; fresh pre/post FAT,
997 original card-file hashes and independent package/init/updater readback pass.
Normal init exact, no other test armed.6 host checks cover staging, wrong-card/
existing-update/competing-runtime refusal and health-failure rollback. Preserve
the expected full-image hash including vendor CRC/time mutation. Physical flash,
second-animation acceptance and recovery remain pending; first static screen
preserved and audio unresolved. Update execution gate, return/unstage/readback
instructions and exact handoff. No vendor-containing files published.
[Result and next physical step](docs/vesper-sd-firmware-update.md).

## Physical board photographs and recovery equipment selection — 2026-10-09

Preserve/hash-verify five supplied photographs privately. Confirm this unit's
VT569B and exposed eight-pin flash package; preserve the user's MD-marked
transcription separately from apparent25Q64CSIG interpretation. Match compatible
family to captured c84017/8MiB evidence and manufacturer3.3V/SOP8 208mil data.
Recommend assembled CH347 adapter and compatible SOIC clip; actual voltage,
mapping, isolation, external read/write/recovery remain pending. Case may be
reassembled. No device change or firmware installation. [Findings and next work](docs/board-identification.md).

## Exact loader/updater qualification and private full Vesper candidate — 2026-10-09

Recover Thumb loader contracts and verify the first static bitmap's boot-code
pointer. Prepare a private8MiB candidate changing only rootfs/table length;
kernel, DT, bootstrap/static bitmap and GPDA remain exact. Execute captured
parser/getter/header selection/section loading and DT initrd patch under QEMU.
Execute exact vrtemu UpdateROM/ZIP/UpdateROMProc with intercepted hardware and
RAM-only erase/program callbacks. Nine offline outcomes qualify acceptance,
four no-write refusals, private-output guard and a malformed-ZIP NULL-image fault.
Compatible image fully matches simulated readback:55 erases/14,080 page programs,
including boot-code block0 because vendor metadata changes. No device writes,
SD staging, kernel execution or recovery claimed. Programmer unavailable;
chip marking/package/access is the next physical dependency. Publish only
interpreted metadata; preserve all prior evidence hashes. Audio unresolved.
[Qualification and exact next work](docs/firmware-offline-qualification.md).

## Full SPI backup, boot layout and private Vesper rootfs candidate — 2026-10-09

Archive the complete16MiB return, independently verify two identical8MiB passes,
CRCs/SHA256, run/wrapper/completion and4,111 messages in103.771059s. FAT is clean;
51 MVP/progress,49 lab and43 prior-profile files preserved. Restore exact normal
init after fresh health; independent protected/result readback and postrestore
FAT pass, nothing armed. No repair or flash/configuration write.

Locate kernel/gzip-cpio rootfs/device-tree sections in the exact image. Extract
the same original `/showlogo`, init, power-key and watchdog as runtime captures.
Prepare only a private rootfs candidate with the qualified Vesper ZIP; all other
cpio bytes stay exact, compressed payload fits with108,732 bytes spare. Six
checks pass including independent libarchive extraction and GNU gzip. Locate a
matching first-screen raw bitmap visually; boot-code reference remains unknown.
No full flash image/update package staged. Built-in kernel cpio has no rescue
init. Boot validation, recovery and persistent replacement remain unqualified;
audio unresolved. [Return and exact next work](docs/spi-readback-return.md).

## Physical SPI ID and qualified two-pass reader — 2026-10-09

Archive successful ID run: three c84017c84017 replies, status00, no competing
owner/error/timeout, matching consumed marker and wrapper exit0. FAT is clean;
51 MVP/progress and49 lab hashes preserved. Restore exact init after fresh health.
Match the triplet to GigaDevice64-Mbit NOR/nominal8MiB using primary manufacturer
and Linux references; exact silicon revision/package remain unverified.

Build fixed05/9f/03 two-pass reader with4KiB packets, working1MHz limit, byte
comparison, indexed result bundle/CRCs, owner/settings/identity guards and240s
owned-child deadline.9 native/ARM/return/health/sparse-shell/ABI checks pass.
Install readback-only profile, independent release/init/marker and protected
progress/prior-result readback, healthy postinstall FAT. Physical full readback
pending; raw contents private, no flash/configuration writes, recovery or splash
replacement. [ID return](docs/spi-identify-return.md), [next run](docs/spi-readback.md).

## Survey2 physical return and read-only SPI identification — 2026-10-09

Archive all905 capture ranges; verify CRCs/lengths/completion, matching run and
wrapper exit0. No failed/truncated reads or caps; returned FAT is clean. Preserve
51 MVP/progress and49 lab files, then restore exact init after fresh health check.
This is one successful storage return, not general shutdown/media qualification.

Discover stock vrtemu PID521 owns SPI0.0 on FD8. Build a synchronous early-init
chip-ID probe with fixed05/9f commands, ownership/configuration/busy/response
guards and owned-child deadline/reap.11 software checks pass. Install with
independent protected readback and healthy postinstall FAT; only this probe is
armed. Physical identification remains pending; no flash/configuration writes,
internal splash replacement or audio fix. [Return](docs/device-survey-2-return.md),
[probe and exact next run](docs/spi-identify.md).

## Survey1 return, FAT repair, indexed survey2 and updater recovery — 2026-10-09

Preserve329 returned captures and all private progress; reject completeness despite
the successful wrapper tail.521 nonempty missing files require exactly17,856 KB,
matching recovered chains. Approved repair leaves all789 readable files unchanged;
archive1,310 repaired files. Replace many FAT capture entries with an indexed CRC32
bundle/report, retain v1 analysis, reject corrupt/torn ranges and gate restoration
on fresh filesystem health.21 software checks pass; survey2 armed with protected
readback and healthy postinstall FAT. Physical durability pending.

Recover exact vrtemu SD-to-SPI updater from machine code: executable-dir
update/Code.bkp, WQW/ZIP/CRC/compatibility checks and03 reads/D8 erase/02 program.
SPI NOR DT candidate found; no physical flash access or recovery qualified.
[Return](docs/device-survey-1-return.md), [updater](docs/firmware-update-contract.md).

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

Earlier entries below preserve chronology. The latest resume is the boot-owner probe.

## Animated Vesper loading screen installed — 2026-10-09

On the repaired healthy card, install qualified cyan feathered V/heart artwork
and18-frame loading dots over stock showlogo. Archive original first; exact
patched hash and all stock bytes outside the artwork verify. Fresh51-MVP and
49-lab protected files plus recovered chains remain unchanged. Post-install
read-only FAT check passes; game/lab remain unarmed. Older whole-card archive
differs in volatile swapfile; preserve its current bytes privately and report
the historical comparison limit. Physical boot/handoff appearance remains
pending. [Receipt, preview and guarded rollback](docs/vesper-boot.md).

## Approved FAT recovery preserves files and retrieves1.18 fault — 2026-10-09

Rehash all412 private backups and compare the card before approved administrator
CHKDSK/F. AnswerY to save lost chains:14 files/1472KB recovered, filesystem
corrected. Fresh read-only checks pass. Complete426-file private archive shows
all412 previously readable files unchanged. Recover actual1.18 session/PCM
text and two SRAM prefixes matching verified pre-test progress. Preserve the
empty current SRAM, then restore that known8192-byte copy with atomic/readback
verification; no newer save identified. Final strict51-MVP/49-lab archive passes.

Recovered2238-call session and96-operation PCM history show the prior reserve
erosion/pointer divergence/EBADFD pattern; no audio fix or controlled cache-speed
claim. Preserve all raw chains privately and publish identified text/metadata
with source hashes. Stock/snapshots/exact1.18 remain intact; splash uninstalled,
both one-shots unarmed. [Recovery and resume](docs/fat-recovery-2026-10-09.md).

## FAT repair need re-verified — 2026-10-09

Fresh read-only CHKDSK on the known card repeats both invalid backup allocation
units and 1,472 KB in 14 lost-chain files. Independent byte reads fail with
Windows1392 on the same entries; current SRAM remains empty and stock splash
hash matches. Record the active-volume false-positive caveat and corroborating
evidence. Repair/recovery remains approval-gated; no card repair, splash install
or re-arm. Audio cause and card hardware health remain unresolved.
[Verification and exact resume point](docs/fat-verification-2026-10-09.md).

## MVP1.18 return and Vesper boot artwork — 2026-10-09

Magitek Bio Blast again produces an audio descriptor error and returns to our
library. Exact1.18 payloads match. Fresh failure/session/PCM files and current
SRAM are zero bytes; two backup entries are unreadable. Read-only FAT32 check
confirms invalid first allocation units and lost chains. Preserve51 readable
MVP/progress files,49 lab files and a private hash-verified412-file full-card
backup. Snapshots and earlier SRAM copies survive. Stale1.16 stderr is not new
1.18 evidence; cache performance and the current PCM stop cannot be priced.
Backed-up repair/recovery consent is pending; no card writes or re-arm.

Build the requested black/cyan feathered V/heart loading screen from the user's
preferred reference. Recover the embedded ZIP/sprite ABI and replace only its
artwork span, keeping all stock code/handoff bytes exact. The actual stock ARM
decoder and all18 sprite draws pass pixel/canary checks. Publish authored art,
packer, original-code checker and guarded install/rollback source; vendor ELF
stays private. Installation and physical appearance wait for a healthy card.

[1.18 return](docs/snes-mvp-1.18-return.md), [boot artwork](docs/vesper-boot.md).

## SNES MVP1.18 caches colors for Magitek Bio Blast — 2026-10-08

1.17 starts FF6 on the first attempt and sustains35,763 calls overall before
Terra's Magitek armor Bio Blast drains audio reserve and returns to our library.
The move is not Edgar's Tools Bio Blaster. Final ordinary calls average17.981ms
wall /16.638ms main CPU; sampled inclusive PPU rises from3–4ms to8.150ms.
Fresh native failure records verify; wrapper run log/session backup are stale1.16.
The user withdrew expected driving snow after checking playthroughs.

Reproduce the actual Magitek effect offline from a private Narshe snapshot,
forcing only battle entry, then using real menu inputs. Add a bounded36KiB RGB
color cache keyed by indexed tile, palette, bit depth and color epoch. Actual
VRAM decode, both CGRAM half-writes, brightness and load rebuilds invalidate it.
Transparency/depth/flips/math remain dynamic. All original renderer work counts
are identical;93.36% tile reuse removes48.71% of palette-lookup row work in the
matched effect window. The earlier losing Lab1 cache remains a negative result;
this candidate still needs A7 performance proof.

Independent pixel/depth/math/cache/collision/wrap tests and131,072 extracted
CGRAM seam cases pass.1,200 full Magitek frames plus12,000 intro/Narshe frames
match original pixels/native PCM/geometry/periodic state. Native PCM, snapshots,
input, splash, display ownership and diagnostic isolation pass. Preserve saves,
stock/hook and lab; create a separate core-matched snapshot header.
Installed02:45 UTC (October8 Chicago): all28 prior private and49 lab files,
stock and hook independently verify; game armed, lab unarmed. Hardware pending.


[1.17 return](docs/snes-mvp-1.17-return.md), [implementation](docs/snes-mvp-1.18.md),
[physical test](docs/snes-mvp-1.18-test.txt).

## SNES MVP1.17 isolates diagnostics after sustained1.16 result — 2026-10-06

Archive the1.16 return read-only: exact release,48 MVP/49 lab files,19 prior
game-progress files unchanged and two updated SRAM files safely archived.
Successful retry delivers31,601 full video callbacks over526.812 active seconds
(59.985 calls/sec), zero held drawings/duplicate callbacks/audio-write errors,
one successful snapshot load, four pauses and clean save/exit. User reports
significant improvement. Both wind sound and blowing snow seem missing in
opening outdoor Narshe gameplay; correctness remains unresolved.
[Return and limits](docs/snes-mvp-1.16-return.md).

First-attempt70-call failure survives under its unique1.16 failure bundle.
Main CPU stays roughly9ms while wall cost reaches18–39ms. Wrapper discovery
and SD copies run11.27–11.57s uptime, overlapping reserve collapse and11.470791s
fault. Strong scheduling-interference hypothesis, not yet proven causal.
Move routine inventory/sync before child launch and final log copies after
child exit; remove the live background monitor entirely. Fault traces and
failed-session reports remain durable, while abrupt poweroff can lose RAM-only
routine progress. Keep the1.16 core and sound/render/admission policies exact.

Actual wrapper fixture rejects old live diagnostic writes and qualifies new
isolation, final progress, fault persistence and splash/ready/watchdog contracts.
ARM runner audio/state/save/display contracts pass.12,000 full-core frames
match clean pixels, native PCM, geometry and periodic state. Add private offline
scene-capture source; game pixels/PCM and all private inputs remain local.

Installed and independently read back at13:21 UTC: all26 original private and49
lab files, stock/hook, original wrapper and snapshots preserved. Game one-shot
armed; lab unarmed. Owned release and curated qualification are immutable.
[Implementation](docs/snes-mvp-1.17.md), [next test](docs/snes-mvp-1.17-test.txt).

## SNES MVP1.16 fixes redundant fixed-color raster invalidation — 2026-10-06

Archive the1.15 return read-only: exact payload,45 MVP/49 lab files, all21
game-progress files and stock/hook unchanged. Three audio-failed attempts,
two retained final reports; both snapshot loads succeed before19/18 calls
and controlled audio failure. Ordinary restored-scene main CPU about18ms,
wall19.3–19.5ms and sampled PPU about10ms. First detailed fault history was
overwritten by retries. [Return](docs/snes-mvp-1.15-return.md).

Replay the exact private state locally. All214 pending `$2132` flushes per
frame leave effective fixed color unchanged; raw component-tag changes force
unnecessary scanline render jobs. Flush on actual selected-component changes,
preserving original assignments and byte latch. PPU updates drop217–223 to4–10,
with identical31,520 requested tile rows and full output.16,777,216 extracted
stock/patched register cases and1,200 exact-core frames pass. This is removed
work, not a measured physical speedup. [Repair](docs/snes-mvp-1.16.md).

Retain up to eight failed-session report/PCM pairs per process after failed
worker cleanup, with kernel-time/PID attribution to reject stale trace copies.
Real native failure/retry/later-failure fixture proves preservation. Correct
host-header C23 scanf redirection to the device's existing legacy ABI. All
runtime/core/boot/input/display/snapshot/lifecycle qualifications pass.

Install at2026-10-06 06:23 UTC, after another45-MVP/49-lab archive. Independent
readback verifies exact new payload, all23 original private files, stock/hook,
older wrapper, lab files and separate new-core state. Game armed, lab unarmed.
Immutable owned release and25 qualification artifacts published. Full native
speed, complete sound and first-launch stability remain physical acceptance.

## SNES MVP1.15 final candidate retains sampled phase history — 2026-10-06

Retain eight sampled call records separately from the last24 ordinary calls,
so APU/PPU measurements survive a long unsampled stretch. No additional
sampling or healthy card writes. Exact optimized1.14 core remains unchanged;
runner/native lifecycle/starvation and production-path qualification rerun.
Retire1.14's exact unconsumed marker only after archiving all files. Preserve
its release/evidence bytes.1.14 had no physical test;1.15 is the delivery
candidate for the same coherent execution-budget rewrite. [Details](docs/snes-mvp-1.15.md).

Final install archives45 MVP/49 lab files before writes; independent readback
verifies exact payload, all23 original private files, archived/nonpayload
files, stock/hook/older wrapper and separate qualified snapshot. Game one-shot
armed, lab unarmed. Curated24 checks and owned release published; device
native speed, sound and stability remain pending physical qualification.

## SNES MVP1.14 A7 execution-budget rewrite — 2026-10-06

Build the pinned Plus core with O3/LTO, hidden internals and explicit API
exports; permit builtin memory optimization and apply O3/LTO to the runner.
Replace planar tile decoding with NEON2/4/8bpp expansion into the existing
VRAM-invalidated cache. Reduce32040/44100 frontend arithmetic to178/245 with
exact signed truncation and preserved batch state. Reuse locked post-write
PCM observations while requiring freshness after each unlocked wait/request.

Retain24 recent per-call costs in RAM and sample inclusive APU/PPU thread CPU
on one call in64 after reset/resume. Include sampled status, frontend costs,
epoch and admission waits; do not mistake inclusive regions or observer costs
for an exclusive CPU census. Core equivalence passes1,200 frames with exact
pixels/PCM/geometry/logical state, plus independent planar/converter oracles.
Native runner checks now replay sustained19.8805ms production and expose
starvation without hidden re-priming, frame suppression or accounting loss.

Provide a guarded consumed1.13 installer, separate qualified old-snapshot
copy, independent readback and immutable publication. Full-speed/full-sound
device acceptance remains pending; core code growth and cache-miss-dependent
decode benefit are explicit limitations. [Implementation](docs/snes-mvp-1.14.md).

## MVP1.13 return and execution-budget review — 2026-10-06

Archive 44 MVP/49 lab files read-only, exact release, consumed markers and
unchanged stock/hook/core plus all 20 private progress files. Two fresh reports
fail after 26/230 calls; retry loads the snapshot successfully. Both report
successful synchronized capture. The second 96-operation history survives,
including 16,335 kernel READ_ALL bytes; retry replaced the first history.

The retained interval accepts 5,888 frames in 159.044ms (37,021/sec), while
reported hardware advances 6,912. Nine large batches average 19.8805ms apart.
Reserve erodes before application pointer diverges by 128, then 256, then 384
frames and SETUP. Starvation is the leading trigger; exact vendor mutation/
stop path remains unknown. No full software queue, partial transfers or EAGAIN
occur. Whole-session averages do not qualify the expensive phase. Display
reservation totals 1.066ms across 230 calls, so queue admission is not the
observed multi-ms loss per frame.

Add a read-only flight-history analyzer and [execution-budget proposal](docs/execution-budget-review.md):
phase attribution on the expensive state, whole-program A7 compilation,
targeted custom core paths and cheaper frontend servicing. Buffering/isolated
stall fixtures cannot prove sustained production. No new executable, card
writes or re-arm; prior whole-device poweroffs remain unexplained. See
[return](docs/snes-mvp-1.13-return.md).

## SNES MVP1.13 durable PCM fault capture — 2026-10-05

Archive the consumed 1.12 return: exact payload, 43 MVP/49 lab files, stock/hook/
core and 19 prior progress files unchanged; retain the changed SRAM backup.
One fresh final report has 1,106 calls, a successful snapshot load and the same
SYNC_OBSERVE/SETUP/384-frame discrepancy. Its aggregate rate is 59.819 active
calls/sec, with no intentional holds. The PCM history is absent and stderr is
empty; later periodic/final copies do not survive. Exact diagnostic loss and
native stop causes remain unknown. The backup session belongs to 1.11.
See [return](docs/snes-mvp-1.12-return.md).

Capture the first fault directly to the card, flush and fsync the file, rename
and fsync its directory before returning the PCM error. Preserve failed temp
evidence and append capture errno/sync status/bytes to error detail. Read the
kernel ring before card I/O; a refused read does not discard PCM history.
Retain unchanged core, PCM settings, admission and full drawing. No new healthy
file I/O; this is an observability repair, not a claimed playback fix.

Actual ARM client tests pass file/directory sync and injected sync failure
without hiding PCM errno. Real FF6 runner fault capture completes before return;
clean retry/two snapshot resumes pass. Wrapper immediate-error/direct-path and
existing runtime/core checks pass. Physical capture durability remains pending.

Install/readback complete at 2026-10-06 04:42 UTC (October 5 locally), after a
fresh 43-MVP/49-lab archive. All 22 current private files, snapshots, current
SRAM/backup, 49 lab files and stock/hook/core/older wrapper match their hashes.
Game one-shot armed; lab unarmed. [Capture contract](docs/snes-mvp-1.13.md).

## SNES MVP1.12 PCM fault history — 2026-10-05

Archive the consumed 1.11 return: 43 MVP/49 lab files, exact release and unchanged
stock/core/hook. Nineteen prior progress files and every snapshot/current SRAM
match; retain the changed SRAM backup. User confirms audio error/our library.
Two final reports contain 2,195/253 calls; the latter explicitly loads a
snapshot successfully. Both fail on SYNC_OBSERVE with post-fault SETUP. An
earlier stderr fault and both reports have appl_ptr minus accepted epoch count
of 384 frames. Cause remains unknown; the 59.897-calls/sec interval is not
sustained clean-play acceptance. See [return](docs/snes-mvp-1.11-return.md).

Add a 96-entry in-memory native PCM transaction history and capture it before
cleanup on the first sticky fault. Read the kernel ring through read-only
SYS_syslog READ_ALL, with explicit unsupported/permission errors. The wrapper
clears stale history and preserves the fresh file before child exit. No healthy
transfer formatting, kernel-log reads or SD writes; timestamp/memory overhead
is not physically measured. Keep the exact core, parameters, reserve and
controller. This is a diagnostic build, not a claimed fix.

ARM recorder/owner/native lifecycle, wrapper persistence and existing runtime
checks pass; unchanged core exact-output checks pass. Guard consumed-1.11
installation, archive first and independently read back all protected files.
Physical capture, stream stability and full-speed sound remain pending.
See [capture contract](docs/snes-mvp-1.12.md).

Installation completes at 2026-10-06 04:13 UTC (October 5 in America/Chicago)
after a fresh 43-MVP/49-lab archive. Independent readback verifies the qualified
1.12 payload, all 22 current private files including the changed SRAM backup,
all 49 lab files and unchanged core/stock/hook/original snapshots/older wrapper.
Game one-shot is armed; lab remains unarmed. Physical capture is pending.

## SNES MVP1.11 coherent PCM observations and resume — 2026-10-05

Archive the consumed 1.10 return: 43 MVP/49 lab files, exact release bytes,
19 unchanged prior game-progress files and updated FF6 SRAM retained. Both
attempts start native playback, then WRITEI fails with EBADFD after 72/605 calls.
The queue-overflow label was false; software high is 2823/8192. One pause and
re-priming survive; snapshot success was not explicitly logged. Stock fallback
follows library B exit/cleanup. dmesg is absent; vendor state-transition cause
and earlier whole-device poweroffs remain unproved.

Paced admission now waits for the worker's fresh generation. The exact shipped
owner fails a deterministic changed-device counterexample; the repair passes.
Read post-HWSYNC state/control using SYNC_PTR GET flags and negotiated-boundary
arithmetic. Retain fresh post-WRITEI-fault state and accepted counts per epoch.
Restore period readiness after drain/reset. Stop failed drains before snapshot
work; distinguish worker errors from true queue capacity faults. Add snapshot
load/rejection counters and RAM phase markers. Keep the same core, full drawing,
64ms priming and rate/period/buffer candidates; no silent stream recovery.

Actual ARM client/owner checks and the real FF6 native lifecycle fixture pass:
injected WRITEI failure, clean retry, two snapshot loads/re-primes, 25ms producer
stalls, 120 full drawings and exact successful PCM accounting. Existing
input/splash/display/save/final-runtime checks remain. QEMU is not handheld
performance evidence. Guard consumed 1.10 installation, archive before writes,
retain all returned progress and independently read back before publication.
See [repair](docs/snes-mvp-1.11.md) and [return](docs/snes-mvp-1.10-return.md).

Installation completes after another verified 43-MVP/49-lab archive. Independent
readback verifies the exact 1.11 payload, all 22 current private files including
the returned updated SRAM, all 49 lab files, original snapshots and unchanged
core/stock/hook/older-wrapper hashes. Game one-shot is armed; lab remains
unarmed. Physical playback, snapshot resume, speed and stability are pending.

## SNES MVP1.10 PCM startup repair — 2026-10-05

Archive the consumed 1.9 return before updates: 43 MVP and 49 lab files,
exact released payload and 18 unchanged previously protected game-progress
files. Native PCM accepts 44,100Hz/128-period/3,712-buffer and all 2,823 priming
frames, then EBADFD prevents emulation. The failed operation and after-write
state were not retained; no game performance or hardware limit is measured.

Repair the client assumption that an accepted priming write leaves PREPARED.
Use the priming threshold, acknowledge RUNNING after full priming, START only
from PREPARED, and verify RUNNING afterward. Accept EBADFD only with a fresh
RUNNING observation. Retain operation, errno, state, availability and pointers
even on failure, plus running-stream playable minima. Preserve accepted-frame
accounting, visible XRUN and the exact 1.9 core. Replace byte-tail logging with
bounded shell-builtin runtime/kernel capture and test with tail/head/sed absent.

Independent ARM fixtures cover write-driven startup, healthy explicit START,
verified EBADFD race, rejected early/nonrunning starts and SW_PARAMS mismatch.
Final runner/owner/ownership checks and 1,200 exact core-output frames pass.
Source/check hashes gate the guarded consumed-1.9 update and independent
readback. Physical startup/audio/full-speed/stability and prior whole-device
poweroffs remain unqualified. See [repair](docs/snes-mvp-1.10.md) and
[return](docs/snes-mvp-1.9-return.md).

Installation completes after a fresh 43-MVP/49-lab archive. Independent readback
verifies the exact 1.10 payload, all 22 current private files, 49 lab files and
unchanged core/stock/hook/original-wrapper hashes. No snapshot migration or core
replacement occurs. Game one-shot is armed; lab remains unarmed. Physical
startup, playback, speed and stability are pending.

## SNES MVP1.9 native PCM owner — 2026-10-05

Implement documented ARM32 native PCM negotiation/readback, explicit playable
priming/START, STATUS/XRUN observation, SYNC_PTR readiness thresholds and bounded
DRAIN. One owner holds software/transfer/device accounting; device consumption
and eventfd notifications replace the game's intended1ms polling and separate
deadline gate. Prefer native32040Hz and bypass userspace conversion when accepted;
retain continuous conversion for a negotiated rate mismatch. Preserve every
drawing, the A7 renderer and proven UI/input/splash/display contracts.

Publish already-finalized/mixed Plus PCM at existing in-frame APU callback points
without changing emulation order. Exact1200-frame pixels/nativePCM/geometry/state
checks pass;1196 frames split identical PCM into earlier batches. Final runtime
passes180/30-frame mock runs, snapshot/SRAM and actual ownership/lifecycle seams.
Independent ARM fixtures cover constrained settings, partial/EAGAIN, START
failure after acceptance, XRUN, consumption-driven admission,30ms bursts, false
readiness, fixed admission deadlines, blocked cancellation and bounded flush.
Visible failure replaces silent stream recovery; physical sound/speed/stability
and the prior poweroff cause remain unqualified.

Add exact Lab2-return updater, archive-first/save-preserving deployment,
independent card readback and immutable selected publication with source/check
hashes. Keep vendor/core dependencies and all private progress local. Record
the wider hardware goal in a capability/cost/ownership roadmap; smooth FF6 is
not proof that the hardware is exhausted. See [1.9](docs/snes-mvp-1.9.md) and
[hardware roadmap](docs/hardware-capability-roadmap.md).

Install and arm after a fresh41-MVP/49-lab archive. Independent readback verifies
exact1.9 payload,20 original private entries,49 retained lab files, a separate
qualified snapshot and unchanged stock/hook/older-wrapper hashes. Lab remains
unarmed; following reboot takes stock after the consumed game one-shot.
Physical acceptance is pending.

## Lab2 physical return and source-first interface review — 2026-10-05

Archive and independently verify 41 MVP/49 lab files, the exact lab2 payload,
20 protected private entries and unchanged stock/hook/dispatcher/game paths.
Both one-shots consumed; zero card writes, no new build or re-arm. User reports
clicks between tests and some clicking during tests. Wrapper exits normally.

Retain all 1152 timer observations, nine audio traces, four 240-drawing producer
traces and 10712 driver calls with zero trace drops. Every short timeout method
averages about 10ms across load/slack settings; audio readiness can wake sooner.
All PCM targets are accepted, but accepted bytes and zero GETODELAY do not prove
complete playback. Bursty production exceeds nominal playable reserve; preserve
gap indicators as risks rather than measured xruns. All 973 scaler statuses are
FRAME_DONE|BUF_A_DONE: the suspected ten-sleep fallback never fires. Scaler
lifecycle means 2.26–2.29ms, with about 0.36–0.37ms in nonwait syscall brackets;
worker waits overlap production and are not serial core CPU costs.

Research Linux 4.19 OSS/native PCM and a pinned TinyALSA client. Document partial
fragment staging, POST versus SYNC/RESET, native parameter negotiation, priming,
device-driven refill, stream state and graceful drain. Identify split accounting
and multiple timing gates in current game source. ARM clients need the standard
SYNC_PTR path rather than assuming x86-style mapped status/control records.
Distinguish this source fact from vendor qualification. Matching Generalplus
sources remain unlocated; distinguish that search limit from hardware capability.
Propose one native PCM owner and publication of already-emulated audio during
long core calls before the next actual game acceptance. Extend the analyzer with
drain residues, nominal lead gaps and matched scaler lifecycles; independent
hand-calculated fixtures pass. Publish curated data with hash provenance.
See [return](docs/platform-lab-2-return.md) and [research](docs/platform-interface-research.md).

## Lab2 infrastructure contracts — 2026-10-05

Build the authorized next native probe around independently timed waits,
inherited/reduced/restored thread timer slack, OSS capability/readiness/drain/
reset behavior, actual32040/44100Hz streams, heap/chunk memory costs and coherent
audio admission under12ms steady/28ms occasional CPU work. Preserve every
synthetic drawing and PCM byte; native game performance is still unqualified.

Recover exact scaler/display ioctl sites and argument shapes from the pinned
driver. Command0x80045004 receives scalar3000 despite read-direction encoding;
status tests bit2 and its not-done path performs ten sleeps without rechecking.
Record real config addresses/queue flags, bitmap addresses, status and per-call
cost through exported syscall observers. No additional scaler command, hardware
queue, frequency, MMIO, scheduler-priority or watchdog change.

Actual ARM tests cover independent PCM bytes under odd shorts/EAGAIN/misleading
readiness, RTLD_LOCAL driver interception, timer slack restoration, sparse shell
splash/one-shot recovery and supervised TERM/KILL/reap. Draw readable labels at
their real resolution and ramp/drain tones. Bounded RAM traces persist as separate
phase batches. Add guarded lab1-to-lab2 updater, analyzer and hand-calculated
analysis fixtures. See [scope and boundaries](docs/platform-lab2.md).

Install and arm the isolated lab2 after a fresh41-MVP/17-lab archive. Independent
readback verifies both one-shots, exact released payload,13 retained lab files,
20 protected private entries and unchanged stock/hook/dispatcher/game/original
wrapper hashes. Physical test remains pending; no game performance claim.

## Hardware lab1 physical return — 2026-10-04

Completes and returns to stock; user reports clicks between tests and poor text
readability. Archive41 MVP plus17 lab files read-only, preserving20 private
entries and exact stock/hook/game/core/original-wrapper hashes. Markers consumed;
no card writes, replacement build or re-arm. Publish selected raw/derived data.

All four display phases complete240/240 jobs, including12ms CPU load at59.91
producer calls/sec. Audio samples retain34.83–46.44ms of negotiated-rate lead,
with zero write/query errors and~22.9ms maximum write gaps. This synthetic load
does not prove full-speed FF6 or resolve prior shutdowns. NEON beats scalar~2.5x
in the fixture; this color cache loses43–127% against NEON. CPU slicing gives
no clear benefit.5ms deadline lateness averages5.482ms, making intended1ms
poll sleeps suspect; timer quantum/config/slack remain unqualified.

Retain negative GETOSPACE; correct unqualified modulo-2^32 cursor analysis.
Add independently calculated staging/error/reset fixtures and returned-bundle/
private-preservation verification. Explain OSS non-mmap staging/block semantics,
UI downsampling and tone-reset boundaries; name the timer/consumption probe and
controller/PCM-publication/compact-kernel work next. See [return](docs/platform-lab-1-return.md).

## Hardware lab1 and custom-code investigation — 2026-10-04

Ben authorizes a bounded native test program to discover useful system behavior.
Build a separate A7/OSS/display lab with the qualified splash/GPIO/kernel-clock/
chunk ownership seams. Price scalar/NEON/generation-tagged tile color caching
under reuse/churn/thrashing; retain every draw's current compositing semantics.
Record raw OSS negotiation/queue/pointer/errors and service gaps with one writer/
observer, then exercise audio/display with equal12ms burst/sliced CPU budgets.
Buffer samples in RAM and fsync identified phase results outside timing.

Add whole-run60s supervision, TERM/KILL/reap, blocked-owner exclusion and reboot
hold after forced termination. Pass12,300 exact kernel cases, byte-granular
hostile transport, actual ARM null smoke/stuck-child checks, old-glibc ABI and
sparse-PATH wrapper/splash/one-shot cases. Add guarded archive-first installer,
read-only collector, analyzer and custom-code proposals. No full-speed or
physical stability claim; hardware test is pending. Install/arm only the
isolated lab after a39-file read-only archive; preserve20 private entries plus
stock, boot hook, game runner/core and original wrapper hashes. See [lab1](docs/platform-lab.md).

## MVP1.8 physical return and diagnostic repair — 2026-10-04

Played okay but clicking returned, followed by confirmed whole-device power-off.
Archive and verify39 files read-only; all19 pre-existing private files and
stock/hook hashes are intact. Exact returned release matches. Card unarmed.
Fresh previous checkpoint has1,648 calls, zero holds, ~57.93 active-loop calls/sec,
13.33ms mean core wall and3.00ms audio-lead wait per call. PCM accounting balances,
but device queue sampled empty and maximum accepted-write gap is40.004ms.
Shutdown cause and uninterrupted sound remain unproven; empty latest/tails and
stale1.7 final totals are explicit collection limits.

Correct the unsupported sed assumption: firmware lacks both head and sed.
Use shell builtins for line limits and splash zombie parsing; the actual wrapper
passes with both absent and no gameplay global sync. Source only, not installed.
Exact returned core passes10,000 visible-pixel/native-PCM/state equivalence
frames. Extend the harness without breaking device glibc2.30 compatibility.
Guard historical1.8 publication against changed qualified input bytes before
any writes; publish curated return and checks, retaining all historical hashes.
Document recovered factory poweroff path without claiming it fired. Next work
is bounded audio-headroom production and durable targeted crash records, with
full drawing retained. See [return review](docs/snes-mvp-1.8-return.md).

## SNES MVP1.8 forward A7 build — 2026-10-04

User directs a smarter A7 build instead of another device comparison. Specialize
seven NEON tile modes in emitted code, deinterleave palettes once per tile,
skip disabled/fixed-only color work and unused full math in half-blend rows,
and directly store fully covered spans. Add NEON backdrop/color-window passes
with original scalar tails. Catch/fix reversed-clip unsigned underflow at FF6
intro frame87 before deployment; exact pixels, native PCM and state now pass.

Retain O2, accurate Blargg sound, full drawing and queue ownership. Replace
repeated process/kernel discovery and global sync during play with one capture
and small30-second checkpoints. Test actual sync calls and sparse firmware
PATH. Add60k span/canary cases, palette guard page and emitted-code checks to
the existing8.4M color/280k row/1200-frame output qualification. Version fresh
checkpoints1.8. Guard installation over unarmed1.7, archive first, preserve new
Save Point SRAM and add a separate older qualified snapshot. Publish owned
release/evidence with history intact. Installed/armed after preserving all19
existing private files plus stock/hook hashes. Physical speed/audio pending.
See [1.8](docs/snes-mvp-1.8.md).

## MVP1.7 physical return — 2026-10-04

No crash; user reached a Save Point, saved and exited normally. Lag remains;
FF6's party menu helps partially. Archive/hash-verify 38 files with zero card
writes, preserving newly changed SRAM and backup. Marker consumed; card stays
unarmed. Exact release/core and stock hashes match. Fresh final/checkpoint
identities agree; main rc=0, display join and cleanup survive.

Record 7,068 rendered calls with zero holds, 129.381 seconds active loop,
54.629 calls/sec (91.17% native), mean core wall15.384ms/CPU13.986ms,
p95[21,22)ms, p99[35,36)ms and 31.084% definitely over budget. All generated
PCM plus priming accepted, but sampled empty device queue and71.280ms maximum
write gap leave starvation risk. Price producer display wait0.736ms and
audio-lead wait1.876ms per call without double-counting overlapping worker wall
or treating all throttling as recoverable cost. Add observed-loop analysis
with explicit timing limits.

Capture/sync windows average234.4ms; system CPU/meminfo/IRQ collection failed
because the firmware has no head command. Replace it with qualified sed in
source; test the actual wrapper with a restricted PATH lacking head and verify
CPU/memory contents. Keep released/installed1.7 bytes unchanged and guard its
exporter against replacement. Publish selected return evidence; private
SRAM/states remain local. No new runtime installed or test armed. See the
[return review](docs/snes-mvp-1.7-return.md) for remaining evidence gaps and next work.

## SNES MVP1.7 logging retry — 2026-10-04

After the failed 1.6 run, the user confirms stock boot and requests logging plus
another physical test. Retain the exact A7 core, full-render policy, UI and
audio/display pipeline. Add build/core/session identity, phases and coherent
progress checkpoints in RAM about once a second, outside core callbacks.
Include live audio-worker CPU, producer audio waits and existing core/display
metrics. Measure checkpoint duration and errors.

The wrapper persists the latest two progress records, three early thread
snapshots and a bounded latest thread/CPU/memory/interrupt/helper/kernel view.
Capture after two seconds, then five-second waits for 63 iterations; record
capture/sync duration and cancel/reap on child exit. This closes the end-only
report gap; sudden power loss may still lose the latest interval. Logging is
not a speed fix and may perturb timing.

Pass the full ARM/QEMU contract suite, a real-runner SIGKILL checkpoint check
and wrapper persistence while its child is alive. Archive/hash-verify the
returned card before updating. Install only owned runner/wrapper/test notes;
retain all 19 pre-install private progress files, core, boot hook and stock
binaries by hashes. Arm the one-shot last. Publish owned release and selected
verification without game/save/vendor files; retain historical 1.5/1.6 releases.
Physical result pending. See [test and evidence boundaries](docs/snes-mvp-1.7.md).

## MVP1.6 physical failure — 2026-10-04

The user reports very choppy sound, slow movement, good-looking graphics and
then whole-device power-off. Archive and hash-verify 33 returned files before
mutation. Launcher/core/wrapper match the installed release; stock binaries and
all 18 original progress files match the protected originals. The one-shot is
consumed; this return performs no card writes or re-arm.

Startup/splash/input and early runtime snapshots survive, but no child-exit
record or fresh 1.6 session report does. The retained last-session file is
byte-identical to 1.5 and must not be analyzed as this run. Early RSS is about
12 MiB with zero reported process swap; these samples do not identify the
shutdown mechanism or establish full-session memory/performance. Withdraw 1.6
from unchanged retesting, record the failed expectation, and require durable
session telemetry plus a controlled original/A7 hardware comparison before
another performance claim. Add actual-core validation to the report analyzer;
API/CLI checks preserve analysis for the original core and reject this stale
report for A7 without writing output. See [failure review](docs/snes-mvp-1.6-failure.md).

## SNES MVP1.6 — 2026-10-04

Implement A7 NEON 2/4bpp tile/color kernels and audio-first delivery in pinned
Plus. Remove adaptive drawing holds. Add a three-source ordered display FIFO
with buffer/publication reservation before the core and source release before
scanout. Add independent joined PCM service, partial/EAGAIN preservation,
transition-clear accounting, bounded lead and worker/device timing. Retain
accurate Blargg, the validated splash/GPIO/clock path and the known scaler backend.

Verify 8.4 million color comparisons, 280k rows, 1,200 exact pixel/native-PCM frames
and normalized emulated state; actual migrated-state runner resume for 120 frames;
full-render smoke for 180 frames and paced smoke for 30; real FIFO backpressure/teardown and legacy
contracts. Raw snapshots contain process pointers, now explicitly accounted
for in comparison. Install isolated core and separate FF6 snapshot copy; stock,
boot hook and 18 original progress files hash-protected. One-shot armed.
Physical 60 FPS/audio result remains pending. See [implementation](docs/snes-mvp-1.6.md).

## MVP 1.5 physical result and full-speed proposal — 2026-10-04

Physically confirm all four directions in launcher and FF6. Archive/hash-verify
returned logs and all private progress before any update; the card remains
unarmed and unchanged. Returned 23,872 calls with 2,826 held drawings (11.838%),
core-call mean wall14.591ms/CPU13.230ms, p95[19,20)ms and maximum40.844ms.
User reports occasional lag and rare random normal-play crackles. Zero write
errors and sampled nonempty queues do not establish zero playback underruns.

Publish the return analysis and a proposal combining ordered display queuing,
source release before scanout, audio delivery independent of video waits, one
pacing owner, and exact Cortex-A7 NEON tile/color kernels in Plus. Record the
recovered scaler fallback's unchecked sleeps and DSP arithmetic constraints.
This entry adds evidence/docs/collection tooling; no runtime/core behavior is
changed or new device test armed.

## SNES MVP 1.5 — 2026-10-04

Correct the shared physical D-pad map to GPIO200 Up, GPIO201 Down, GPIO202 Left, GPIO203 Right. The previous interpretation of native 10/40/80/20 masks was wrong. Regression expectations now come from the pinned stock executable's actual libretro mask table, with an independent Down+Left check. All ARM checks pass; the subsequent return physically confirms the correction. Original/private progress and production binaries remain unchanged during installation.

## SNES MVP 1.4 — 2026-10-04

Replace libc-clock absolute waits with direct kernel timing and relative remaining-duration sleeps. Keep menu repeats, logs, heartbeat and game deadlines on that clock. Captured hardware clocks later read kernel monotonic/boottime 8.361 seconds versus libc monotonic 447.327 seconds. **Device confirmed:** launcher operation, game start and save-state load. D-pad labels still incorrect. Returned report: 2,465 frames, two pauses, no audio-write errors.

## SNES MVP 1.3 — 2026-10-04

Add bounded input/exit/cleanup and runtime evidence. Preserve the stock shared heartbeat. Input remained dead: snapshots caught the main thread in the same absolute sleep six seconds apart. The D-pad change introduced an incorrect direction permutation and is superseded by 1.5. The autonomous /wdt helper was not shown to depend on our heartbeat.

## SNES MVP 1.2 — 2026-10-04

Complete the stock showlogo marker handshake before opening the MVP display. Device logs confirm splash exit and acknowledgment. Input still failed; readiness alone did not prove a functioning UI.

## SNES MVP 1.1 — 2026-10-04

Remove unbounded wait-for-all-buttons-released before the first frame. Independently suppress initially held keys. Add durable bring-up logging and bounded startup timeout. Device reached READY but the still-running splash replaced the UI.

## SNES MVP 1.0 — 2026-10-04

Initial SNES library, direct Plus runner, chunk-backed display worker, OSS audio, private SRAM/snapshots and simple pause UI. Local checks passed; the first handheld test stayed on the loading animation.

## Earlier adapter and hardware work

v11 retained adaptive internal drawing suppression and removed automatic diagnostic overhead. A v10 physical listening test was clean. v9 showed heavy full-render core calls missing the frame budget; rendering-disabled calls were much cheaper. Hardware v1/v2 established platform/ABI/runtime details. Hardware v3 showed stdout/stderr suppression did not materially reduce the UART interrupt storm or comparable CPU load. See [investigation history](docs/investigation-history.md).

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
