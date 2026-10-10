# Changelog

## ROM-derived Bio Blast cause map and isolated window patch - 2026-10-10

Rebuild the owner3 MiB FF6 ROM byte for byte from pinned annotated assembly;
lift103,538 native CPU instruction addresses into eight private C banks and
write a readable Bio Blast script/wave model.178 real wave-kernel executions
match all32 expected words. Frame320 scroll writes cause no pending-render
flushes; circular-window edges cause123. Patch a separate core to retain BG1
window bounds per scanline and defer eligible edge flushes.

Independent original clip code matches all524,288 edge/polarity/masking states;
3,600 actual ARM comparison frames match per-frame visible/PCM CRCs, sample
counts, geometry and periodic normalized serialized bytes. Effect PPU updates
drop78.97%, but color-row materialization rises34.58%; no hardware speed/audio
claim. Shipping1.19 core and card remain unchanged by this experiment. Publish
authored tools/models and six bounded evidence files, preserving659 prior hashes;
private ROM/assets/generated bank maps/states/dependency bytes remain local.
[Cause map and exact limits](docs/ff6-bio-blast-cause-map.md).

## Focus1 unchanged-core diagnostics qualified and armed - 2026-10-10

Retain64 recent frame records and sample phases/callback CPU one in eight under
ordinary-call load, with sampled-cost feedback excluded. Actual ARM runner,
resampler, failing-interval cadence, report-capacity and consuming native PCM
fault/retry/load/drain/deficit checks pass. Archive58 MVP/progress and49 lab
files before installing the owned runner/instructions. Independent readback
checks138 protected hashes, exact1.19 core/wrapper and clean FAT. Only SNES
armed, no firmware trigger. Physical attribution pending; no audio fix claimed.
Publish the runner-only release and14 curated files without dependencies,
preserving645 prior evidence hashes. [Test](docs/snes-focus-1.md).

## SNES1.19 Bio Blast still fails; clean exit preserved - 2026-10-10

Collect58 MVP/progress and49 lab files with verified hashes before any changes.
Exact1.19, all prior files, nine snapshots and three SRAM generations survive;
fresh FAT is clean.1,713 core calls end with native SYNC_OBSERVE errno77/SETUP.
Near failure, accepted audio is38,764 frames/sec against44,100 Hz; final ordinary
calls average18.287 ms wall /16.935 ms CPU. Offline color-work savings have not
fixed physical audio. No phase sample covers the final24-call window.

B exits our library after the game error; display join/close and wrapper final
copies complete. Fresh failure reports and stderr agree; recorded255 status
is the failed game's rc=-1, not a signal crash. Stock/current Vesper SD artwork,
normal init and58 archived files independently reread exact. No card writes,
repair or rearm; all tests and Code.bkp absent. Guarded return publisher keeps
private progress/binaries local and preserves637 prior evidence hashes. Next
engineering step is bounded phase attribution during the failing interval.
[Return](docs/snes-mvp-1.19-return.md).

## SNES1.19 rearmed for proper game exit - 2026-10-10

User explicitly requests rearming the unchanged build to exit properly.
Archive56 returned MVP/progress files and49 lab files before a clean read-only
FAT check. Verify exact1.19 payload and138 current protected file hashes,
including27 reader files and the current Vesper/stock boot baseline. Recreate
only the SNES one-shot marker; all archived bytes remain exact. No payload/save
or flash changes and no new audio acceptance inferred.
[Rearm receipt](evidence/2026-10-10/snes-mvp-1.19-rearm/rearm.json).

## SNES1.19 demand-driven colors qualified and armed - 2026-10-10

Resume SNES from the recovered1.18 Bio Blast production deficit. Test index/depth
visibility before RGB preparation and cache only demanded rows, retaining the
36 KiB footprint. Repeated1.18 baseline reproduces all1,200 census rows;
162 effect frames need667,001 palette lookup rows versus1,003,928, down33.56%.
All other126 counters and command-boundary pixel/PCM CRCs match. Row-tag
requests increase slightly; work reduction is not an A7 speedup claim.
Shipping core passes14,400 clean-core equivalent frames including the complete
Magitek effect, independent color/cache/CGRAM checks and actual ARM runner,
snapshot, native PCM, wrapper and display lifecycle checks.

Archive51 MVP/progress files and49 lab files before installing exact1.19.
Preserve29 private save/state files and27 SPI-reader files; stock/current Vesper
SD artwork and normal init retain their verified hashes. Create a separate
snapshot header with original payload. FAT clean before writes and after
payload; independent readback passes. Only SNES armed, no Code.bkp, no flash
write. The first historical showlogo guard refused before writes; pin the
already verified Vesper release hash for the current baseline. Physical audio
and speed remain pending. [Candidate and next test](docs/snes-mvp-1.19.md).

## Both Vesper screens verified; normal startup restored - 2026-10-10

Returned run `db7079b5f61b4ee5b7d36d22e58472fd` completes two 8 MiB SPI reads
in 103.790618 seconds. Both match the expected programmed image byte for byte,
SHA256 `509cdc305deca2654fbf48184eb16d523b4b6cae0effffc4a3cba6845622d9fd`,
CRC32 `cdf3f0aa`. Marker/run, wrapper exit, ID/status/counts and CRC checks pass.
Archive twice before fresh FAT/run/init gates and original startup restoration.
Independent reread verifies normal init, no Code.bkp/armed markers, five stock
hashes, 51 protected MVP/progress files, 49 lab files, both nine-file prior reader
profiles and all returned captures. Final FAT clean; no flash/config writes.
The user's earlier Vesper static -> Vesper animation -> stock launcher report
and complete installed equality finish both requested replacements. Ready for
normal use with no verification delay. External recovery unqualified; audio
unresolved. [Verified result](docs/vesper-static-firmware-update.md).

## Both Vesper boot screens accepted; read-only verification armed - 2026-10-10

User explicitly confirms Vesper static -> Vesper animation -> stock launcher.
Archived 51 MVP/progress files, 49 lab files, profiles/root/display logs and the
exact package before removing Code.bkp through fresh FAT checks. Stock/progress
hashes remain exact. Retained all nine second-animation capture files and nine
older factory-reader files; reused the unchanged qualified reader/wrapper with
fresh run `db7079b5f61b4ee5b7d36d22e58472fd`.
Independent marker/no-stale-results/init/rollback/reader/manifest/protected/
retained-profile checks and post-arm FAT pass. Only read-only reader armed,
targeting the new expected full image, SHA256
`509cdc305deca2654fbf48184eb16d523b4b6cae0effffc4a3cba6845622d9fd`.
Full 8 MiB equality and the next boot without the trigger are pending. First/second
appearance acceptance is the user's report. External recovery unqualified;
audio unchanged. [Current physical verification/return](docs/vesper-static-firmware-update.md).

## First static Vesper update qualified and staged - 2026-10-10

Replace the exact640 x480 RGB565 bitmap using the accepted animation background.
Start from the physically verified Vesper-installed image; preserve every byte
outside bitmap0x8854/614400, including boot instructions/header and second
animation/rootfs/kernel/tables. Ten offline checks execute the actual Thumb
bitmap stores/loader and captured updater with RAM-only flash, including refusal
fixtures. Valid simulation erases ten64KiB blocks/2560 pages; metadata
17e40b24/5d4a6000. Seven host stage/rollback/card/baseline/refusal checks pass.
Archive current progress/profile/logs and verified full backup before staging.
All1,006 original readable card files exact; only qualified Code.bkp added.
Independent package/init/protected/profile reads and fresh FAT pass. Normal
init exact and no test armed; user SD update/first-screen boot/full new-image
verification remain pending. External recovery unqualified, audio unresolved.
[Exact staged image and next physical/return steps](docs/vesper-static-firmware-update.md).

## Installed Vesper image verified; normal startup restored - 2026-10-10

Run c4a59205933b4459a9d88ed6aafe5dd2 returns two complete8MiB SPI reads in
103.776166 seconds, each exactly equal to the expected vendor-mutated image.
Archive twice before restoring original SD init through fresh FAT/run/hash gates.
Independent card reread confirms full captures, original init, absent Code.bkp/
armed markers, five pre-update stock/runtime hashes,51 protected MVP/progress,
49 lab and9 retained prior-reader files. Final FAT clean. This establishes
installed bytes and init execution without the update trigger, supplementing
the user's earlier static D-R35 -> Vesper -> default launcher acceptance.
No additional visual report supplied on this return. Ready for normal use;
first static screen preserved, external write recovery unqualified, audio
unresolved. Publish metadata only; raw flash and private progress stay local.
[Verified return](docs/vesper-flash-verification.md).

## Post-update return, trigger cleanup and read-only verification rearm

Archive51 MVP/progress,49 lab and all prior profiles/logs before card changes.
Stock runtime/core and protected progress match pre-update hashes; fresh FAT
passes before/after removing the exact Code.bkp trigger. Keep all9 prior reader
files intact via guarded archived rename; reuse unchanged qualified ARM reader/
wrapper and fresh run identity.8 host checks qualify manager rearm/rollback,
directory-move/update refusal and full-byte match/difference/incomplete analysis.
Independent installed reader/init/marker/retained-profile/protected hashes and
post-install FAT pass. Only read-only verification armed; full8MiB comparison
and boot without updater trigger pending. Physical splash acceptance retained;
no new flash program/erase, audio unchanged. [Run and physical procedure](docs/vesper-flash-verification.md).

## Original second-splash replacement physically accepted — 2026-10-09

User confirms normal manual power-on shows static D-R35, then Vesper replacing
the regular D-R35 animation, then default launcher. Requested physical boot/
animation acceptance passes; first static screen stays. Record outcome and exact
card-return resume without another write. Collect/archive before removing the
known update trigger; full SPI comparison and repeat cold boot without trigger
remain pending. External recovery unqualified and audio unresolved.
[Accepted result and return procedure](docs/vesper-sd-firmware-update.md).

## First SD update report:100% then power-off — 2026-10-09

User reports battery-only startup, progress100% and power-off without observed
automatic restart. Re-inspect the exact captured completion path: successful
programming return invokes sync then reboot(0x01234567). Correct the physical
instruction: normal manual power-on once with card inserted; no ten-minute wait
in an actually powered-off device. Boot/animation/full readback and recovery
remain unverified; no new card access or writes. Preserve exact current resume.

## Authorized SD firmware staging before external recovery — 2026-10-09

User explicitly chooses SD update now with programmer purchase if boot fails.
Stage only the exact privately qualified WQW package as retro/update/Code.bkp.
Archive current logs/progress and original SPI backup first; fresh pre/post FAT,
997 original card-file hashes and independent package/init/updater readback pass.
Normal init exact, no other test armed.6 host checks cover staging, wrong-card/
existing-update/competing-runtime refusal and health-failure rollback. Preserve
the expected full-image hash including vendor CRC/time mutation. Physical flash,
second-animation acceptance and recovery remain pending; first static screen
preserved and audio unresolved. Update execution gate, return/unstage/readback
instructions and exact handoff. No vendor-containing files published.
[Result and next physical step](docs/vesper-sd-firmware-update.md).

## Physical board photographs and recovery equipment selection — 2026-10-09

Preserve/hash-verify five supplied photographs privately. Confirm this unit's
VT569B and exposed eight-pin flash package; preserve the user's MD-marked
transcription separately from apparent25Q64CSIG interpretation. Match compatible
family to captured c84017/8MiB evidence and manufacturer3.3V/SOP8 208mil data.
Recommend assembled CH347 adapter and compatible SOIC clip; actual voltage,
mapping, isolation, external read/write/recovery remain pending. Case may be
reassembled. No device change or firmware installation. [Findings and next work](docs/board-identification.md).

## Exact loader/updater qualification and private full Vesper candidate — 2026-10-09

Recover Thumb loader contracts and verify the first static bitmap's boot-code
pointer. Prepare a private8MiB candidate changing only rootfs/table length;
kernel, DT, bootstrap/static bitmap and GPDA remain exact. Execute captured
parser/getter/header selection/section loading and DT initrd patch under QEMU.
Execute exact vrtemu UpdateROM/ZIP/UpdateROMProc with intercepted hardware and
RAM-only erase/program callbacks. Nine offline outcomes qualify acceptance,
four no-write refusals, private-output guard and a malformed-ZIP NULL-image fault.
Compatible image fully matches simulated readback:55 erases/14,080 page programs,
including boot-code block0 because vendor metadata changes. No device writes,
SD staging, kernel execution or recovery claimed. Programmer unavailable;
chip marking/package/access is the next physical dependency. Publish only
interpreted metadata; preserve all prior evidence hashes. Audio unresolved.
[Qualification and exact next work](docs/firmware-offline-qualification.md).

## Full SPI backup, boot layout and private Vesper rootfs candidate — 2026-10-09

Archive the complete16MiB return, independently verify two identical8MiB passes,
CRCs/SHA256, run/wrapper/completion and4,111 messages in103.771059s. FAT is clean;
51 MVP/progress,49 lab and43 prior-profile files preserved. Restore exact normal
init after fresh health; independent protected/result readback and postrestore
FAT pass, nothing armed. No repair or flash/configuration write.

Locate kernel/gzip-cpio rootfs/device-tree sections in the exact image. Extract
the same original `/showlogo`, init, power-key and watchdog as runtime captures.
Prepare only a private rootfs candidate with the qualified Vesper ZIP; all other
cpio bytes stay exact, compressed payload fits with108,732 bytes spare. Six
checks pass including independent libarchive extraction and GNU gzip. Locate a
matching first-screen raw bitmap visually; boot-code reference remains unknown.
No full flash image/update package staged. Built-in kernel cpio has no rescue
init. Boot validation, recovery and persistent replacement remain unqualified;
audio unresolved. [Return and exact next work](docs/spi-readback-return.md).

## Physical SPI ID and qualified two-pass reader — 2026-10-09

Archive successful ID run: three c84017c84017 replies, status00, no competing
owner/error/timeout, matching consumed marker and wrapper exit0. FAT is clean;
51 MVP/progress and49 lab hashes preserved. Restore exact init after fresh health.
Match the triplet to GigaDevice64-Mbit NOR/nominal8MiB using primary manufacturer
and Linux references; exact silicon revision/package remain unverified.

Build fixed05/9f/03 two-pass reader with4KiB packets, working1MHz limit, byte
comparison, indexed result bundle/CRCs, owner/settings/identity guards and240s
owned-child deadline.9 native/ARM/return/health/sparse-shell/ABI checks pass.
Install readback-only profile, independent release/init/marker and protected
progress/prior-result readback, healthy postinstall FAT. Physical full readback
pending; raw contents private, no flash/configuration writes, recovery or splash
replacement. [ID return](docs/spi-identify-return.md), [next run](docs/spi-readback.md).

## Survey2 physical return and read-only SPI identification — 2026-10-09

Archive all905 capture ranges; verify CRCs/lengths/completion, matching run and
wrapper exit0. No failed/truncated reads or caps; returned FAT is clean. Preserve
51 MVP/progress and49 lab files, then restore exact init after fresh health check.
This is one successful storage return, not general shutdown/media qualification.

Discover stock vrtemu PID521 owns SPI0.0 on FD8. Build a synchronous early-init
chip-ID probe with fixed05/9f commands, ownership/configuration/busy/response
guards and owned-child deadline/reap.11 software checks pass. Install with
independent protected readback and healthy postinstall FAT; only this probe is
armed. Physical identification remains pending; no flash/configuration writes,
internal splash replacement or audio fix. [Return](docs/device-survey-2-return.md),
[probe and exact next run](docs/spi-identify.md).

## Survey1 return, FAT repair, indexed survey2 and updater recovery — 2026-10-09

Preserve329 returned captures and all private progress; reject completeness despite
the successful wrapper tail.521 nonempty missing files require exactly17,856 KB,
matching recovered chains. Approved repair leaves all789 readable files unchanged;
archive1,310 repaired files. Replace many FAT capture entries with an indexed CRC32
bundle/report, retain v1 analysis, reject corrupt/torn ranges and gate restoration
on fresh filesystem health.21 software checks pass; survey2 armed with protected
readback and healthy postinstall FAT. Physical durability pending.

Recover exact vrtemu SD-to-SPI updater from machine code: executable-dir
update/Code.bkp, WQW/ZIP/CRC/compatibility checks and03 reads/D8 erase/02 program.
SPI NOR DT candidate found; no physical flash access or recovery qualified.
[Return](docs/device-survey-1-return.md), [updater](docs/firmware-update-contract.md).

## Reusable passive device survey and test catalog — 2026-10-09

Build native Cortex-A7 inventory collector, exact firmware BusyBox one-shot
wrapper, guarded install/rearm/collect/restore commands, SHA-mapped analyzer and
private offline ELF review. Prioritize NAND helpers/module candidates, SPI/USB
identity and device tree; also capture platform/process/memory/power/input/audio
metadata and runtime/module inventories. Bound reads, bytes/jobs and scheduling;
explicitly retain errors, missing paths, truncation, caps and stale-run rejection.
16 independent native/ARM/timeout/sparse-shell/analyzer checks pass; physical
capture pending. Archive progress and restore exact init before repeats. No raw
hardware reads, vendor utility execution, flash writes or active lab rearming.
Catalog19 investigation questions and reuse existing active labs with their
ownership/contracts. NAND tools already preserved privately contain driver-load
and storage-operation code; inspect copies before invoking anything on-device.
[Suite coverage and next run](docs/device-survey.md).

## Physical success is an added SD-stage animation — 2026-10-09

Ben observed: static D-R35, animated D-R35, then Vesper. Vesper is physically
accepted as an added SD-stage animation, not a replacement of either stock screen.
Returned startup log reports stock_released=1, owned child484 exit0 and reaped
before launcher. Strict51-MVP/49-lab archive plus complete animation files are
preserved in device-evidence/snes-mvp-return-20261009T163638Z. Marker consumed;
no rearming. The next boot follows stock. Audio remains unresolved.

Captured /init.project.rc starts internal /showlogo before sleep2 and SD init.
The internal executable matches the qualified stock ZIP owner. Replacing that
original animation requires an earlier boot hook or modifying the embedded root
filesystem image; SD init alone cannot change already displayed frames. Rootfs
is RAM-backed at runtime; editing its live copy would not establish persistence.
The static screen asset/owner remains unknown: bootloader or kernel is a hypothesis.
Prior investigation found no registered /proc/mtd partitions. No verified firmware
image/repack/flashing/recovery route is established. Do not flash or claim both
screens can be replaced yet. Next engineering scope is read-only firmware/boot
image inventory and recovery-method verification, not another SD display test.

## Captured boot route and SD-stage animation test — 2026-10-09

Corrected capture succeeds: init.project.rc launches /showlogo before sleep2,
mounts card /retro at /usr/retro, then launches SD init. Internal rootfs is RAM
rootfs; no firmware replacement is attempted. Captured stock owner and boot
scripts are archived privately in snes-mvp-return-20261009T162604Z. Diagnostic
init was restored exactly. New one-shot launch-vesper-boot.sh signals stock via
/tmp/vrtemu.log, waits for all non-zombie showlogo owners to exit, removes only
the RAM stop marker, launches qualified SD showlogo for3 seconds, signals it,
then waits/reaps its owned child before stock launcher. A release timeout refuses
replacement; an owned-child stall waits rather than starting a competing display.
Device BusyBox syntax and independent dummy-executable one-shot/reap/no-op checks
pass; physical display remains pending. Early solid firmware logo remains stock.
Installer checks healthy FAT, exact init/splash, archives progress and arms last.
No SNES/lab arming or audio change. This is a userspace animation handoff test,
not replacement of the earlier internal boot interval.

## Actual animation owner captured — 2026-10-09

Second physical test remains stock. Passive capture proves PID447 executes
`/showlogo` from internal root: captured198408-byte executable SHA
436d8018808b150c926274575a195f664e61db646f44713371019e9ae10caf3b
matches stock, not patched SD copy. Source-script capture failed because firmware
PATH lacks tr. Correct filename mapping uses shell case only; capture fixture
passes. Strict51-MVP/49-lab archive and all probe files preserved privately in
`device-evidence/snes-mvp-return-20261009T161740Z`; original init restored exactly
before corrected capture installation. No firmware mutation or audio changes.
Next capture must recover init.rc/init.project.rc and mountinfo to identify a
reversible startup seam. Internal solid-logo owner remains unproven.

## Physical boot return: Vesper unchanged — 2026-10-09

Ben saw unchanged solid boot and stock animation, then stock launcher. Returned
patched showlogo still has SHA ab56a67ae629e816a5752b1ad7cec2c335b46c82df84856f8a41376d2f919ebe.
FAT is healthy; strict archive snes-mvp-return-20261009T160157Z preserves51 MVP
and49 lab files. SD init does not launch showlogo. Actual early-boot owner is
unverified; offline sprite qualification did not establish executable ownership.
A passive consumed-once probe captures startup scripts, mountinfo and any active
showlogo executable privately. It never launches a splash, signals processes,
controls display or writes firmware. Offline capture fixture and archived device
BusyBox syntax checks pass. SNES/lab remain unarmed; audio remains unresolved.
On next return archive retro/vesper-boot-probe/results first, then restore exact
init.before-probe from the installation receipt. Physical acceptance has failed.

Earlier entries below preserve chronology. The latest resume is the boot-owner probe.

## Animated Vesper loading screen installed — 2026-10-09

On the repaired healthy card, install qualified cyan feathered V/heart artwork
and18-frame loading dots over stock showlogo. Archive original first; exact
patched hash and all stock bytes outside the artwork verify. Fresh51-MVP and
49-lab protected files plus recovered chains remain unchanged. Post-install
read-only FAT check passes; game/lab remain unarmed. Older whole-card archive
differs in volatile swapfile; preserve its current bytes privately and report
the historical comparison limit. Physical boot/handoff appearance remains
pending. [Receipt, preview and guarded rollback](docs/vesper-boot.md).

## Approved FAT recovery preserves files and retrieves1.18 fault — 2026-10-09

Rehash all412 private backups and compare the card before approved administrator
CHKDSK/F. AnswerY to save lost chains:14 files/1472KB recovered, filesystem
corrected. Fresh read-only checks pass. Complete426-file private archive shows
all412 previously readable files unchanged. Recover actual1.18 session/PCM
text and two SRAM prefixes matching verified pre-test progress. Preserve the
empty current SRAM, then restore that known8192-byte copy with atomic/readback
verification; no newer save identified. Final strict51-MVP/49-lab archive passes.

Recovered2238-call session and96-operation PCM history show the prior reserve
erosion/pointer divergence/EBADFD pattern; no audio fix or controlled cache-speed
claim. Preserve all raw chains privately and publish identified text/metadata
with source hashes. Stock/snapshots/exact1.18 remain intact; splash uninstalled,
both one-shots unarmed. [Recovery and resume](docs/fat-recovery-2026-10-09.md).

## FAT repair need re-verified — 2026-10-09

Fresh read-only CHKDSK on the known card repeats both invalid backup allocation
units and 1,472 KB in 14 lost-chain files. Independent byte reads fail with
Windows1392 on the same entries; current SRAM remains empty and stock splash
hash matches. Record the active-volume false-positive caveat and corroborating
evidence. Repair/recovery remains approval-gated; no card repair, splash install
or re-arm. Audio cause and card hardware health remain unresolved.
[Verification and exact resume point](docs/fat-verification-2026-10-09.md).

## MVP1.18 return and Vesper boot artwork — 2026-10-09

Magitek Bio Blast again produces an audio descriptor error and returns to our
library. Exact1.18 payloads match. Fresh failure/session/PCM files and current
SRAM are zero bytes; two backup entries are unreadable. Read-only FAT32 check
confirms invalid first allocation units and lost chains. Preserve51 readable
MVP/progress files,49 lab files and a private hash-verified412-file full-card
backup. Snapshots and earlier SRAM copies survive. Stale1.16 stderr is not new
1.18 evidence; cache performance and the current PCM stop cannot be priced.
Backed-up repair/recovery consent is pending; no card writes or re-arm.

Build the requested black/cyan feathered V/heart loading screen from the user's
preferred reference. Recover the embedded ZIP/sprite ABI and replace only its
artwork span, keeping all stock code/handoff bytes exact. The actual stock ARM
decoder and all18 sprite draws pass pixel/canary checks. Publish authored art,
packer, original-code checker and guarded install/rollback source; vendor ELF
stays private. Installation and physical appearance wait for a healthy card.

[1.18 return](docs/snes-mvp-1.18-return.md), [boot artwork](docs/vesper-boot.md).

## SNES MVP1.18 caches colors for Magitek Bio Blast — 2026-10-08

1.17 starts FF6 on the first attempt and sustains35,763 calls overall before
Terra's Magitek armor Bio Blast drains audio reserve and returns to our library.
The move is not Edgar's Tools Bio Blaster. Final ordinary calls average17.981ms
wall /16.638ms main CPU; sampled inclusive PPU rises from3–4ms to8.150ms.
Fresh native failure records verify; wrapper run log/session backup are stale1.16.
The user withdrew expected driving snow after checking playthroughs.

Reproduce the actual Magitek effect offline from a private Narshe snapshot,
forcing only battle entry, then using real menu inputs. Add a bounded36KiB RGB
color cache keyed by indexed tile, palette, bit depth and color epoch. Actual
VRAM decode, both CGRAM half-writes, brightness and load rebuilds invalidate it.
Transparency/depth/flips/math remain dynamic. All original renderer work counts
are identical;93.36% tile reuse removes48.71% of palette-lookup row work in the
matched effect window. The earlier losing Lab1 cache remains a negative result;
this candidate still needs A7 performance proof.

Independent pixel/depth/math/cache/collision/wrap tests and131,072 extracted
CGRAM seam cases pass.1,200 full Magitek frames plus12,000 intro/Narshe frames
match original pixels/native PCM/geometry/periodic state. Native PCM, snapshots,
input, splash, display ownership and diagnostic isolation pass. Preserve saves,
stock/hook and lab; create a separate core-matched snapshot header.
Installed02:45 UTC (October8 Chicago): all28 prior private and49 lab files,
stock and hook independently verify; game armed, lab unarmed. Hardware pending.


[1.17 return](docs/snes-mvp-1.17-return.md), [implementation](docs/snes-mvp-1.18.md),
[physical test](docs/snes-mvp-1.18-test.txt).

## SNES MVP1.17 isolates diagnostics after sustained1.16 result — 2026-10-06

Archive the1.16 return read-only: exact release,48 MVP/49 lab files,19 prior
game-progress files unchanged and two updated SRAM files safely archived.
Successful retry delivers31,601 full video callbacks over526.812 active seconds
(59.985 calls/sec), zero held drawings/duplicate callbacks/audio-write errors,
one successful snapshot load, four pauses and clean save/exit. User reports
significant improvement. Both wind sound and blowing snow seem missing in
opening outdoor Narshe gameplay; correctness remains unresolved.
[Return and limits](docs/snes-mvp-1.16-return.md).

First-attempt70-call failure survives under its unique1.16 failure bundle.
Main CPU stays roughly9ms while wall cost reaches18–39ms. Wrapper discovery
and SD copies run11.27–11.57s uptime, overlapping reserve collapse and11.470791s
fault. Strong scheduling-interference hypothesis, not yet proven causal.
Move routine inventory/sync before child launch and final log copies after
child exit; remove the live background monitor entirely. Fault traces and
failed-session reports remain durable, while abrupt poweroff can lose RAM-only
routine progress. Keep the1.16 core and sound/render/admission policies exact.

Actual wrapper fixture rejects old live diagnostic writes and qualifies new
isolation, final progress, fault persistence and splash/ready/watchdog contracts.
ARM runner audio/state/save/display contracts pass.12,000 full-core frames
match clean pixels, native PCM, geometry and periodic state. Add private offline
scene-capture source; game pixels/PCM and all private inputs remain local.

Installed and independently read back at13:21 UTC: all26 original private and49
lab files, stock/hook, original wrapper and snapshots preserved. Game one-shot
armed; lab unarmed. Owned release and curated qualification are immutable.
[Implementation](docs/snes-mvp-1.17.md), [next test](docs/snes-mvp-1.17-test.txt).

## SNES MVP1.16 fixes redundant fixed-color raster invalidation — 2026-10-06

Archive the1.15 return read-only: exact payload,45 MVP/49 lab files, all21
game-progress files and stock/hook unchanged. Three audio-failed attempts,
two retained final reports; both snapshot loads succeed before19/18 calls
and controlled audio failure. Ordinary restored-scene main CPU about18ms,
wall19.3–19.5ms and sampled PPU about10ms. First detailed fault history was
overwritten by retries. [Return](docs/snes-mvp-1.15-return.md).

Replay the exact private state locally. All214 pending `$2132` flushes per
frame leave effective fixed color unchanged; raw component-tag changes force
unnecessary scanline render jobs. Flush on actual selected-component changes,
preserving original assignments and byte latch. PPU updates drop217–223 to4–10,
with identical31,520 requested tile rows and full output.16,777,216 extracted
stock/patched register cases and1,200 exact-core frames pass. This is removed
work, not a measured physical speedup. [Repair](docs/snes-mvp-1.16.md).

Retain up to eight failed-session report/PCM pairs per process after failed
worker cleanup, with kernel-time/PID attribution to reject stale trace copies.
Real native failure/retry/later-failure fixture proves preservation. Correct
host-header C23 scanf redirection to the device's existing legacy ABI. All
runtime/core/boot/input/display/snapshot/lifecycle qualifications pass.

Install at2026-10-06 06:23 UTC, after another45-MVP/49-lab archive. Independent
readback verifies exact new payload, all23 original private files, stock/hook,
older wrapper, lab files and separate new-core state. Game armed, lab unarmed.
Immutable owned release and25 qualification artifacts published. Full native
speed, complete sound and first-launch stability remain physical acceptance.

## SNES MVP1.15 final candidate retains sampled phase history — 2026-10-06

Retain eight sampled call records separately from the last24 ordinary calls,
so APU/PPU measurements survive a long unsampled stretch. No additional
sampling or healthy card writes. Exact optimized1.14 core remains unchanged;
runner/native lifecycle/starvation and production-path qualification rerun.
Retire1.14's exact unconsumed marker only after archiving all files. Preserve
its release/evidence bytes.1.14 had no physical test;1.15 is the delivery
candidate for the same coherent execution-budget rewrite. [Details](docs/snes-mvp-1.15.md).

Final install archives45 MVP/49 lab files before writes; independent readback
verifies exact payload, all23 original private files, archived/nonpayload
files, stock/hook/older wrapper and separate qualified snapshot. Game one-shot
armed, lab unarmed. Curated24 checks and owned release published; device
native speed, sound and stability remain pending physical qualification.

## SNES MVP1.14 A7 execution-budget rewrite — 2026-10-06

Build the pinned Plus core with O3/LTO, hidden internals and explicit API
exports; permit builtin memory optimization and apply O3/LTO to the runner.
Replace planar tile decoding with NEON2/4/8bpp expansion into the existing
VRAM-invalidated cache. Reduce32040/44100 frontend arithmetic to178/245 with
exact signed truncation and preserved batch state. Reuse locked post-write
PCM observations while requiring freshness after each unlocked wait/request.

Retain24 recent per-call costs in RAM and sample inclusive APU/PPU thread CPU
on one call in64 after reset/resume. Include sampled status, frontend costs,
epoch and admission waits; do not mistake inclusive regions or observer costs
for an exclusive CPU census. Core equivalence passes1,200 frames with exact
pixels/PCM/geometry/logical state, plus independent planar/converter oracles.
Native runner checks now replay sustained19.8805ms production and expose
starvation without hidden re-priming, frame suppression or accounting loss.

Provide a guarded consumed1.13 installer, separate qualified old-snapshot
copy, independent readback and immutable publication. Full-speed/full-sound
device acceptance remains pending; core code growth and cache-miss-dependent
decode benefit are explicit limitations. [Implementation](docs/snes-mvp-1.14.md).

## MVP1.13 return and execution-budget review — 2026-10-06

Archive 44 MVP/49 lab files read-only, exact release, consumed markers and
unchanged stock/hook/core plus all 20 private progress files. Two fresh reports
fail after 26/230 calls; retry loads the snapshot successfully. Both report
successful synchronized capture. The second 96-operation history survives,
including 16,335 kernel READ_ALL bytes; retry replaced the first history.

The retained interval accepts 5,888 frames in 159.044ms (37,021/sec), while
reported hardware advances 6,912. Nine large batches average 19.8805ms apart.
Reserve erodes before application pointer diverges by 128, then 256, then 384
frames and SETUP. Starvation is the leading trigger; exact vendor mutation/
stop path remains unknown. No full software queue, partial transfers or EAGAIN
occur. Whole-session averages do not qualify the expensive phase. Display
reservation totals 1.066ms across 230 calls, so queue admission is not the
observed multi-ms loss per frame.

Add a read-only flight-history analyzer and [execution-budget proposal](docs/execution-budget-review.md):
phase attribution on the expensive state, whole-program A7 compilation,
targeted custom core paths and cheaper frontend servicing. Buffering/isolated
stall fixtures cannot prove sustained production. No new executable, card
writes or re-arm; prior whole-device poweroffs remain unexplained. See
[return](docs/snes-mvp-1.13-return.md).

## SNES MVP1.13 durable PCM fault capture — 2026-10-05

Archive the consumed 1.12 return: exact payload, 43 MVP/49 lab files, stock/hook/
core and 19 prior progress files unchanged; retain the changed SRAM backup.
One fresh final report has 1,106 calls, a successful snapshot load and the same
SYNC_OBSERVE/SETUP/384-frame discrepancy. Its aggregate rate is 59.819 active
calls/sec, with no intentional holds. The PCM history is absent and stderr is
empty; later periodic/final copies do not survive. Exact diagnostic loss and
native stop causes remain unknown. The backup session belongs to 1.11.
See [return](docs/snes-mvp-1.12-return.md).

Capture the first fault directly to the card, flush and fsync the file, rename
and fsync its directory before returning the PCM error. Preserve failed temp
evidence and append capture errno/sync status/bytes to error detail. Read the
kernel ring before card I/O; a refused read does not discard PCM history.
Retain unchanged core, PCM settings, admission and full drawing. No new healthy
file I/O; this is an observability repair, not a claimed playback fix.

Actual ARM client tests pass file/directory sync and injected sync failure
without hiding PCM errno. Real FF6 runner fault capture completes before return;
clean retry/two snapshot resumes pass. Wrapper immediate-error/direct-path and
existing runtime/core checks pass. Physical capture durability remains pending.

Install/readback complete at 2026-10-06 04:42 UTC (October 5 locally), after a
fresh 43-MVP/49-lab archive. All 22 current private files, snapshots, current
SRAM/backup, 49 lab files and stock/hook/core/older wrapper match their hashes.
Game one-shot armed; lab unarmed. [Capture contract](docs/snes-mvp-1.13.md).

## SNES MVP1.12 PCM fault history — 2026-10-05

Archive the consumed 1.11 return: 43 MVP/49 lab files, exact release and unchanged
stock/core/hook. Nineteen prior progress files and every snapshot/current SRAM
match; retain the changed SRAM backup. User confirms audio error/our library.
Two final reports contain 2,195/253 calls; the latter explicitly loads a
snapshot successfully. Both fail on SYNC_OBSERVE with post-fault SETUP. An
earlier stderr fault and both reports have appl_ptr minus accepted epoch count
of 384 frames. Cause remains unknown; the 59.897-calls/sec interval is not
sustained clean-play acceptance. See [return](docs/snes-mvp-1.11-return.md).

Add a 96-entry in-memory native PCM transaction history and capture it before
cleanup on the first sticky fault. Read the kernel ring through read-only
SYS_syslog READ_ALL, with explicit unsupported/permission errors. The wrapper
clears stale history and preserves the fresh file before child exit. No healthy
transfer formatting, kernel-log reads or SD writes; timestamp/memory overhead
is not physically measured. Keep the exact core, parameters, reserve and
controller. This is a diagnostic build, not a claimed fix.

ARM recorder/owner/native lifecycle, wrapper persistence and existing runtime
checks pass; unchanged core exact-output checks pass. Guard consumed-1.11
installation, archive first and independently read back all protected files.
Physical capture, stream stability and full-speed sound remain pending.
See [capture contract](docs/snes-mvp-1.12.md).

Installation completes at 2026-10-06 04:13 UTC (October 5 in America/Chicago)
after a fresh 43-MVP/49-lab archive. Independent readback verifies the qualified
1.12 payload, all 22 current private files including the changed SRAM backup,
all 49 lab files and unchanged core/stock/hook/original snapshots/older wrapper.
Game one-shot is armed; lab remains unarmed. Physical capture is pending.

## SNES MVP1.11 coherent PCM observations and resume — 2026-10-05

Archive the consumed 1.10 return: 43 MVP/49 lab files, exact release bytes,
19 unchanged prior game-progress files and updated FF6 SRAM retained. Both
attempts start native playback, then WRITEI fails with EBADFD after 72/605 calls.
The queue-overflow label was false; software high is 2823/8192. One pause and
re-priming survive; snapshot success was not explicitly logged. Stock fallback
follows library B exit/cleanup. dmesg is absent; vendor state-transition cause
and earlier whole-device poweroffs remain unproved.

Paced admission now waits for the worker's fresh generation. The exact shipped
owner fails a deterministic changed-device counterexample; the repair passes.
Read post-HWSYNC state/control using SYNC_PTR GET flags and negotiated-boundary
arithmetic. Retain fresh post-WRITEI-fault state and accepted counts per epoch.
Restore period readiness after drain/reset. Stop failed drains before snapshot
work; distinguish worker errors from true queue capacity faults. Add snapshot
load/rejection counters and RAM phase markers. Keep the same core, full drawing,
64ms priming and rate/period/buffer candidates; no silent stream recovery.

Actual ARM client/owner checks and the real FF6 native lifecycle fixture pass:
injected WRITEI failure, clean retry, two snapshot loads/re-primes, 25ms producer
stalls, 120 full drawings and exact successful PCM accounting. Existing
input/splash/display/save/final-runtime checks remain. QEMU is not handheld
performance evidence. Guard consumed 1.10 installation, archive before writes,
retain all returned progress and independently read back before publication.
See [repair](docs/snes-mvp-1.11.md) and [return](docs/snes-mvp-1.10-return.md).

Installation completes after another verified 43-MVP/49-lab archive. Independent
readback verifies the exact 1.11 payload, all 22 current private files including
the returned updated SRAM, all 49 lab files, original snapshots and unchanged
core/stock/hook/older-wrapper hashes. Game one-shot is armed; lab remains
unarmed. Physical playback, snapshot resume, speed and stability are pending.

## SNES MVP1.10 PCM startup repair — 2026-10-05

Archive the consumed 1.9 return before updates: 43 MVP and 49 lab files,
exact released payload and 18 unchanged previously protected game-progress
files. Native PCM accepts 44,100Hz/128-period/3,712-buffer and all 2,823 priming
frames, then EBADFD prevents emulation. The failed operation and after-write
state were not retained; no game performance or hardware limit is measured.

Repair the client assumption that an accepted priming write leaves PREPARED.
Use the priming threshold, acknowledge RUNNING after full priming, START only
from PREPARED, and verify RUNNING afterward. Accept EBADFD only with a fresh
RUNNING observation. Retain operation, errno, state, availability and pointers
even on failure, plus running-stream playable minima. Preserve accepted-frame
accounting, visible XRUN and the exact 1.9 core. Replace byte-tail logging with
bounded shell-builtin runtime/kernel capture and test with tail/head/sed absent.

Independent ARM fixtures cover write-driven startup, healthy explicit START,
verified EBADFD race, rejected early/nonrunning starts and SW_PARAMS mismatch.
Final runner/owner/ownership checks and 1,200 exact core-output frames pass.
Source/check hashes gate the guarded consumed-1.9 update and independent
readback. Physical startup/audio/full-speed/stability and prior whole-device
poweroffs remain unqualified. See [repair](docs/snes-mvp-1.10.md) and
[return](docs/snes-mvp-1.9-return.md).

Installation completes after a fresh 43-MVP/49-lab archive. Independent readback
verifies the exact 1.10 payload, all 22 current private files, 49 lab files and
unchanged core/stock/hook/original-wrapper hashes. No snapshot migration or core
replacement occurs. Game one-shot is armed; lab remains unarmed. Physical
startup, playback, speed and stability are pending.

## SNES MVP1.9 native PCM owner — 2026-10-05

Implement documented ARM32 native PCM negotiation/readback, explicit playable
priming/START, STATUS/XRUN observation, SYNC_PTR readiness thresholds and bounded
DRAIN. One owner holds software/transfer/device accounting; device consumption
and eventfd notifications replace the game's intended1ms polling and separate
deadline gate. Prefer native32040Hz and bypass userspace conversion when accepted;
retain continuous conversion for a negotiated rate mismatch. Preserve every
drawing, the A7 renderer and proven UI/input/splash/display contracts.

Publish already-finalized/mixed Plus PCM at existing in-frame APU callback points
without changing emulation order. Exact1200-frame pixels/nativePCM/geometry/state
checks pass;1196 frames split identical PCM into earlier batches. Final runtime
passes180/30-frame mock runs, snapshot/SRAM and actual ownership/lifecycle seams.
Independent ARM fixtures cover constrained settings, partial/EAGAIN, START
failure after acceptance, XRUN, consumption-driven admission,30ms bursts, false
readiness, fixed admission deadlines, blocked cancellation and bounded flush.
Visible failure replaces silent stream recovery; physical sound/speed/stability
and the prior poweroff cause remain unqualified.

Add exact Lab2-return updater, archive-first/save-preserving deployment,
independent card readback and immutable selected publication with source/check
hashes. Keep vendor/core dependencies and all private progress local. Record
the wider hardware goal in a capability/cost/ownership roadmap; smooth FF6 is
not proof that the hardware is exhausted. See [1.9](docs/snes-mvp-1.9.md) and
[hardware roadmap](docs/hardware-capability-roadmap.md).

Install and arm after a fresh41-MVP/49-lab archive. Independent readback verifies
exact1.9 payload,20 original private entries,49 retained lab files, a separate
qualified snapshot and unchanged stock/hook/older-wrapper hashes. Lab remains
unarmed; following reboot takes stock after the consumed game one-shot.
Physical acceptance is pending.

## Lab2 physical return and source-first interface review — 2026-10-05

Archive and independently verify 41 MVP/49 lab files, the exact lab2 payload,
20 protected private entries and unchanged stock/hook/dispatcher/game paths.
Both one-shots consumed; zero card writes, no new build or re-arm. User reports
clicks between tests and some clicking during tests. Wrapper exits normally.

Retain all 1152 timer observations, nine audio traces, four 240-drawing producer
traces and 10712 driver calls with zero trace drops. Every short timeout method
averages about 10ms across load/slack settings; audio readiness can wake sooner.
All PCM targets are accepted, but accepted bytes and zero GETODELAY do not prove
complete playback. Bursty production exceeds nominal playable reserve; preserve
gap indicators as risks rather than measured xruns. All 973 scaler statuses are
FRAME_DONE|BUF_A_DONE: the suspected ten-sleep fallback never fires. Scaler
lifecycle means 2.26–2.29ms, with about 0.36–0.37ms in nonwait syscall brackets;
worker waits overlap production and are not serial core CPU costs.

Research Linux 4.19 OSS/native PCM and a pinned TinyALSA client. Document partial
fragment staging, POST versus SYNC/RESET, native parameter negotiation, priming,
device-driven refill, stream state and graceful drain. Identify split accounting
and multiple timing gates in current game source. ARM clients need the standard
SYNC_PTR path rather than assuming x86-style mapped status/control records.
Distinguish this source fact from vendor qualification. Matching Generalplus
sources remain unlocated; distinguish that search limit from hardware capability.
Propose one native PCM owner and publication of already-emulated audio during
long core calls before the next actual game acceptance. Extend the analyzer with
drain residues, nominal lead gaps and matched scaler lifecycles; independent
hand-calculated fixtures pass. Publish curated data with hash provenance.
See [return](docs/platform-lab-2-return.md) and [research](docs/platform-interface-research.md).

## Lab2 infrastructure contracts — 2026-10-05

Build the authorized next native probe around independently timed waits,
inherited/reduced/restored thread timer slack, OSS capability/readiness/drain/
reset behavior, actual32040/44100Hz streams, heap/chunk memory costs and coherent
audio admission under12ms steady/28ms occasional CPU work. Preserve every
synthetic drawing and PCM byte; native game performance is still unqualified.

Recover exact scaler/display ioctl sites and argument shapes from the pinned
driver. Command0x80045004 receives scalar3000 despite read-direction encoding;
status tests bit2 and its not-done path performs ten sleeps without rechecking.
Record real config addresses/queue flags, bitmap addresses, status and per-call
cost through exported syscall observers. No additional scaler command, hardware
queue, frequency, MMIO, scheduler-priority or watchdog change.

Actual ARM tests cover independent PCM bytes under odd shorts/EAGAIN/misleading
readiness, RTLD_LOCAL driver interception, timer slack restoration, sparse shell
splash/one-shot recovery and supervised TERM/KILL/reap. Draw readable labels at
their real resolution and ramp/drain tones. Bounded RAM traces persist as separate
phase batches. Add guarded lab1-to-lab2 updater, analyzer and hand-calculated
analysis fixtures. See [scope and boundaries](docs/platform-lab2.md).

Install and arm the isolated lab2 after a fresh41-MVP/17-lab archive. Independent
readback verifies both one-shots, exact released payload,13 retained lab files,
20 protected private entries and unchanged stock/hook/dispatcher/game/original
wrapper hashes. Physical test remains pending; no game performance claim.

## Hardware lab1 physical return — 2026-10-04

Completes and returns to stock; user reports clicks between tests and poor text
readability. Archive41 MVP plus17 lab files read-only, preserving20 private
entries and exact stock/hook/game/core/original-wrapper hashes. Markers consumed;
no card writes, replacement build or re-arm. Publish selected raw/derived data.

All four display phases complete240/240 jobs, including12ms CPU load at59.91
producer calls/sec. Audio samples retain34.83–46.44ms of negotiated-rate lead,
with zero write/query errors and~22.9ms maximum write gaps. This synthetic load
does not prove full-speed FF6 or resolve prior shutdowns. NEON beats scalar~2.5x
in the fixture; this color cache loses43–127% against NEON. CPU slicing gives
no clear benefit.5ms deadline lateness averages5.482ms, making intended1ms
poll sleeps suspect; timer quantum/config/slack remain unqualified.

Retain negative GETOSPACE; correct unqualified modulo-2^32 cursor analysis.
Add independently calculated staging/error/reset fixtures and returned-bundle/
private-preservation verification. Explain OSS non-mmap staging/block semantics,
UI downsampling and tone-reset boundaries; name the timer/consumption probe and
controller/PCM-publication/compact-kernel work next. See [return](docs/platform-lab-1-return.md).

## Hardware lab1 and custom-code investigation — 2026-10-04

Ben authorizes a bounded native test program to discover useful system behavior.
Build a separate A7/OSS/display lab with the qualified splash/GPIO/kernel-clock/
chunk ownership seams. Price scalar/NEON/generation-tagged tile color caching
under reuse/churn/thrashing; retain every draw's current compositing semantics.
Record raw OSS negotiation/queue/pointer/errors and service gaps with one writer/
observer, then exercise audio/display with equal12ms burst/sliced CPU budgets.
Buffer samples in RAM and fsync identified phase results outside timing.

Add whole-run60s supervision, TERM/KILL/reap, blocked-owner exclusion and reboot
hold after forced termination. Pass12,300 exact kernel cases, byte-granular
hostile transport, actual ARM null smoke/stuck-child checks, old-glibc ABI and
sparse-PATH wrapper/splash/one-shot cases. Add guarded archive-first installer,
read-only collector, analyzer and custom-code proposals. No full-speed or
physical stability claim; hardware test is pending. Install/arm only the
isolated lab after a39-file read-only archive; preserve20 private entries plus
stock, boot hook, game runner/core and original wrapper hashes. See [lab1](docs/platform-lab.md).

## MVP1.8 physical return and diagnostic repair — 2026-10-04

Played okay but clicking returned, followed by confirmed whole-device power-off.
Archive and verify39 files read-only; all19 pre-existing private files and
stock/hook hashes are intact. Exact returned release matches. Card unarmed.
Fresh previous checkpoint has1,648 calls, zero holds, ~57.93 active-loop calls/sec,
13.33ms mean core wall and3.00ms audio-lead wait per call. PCM accounting balances,
but device queue sampled empty and maximum accepted-write gap is40.004ms.
Shutdown cause and uninterrupted sound remain unproven; empty latest/tails and
stale1.7 final totals are explicit collection limits.

Correct the unsupported sed assumption: firmware lacks both head and sed.
Use shell builtins for line limits and splash zombie parsing; the actual wrapper
passes with both absent and no gameplay global sync. Source only, not installed.
Exact returned core passes10,000 visible-pixel/native-PCM/state equivalence
frames. Extend the harness without breaking device glibc2.30 compatibility.
Guard historical1.8 publication against changed qualified input bytes before
any writes; publish curated return and checks, retaining all historical hashes.
Document recovered factory poweroff path without claiming it fired. Next work
is bounded audio-headroom production and durable targeted crash records, with
full drawing retained. See [return review](docs/snes-mvp-1.8-return.md).

## SNES MVP1.8 forward A7 build — 2026-10-04

User directs a smarter A7 build instead of another device comparison. Specialize
seven NEON tile modes in emitted code, deinterleave palettes once per tile,
skip disabled/fixed-only color work and unused full math in half-blend rows,
and directly store fully covered spans. Add NEON backdrop/color-window passes
with original scalar tails. Catch/fix reversed-clip unsigned underflow at FF6
intro frame87 before deployment; exact pixels, native PCM and state now pass.

Retain O2, accurate Blargg sound, full drawing and queue ownership. Replace
repeated process/kernel discovery and global sync during play with one capture
and small30-second checkpoints. Test actual sync calls and sparse firmware
PATH. Add60k span/canary cases, palette guard page and emitted-code checks to
the existing8.4M color/280k row/1200-frame output qualification. Version fresh
checkpoints1.8. Guard installation over unarmed1.7, archive first, preserve new
Save Point SRAM and add a separate older qualified snapshot. Publish owned
release/evidence with history intact. Installed/armed after preserving all19
existing private files plus stock/hook hashes. Physical speed/audio pending.
See [1.8](docs/snes-mvp-1.8.md).

## MVP1.7 physical return — 2026-10-04

No crash; user reached a Save Point, saved and exited normally. Lag remains;
FF6's party menu helps partially. Archive/hash-verify 38 files with zero card
writes, preserving newly changed SRAM and backup. Marker consumed; card stays
unarmed. Exact release/core and stock hashes match. Fresh final/checkpoint
identities agree; main rc=0, display join and cleanup survive.

Record 7,068 rendered calls with zero holds, 129.381 seconds active loop,
54.629 calls/sec (91.17% native), mean core wall15.384ms/CPU13.986ms,
p95[21,22)ms, p99[35,36)ms and 31.084% definitely over budget. All generated
PCM plus priming accepted, but sampled empty device queue and71.280ms maximum
write gap leave starvation risk. Price producer display wait0.736ms and
audio-lead wait1.876ms per call without double-counting overlapping worker wall
or treating all throttling as recoverable cost. Add observed-loop analysis
with explicit timing limits.

Capture/sync windows average234.4ms; system CPU/meminfo/IRQ collection failed
because the firmware has no head command. Replace it with qualified sed in
source; test the actual wrapper with a restricted PATH lacking head and verify
CPU/memory contents. Keep released/installed1.7 bytes unchanged and guard its
exporter against replacement. Publish selected return evidence; private
SRAM/states remain local. No new runtime installed or test armed. See the
[return review](docs/snes-mvp-1.7-return.md) for remaining evidence gaps and next work.

## SNES MVP1.7 logging retry — 2026-10-04

After the failed 1.6 run, the user confirms stock boot and requests logging plus
another physical test. Retain the exact A7 core, full-render policy, UI and
audio/display pipeline. Add build/core/session identity, phases and coherent
progress checkpoints in RAM about once a second, outside core callbacks.
Include live audio-worker CPU, producer audio waits and existing core/display
metrics. Measure checkpoint duration and errors.

The wrapper persists the latest two progress records, three early thread
snapshots and a bounded latest thread/CPU/memory/interrupt/helper/kernel view.
Capture after two seconds, then five-second waits for 63 iterations; record
capture/sync duration and cancel/reap on child exit. This closes the end-only
report gap; sudden power loss may still lose the latest interval. Logging is
not a speed fix and may perturb timing.

Pass the full ARM/QEMU contract suite, a real-runner SIGKILL checkpoint check
and wrapper persistence while its child is alive. Archive/hash-verify the
returned card before updating. Install only owned runner/wrapper/test notes;
retain all 19 pre-install private progress files, core, boot hook and stock
binaries by hashes. Arm the one-shot last. Publish owned release and selected
verification without game/save/vendor files; retain historical 1.5/1.6 releases.
Physical result pending. See [test and evidence boundaries](docs/snes-mvp-1.7.md).

## MVP1.6 physical failure — 2026-10-04

The user reports very choppy sound, slow movement, good-looking graphics and
then whole-device power-off. Archive and hash-verify 33 returned files before
mutation. Launcher/core/wrapper match the installed release; stock binaries and
all 18 original progress files match the protected originals. The one-shot is
consumed; this return performs no card writes or re-arm.

Startup/splash/input and early runtime snapshots survive, but no child-exit
record or fresh 1.6 session report does. The retained last-session file is
byte-identical to 1.5 and must not be analyzed as this run. Early RSS is about
12 MiB with zero reported process swap; these samples do not identify the
shutdown mechanism or establish full-session memory/performance. Withdraw 1.6
from unchanged retesting, record the failed expectation, and require durable
session telemetry plus a controlled original/A7 hardware comparison before
another performance claim. Add actual-core validation to the report analyzer;
API/CLI checks preserve analysis for the original core and reject this stale
report for A7 without writing output. See [failure review](docs/snes-mvp-1.6-failure.md).

## SNES MVP1.6 — 2026-10-04

Implement A7 NEON 2/4bpp tile/color kernels and audio-first delivery in pinned
Plus. Remove adaptive drawing holds. Add a three-source ordered display FIFO
with buffer/publication reservation before the core and source release before
scanout. Add independent joined PCM service, partial/EAGAIN preservation,
transition-clear accounting, bounded lead and worker/device timing. Retain
accurate Blargg, the validated splash/GPIO/clock path and the known scaler backend.

Verify 8.4 million color comparisons, 280k rows, 1,200 exact pixel/native-PCM frames
and normalized emulated state; actual migrated-state runner resume for 120 frames;
full-render smoke for 180 frames and paced smoke for 30; real FIFO backpressure/teardown and legacy
contracts. Raw snapshots contain process pointers, now explicitly accounted
for in comparison. Install isolated core and separate FF6 snapshot copy; stock,
boot hook and 18 original progress files hash-protected. One-shot armed.
Physical 60 FPS/audio result remains pending. See [implementation](docs/snes-mvp-1.6.md).

## MVP 1.5 physical result and full-speed proposal — 2026-10-04

Physically confirm all four directions in launcher and FF6. Archive/hash-verify
returned logs and all private progress before any update; the card remains
unarmed and unchanged. Returned 23,872 calls with 2,826 held drawings (11.838%),
core-call mean wall14.591ms/CPU13.230ms, p95[19,20)ms and maximum40.844ms.
User reports occasional lag and rare random normal-play crackles. Zero write
errors and sampled nonempty queues do not establish zero playback underruns.

Publish the return analysis and a proposal combining ordered display queuing,
source release before scanout, audio delivery independent of video waits, one
pacing owner, and exact Cortex-A7 NEON tile/color kernels in Plus. Record the
recovered scaler fallback's unchecked sleeps and DSP arithmetic constraints.
This entry adds evidence/docs/collection tooling; no runtime/core behavior is
changed or new device test armed.

## SNES MVP 1.5 — 2026-10-04

Correct the shared physical D-pad map to GPIO200 Up, GPIO201 Down, GPIO202 Left, GPIO203 Right. The previous interpretation of native 10/40/80/20 masks was wrong. Regression expectations now come from the pinned stock executable's actual libretro mask table, with an independent Down+Left check. All ARM checks pass; the subsequent return physically confirms the correction. Original/private progress and production binaries remain unchanged during installation.

## SNES MVP 1.4 — 2026-10-04

Replace libc-clock absolute waits with direct kernel timing and relative remaining-duration sleeps. Keep menu repeats, logs, heartbeat and game deadlines on that clock. Captured hardware clocks later read kernel monotonic/boottime 8.361 seconds versus libc monotonic 447.327 seconds. **Device confirmed:** launcher operation, game start and save-state load. D-pad labels still incorrect. Returned report: 2,465 frames, two pauses, no audio-write errors.

## SNES MVP 1.3 — 2026-10-04

Add bounded input/exit/cleanup and runtime evidence. Preserve the stock shared heartbeat. Input remained dead: snapshots caught the main thread in the same absolute sleep six seconds apart. The D-pad change introduced an incorrect direction permutation and is superseded by 1.5. The autonomous /wdt helper was not shown to depend on our heartbeat.

## SNES MVP 1.2 — 2026-10-04

Complete the stock showlogo marker handshake before opening the MVP display. Device logs confirm splash exit and acknowledgment. Input still failed; readiness alone did not prove a functioning UI.

## SNES MVP 1.1 — 2026-10-04

Remove unbounded wait-for-all-buttons-released before the first frame. Independently suppress initially held keys. Add durable bring-up logging and bounded startup timeout. Device reached READY but the still-running splash replaced the UI.

## SNES MVP 1.0 — 2026-10-04

Initial SNES library, direct Plus runner, chunk-backed display worker, OSS audio, private SRAM/snapshots and simple pause UI. Local checks passed; the first handheld test stayed on the loading animation.

## Earlier adapter and hardware work

v11 retained adaptive internal drawing suppression and removed automatic diagnostic overhead. A v10 physical listening test was clean. v9 showed heavy full-render core calls missing the frame budget; rendering-disabled calls were much cheaper. Hardware v1/v2 established platform/ABI/runtime details. Hardware v3 showed stdout/stderr suppression did not materially reduce the UART interrupt storm or comparable CPU load. See [investigation history](docs/investigation-history.md).

## Firmware route return and USB dispatch correction — 2026-10-09

Complete passive capture archived privately in snes-mvp-return-20261009T165057Z
with strict51-MVP/49-lab progress preservation. Original init restored exactly;
no test armed. Only SD and RAM block devices; empty /proc/mtd and sys/class/mtd.
Vendor /bin/nand_part_info and /bin/nandsync exist; /dev/spidev0.0 exists but
its attached peripheral is unidentified. This does not establish flash access.

Offline exact sysinit disassembly: main at0x11540 dispatches only argument core;
other arguments, including usb_gadget, are ignored. sysInit at0x1151c initializes
PPU/DLA/audio/ADC only. Unreached usb_gadget_init at0x11260 loads usb-common only.
The script command /sysinit usb_gadget is therefore not evidence of active USB
gadget support; earlier suggestion overstated it. No button recovery sequence
found in this dispatch. This does not rule out boot-ROM/bootloader recovery.
Next work: inspect vendor NAND tools and identify SPI peripheral/boot storage
without raw writes; a persistent splash replacement remains unimplemented.
