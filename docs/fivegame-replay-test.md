# Five-game matched test with visible Star Fox replay — 2026-10-17

The user authorizes the matched physical test for all five games, preserving the
verified kernel UART fix, saves and evidence, with no full backup, and fixing
the Star Fox test segment before arming. Both previous physical attempts stopped
in Star Fox's silent 8,656-call replay while the preceding F-Zero picture remained
visible. Their lack of a replay call count could not distinguish slow progress
from a stall. This profile supersedes unchanged rearming of those attempts.

## Replay correction

Star Fox now shows a clear **STAR FOX - COLD REPLAY** notice and completed-call
count from 0 toward 8,656. Updates occur about every two seconds, checked at
the same 64-call boundaries as the existing abort polling. The exact core, cold
input sequence and every emulated video/audio quantum remain intact. No GSU
snapshot is introduced and no emulated calls are skipped. Replay audio callbacks
are still discarded before native PCM opens.

`warmup.txt` is written at start, bounded progress checkpoints and every return
path, including explicit menu/signal abort, malformed/missing input and display/
write failure. The card record is a single bounded current-progress file,
written atomically by the existing durable save helper. It is not per-frame
SD logging and does not enter a measured gameplay window. At most 138 records
can be written per 8,656-call replay, including start/final records.

A small shared mapping lets the owned parent supervisor see the last completed
call and epoch without reading the SD card. If an active replay makes no forward
progress for 60 seconds, the supervisor terminates/reaps its own child and records
the exact observed call count, epoch, active/stall flags and stop reason. The
existing forced-exit safety barrier withholds immediate stock takeover; a reboot
is then needed and the consumed markers make that reboot stock. Advancing replay
is not censored simply for taking more than 60 seconds. The original 35-minute
whole-suite hard deadline remains unchanged.

The progress surface is an owned 640×480 RGB565 allocation copied through the
existing chunk-backed board queue. It is drained before the surface is freed;
board display/worker metrics reset before native audio and measured gameplay.
Warmup returns always restore callbacks and clear scripted buttons. Progress UI
cannot contribute to the 1,200 measured rendered/submitted/flipped counts.

## Matched experiment and evidence boundary

| Game | Scene and starting path | Measured windows |
|---|---|---:|
| Super Mario World, PAL backup | Yoshi Island 2 qualified checkpoint | 4 × 1,200 calls |
| Super Metroid | Ceres qualified checkpoint | 4 × 1,200 calls |
| F-Zero | Starting grid into racing checkpoint | 4 × 1,200 calls |
| Star Fox | 8,656 cold calls into Corneria before each window | 4 × 1,200 calls |
| Rendering Ranger R2 | Stage 1 qualified checkpoint | 4 × 1,200 calls |

Core SHA256 remains
`d7988b2861500eb923b827ad412c14ae841c03dd44e4099f2616a637bf88f62a`.
All 23 frozen payloads, including core, plan, five ROMs, checkpoints, input scripts,
expected pixel/PCM/sample-count oracles and passive UART observer, are byte-exact
to the previous kernel-UART test. Game order still reverses on alternating passes
and each game receives blocking/candidate/candidate/blocking (ABBA): 20 windows,
24,000 measured calls and 34,624 additional Star Fox replay calls. Both arms use
the same rebuilt controller and core; this is a presentation-policy comparison.

This is measurement-only, not emulator promotion. **Measured A7 saving and
remaining native-audio deficit for this rebuilt controller are MISSING.** The
visible notice/SD checkpoints cost time only during cold replay; the temporary
614,400-byte notice surface is freed and drained before measurement. A shared
mapping and supervisor progress checks add a small unpriced common cost. Existing
Ranger synchronization and SuperFX full-layout callback-copy costs remain common.
Do not compare old-controller timing prefixes as if the controller were unchanged.

Break-even still requires measured main/audio/video CPU plus nonoverlapped device
service within the game's native period, valid positive cumulative PCM reserve,
full accounting and safe teardown. The conservative 20% target remains
0.8 × native period. Work counts or skipped presentations are not A7 CPU savings.
A censored or failed window cannot pass. Only a completed physical return can
qualify bounded windows; optical/speaker/live-input acceptance remains separate.

## Qualification

- The actual rebuilt ARM controller passes all 20 oracle epochs: 24,000 exact
  original gameplay pixel/PCM/sample-count comparisons and 34,624 cold calls.
  All mock windows retain 1,200 measured render/submission identities; mock
  telemetry is explicitly rejected as physical proof by the return analyzer.
- Both native consuming-provider policies pass with the exact rebuilt runner:
  busy-credit behavior, 40 intentional skips, fault/retry/drain/full-history
  accounting and sustained-deficit rejection. This is a software provider fixture,
  not all-five-game hardware audio acceptance.
- Nine replay/supervisor fixtures execute the actual header and actual parent:
  completion, menu/signal abort, invalid/missing script, display failure,
  progressing replay, stalled replay and clean child abort. The stall fixture
  uses 300 ms instead of production 60 s and confirms last call 123, reason,
  forced exit and owned-child reaping. Real UI pixels were emitted and inspected.
- Exact firmware BusyBox syntax and eight wrapper cases pass: normal/replay,
  old endpoint, loaded module, observer failures, active splash, crash/forced
  barriers. Ten installer cases cover success, write/FAT rollback boundaries,
  foreign profile/marker and firmware-trigger refusal.
- ARM ABI remains firmware glibc ≤2.30 with explicit 32-bit time. An initial
  supervisor-only fixture omitted that time ABI and falsely expired its deadline;
  matching production flags fixed the fixture. Its C23 `strtoul` binding was also
  changed to the firmware's legacy symbol. Production already used time32.
- The first host wrapper stub left a space-containing redirection path unquoted.
  Its owned eight-byte `executed` file was identified by contents and creation
  time and removed; the stub now quotes the path. The completed controller,
  source, oracle and native proof hashes were retained and revalidated while
  only wrapper fixtures were rerun. No card write occurred during these failures.

[Controller qualification](../evidence/2026-10-17/fivegame-replay/qualification.json) ·
[Replay fixtures](../evidence/2026-10-17/fivegame-replay/replay-checks.json) ·
[Installer fixtures](../evidence/2026-10-17/fivegame-replay/installation-qualification.json).

## Preservation and arming

Fresh sparse archive `uart-kernel-return-20261017T102454234198Z` hashes 1,643
existing files, stores zero new content bytes and passes clean FAT. No full
backup. The existing single host rollback baseline is reused. Static private
core/ROM/fixture bytes are hard-linked between host packages rather than copied.
All unique physical returns and save generations remain preserved.

The target is a fresh `retro/snes-fivegame-kernel2`. The only existing card file
changed is `retro/snes-mvp/launch.sh`; the previous exact dispatcher is already
available as `releases/snes-mvp-1.19/launch.sh`, hash
`35b1c32fa5924e33a0f1da47833b6710e53dadc5ebd832a6b998a86236e2cc13`.
Normal init, kernel UART boot state, stock binaries, ADC/settings, every save and
all earlier evidence are protected by complete hashes. The exact fresh physical
kernel verification receipt is a staging gate. No firmware trigger or module
loader is installed. Payload/FAT checks precede activation; both owned markers
are armed last. Failures remove owned markers and restore the dispatcher after
a healthy-FAT gate. Independent final checking verifies the full exact card file
set, all protected hashes, payloads, both markers, normal init and clean FAT.

[Installation](../evidence/2026-10-17/fivegame-replay/installation.json) ·
[Independent card check](../evidence/2026-10-17/fivegame-replay/live-verification.json).
These receipts establish staging completion; physical results remain pending.

## Physical procedure and return

Safely eject I:, insert with the handheld off, keep charging power connected and
cold boot once. The five-game sequence runs automatically. Star Fox will show
the replay counter before each of its four gameplay windows. Do not press
Select+Start unless intentionally aborting. Allow up to the 35-minute whole-suite
deadline. If the counter stops advancing for 60 seconds, expect the supervisor
to record the stall and require a reboot rather than an unsafe immediate stock
takeover. Do not reflash or repeat the test.

When stock returns, shut down normally and reconnect I:. If stock has not returned
by 35 minutes or a reboot-required message occurs, power off and return I: for
partial evidence collection. Consumed markers make the next boot stock.

Collect sparsely before changes, then use
`python build/report-fivegame-replay.py <archive>` for this exact profile. The
report binds the new payload/marker/plan identities, excludes mock telemetry and
stale pre-measurement buffers, records each Star Fox replay result and supervisor
call/abort/stall evidence, and retains the existing native/CPU/video acceptance
checks. Require all 20 complete windows, matched pairs, valid full PCM histories,
joined workers/idle display and safe reaping before any bounded-playability claim.
Analyze before/after passive UART windows separately from emulator performance.
