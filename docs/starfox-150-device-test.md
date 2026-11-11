# One-boot Star Fox test with a 150 ms audio reserve

I: is armed. Independent readback verified 2,065 file hashes, both boot
markers, and clean FAT32. The previous logs and private progress were
archived before staging.
[Installation readback](../evidence/2026-11-10/snes-throughput/starfox-150-installation.json).

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
cache uses about 1.31 MiB of storage. A7 time saved and the individual
lookup, comparison, miss recording and cache pressure costs are still
unmeasured. The same-binary LCD pair measures the net difference while
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
The frozen replay generates 641,626 source frames. With 44.1 kHz conversion
and the 6,615-frame startup prime, the software queue should accept 888,976
frames in total.

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
separate readback pass. The test is a measurement. Handheld playback and
performance are pending until the device runs it.
