# Manual combined-renderer gameplay test: returned

Latest return: Bio Blast seemed fine; Confuser stopped with native errno77.
Archive `device-evidence/a7-pair-before-20261012T043106Z`, hashes verified,
FAT clean, marker consumed and zero writes. Session225.095s/13,456 calls;
last23 complete calls average17.491ms core+admission, local gap0.803ms.
Sparse PPU growth and reserve erosion lead; exact effect path and vendor edge
remain unresolved. See [return analysis](snes-combined-gameplay-return.md).
Do not rearm or install another diagnostic without the missing replay evidence.

Explicit unchanged retry: user forgot B at library exit and requested quick
re-arm with no extra tests. Return was privately archived at
`device-evidence/a7-pair-before-20261012T042206Z`; fresh readonly FAT is clean.
Only `retro/snes-mvp/armed` was written. All549 existing files, including
returned logs and test progress, remain unchanged. No build, replay, benchmark
or runtime-result analysis ran. This is an explicitly requested retry of the
same test, not a newly qualified experiment. Private proof:
`manual-gameplay-rearm.json` in that archive.

User explicitly authorized a longer manual Bio Blast gameplay test. I: remains
the FAT32 DIIUM D-R35 card, serial11EB-1465. D: is the old system disk; do not
use historical D:-hardcoded installers.

Fresh archive before writes:
`device-evidence/a7-pair-before-20261012T040022Z`.
New owned test folder: `retro/snes-combined-gameplay1`. Existing
`retro/snes-mvp/launch.sh` dispatches its wrapper. Only the existing
`retro/snes-mvp/armed` marker is armed; wrapper consumes it into the new test's
last-launch before startup. Next unarmed boot is stock. Existing init, vendor
binaries/adapter/production runner/core, earlier pair/cost evidence and original
progress remain exact. Staging proof is `manual-gameplay-installation.json`
in the private archive. Payload/arm readback and clean FAT follow collection.

Core is the exact measured combined ee0b241c3b7c561e76efbedbbdcf37bf8e104bb6754d7b0493c3ed4774172155,
CRC b77a9eb3,794156 bytes. Regular1.19 runner is unchanged
c0b56975ea847ecfa737eee43bab0781d8d039b9f3bcc6af5508e7bbfd231310;
its session reports still identify runner1.19, while folder/manifest/startup
identify combined-gameplay1. No forced replay, counter instrumentation or
new renderer change. Sparse/recent regular counters are not a whole-session
per-call timeline. Longer physical behavior is unqualified.

Test SRAM and current1.19 Narshe snapshot are copied into the new owned saves
directory. Snapshot payload is byte-identical, with a separately qualified core
identity header/name. All new progress stays in that folder. Preserve it on
return; never silently merge or overwrite original progress.

Qualification:2,400 additional exact-output frames using this copied snapshot;
180 actual regular-binary frames with full drawings, lossless PCM and orderly
close; native consuming fixture loads/resumes snapshot twice and tests fault,
drain, retained failed evidence and sustained deficit; wrapper tests one-shot,
splash/startup and no live-child card diagnostics. QEMU times are not A7 prices.
Measured pair1 costs, conditional break-even margins and falsifiable gameplay
prediction are in [setup](snes-combined-gameplay.md).

[User procedure](snes-combined-gameplay-test.txt): cold-boot into normal library,
launch FF6, load copied snapshot as useful, play roughly10–15 minutes with
several manual Terra MagiTek/Bio Blast casts. Exit game from pause menu, then B
from our library; wait for stock before powerdown. Observe audio/visual/stability,
duration/cast count and exit. Archive strictly before any writes/rearm on return.
Capture incomplete files honestly; readonly FAT health and source/copy/source
hashes precede updates. Do not re-arm unchanged builds as fresh experiments.
