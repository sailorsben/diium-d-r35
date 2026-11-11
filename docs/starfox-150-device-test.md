# One-boot Star Fox test with a 150 ms audio reserve

The one-shot installation on I: verified 2,065 file hashes, both boot
markers, and clean FAT32. The previous logs and private progress were
archived before staging.
[Installation readback](../evidence/2026-11-10/snes-throughput/starfox-150-installation.json).

## Handheld return

Star Fox completed all 1,200 Corneria ticks with native 44.1 kHz audio
in **19.974 seconds** of gameplay, close to the 20.026-second nominal
duration. The driver started once after accepting the 6,615-frame prime.
It accepted the whole stream and completed its drain with zero underruns
or write errors. Across 5,758 running pointer checks, the application
pointer always matched accepted writes. The lowest observed hardware queue
was 5,042 frames, or about 114 ms, and it held 6,808 frames before drain.

| Matched silent LCD runs | Cache off | Cache on |
| --- | ---: | ---: |
| Gameplay elapsed | 20.078 s | 16.795 s |
| Core thread CPU | 19.114 s | 15.861 s |
| p95 tick wall time | 25.222 ms | 20.598 ms |

The cache saved 3.284 seconds of elapsed time (16.4%) and 3.253 seconds
of core CPU (17.0%) over the same 1,200 ticks. Both silent windows and
the audible run rendered all ticks with frame skipping off. Each flipped
399 pictures and reused 801 identical LCD pictures. The renderer cache
reused 165,006 of 268,800 scanlines in both enabled windows.

The earlier predicted total used the silent sink's accepted count as if it
included a 2,823-frame prime. That sink actually uses 2,048 frames. Both
sinks generated 883,136 resampled frames from 641,626 source frames. With
the 6,615-frame native prime, the correct total was 889,751 accepted frames.

The return archive verified 2,107 files. Both boot markers were consumed.
The dispatcher and swapfile were the only preinstallation files with
changed hashes. Windows reported the dirty flag set, and read-only CHKDSK
found no filesystem problems. The dirty flag remains set.
[Return measurements](../evidence/2026-11-10/snes-throughput/starfox-150-return.json).

The audio result comes from one Corneria replay and the native PCM driver
trace. The 20% headroom target remains unmet in this run.

## Test design

The first window plays the Corneria replay on the real LCD and native
44.1 kHz PCM. It uses the 16-entry Mode 2 cache, exact duplicate LCD
reuse and explicit PCM start after 6,615 stereo frames have been accepted.
Frame skipping is off. Two silent LCD windows follow, with the cache off
and on in the same core and duplicate LCD reuse active in both. A cleanly
reported audio failure still lets those windows measure the renderer.

Each window warms the core through 8,656 scripted ticks and then measures
1,200 gameplay ticks. The wrapper consumes its two boot markers before
waiting for the stock splash to exit. A Menu press ends the test. The next
boot goes to stock. Test output is written under
`retro/snes-starfox-150/results/` on the card.

## What the measurements can establish

The 16-entry cache previously saved 10.2% mean and 7.6% p95 CPU time in an
ARM/QEMU toggle pair. Its two cache states matched the frozen picture and
PCM oracle, and its enabled state reused 165,006 of 268,800 scanlines. The
cache uses about 1.31 MiB of storage. The same-binary LCD pair measures
the net effect of lookup, comparison, miss recording and cache pressure while
holding the renderer build, LCD reuse and audio backend constant. Each
cached window records its actual cache counters after worker cleanup.

The core models about 59.923 NTSC ticks per second, giving 16.688155 ms
per tick and about 735.95 output audio frames per tick. With the 150 ms
prime and a conservative 256-frame margin, the audio model permits
6,359 frames of cumulative drawdown. The previous full silent trace
showed 12,279 frames of drawdown. If native audio adds 0.5–1.0 ms per
tick, the trace needs approximately 0.80–1.30 ms of uniform net renderer
saving per tick to keep up and stay within the reserve. Net saving is
avoided rendering time less the added cache work. A net saving of 1.0 ms
leaves about 2,148 frames of modeled margin at the lower overhead and a
5,920-frame shortfall at the higher overhead. The actual per-tick trace
replaces this uniform-saving estimate when the card returns.
[Reserve model and offline comparisons](snes-stack-audit.md).

An audible pass completes the 1,200 gameplay ticks near the 20.03-second
nominal duration, accepts the complete generated PCM stream in order,
and shows no XRUN, premature SETUP or advance of the application pointer
beyond accepted writes. Check the queue at the end and across the slow
opening so the startup reserve cannot hide a sustained throughput deficit.
The real sound and picture can also be checked while the test is running.

## Preparation and readback

The installer builds the isolated runner, exercises the PCM and display
fixtures, and runs the wrapper through the exact firmware BusyBox. The
profile-guided 16-entry core is checked through the full supervised replay
with the cache off and on, including the frozen oracle and the cache count.
Physical measurements run without the offline per-frame checksums so the
checksum overhead stays out of the timing results.

Before staging, the installer checks the current card against a sparse
archive of saved progress and previous logs plus a full file hash inventory.
It uses the existing rollback-aware one-shot activator and verifies the
payload, protected file hashes, dispatcher, two boot markers and FAT32 in a
separate readback pass.
