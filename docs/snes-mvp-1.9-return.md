# MVP1.9 physical return — 2026-10-05

Ben reports that the game never launched and the UI showed Audio Failure. The
returned one-shot is consumed. A read-only archive contains43 MVP/49 lab files.
Installed runner/wrapper/core match the exact1.9 release and all previously
protected game-progress files (18, including stock save slots) remain unchanged. No game performance measurement
occurred; there is no emulation workload from which to infer a hardware limit.

The fresh final report and saved first-attempt progress both identify1.9,
the new core `42df1bbe` and zero runs/drawings/generated audio. The native client
successfully selects44100Hz, period128, buffer3712, priming target2823. Its first
write accepts all2823 frames, then the audio owner reports EBADFD (77), displayed
as “File descriptor in bad state.” Successful priming count remains zero.
The retained PCM state2/queue0 precedes the failed transfer/start transaction;
1.9 does not preserve its after-write state. Do not call that prewrite state a
measurement of the failure's exact state.

This qualifies the native node, those parameters and one transfer. It does not
qualify START, consumption, audible playback, every32040Hz configuration, DAC
rate, sustained refill or full drawing.44100Hz selection is a bounded fallback
result, not proof that the hardware can only operate at that rate.

The precise bad-state operation is missing. Source trace puts it in the priming
transfer/status/START seam. Upstream Linux4.19's
[write path](https://raw.githubusercontent.com/torvalds/linux/v4.19/sound/core/pcm_lib.c)
can start playback while accepting frames. Its
[START precheck](https://raw.githubusercontent.com/torvalds/linux/v4.19/sound/core/pcm_native.c)
requires PREPARED and returns EBADFD for other states. Our1.9 client calls START
based only on queued frames, without checking the observed state. That is a
concrete client defect; the existing logs do not prove which vendor behavior
triggered this device's EBADFD.1.9 attempted a large automatic-start threshold,
but did not retain software-parameter or after-write state details.

`last-run.log` and `kernel-tail.txt` are empty, even though fresh progress and
platform CPU/memory/interrupt data survive. The wrapper lacks a final process
exit line despite recorded board teardown. Preserve those gaps. The record
does not establish that tail is absent or why its byte-tail captures are empty.
The repair removes that dependency and tests runtime/error capture with tail
absent; it does not invent a firmware utility diagnosis.

[MVP1.10](snes-mvp-1.10.md) repairs startup using a priming threshold and observed
PCM states. It records exact operation/state/pointers on faults and retains
running-stream playable minima independently of final drained zero. The
independent ARM provider models the returned44100/128/3712 settings, auto-start,
explicit-start fallback, a verified EBADFD/RUNNING race, rejected early start
and rejected nonrunning EBADFD. These qualify the repaired client, not the
device's next result. The renderer/core remain unchanged.
