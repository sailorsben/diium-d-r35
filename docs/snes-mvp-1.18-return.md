# MVP1.18 return: Magitek audio exit, damaged filesystem

**Update after approved repair:** filesystem checks are now healthy, and lost
chains recover the actual1.18 session and PCM reports. All412 previously readable
files survive unchanged; verified pre-test SRAM is restored into the empty path.
Audio remains unresolved. The initial missing-data account below is historical;
use the [recovery evidence and current resume](fat-recovery-2026-10-09.md).

Returned 2026-10-09 America/Chicago. Archive:
`device-evidence/snes-mvp-return-20261009T144358Z`.

Terra's Magitek armor **Bio Blast again returns to our library**. The user
reports an audio descriptor failure at the bottom. The color-cache candidate
has therefore not fixed that physical failure. Its speed contribution remains
unmeasured in this return; do not convert offline lookup counts into A7 gains.

## What survived

The exact1.18 runner, core and wrapper match their release. Startup identifies
child503, correct splash exit before InitVFB, a game launch request at14.002s
uptime and library return at53.490s. Stock main/vrtemu/driver/adapter/Plus and
boot hook match the retained baseline. All retained snapshots match, including
the separate1.18 header whose state payload equals the original.

The collector initially stops at Windows `WinError1392` for an SRAM backup.
A deliberate salvage mode then hash-verifies51 MVP/progress/hook files and49
lab files, performing zero card writes. It records two unreadable entries:

- `saves/game-a27f1c7a-3145728.srm.bak`
- `saves/last-session.txt.bak`

A second private archive preserves **412 readable card files,646,926,457 bytes**,
with source/copy/source SHA256 verification and the same two read errors. Full
card contents, games, private progress and vendor binaries remain unpublished.

## What did not survive

Both new `failure-503-14018869000` report/PCM files, latest PCM history,
`last-session.txt` and current FF6 SRAM are **zero bytes**. There are no fresh
effect CPU costs, producer cadence, reserve observations or descriptor errno
records to analyze. `last-run.log` is byte-identical to the old1.16 return; its
descriptor error and successful retry are historical, not evidence about1.18.
The fresh wrapper-start marker is not a gameplay checkpoint.

Read-only Windows CHKDSK confirms FAT32 metadata problems: the two backup
entries have invalid first allocation units; the first check reports about
1,472KB in14 recoverable lost chains. It explicitly runs without `/F` and does
not repair them. The preserved second check reports the same invalid entries
and lost-space quantity. This proves filesystem corruption, **not** defective
card hardware, an unsafe-removal cause, or that storage caused the audio stop.

Earlier private archives retain the pre-test SRAM and both backups. Preserve
them and all snapshots; never silently replace a valid new save with an older
one. Filesystem recovery might retrieve newer SRAM or the missing fault data.

## Next step and evidence boundary

The concrete recovery proposal is FAT repair with lost-chain preservation,
then inspect recovered files for the new session/PCM record and8192-byte SRAM.
That operation can truncate the two invalid entries, so explicit consent is
pending after the full readable backup. Do not update or re-arm this damaged
card. If recovery cannot supply a valid current SRAM, restore only the known
verified prior copy and label its earlier save point clearly.

The audio failure remains unresolved. No speculative PCM reset, larger prime,
frame suppression, new cache size or audio/core tweak ships from missing data.
Recover the actual failed seam first. The old transient production-deficit
model remains prior evidence, not a new measurement of1.18.

Separately, [Vesper boot artwork](vesper-boot.md) is built and qualified through
the actual stock ARM loader/sprite routines. Its guarded installer requires a
clean filesystem and does not arm gameplay. Installation and physical visual
acceptance are pending; the shipped SNES payload has not changed.

[Verified public analysis](../evidence/2026-10-09/snes-mvp-1.18-return/analysis.json)
and [read-only filesystem report](../evidence/2026-10-09/snes-mvp-1.18-return/chkdsk-before-repair.txt).
