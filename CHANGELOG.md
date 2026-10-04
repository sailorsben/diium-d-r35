# Changelog

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
