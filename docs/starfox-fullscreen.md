# Star Fox full-screen LCD prototype

The Corneria replay produces a 256×224 RGB565 frame. Its visible content
fits in source columns 16–241 and rows 16–205. The prototype submits that
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

`wsl -e python3 build/prepare-starfox-fullscreen.py` builds a private
payload with the exact 16-entry core used in the successful physical audio
run. The crop activates only after the cold warmup in the Star Fox fixture.
The raw video oracle sees the original frame. The display worker receives
the packed viewport through its existing chunk-backed queue. The audio
probe still uses the 150 ms prime. Frame skipping remains off.

The ARM fixture passed checks for every packed pixel with padded source
pitch, a change outside the crop, a change on the last included pixel and
ordered flips. The supervised ARM replay matched the frozen video and PCM
oracle on all 1,200 ticks. All excluded pixels were black. The 16-entry
cache reused the same 165,006 rows. The firmware BusyBox check passed the
one-shot wrapper and marker consumption.
The preview resamples replay pixels on the host and does not model the LCD
scaler's filter or panel edge behavior.

## Physical acceptance

The scaler still outputs 640×480 and does the zoom in hardware. Source
payload drops from 114,688 to 85,880 bytes per submitted picture, or 25.1%.
At the baseline's 399 submissions this saves 11,494,392 bytes of packing
and input payload over the replay. There were no direct submissions in
that baseline. Actual A7 CPU and scaler savings have yet to be measured.
The additional work is a viewport calculation per callback. The change
breaks even if the avoided packing, comparison and scaler-input work
exceeds that cost plus any change in scaler time due to the new geometry.

The prior native run kept at least 5,042 frames in the observed hardware
queue. With a 256-frame margin, 4,786 frames (108.5 ms at 44.1 kHz) were
available at that low point. If the viewport adds no net time to that trace,
it predicts zero additional audio deficit. Compare the returned queue curve
and worker metrics to check that estimate on the real device.

The one-shot test should fill the LCD through the Corneria window, with a
legible HUD, correct row alignment and no tearing. Require all 1,200 ticks
with sound near the 20.03-second nominal duration, no XRUN or premature PCM
SETUP and clean teardown. Then the next boot goes to stock. This scope
covers one gameplay sequence. Title screens, menus and other stages need
their own picture checks before using the crop in regular gameplay.

The payload is built locally. I: has its FAT dirty flag set, and its
read-only filesystem scan found no errors. The prototype has not been
installed or armed.
