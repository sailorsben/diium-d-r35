# Changelog

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
