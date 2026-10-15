# UART-corrected FFVI return: better reserve and two recovered Meteor windows

The correction improves this bounded test's resilience. All48 epochs finish;
46 qualify as clean physical windows, versus44 previously. Both raw demand-v3
Meteor controls now complete with valid pointers and full PCM histories. The
draw-order candidate retains40/40 clean windows, and its minimum reserve improves
in36 matched runs and stays equal in four. No candidate reserve regresses.
Quasar's six consecutive pricing runs all finish; the observed repetition was
the planned sequence, not an indefinite loop.

| Same core/fixture runs | Previous return | UART-corrected return |
| --- | --- | --- |
| Draw-order candidate, all contexts/pricing |40/40 clean |40/40 clean |
| Raw demand-v3 Meteor controls |0/2 clean |2/2 clean |
| Fixed-APU-only Meteor controls |0/2 clean |0/2 clean |
| All epochs |44/48 clean |46/48 clean |
| Nominal completions with invalid pointers |1 |0 |

The remaining two failures are fixed-APU-only Meteor, both reporting
`Audio publication failed: File descriptor in bad state`. They reach521 calls
versus489 previously, but valid frame prefixes end at496 versus474/472. Do not
count the later invalid frames as recovered throughput. Worker/display joins
and cleanup complete; the suite reports failures2 and stopped0. All46 accepted
windows have1,200 calls,55,200 total scaled/flipped frames, matching effects,
valid pointers and complete PCM histories. The candidate accounts for48,000.

The newly passing raw Meteor controls retain minimum valid reserves937 and1,161
frames, versus139/138 before pointer drift previously. Their complete running
histories recover193/321 frames above the initial2,823-frame reserve. Previous
trustworthy prefixes lost2,075/2,076 frames before drift. These are consistent
vendor logical accounting identities, not independent DAC measurements.

In matched Quasar candidate pricing runs, minimum reserve rises from1,705/1,704
to1,834/1,833 frames:129 additional frames each, about2.93ms at44,100Hz. The floor
moves from about38.64ms to41.56ms. Regression-pass Quasar rises1,706→1,833 in the
first pass and remains1,833 in the second. Candidate Meteor's four minimums rise
from2,031–2,059 to2,122–2,125 frames. This is useful extra tolerance.

It is not a demonstrated general CPU speedup. Across all40 candidate runs, the
median matched warm thread-CPU change is a0.0404ms/call increase, while median
wall service (step minus pacing wait) improves0.0358ms/call. The regression-only
medians are0.0378ms more thread CPU and0.0387ms less wall service. Values vary by
run; IRQ execution is not independently priced by these thread clocks, and the
returns came from separate boots. Do not turn a99% IRQ-count reduction into a
CPU percentage or subtract unrelated worst windows.

Quasar's draw-order regression remains: within the corrected boot, the candidate
costs raw v3 another0.545/0.562ms of recorded warm thread CPU per call. Its worst16
recorded CPU rises slightly to16.760–16.763ms across four runs, versus the nominal
16.688ms quota. All candidate conservative20%-headroom reports remain NOT_MET;
that overlap-prone proxy is not an independently measured missed-flip count.
Keep the successful UART correction; neither promote the whole draw-order build
as universally faster nor claim the remaining emulator margin is solved.

## Sustained UART result

The boot helper reports successful attachment, and both suite boundaries show
attached1, FIFO8, cap0, fault0 and bypass0. There are70,633 intercepted calls:
65,730 added services (65,725 one-byte writes and five empty-queue stops) plus
4,903 original-handler fallbacks. Reported TX advances84,564 bytes and both
boundary queues are empty. No full-FIFO, urgent or stopped-TTY service occurs.

Wrapper IRQ19 samples rise140,843→211,361 across984.49seconds:71.63/sec. The prior
unfixed suite recorded6,920.94/sec. That is a98.965% sustained rate reduction
across approximately16.4minutes, including inter-epoch I/O; it is not a per-frame
IRQ-time price. Module and wrapper boundaries are taken at different instants,
so their call deltas need not match exactly.

RX and break counters each advance54; frame/parity/overrun remain zero. This
bounded return includes RX/break activity through the retained vendor path, but
does not validate arbitrary serial wire data, mixed traffic or silicon full-FIFO
behavior. The vendor PutChar implementation is unchanged. Longer uptime beyond
the former cutoff and counter wrap remain compiled-model checks rather than
new physical observations.

## Evidence and current card

Strict archive `device-evidence/a7-pair-before-20261015T072449Z` preserves8,275
files /2,026,867,632 bytes, hash-verified with clean FAT32 serial11EB-1465. All86
test payloads, persistent module/helper/wrapper/init, receipt, original init and
consumed marker verify. Of7,827 protected preinstall files, only the expected
stock `retro/swapfile` changes;7,826 remain exact. Stock binaries, old test logs,
original progress and live ROM verify. The controller, all three cores, plan,
states, expected effects and inputs remain byte-identical to the old return.
The evaluator rechecks every frozen baseline input hash and reproduces all48
previous acceptance statuses before comparing the new run.

No card writes, emulator recoding, rollback or rearm occurred during collection
and analysis. I: is unarmed. Its next boot runs stock with the persistent UART
correction retained. First persistent boot and this bounded suite pass; broad
production performance, independent speaker/panel quality and long-term serial
qualification remain separate.

Reproduce with:

```text
python build/evaluate-uart-spells-return.py <strict-archive> --verify-live
python build/check-uart-spells-reporter.py
```

`--verify-live` is read-only. Seven reporter checks reject mock data, detached/
capped/faulty UART status, broken count conservation and invented incomplete
fixed-interval savings. Full private raw histories and valid-prefix comparisons
are retained. [Published return](../evidence/2026-10-15/uart-spells1/return.json),
[reporter checks](../evidence/2026-10-15/uart-spells1/return-reporter-qualification.json),
[previous result](snes-draw-order-return.md),
[persistent fix and rollback](uart-persistent-fix.md).
