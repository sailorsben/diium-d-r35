# Demand-v3 manual return: clean opening-scene run

Ben returned I: and reported: “It's just the opening scene. Confuser worked
fine. I can't test Ultima, Holy, etc.” This is opening-scene/Confuser coverage.
There is no late-game physical spell coverage, retained cast identity or input
replay. Earlier Confuser-gameplay also had a successful manual return, so this
is a successful demand-v3 run, not a demonstrated incremental Confuser fix.

## Collection and identity

Read-only strict archive `device-evidence/a7-pair-before-20261014T070253Z`
preserves6,340 retro files/1,658,860,825 bytes with source/copy/source hashes.
Every archived byte was verified again during analysis. Read-only CHKDSK shows
clean FAT and serial11EB-1465. Fourteen live/archived boot, stock, adapter, core,
runtime, dispatcher and test-identity files verify; the original ROM ZIP hash
also matches. No card writes, update, restoration or rearm were performed.

The exact installed ordinary demand-v3 core SHA256 is
`1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8`,
CRC02bb090e,857380 bytes; the owned-output runner is unchanged. The one-shot
marker was consumed into the expected last-launch record. No armed marker or
firmware update trigger remains; next boot selects stock by the verified hook.
Of6,316 protected prior retro files,6,315 remain exact; only the stock runtime's
swapfile changed. Original saves/progress and production binaries remain exact.
All four newly copied state/SRAM files also remain exact.

## Observed session

| Measurement | Result |
|---|---:|
| Session / active play | 70.129 /65.872 s |
| Completed core calls / active cadence | 3,952 /59.995 calls/s |
| Submitted frames / held / duplicates | 3,952 /0 /0 |
| Native / converted audio frames | 2,113,012 /2,908,357 |
| Accepted non-priming audio frames | 2,908,357 |
| PCM write errors / reported underruns | 0 /0 |
| Cleared / remaining software audio | 0 /0 |
| State loads / rejections / pauses | 1 /0 /2 |
| Minimum reported running reserve | 2,028 frames /45.986 ms |
| Minimum reported admission reserve | 2,411 frames |
| Core wall / main core CPU mean | 11.266 /10.459 ms/call |
| Audio / display worker CPU mean | 0.521 /0.681 ms/call |
| Sum of those distinct recorded CPU regions | 11.660 ms/call |
| Video callback mean / copy timer total | 0.243 ms /27.326 ms |
| Maximum core wall time | 25.076 ms |

The final epoch's application pointer equals its transferred count; application
minus hardware pointer3008 also equals buffer3712 minus available704. These
endpoint checks and exact software accounting are consistent with healthy PCM.
They do not independently validate every earlier pointer observation or replace
the missing complete reserve timeline across pause/load/recovery. The two epochs
include5,646 priming-silence frames, excluded from accepted game-audio accounting.

The runtime reports finished with empty error fields, no retained fault files,
and zero diagnostic RAM errors. Splash exited before InitVFB. Library startup,
copied state load, game close, B library exit, display worker join and FreeVFB
completed; wrapper exit status0, ready=yes. Display counts3,958 include six
additional menu/pause draws. They establish completed driver calls, not a pixel
comparison or independent visual coherency certification.

## Timing interpretation

The nominal cycle-derived quota is16.688153 ms, with13.350522 ms for a20% margin.
The whole-session recorded CPU sum is below that target on average, but omits
other main-thread, OS/kernel and unrelated-process costs. It cannot certify
worst-effect headroom. Core wall already includes nested audio/video callbacks;
do not add their times or inclusive APU times again. No profiling overhead is
subtracted and no sustained frequency is assumed.

The coarse1ms core-wall histogram contains9–18 calls beyond the nominal quota
and195–462 beyond the20% target. The bounds reflect the partially overlapping
16ms and13ms bins, respectively; sampled calls are included. The zero late-call
counter is a different admission test: lateness greater than one period, not
absence of all core-duration overruns. Transient25.076ms work did not produce a
logged underrun in this run. Its spell/scene identity is unavailable.

The24 retained unsampled tail calls average12.038ms wall/11.096ms CPU. The last
eight phase samples average4.086ms PPU and3.774ms APU-inclusive CPU. They cover
runs3452–3900, not the full run or each cast. There is no matched baseline and
no complete per-call thread/service/reserve trace. These values cannot price
individual optimizations or establish a Meteor/Quasar improvement.

The display copy timer totals27.326ms, about6.91us divided by game calls. This
is consistent with copy avoidance; the frozen runner does not persist direct
submission counts or copied bytes, and menu draws contribute. Do not turn it
into an exact direct-hit count or a matched speedup claim.

## Outcome and resume point

Clean observed manual run, Confuser reported working, no production promotion.
Physical Ultima/Holy/other late-game effects, complete worst-effect reserve,
incremental A7 saving and broad output coherency remain unqualified. The
previous offline exactness evidence is unchanged. The card remains unarmed.

Further spell coverage can use the existing private archived fixtures in an
explicitly authorized automated physical replay, so Ben need not reach late-game
content manually. The existing72-epoch measurement plan remains a plan; no new
test is installed or armed here.

Evidence: [analysis](../evidence/2026-10-14/demand-gameplay-return/analysis.json),
[session telemetry](../evidence/2026-10-14/demand-gameplay-return/session-telemetry.txt).
Reproduce with `python build/analyze-demand-gameplay-return.py
device-evidence/a7-pair-before-20261014T070253Z`; analysis reads only the archive.
