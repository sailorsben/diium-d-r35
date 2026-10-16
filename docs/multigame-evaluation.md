# Five-game evaluation — 2026-10-16

**Superseded by the [corrected five-game gameplay rerun](five-gameplay-fixes.md).**
The failures below are preserved as the initial negative evidence.

**Do not call the whole emulator fixed yet.** Retain the verified UART,
diagnostic shutdown and bounded FFVI presentation-recovery fixes. The broader
game test finds a Rendering Ranger black-screen blocker and an unresolved
Star Fox state-comparison failure. It also exposes gaps in gameplay coverage.

Ben requested Super Mario World, Super Metroid, F-Zero, Star Fox and Rendering
Ranger from the retained backup. All five were found in `E:\R35\002`; their ZIP
and extracted ROM hashes are bound in the [public review](../evidence/2026-10-16/multigame/review.json).
The original ZIPs still hash identically after testing. No card was accessed,
installed, armed or written; no full backup was created. Existing saves and
evidence remain untouched. Extracted ROMs, captured images and raw logs stay
private and are excluded from Git.

## Candidate and tests

“Best model” here means the exact demand-visible-v3 ARM core used in the
returned FFVI presentation test:
`1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8`.
Its compatible presentation gameplay runner is separately tested under both
policies. The earlier common-band ARM core is the regression reference; it is
not an independent original-console accuracy oracle.

`build/check-multigame.py` extracts only these five private ROMs. Its ARM
harness cold-boots two independently loaded cores with identical scripted
buttons. The planned window is 6000 emulated refreshes per game. Every call
compares full visible pixel bytes, PCM sample bytes/count and geometry; every
30th call compares serialized state with only the established named host
pointers normalized. Output acquisition cycles through two accepted-target
requests and a no-acquisition fallback request. Both accepted requests use the
same aligned guarded heap allocation: the core sees the same ABI for a direct
or scratch target. This test does not establish separate buffer ownership.
Canary bytes
outside the documented writable prefix/tail are checked. This exercises core
output semantics, not physical display-worker contention or presentation loss.

`build/check-multigame-runner.py` also runs the exact qualified presentation
gameplay executable for 600 cold-boot calls per game per policy: ten cells,
6000 calls total. All pass mock-board frontend/core/software PCM accounting,
600 renders/presentations per cell, no errors, no remaining/cleared audio and
accepted = enqueued + prime. They do not exercise native ALSA or real scanout.

## Observed results

| Backup copy | Core refresh Hz | Strict comparison | Inspected scene coverage |
| --- | ---: | --- | --- |
| Super Mario World | 50.319739654 | 6000 calls pass | Title, welcome, Yoshi's House, overworld; ordinary course not established |
| Super Metroid, backup labeled Chinese translation | 59.922743404 | 6000 calls pass | Opening narrative/flashbacks; controllable Ceres/Zebes not established |
| F-Zero | 59.922743404 | 6000 calls pass | Menus, race, crash and you-lost; sustained successful racing not established |
| Star Fox | 59.922743404 | Stops at state comparison frame150 | Boot prefix; gameplay not established |
| Rendering Ranger R2 | 59.922743404 | 6000 calls match reference | Black at inspected checkpoints599–5999; no playable boot |

The four completed windows give 24,000 per-frame output comparisons and 800
periodic state comparisons. Star Fox retains 150 recorded matching frames;
output at frame150 also matches, but that frame's state does not. No failed
window is promoted from its valid prefix. All three acquisition request paths
occur 2000 times per completed window; requests are not proof that every game
mode admits compact direct output.

The Mario copy has header region2 and reports about50.32 Hz; the runner reads
the core's native timing instead of imposing a60 Hz simulation. Metroid is
the copy labeled as translated in the backup, not a certified unmodified
regional release. Reported timing and exact hashes identify what was tested.

Rendering Ranger has matching internal checksum/complement and declared
2 MiB size; those checks alone are not independent known-good ROM validation.
Matching black output is explicitly **not** a successful boot/playability test.
A single-instance run of the older `plus-a7-out/plus-a7.so`,600 neutral calls
then600 held-Start calls, also produces an inspected black final image. Thus
the black screen is not established as specific to the new output policy.
Its cause remains unresolved: isolate the ROM/core boot behavior against an
independent known-working implementation before changing scheduling.

Star Fox differs at serialized offsets347957–347958, inside FillRAM at
0x4325/0x4326, DMA channel2 transfer-size registers. Two separately loaded
copies of the identical candidate reproduce a frame150 divergence at those
same offsets while pixels/PCM still match. Therefore this is not evidence of
an optimization-specific regression. It remains a failed strict determinism
check. These are emulated registers, not named host pointers; do not erase
them in normalization merely to obtain a pass. The existing serialization
routine also does not include the SuperFX internal GSU structure; save/restore
coverage for this game must be explicitly established before release claims.

Initial harness-only failures are retained privately: a guard incorrectly
included the core's documented writable32-byte prefix, and loading an initial
serialized reference state into only the candidate produced immediate state
differences. The accepted harness uses independent cold boots, as the prior
equivalence tests do, and guards only outside the ABI region. Neither initial
attempt counts as a game regression or pass. Initial compile/toolchain errors
also do not contribute to game results. No emulator sources were changed.

## What this says about refresh, rendering and “fixed”

The proposed distinction is useful, but the current fix only skips
**presentation** when display credit is unavailable. It still executes every
emulated refresh, renders its pixels and generates its audio. A game's repeated
pictures do not automatically make CPU/PPU emulation optional. Skipping PPU
rendering is a separate candidate requiring its own pixel/state/timing checks.

The scripted runs record adjacent pixel-picture changes: Mario2562,
Metroid2280, F-Zero4777, Ranger30, and Star Fox0 in its150 recorded calls.
Those counts include titles, dialogue, black screens, transitions and losing
screens. They are **not** per-game native FPS estimates or evidence that most
games could safely run at30 emulation ticks. None is an A7 timing measurement.

The FFVI physical result remains good evidence for one specific fix: both48 ms
candidate windows complete all1200 renders/all seven bursts, while both
blocking controls fail. Candidate sampled reserve reaches5.374 ms, so that
result does not establish the earlier20% sustained headroom gate. Ben's “no
obvious issues” observation applies to that FFVI return, not to these games.

Recommended next work, in order:

1. Resolve Rendering Ranger boot and Star Fox determinism/save coverage. Keep
   both failures visible; do not change emulation rates to conceal them.
2. Establish repeatable player-controlled fixtures: an ordinary Mario course,
   Metroid gameplay beyond the prologue, a full F-Zero race, Star Fox combat,
   and Rendering Ranger gameplay with its demanding effects. Preserve input,
   ROM and starting-state identities and verify scenes visually.
3. Run matched physical blocking/candidate tests with permanent UART retained,
   using each ROM's reported timing. Proposed minimum:10 sustained minutes of
   actual gameplay per title, plus repeatable stress scenes, recording native
   CPU/deadline costs, complete PCM reserve/accounting and presentation cadence.
   Keep the existing20% headroom gate where measurable; characterize skip
   bursts rather than accepting a good average. Check real input, speaker,
   pause/resume, saves and stock return. Proposed duration is a next test plan,
   not a claim that it has run or is a universal compatibility certification.

The defensible present claim is: **specific UART and presentation-recovery
failures are fixed in measured tests; general SNES compatibility and sustained
handheld performance remain unqualified.**
