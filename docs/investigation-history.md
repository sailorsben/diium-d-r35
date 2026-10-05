# Investigation history and negative results

This history preserves what changed, what was observed, and the inference boundary. It does not retroactively turn proposals into device results. Deeper dated reviews and selected raw returns are published under `docs/reference` and `evidence`.

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

The user reported Right→Down, Left→Right, Up→Up, Down→Right and repeated the duplicate-Right observation before1.5. The unlabelled raw traces cannot attribute each physical press independently. The stock callback establishes four distinct canonical directions; the1.5 physical return confirms all four. Do not silently edit the historical report to fit a neat permutation.

## Corrections that must survive future work

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
