# DIIUM D-R35: device findings and SNES platform

Source, hardware investigation and a working SNES-only launcher/runtime prototype for one tested D-R35. This device runs **embedded Linux on a single Cortex-A7**, with limited RAM and vendor display/scaler interfaces. It is not an Android/RetroArch port.

The project replaces the launcher/runtime in userspace while retaining the working kernel and display driver. It also preserves the earlier SNES Plus adapter and diagnostic tools, so successful work and failed hypotheses remain reproducible.

## Current status — 2026-10-05

- **MVP1.13 durable diagnostic is installed and armed:** 1.12 fails after 1,106 calls and a successful snapshot load, again with SETUP and a 384-frame pointer/count discrepancy. Its final report survives but PCM history does not. 1.13 writes fault history directly to the card and synchronizes file/directory before error return, with explicit capture status. Playback remains unchanged. Independent readback verifies all 22 current private files, 49 lab files and stock/hook/core. Native failure cause, sustained sound and stability remain unresolved. [1.12 return](docs/snes-mvp-1.12-return.md), [1.13 capture](docs/snes-mvp-1.13.md).
- **Hardware confirmed:** MVP 1.5 boots into its library, starts Final Fantasy VI and loads the imported save state. All four directions work in the launcher and game.
- **Returned MVP 1.5:** 23,872 core calls, 2,826 held drawings (11.838%), no reported audio-write errors. The user heard rare random crackles in normal play and occasional lag. Full rendering and uninterrupted playback remain the target.
- **MVP1.6 failed its physical run:** very choppy sound, slow movement, clean-looking graphics, then the whole device powered off. The returned build hashes match; originals are intact and the one-shot is consumed. No fresh session totals survived. Do not re-arm this release unchanged. [Failure review](docs/snes-mvp-1.6-failure.md).
- **MVP1.7 returned without a crash:** reached a Save Point, saved and exited normally, but remained laggy; FF6's party menu helped partially. Fresh counters show 7,068 calls, zero holds, about 54.63 emulation calls/sec of active-loop time and 31.08% of calls definitely over budget. That return was archived read-only before updating; new SRAM is preserved. Missing `head` left diagnostic gaps, corrected and tested for1.8. [Return review](docs/snes-mvp-1.7-return.md).
- **MVP1.8 returned with clicking and whole-device power-off:** fresh checkpoint records1,648 calls, zero held drawings and about57.93 calls/sec of active-loop time. Saved progress and stock/hook hashes were intact and the returned card was unarmed. Shutdown cause remains unknown. Firmware also lacks `sed`; the capture fix passes without `head` or `sed` and is incorporated in1.9. The exact returned core passes10,000 output-equivalence frames. [Return review](docs/snes-mvp-1.8-return.md), [implementation](docs/snes-mvp-1.8.md).
- **Working reference:** v11 SNES Plus adapter in the vendor launcher. Intro/Narshe/wind listening tests were clean with adaptive internal drawing suppression.
- **Not established:** full rendering at all times, a measured speedup over v11, broad emulator compatibility, usable hardware GPU acceleration, or factory-card compatibility of the current installer.
- **Hardware lab1 returned successfully:** stock launcher resumed; all four display phases complete240/240 jobs, including a12ms CPU load, while audio remains buffered in samples. NEON wins the tile fixture; the experimental color cache loses.5ms deadlines average5.48ms late, making timer-polled pacing a concrete next target. Text readability and transition clicks are recorded. Its return was archived and its one-shot consumed. [Physical findings](docs/platform-lab-1-return.md), [scope](docs/platform-lab.md).
- **Lab2 returned complete, with clicks:** all nine PCM byte targets and all four 240-drawing phases complete, but the user hears clicks between and during tests. All short timeout methods average about 10ms despite timer-slack reduction; audio readiness wakes around 2.77ms in the smallest-fragment transport. Burst production exceeds the available playable reserve. All 973 scaler statuses contain FRAME_DONE; the ten-sleep fallback never runs. Archive verifies 41 MVP/49 lab files and 20 protected private entries. Card unarmed, zero writes. [Physical findings](docs/platform-lab-2-return.md).
- **Source research leads1.9:** Linux 4.19 OSS source exposes partial-fragment staging and explains why POST/zero-delay/RESET does not qualify complete tail playback. Native ALSA defines negotiation, priming, device-driven refill, stream-state observation and drain; its playback node exists on this device. That contract is now implemented with one coherent PCM owner. Exact vendor behavior and full-speed FF6 remain unqualified. [Interface research](docs/platform-interface-research.md).

## Start here

| Topic | Document |
|---|---|
| Hardware, OS, memory, clocks, display, audio, UART | [Device findings](docs/device-findings.md) |
| Splash handoff, GPIO map, clocks, ABI and lifecycle | [Boot and hardware contracts](docs/boot-and-hardware-contracts.md) |
| Source, dependencies, checks, installation and recovery | [Build and test](docs/build-and-test.md) |
| What each investigation proved or ruled out | [Investigation history](docs/investigation-history.md) |
| Runtime ownership and next engineering work | [Architecture](docs/architecture.md) |
| Current native PCM build and physical acceptance | [MVP1.13](docs/snes-mvp-1.13.md) |
| Hardware resources, measured costs and remaining opportunities | [Capability roadmap](docs/hardware-capability-roadmap.md) |
| Latest infrastructure result and researched audio contracts | [Lab2 return](docs/platform-lab-2-return.md), [interface research](docs/platform-interface-research.md) |
| Concrete Cortex-A7 core and pipeline proposal | [Full-speed SNES plan](docs/full-speed-snes-plan.md) |
| Forward A7 renderer implementation | [MVP1.8](docs/snes-mvp-1.8.md) |
| Latest game failures and evidence limits | [MVP1.12 return](docs/snes-mvp-1.12-return.md) |
| Logging retry implementation | [MVP1.7](docs/snes-mvp-1.7.md) |
| A7 full-render implementation and failed test | [MVP1.6](docs/snes-mvp-1.6.md), [failure review](docs/snes-mvp-1.6-failure.md) |
| Actual shipped emulator identities and limitations | [Core inventory](docs/core-inventory.md) |
| Evidence preservation and future changes | [Maintenance](docs/maintenance.md) |

The particularly expensive discoveries are written down explicitly: **finish the vendor splash handoff before opening a display; compare libc clocks with direct kernel clocks; translate GPIO through the stock input callback's mask table; retain DMA buffer ownership until completion.**

![Launcher UI preview](docs/assets/launcher.png)

Rendered UI preview; this is not a handheld photograph.

## Repository layout

- `build/snes-mvp/`: launcher, runner, UI, board backend, timing, state importer and checks.
- `build/`: current and historical adapter/probe source, analyzers, builders and guarded installers. Historical installers are not generic deployment tools.
- `evidence/`: selected returned logs, analysis, recovered ABI data and verification, with a provenance/hash manifest.
- `docs/reference/`: dated deeper hardware/runtime/core reviews. These are proposals or historical reviews where marked; current corrections in the guides take precedence.
- `releases/`: owned versioned ARM executables, wrappers and verification. Games, private saves, vendor driver/core/runtime libraries and full firmware backups are not included.

Only one hardware unit has been tested. Confirm the identity and software hashes of another unit before applying recovered private ABIs. A filename or identical product label does not establish matching firmware.

## Contributing

Preserve the known working path, make bounded changes, record physical results separately from QEMU checks, and update the relevant guide and changelog in the same commit as the fix. See [maintenance](docs/maintenance.md). Code and dependencies retain their own notices; see [NOTICE](NOTICE.md).
