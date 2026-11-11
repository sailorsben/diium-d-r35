# Star Fox full-screen LCD prototype

## Corrected handheld return

The replacement completed the 1,200-tick Corneria replay in **19.975
seconds** with native 44.1 kHz sound and no frame skipping. It flipped 399
pictures and reused 801 identical ones. The longest scaler call was
**2.529 ms**. The PCM driver accepted all 889,751 frames, including the
prime, and drained without an underrun or write error. The running audio
queue bottomed out at 5,042 frames, about 114 ms. The launcher and both
workers exited cleanly. [Return measurements](../evidence/2026-11-10/snes-throughput/starfox-fullscreen2-return.json).

| Same Corneria replay on separate boots | Bordered | Full-screen |
| --- | ---: | ---: |
| Gameplay elapsed | 19.974 s | 19.975 s |
| Source comparison, total | 678.389 ms | 510.172 ms |
| Packing and any expansion, total | 310.926 ms | 434.133 ms |
| Combined comparison and packing, total | 989.315 ms | 944.305 ms |
| Longest scaler call | 2.477 ms | 2.529 ms |

Comparing the smaller viewport saved 168 ms in this replay. Expanding
changed pictures added 123 ms to packing, leaving a measured 45 ms
reduction in those two stages. The gameplay clock was within 1 ms of the
bordered run. This window still missed the 20% headroom target. The logs
verify display jobs and audio delivery. A direct look at the LCD is needed
to judge edges, tearing and HUD appearance.

The return archive verified 2,151 files. Both markers were consumed.
Among preexisting files only the swapfile hash changed. The card retained
the dirty flag, and the read-only FAT32 scan found no errors. Collection
made no card writes.

## Handheld failure and replacement

The direct-crop test completed all 8,656 warmup ticks. After five gameplay
callbacks a scaler call took 3.267 seconds, against a maximum of 2.477 ms in
the successful 256×224 control. The two-entry display queue filled. On the
sixth tick the producer waited 3.162 seconds for a slot, and native PCM
underran during that wait. Before the underrun the PCM application pointer
matched all 10,293 accepted frames. The supervisor reaped the runner normally
and both workers cleaned up. [Handheld return](../evidence/2026-11-10/snes-throughput/starfox-fullscreen-return.json).

The vendor path passes a 3,000 ms timeout to the scaler and has a sleep
fallback when completion is absent. The call duration is consistent with
that path. The return did not capture the scaler ioctl status, so the
precise hardware constraint on 226×190 remains unverified.

The replacement keeps the 226×190 game viewport and expands it into the
same 256×224 RGB565 input the original playback used. It retains the raw
viewport in the unused portion of each owned chunk slot and compares it
before expansion. Every source pixel survives the nearest-neighbor
expansion, and identical pictures still bypass the scaler entirely. The
ARM display-worker fixture verifies the full-size input, all viewport
pixels, repeated pictures and mode transitions.

`wsl -e python3 build/prepare-starfox-fullscreen.py` built the replacement.
The full supervised replay matched all 1,200 original video and PCM checks.

## Direct-crop experiment

The Corneria replay produces a 256×224 RGB565 frame. Its visible content
fits in source columns 16–241 and rows 16–205. The first prototype submitted that
226×190 viewport to the existing hardware scaler. The vendor's `DrawVFB`
passes the source dimensions and the panel's full 640×480 dimensions to
`PScaleRun`. The kernel programs the supplied width and height into its
input-size registers. [Vendor geometry call](../evidence/2026-10-05/lab2-driver-contract/disassembly.txt#L73).

The fixed crop makes the picture 13.3% wider and 17.9% taller on the panel.
The result is about 3.9% narrower relative to its height than the current
display mapping. A nearly proportional 216×190 crop clipped visible pixels
in all 1,200 Corneria frames, including part of the lives icon in the preview.
The 226×190 crop keeps the HUD and game picture in the tested sequence.

## Scope and qualification

Both variants use the exact 16-entry core from the successful physical
audio run and activate the viewport after the cold warmup. The raw video
oracle sees the original frame. The native audio probe uses the 150 ms
prime and frame skipping stays off.

The ARM fixture passed checks for every packed pixel with padded source
pitch, a change outside the crop, a change on the last included pixel and
ordered flips. The supervised ARM replay matched the frozen video and PCM
oracle on all 1,200 ticks. All excluded pixels were black. The 16-entry
cache reused the same 165,006 rows. The firmware BusyBox check passed the
one-shot wrapper and marker consumption.
The preview resamples replay pixels on the host and does not model the LCD
scaler's filter or panel edge behavior.

## Timing and physical acceptance

In the direct-crop experiment the scaler still outputs 640×480. Source
payload drops from 114,688 to 85,880 bytes per submitted picture, or 25.1%.
At the baseline's 399 submissions this saves 11,494,392 bytes of packing
and input payload over the replay. There were no direct submissions in
that baseline. Actual A7 CPU and scaler savings have yet to be measured.
The additional work is a viewport calculation per callback. The change
breaks even if the avoided packing, comparison and scaler-input work
exceeds that cost plus any change in scaler time due to the new geometry.
The physical result rejected that geometry.

The prior native run kept at least 5,042 frames in the observed hardware
queue. With a 256-frame margin, 4,786 frames (108.5 ms at 44.1 kHz) were
available at that low point. The replacement's added cost is the expansion
on changed frames only. It keeps the control's scaler payload size. The
native acceptance measurement compares the cost of copying and expanding a
changed frame against the former copy cost plus the time saved by comparing
smaller viewports. The corrected handheld return measures those costs and
the actual remaining audio queue.
In a synthetic ARM/QEMU loop the median costs were 18 µs for the old copy,
182 µs for scalar crop and expansion, and 178 µs for NEON crop and expansion.
These numbers price the software on the host only.

The one-shot test should fill the LCD through the Corneria window, with a
legible HUD, correct row alignment and no tearing. Require all 1,200 ticks
with sound near the 20.03-second nominal duration, no XRUN or premature PCM
SETUP and clean teardown. Then the next boot goes to stock. This scope
covers one gameplay sequence. Title screens, menus and other stages need
their own picture checks before using the crop in regular gameplay.

## Installation

I: was armed for one boot from `6516e13`. The pre-install archive retained
the logs and private progress, and the FAT32 mark-clean scan found no
filesystem errors. Readback matched all 2,114 expected files, including
both markers and the stock binaries and saves. The launcher dispatcher
was the only preexisting file changed.
[Installation receipt](../evidence/2026-11-10/snes-throughput/starfox-fullscreen-installation.json).

Both markers were consumed. The return archive verified the payloads,
stock binaries and all prior progress. The read-only FAT32 scan found no
filesystem errors. The dirty flag was set. The replacement build was not
installed or armed during collection.

The replacement from `0751cb1` was armed on I: for one boot. All
2,129 preexisting files matched the crash archive before installation.
Readback matched all 2,136 expected files, including both boot markers,
and the FAT32 dirty flag was clear. The test still runs the 1,200-tick
Corneria sequence with sound and submits 256×224 frames to the scaler.
[Replacement installation receipt](../evidence/2026-11-10/snes-throughput/starfox-fullscreen2-installation.json).
