# MVP1.16 return: sustained full rendering, separate cold-start failure

The user reports a significant improvement: very playable combat and party
menu, successful Save Point save and snapshot load. The first FF6 launch still
returns an audio error; the second works. Both wind sound and blowing snow seem
missing in opening outdoor Narshe gameplay. This report does not establish
whether the precise expected weather effect belongs to that gameplay map or
the earlier story/march sequence.

Read-only return archive: `snes-mvp-return-20261006T125627Z`,48 MVP and49 lab
files, source/copy/source hashes checked, both one-shots consumed. Installed
runner/wrapper/core match1.16 exactly. Stock/hook/core and19 prior game-progress
files match; two changed SRAM files are archived. All original snapshots remain
unchanged. Private ROM/state/SRAM and rendered game captures are not published.

## Successful retry

| Returned measurement | Result |
|---|---:|
| Consecutive core calls / video submissions |31,601 /31,601|
| Active gameplay loop time |526.812s (8.78min)|
| Core calls / active second |59.9854|
| Intentional held drawings / duplicate callbacks |0 /0|
| Audio write errors |0|
| Snapshot loads / rejected loads |1 /0|
| Pause/resume epochs |4|
| Mean main core wall / CPU |12.179 /11.287ms|
| Mean producer wait for display credit |0.0349ms|
| Minimum running playable reserve |1,068 frames (24.2ms)|

Every generated sample is accounted for:16,896,612 native frames,
23,256,570 resampled frames,11,292 separately counted priming-silence frames,
23,267,862 accepted frames, zero remaining/cleared frames. The final application
pointer equals the accepted epoch count. Save/exit, joined display shutdown
and wrapper exit0 are recorded.

This is substantial physical evidence of sustained production after the raster
repair, unlike the earlier1.15 failures after18/19 expensive calls. It is not a
controlled same-scene CPU comparison: the user traversed and saved progress.
There are occasional long calls (maximum36.9ms). Generated/submitted video is
not independent panel scanout timing, and complete accepted PCM is not proof
of every intended audible effect.

## First launch: observer workload overlaps the stall

The new unique failure bundle retains the first70 calls and their PCM history
despite the later successful retry. Calls47–62 cost roughly7–9ms CPU and wall.
Then:

| Call | Wall | Main CPU | Audio callback wall |
|---|---:|---:|---:|
|63|18.086ms|9.255ms|3.692ms|
|64|38.720ms|9.519ms|18.208ms|
|65|19.644ms|9.140ms|9.950ms|
|66|17.952ms|9.086ms|8.294ms|
|68 (sampled)|27.711ms|10.169ms|5.666ms|
|69|26.601ms|9.450ms|7.710ms|

The last call includes fault persistence and is not a normal latency sample.
The successful observation at11.437640s has762 queued frames; the fault at
11.470791s follows a33.151ms observation gap. The final post-fault SETUP read
has a384-frame application-pointer/count discrepancy. This trace does not
individually resolve three128-frame steps or identify who advances the pointer.

The wrapper's first diagnostic checkpoint runs **11.27–11.57s uptime**, exactly
overlapping the off-CPU stalls and failure. It inventories every child task,
reads CPU/memory/interrupt state, launches helper processes and copies several
files to the SD card. Removing global `sync` had left all this work in live
gameplay. Later small checkpoints take30–40ms; the first takes300ms. Their
elapsed duration alone is not CPU usage or proof of blocked ioctl duration.

This is a strong owned scheduling-interference hypothesis, not proven causality.
The roughly9ms main CPU distinguishes this short cold-start failure from the
old sustained18ms CPU deficit. The second launch begins after discovery and
runs nearly nine minutes. [1.17](snes-mvp-1.17.md) removes the entire live
diagnostic workload instead of delaying it to another arbitrary gameplay time.

## Narshe effects boundary

Extended local replay compares12,000 full frames against the clean core:6,000
boot/intro and6,000 from the unchanged private Narshe snapshot, with scripted
movement/menu inputs. Visible pixels, native PCM, geometry and periodic logical
serialized state match exactly. A separate600-frame no-input private capture
shows the outdoor mine entrance, with no visible blowing-snow overlay in the
inspected frames. It produces320,813 native stereo PCM frames.

That narrows investigation to game phase/state or baseline emulation before
the display path. It does not establish that the clean core is correct, that
the whole story sequence was reached, or that wind is audibly correct. No
effect-disable setting or DSP change was introduced by1.16. The Blargg APU
still implements noise, echo and signed BRR/interpolation behavior; no speculative
DSP or layer patch ships with the diagnostic-isolation repair.

Curated reports, first PCM flight history, checkpoint times and extended replay:
[`evidence/2026-10-06/snes-mvp-1.16-return/`](../evidence/2026-10-06/snes-mvp-1.16-return/analysis.json).
