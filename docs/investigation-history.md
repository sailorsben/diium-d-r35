# Investigation history and negative results

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
