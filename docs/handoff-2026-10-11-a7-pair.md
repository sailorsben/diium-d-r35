# A7 pair1: physical return analyzed

## Return supersedes pending state

I: returned and was strictly archived at
`device-evidence/a7-pair-before-20261012T034845Z`. FAT is clean, staged payloads
match and the marker is consumed; next boot is stock. All6 combined passes
complete, all6 baselines fail errno77/SETUP. Full combined replays reach500
drawings/effect/recovery with stable reserve. Aligned pairs save~2.9ms CPU and
~3.2ms core wall. No return-handling card writes or rearm. See
[return](snes-a7-pair-return.md) for sample coverage, costs, pointer epochs,
visual observations and next qualification. Earlier staging account below is
historical; do not treat it as current armed state.

The user replaced the system disk: C: is the new4TB drive, D: the old system
drive, and **I: the original D-R35 test card**. Never run historical installers
against D:. Card identity remains FAT32 DIIUM D-R35, serial11EB-1465.

The user explicitly authorized staging/testing the combined renderer design.
The separate1.19-pair1 suite is armed through the existing consumed-one-shot
hook. It compares the exact shipping baseline with a counter-free combined
window/palette/prefix core. Three aligned starts, each baseline/combined/
combined/baseline, use full native audio/display workers. No production core,
adapter, stock binary or init was replaced. See [suite](snes-a7-pair-suite.md)
for measured targets, observer scope, qualification and remaining boundaries.

Private archive before any write:
`device-evidence/a7-pair-before-20261012T032639Z`.
Every457 retro files was copied and source/copy/source SHA256 verified; FAT
passed readonly CHKDSK before and immediately before staging, after payload
and after arm.456 earlier retro files are protected unchanged; the sole
exception is owned `retro/snes-mvp/launch.sh`, now dispatching pair1. New
payload and old dispatch rollback identity are recorded in
`pair-installation.json`. ROM content is also verified unchanged.

Owned new card path `retro/snes-pair1`; existing `retro/snes-cost1` and all its
results remain unchanged. Only `retro/snes-mvp/armed` is armed. Next cold boot
consumes it and automatically runs12 independent experiments. Do not re-arm
unchanged builds. MENU aborts. Observe appearance/sound/shutdown/stock return;
do not navigate the replay manually. [Physical steps](snes-a7-pair-test.txt).

On return, confirm the card's current drive letter and strictly archive all
retro files before writes. Preserve pair1 partial/full captures and private
progress with hashes; perform read-only health checks. Analyze matching replay
call numbers, warmup convergence, both ABBA positions, known/unknown frequency,
observer cost, core CPU/wall plus admission/complete-step, reserve trajectory
and valid pointer epochs. Short late starts have fresh audio reserve and cannot
prove uninterrupted whole-effect output/recovery. Full replay success, exact
cadence and sustained PCM must establish any production installation gate.

Qualification:6,000 exact pixel/PCM/geometry/state comparisons;12 mock passes,
2,704 submitted frames with no loss or progress saves; baseline and combined
native consuming/fault/drain/deficit checks; actual wrapper splash/one-shot/
startup/no-live-card-write checks. All QEMU durations are excluded from A7
performance. Private build: `build/a7-pair-private-v1`; separate release identity:
`releases/snes-a7-pair-1/manifest.json`. Public proofs contain no ROM, states,
vendor cores, dependencies, full archive or personal/account data.
