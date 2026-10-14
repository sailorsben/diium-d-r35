# Automatic tests for unresolved demand-v3 effects

Prepared in response to “Put together a test for the spells that we haven't
fixed.” This is a ready local package, not an installed or armed test. I: remains
unarmed. Physical installation is a separate action through the guarded installer.

The last combined automatic return still failed both Meteor and Quasar. Its
other passing windows had limited margins, while demand-v3 has only the manual
opening-scene/Confuser result. Test all18 archived contexts on demand-v3 twice;
include unchanged common-band-v3 controls for Meteor and Quasar in opposite
orders. Confuser serves as a previously working control. This is40 epochs of
1,200 calls,48,000 total; nominal emulated duration13.35 minutes, roughly15–20
minutes allowing load/flush overhead. No late-game user progress is needed.

| Context group | Fixtures |
|---|---|
| Magic | Holy/Pearl, Meteor, Ultima, Meltdown, Slow2 |
| Summon/effect | Siren, Bahamut, Carbunkl, Quasar, Grandtrain, Terrato |
| Rage branches |004,005,032,086,088 |
| Magitek/control | Bio Blast, Confuser |

These are original archived state/input/expected-property fixtures. New private
state copies change only the core identity header; every emulated payload stays
exact. Conditional/random cases cover the recorded branch, not every branch.
The test automatically loads and replays each case, captures its observed effect
properties, and returns to stock when the suite ends. Select+Start aborts.
No frame omission, effect simplification, fast-forward or hidden audio reset.

## What is exercised and measured

The controller is a fresh copy of the qualified combined measurement runner.
It uses the actual owned-output board implementation, reserves source/FIFO
credit before acquiring the core buffer, and retains worker join/drain behavior.
The unchanged ordinary demand-v3 core SHA256 is
`1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8`;
reference SHA256 is
`e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129`.
Existing exactness over18 original-command contexts is reused by hash.

Unlike the manual runner, this version persists per-call direct-submission
counts and copied payload bytes. It retains per-call main step/thread CPU,
worker CPU, frames, frequency observations, effect properties and PCM pointers,
plus a32,768-entry PCM trace. It logs in RAM while workers run, then flushes
after audio join/display idle between epochs. Trace truncation remains explicit.
Nested core phase timers are disabled; observer costs stay included. Frequency
pinning is disabled even if requested through ambient environment variables.
Scheduling and CPU clocks use kernel syscalls, with relative waits.

The new native-provider fixture exercised149 acquired-output callbacks, forced
EBADFD, clean120-frame retry/drain and sustained producer deficit. The actual
40-epoch ARM controller completed48,000 mock calls; all18 requested property
fixtures were observed, every frame submitted, native PCM accounting exact.
Actual wrapper splash/startup/consumed marker and no live-child diagnostics
checks pass; ELF glibc requirements are <=2.30. These qualify software contracts,
not A7 throughput, speaker/panel correctness or physical spell acceptance.

## Return classification

`report-demand-spells.py` reads only strict returned archives. It rejects mock
telemetry on the physical route; missing epochs, early faults, pointer drift,
truncated trace, lost PCM or missing expected properties stay incomplete. It
reports full-window completion separately from worst16-call recorded CPU,
valid running reserve and actual direct/copy counts. Whole-combination matched
Meteor/Quasar savings use identical retained call indices in AB/BA orders.

The thread-CPU sum excludes other processes/kernel work and unsampled final
worker residuals; averages are provisional, not production acceptance. The
nominal quota is16.688153ms/call and20% target13.350522ms. Complete effect and
recovery interpretation and physical output observation are still required.
No isolated optimization prices, frequency assumptions or overhead subtraction.
The existing synthetic239-line baseline HDMA defect remains unchanged.

## Package and installation boundary

Private payload: `build/demand-spells-private-v1`; future card target:
`retro/snes-demand-spells1`. The installer requires a fresh strict I: archive,
clean FAT/known serial, original hashes, clean pushed source commit, no armed
marker/update trigger, exact frozen payload and sufficient free space. It changes
only its new folder, the existing launch dispatcher and one consumed marker;
stock/adapter/production core/ROM and original progress remain protected. It has
not been run. No binaries, ROMs, states/SRAM or vendor dependencies are published.

[Ready receipt](../evidence/2026-10-14/demand-spells/ready.json),
[plan](../evidence/2026-10-14/demand-spells/plan.json),
[device instructions](snes-demand-spells-test.txt).

Build sequence: `python build/prepare-demand-spells.py`,
`wsl sh build/build-demand-spells.sh`, `wsl python3 build/qualify-demand-spells.py`.
After a future authorized install/return, first strict-archive I:, then run
`python build/report-demand-spells.py <archive>`; no card access by the reporter.
