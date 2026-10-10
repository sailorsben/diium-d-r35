# Investigation history and negative results

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
