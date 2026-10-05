# Changelog

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
