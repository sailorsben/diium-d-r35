# One-boot Star Fox LCD and audio measurement

Armed on I: from `7e3e014`. Independent readback verified all 2,005 files,
both markers and a clean FAT32 volume. The card arrived dirty and passed
the read-only filesystem scan. The dirty flag was cleared after sparse
archiving, and every original file hash matched before staging.
[Installation receipt](../evidence/2026-11-10/snes-throughput/stock-shell-display-installation.json).

## Handheld return

Both silent windows completed 1,200 emulated ticks on the real LCD. With
reuse enabled the scaler flipped 399 pictures and retained the previous
picture 801 times after comparing every visible byte. Both runs generated
641,626 source PCM frames and the software sink accepted all 885,184
queued frames, including its startup prime. One control and one reuse
window ran in that order on the same boot.

| Silent Star Fox measurement | Control | Identical-picture reuse |
| --- | ---: | ---: |
| Elapsed measured gameplay | 20.835 s | 19.813 s |
| Average emulated ticks per second | 57.60 | 60.57 |
| Mean wall time per tick | 17.363 ms | 16.511 ms |
| p95 wall time per tick | 26.307 ms | 25.081 ms |
| Main, audio and display thread CPU | 20.553 s | 19.656 s |
| Display worker CPU | 909.7 ms | 316.3 ms |
| Repack wall time | 1,053.9 ms | 307.1 ms |
| Comparison wall time | 0 ms | 680.1 ms |

The measured net saving was 0.852 ms wall and 0.747 ms of observed thread
CPU per tick. Repack and comparison timings are wall measurements. Worker
CPU and elapsed time can overlap. Both native windows ended before the
full workload, so the silent throughput does not establish sustained
audible playback.

| Native 44.1 kHz playback | Control | Identical-picture reuse |
| --- | ---: | ---: |
| Completed emulated ticks | 22 | 40 |
| Time from PCM RUNNING to failure | 421 ms | 724 ms |
| Minimum sampled queue before pointer drift | 134 frames | 161 frames |
| Application pointer advance beyond accepted writes | 384 frames | 384 frames |

Both traces record three 128-frame application-pointer advances followed
by `SYNC_OBSERVE errno=77` in `SETUP`. That matches the recovered vendor
low-reserve fill and DROP path. Both supervisors reaped their runner after
audio-worker join and display cleanup. Reuse postponed the failure by
about 303 ms in this pair.
[Vendor PCM behavior](snes-throughput-architecture.md#what-the-pcm-trace-now-explains).

Using the measured silent tick times and the full cycle-derived sample
quota, the end-of-tick publication model drops the maximum cumulative
deficit from 36,670 to 12,279 frames. The reuse case still exceeds the
2,567-frame prime budget after the guard by 9,712 frames despite its
16.511 ms mean. This model omits native audio overhead and assumes
publication at tick end. Its output describes sensitivity to sustained
bursts rather than observed playable PCM reserve.

The next device comparison can use the stock-shell prototype's vendor
`/dev/dsp` transport with the same core and separately record audio
acceptance and recovery. The stock driver binary opens that interface and
uses `write` for playback. The native windows above exercised direct ALSA
and leave the stock transport unmeasured for this workload.

The sparse return verified 2,058 file hashes. Both markers were consumed,
the FAT32 scan passed and the dirty flag was clear. The expected boot
dispatcher and swapfile were the only changed preexisting file hashes.
[Return measurements](../evidence/2026-11-10/snes-throughput/stock-shell-display-return.json).

## Test design

This is the handheld measurement that precedes the stock-shell prototype.
The controller runs the same pinned PGO core in four windows. Each window
replays 8,656 scripted warmup ticks and then 1,200 gameplay ticks. Both LCD
windows use the real scaler and flip worker with a software audio sink.
Both playback windows open the native 44.1 kHz PCM device. Each pair runs
once with identical-picture reuse off and once with it on. Frame skipping
is off throughout. The only setting changed within each pair is reuse.

The separate LCD pair can finish collecting timings if native playback
hits the SETUP/errno 77 failure again. A normal PCM failure still permits
the second native window. An aborted test returns to stock after cleanup.
If the supervisor cannot verify cleanup, reboot to return to stock. The
two markers are consumed before any display ownership. The next boot
uses the original frontend and the original stock libraries. The test
reads the existing Star Fox fixtures on the card and writes its progress
and evidence to its own profile.

## Measurement budget

The latest physical baseline is 15.357 ms mean core wall per tick across
the complete Star Fox window. The 16.688155 ms deadline leaves 1.331 ms
for added critical-path work. The first 13 comparable native playback
ticks previously added 2.466 ms over the aligned core-only replay.
Physical measurements for the PGO core, comparisons and added fencing
are pending. The prior measured costs per submitted picture are 0.863 ms
of repack wall and 0.767 ms of worker CPU in that short opening. They can
overlap. QEMU's 6.59–7.94% PGO core saving and 0.093 ms comparison cost
give reference values for sensitivity only.

For a repeat fraction `r`, break-even CPU is `r × (repack CPU + worker
CPU) > compare CPU + extra fence CPU`. The full-path mean wall must
also satisfy `core wall + native overhead − PGO wall saving − reused-job
wall saving + comparison/fence wall ≤ 16.688155 ms`. For the same PGO
core on both LCD paths, the comparison isolates the incremental cost
of reuse. Expect about 800 of 1,200 LCD jobs to disappear with unchanged
emulation and PCM. A positive net saving in measured CPU and elapsed
service time is the performance hypothesis. Report any regression.

The cumulative reserve model uses the cycle-derived quota of 534.688
source frames, or 735.948 sink frames, per nominal NTSC tick. Under the
2.466 ms overhead scenario with 8% PGO savings, 1.0 ms saved per repeated
picture and 0.1 ms comparison per tick, the predicted refill-limited
drawdown is 3,656 frames. That exceeds the 2,567-frame budget after the
256-frame guard by about 1,089 frames. At 1.63 ms saved per repeated picture
the same model gives 2,031 frames, about 536 frames inside budget. The
opening can therefore still fail at a viable average. Use the returned
native acceptance and pointer history to distinguish valid reserve from
vendor-added fill periods. Treat an early SETUP as a censored window.
[Full-window model](snes-native-throughput-followup.md#audio-reserve-is-a-second-deadline).

The stock-shell frontend is a separate build. Its game loop and stock
PCM path need their own device test after the LCD result. This package
measures the optimization in the existing isolated native controller.

## Running it

Safely eject I: and boot the handheld once. The first two gameplay
windows are silent. The latter two attempt native audio. The four
warmups may take six to eight minutes in total. Let the stock menu
return, then power down and reconnect the card. The Menu button
requests an early stop during the replay. Logs and prior progress are
archived before interpreting the return or arming another test.

Build and rehearse with `build/install-stock-shell-display-test.py prepare`.
The separate `stage` and `verify` operations check the existing card file
hashes, protected frontend, fixture identities, clean FAT and both markers.
The exact firmware BusyBox wrapper passed normal order, unarmed return,
PCM failure, user abort, crash and active-splash checks. The shared staging
fixture passed rollback checks at all three activation boundaries.
Reports are written under `retro/snes-shell-display1/results/`.
