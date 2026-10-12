# Combined renderer manual return — 2026-10-11

Ben reports Bio Blast seemed fine, then Confuser crashed. The exact staged
core and regular runner hashes match. All returned retro files are privately
archived and hash-verified at `device-evidence/a7-pair-before-20261012T043106Z`.
Readonly FAT is clean; marker consumed; zero card writes and no rearm.

The retained session lasts225.095 seconds, with13,456 core calls,13,455 submitted
and flipped drawings, zero held drawings and one audio publication failure.
It returns to our library, accepts B and closes the display orderly. This is
a handled PCM failure, not evidence of a C crash, segmentation fault or device
power loss. Native SYNC_OBSERVE returns errno77, then reports SETUP/state1.

The23 complete calls immediately before the failed call average17.298ms core
wall,15.953ms core CPU and0.193ms admission:17.491ms against16.688ms nominal.
That predicts a local deficit of roughly2,024 sink frames/sec (4.59%), requiring
at least0.803ms saved per call before other loop costs and headroom. This short
tail is a local prediction, not a whole-effect sustainable throughput price.
The final aborted call takes28.524ms including13.057ms audio failure handling;
using it as a renderer cost would manufacture the wrong diagnosis.

Sparse PPU CPU samples rise from3.232ms at run13316 to6.701ms at13380 and7.652ms
at13444; APU-inclusive samples are4.048,4.166,4.261ms. Rendering growth is the
leading cost explanation, but sparse samples cannot identify which renderer
path grew. The effect name is supplied by Ben; telemetry has no effect marker.

The native tail shows reserve erosion followed by application-pointer advances
without matching successful writes: bias0 ->128 ->256 ->384 frames, then SETUP.
This resembles the failing baseline Bio Blast handshake. Reported reserve is
not an independent physical measure once those extra pointers appear. The
vendor stop edge remains unresolved; underproduction is a leading trigger,
not a proved complete account of the driver behavior.

Ranked explanations: (1) Confuser exercises remaining expensive rendering work,
possibly outside the narrow window-batching eligibility; (2) main/audio/display
contention contributes to deadline misses; (3) vendor PCM state behavior turns
a depleted reserve into the fatal publication stop. A new renderer correctness
bug remains possible, but this return provides no invalid access or pixel
mismatch evidence for it. Bio Blast's observed success supports the bounded
optimization; it does not qualify all effects.

Before another build, inspect the existing ROM effect script and combined C
eligibility, and establish a reproducible pre-Confuser state/input sequence.
Missing evidence is the exact effect-aligned state/input replay, renderer
mode/window/mosaic/color-math eligibility and subphase/work counts, a complete
effect/recovery timing timeline, and independent vendor pointer-stop semantics.
Current saves are preserved but not assumed to capture immediately before
Confuser. No diagnostic, candidate or audio recovery policy is installed.

Reproduce derived costs with `python build/analyze-combined-gameplay-return.py
device-evidence/a7-pair-before-20261012T043106Z`. Raw private state/SRAM and
full-card artifacts stay outside publication.
