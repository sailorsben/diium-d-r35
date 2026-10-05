# MVP1.8 return: clicking and whole-device power-off

Physical return, 2026-10-04 America/Chicago. Ben reports that play was okay,
the sound was closer to the earlier clicking issue, and the whole device
powered off. Full-speed, uninterrupted sound and stability have not passed.
The location in FF6 and shutdown trigger are unknown.

## Preserved card and release identity

Archive `device-evidence/snes-mvp-return-20261005T030941Z` contains 39 files,
verified against the card before and after copying. Collection made zero card
writes. All 19 pre-existing private progress files, stock binaries and boot
hook match their protected baselines. This preserves existing saved progress;
it does not recover gameplay that was never saved. The consumed card is unarmed.

The returned executable, wrapper and core match released1.8 exactly. Core CRC32
is `666af55a`, 665,008 bytes. Selected public evidence is under
[snes-mvp-1.8-return](../evidence/2026-10-04/snes-mvp-1.8-return/analysis.json);
private states, SRAM and dependencies remain local.

## What survived, and what did not

`last-progress.txt` is empty. Its previous record is fresh1.8, session
`492-10387597000`, phase `running`, kernel uptime41.124828s. The final
`last-session.txt` is byte-identical to the prior1.7 return and describes core
`90fbcc4e` with7,068 calls: those totals do not belong to this run. Kernel and
stderr tails are empty, and no fresh main/child/cleanup exit record survived.

The checkpoint is a retained point during gameplay, not a crash timestamp or
complete session. The original analysis predates the clarification; the
[observation follow-up](../evidence/2026-10-04/snes-mvp-1.8-return/observation-followup.json)
records the confirmed whole-device power-off. No shutdown cause is established.

## Fresh checkpoint measurements

| Measurement | Retained result | Meaning |
|---|---:|---|
| Core calls / held drawings / video submissions | 1,648 / 0 / 1,648 | Full rendering in this retained interval |
| Active-loop time | 28.446872s | Omits pause/menu/load and some bookkeeping |
| Calls per active second | 57.9326 | About96.68% of native59.9227; not optical FPS |
| Mean core wall / thread CPU | 13.3300 / 12.4184ms | Includes callbacks; not isolated PPU cost |
| Core p95 / p99 / maximum | [18,19) / [23,24) / 39.846ms | Expensive calls exceed the16.688ms native budget |
| Definitely over-budget calls | 369,22.39% | Eight additional calls fall in the ambiguous[16,17)ms bin |
| Producer audio-lead wait | 3.0015ms/call | Some may be legitimate throttling |
| Producer display reservation wait | 0.8144ms/call | Separate from callback and overlapping worker wall |
| Audio worker / display worker CPU | 0.1900 / 0.7018ms/call | Workers share the single CPU |
| Sampled device PCM queue | 0–2,048frames | Zero suggests starvation risk; no xrun counter |
| Maximum accepted-write gap | 40.004ms | PCM continuity in memory does not prove continuous playback |
| Audio write errors | 0 | Partial/EAGAIN writes were retained, not treated as loss |

PCM accounting balances: 1,212,734 converted frames plus4,096 priming frames
equals1,216,179 accepted plus651 remaining; no software clear is recorded.
That rules down simple dropped-tail accounting at this checkpoint. It does
not exonerate delivery timing. Clicking, an empty sampled device queue and
40ms submission gaps support a starvation hypothesis without proving it.

The full producer step averages17.2615ms despite a13.3300ms core call. Queue
control is a concrete engineering target. It would be wrong to promise that
all3ms of lead wait can be recovered, add overlapping scaler/flip wall as
serial CPU, or call the different1.7/1.8 workloads a measured speedup.

## Diagnostic defect and source repair

The firmware lacks both `head` and `sed`. The1.7 return proved the first;
the1.8 wrapper exposed the second. The previous claim that `sed` already
worked was an unsupported assumption, and the host fixture failed to expose
it. System CPU/memory/IRQ and bounded process capture therefore have gaps.

Current source uses shell builtins for bounded line reads and splash zombie
parsing. The actual wrapper passes with both tools absent, captures CPU/memory
contents, ignores a released zombie, retains live progress and performs no
global sync during gameplay. This repair is not installed or armed; shipped
1.8 bytes and historical verification remain unchanged.

Checkpoint copies were not fsynced. An empty latest file with a valid previous
record is consistent with lost writeback, but does not locate the shutdown
inside a capture window. Early RSS11,708KiB, high-water14,432KiB and zero
process swap establish only that early sample, not late memory/OOM behavior.

## Shutdown and output boundaries

Read-only disassembly of the exact factory `power_key` helper identifies a
shutdown path: poll bit0x08 at0xd0000068 every200ms; after eleven consecutive
asserted samples, switch off the backlight via GPIO0x108 and call `poweroff`.
The hardware watchdog helper independently feeds every500ms. The early
snapshot shows both helpers sleeping normally. No late pin sample, shutdown
message or watchdog expiry record identifies which path fired. These are
recovered code paths, not permission to probe MMIO or alter power GPIOs.

After this crash, the exact returned core passed10,000 output-equivalence
frames:5,000 intro and5,000 from the returned private snapshot, comparing
visible pixels, native PCM, geometry and periodic state with only named host
pointers normalized. This broadens output correctness evidence; QEMU cannot
establish handheld speed, sound deadlines or the power-off cause.

The1.8 publisher now checks actual qualified input bytes before any writes.
A changed source wrapper is rejected even with stale verification metadata;
the contract check confirms historical release/evidence bytes are preserved.

## Next engineering step

Implement one bounded audio-headroom production controller in place of the
serial clock and fixed70ms lead gate. Preserve native average speed, bounded
lookahead, every rendered frame, PCM accounting and ordered display ownership.
Add small durable crash records and the repaired platform capture, explicitly
budgeting their I/O cost. Qualify the new source and release under a new version
before installation. This return does not justify re-arming unchanged1.8,
disabling the watchdog or claiming that the power-off has been fixed.
