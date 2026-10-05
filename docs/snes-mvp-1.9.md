# SNES MVP 1.9 — native PCM and production ownership

Built 2026-10-05 after the Lab2 return and Linux 4.19 interface review. This
replaces the game's OSS path and timer-polled production gates with one native
PCM owner. It retains the A7 renderer, every drawing, ordered display ownership,
library/pause UI, corrected GPIO translation and splash handoff. Physical native
PCM acceptance, uninterrupted sound, sustained speed and stability are pending.
The whole-device poweroffs in 1.6/1.8 remain unexplained.

## Implemented contract

`native-pcm.c` opens `/dev/snd/pcmC0D0p` nonblocking. It uses documented ARM32
Linux PCM structures and independently checked ioctl numbers; no ALSA library
or assumed x86 status/control mapping is required. It queries protocol/identity,
refines exact RW_INTERLEAVED/S16_LE/stereo settings, and reads back the selected
rate/buffer. It tries 32040Hz first, then 44100/48000Hz, periods 128/256/512/1024
frames and a bounded set of buffers. Unsupported settings fail visibly and are
logged. Node existence and local fixtures do not prove vendor acceptance.

The playable priming target is ceil(rate × 64ms), with at least another 20ms
of device capacity. At 32040Hz this means 2051 priming frames. Explicit START
occurs only after these frames are accepted into PCM and STATUS observes that
reserve. Priming is accounted silence; it is not counted as emulated audio.
There is no automatic underrun restart or silence insertion during gameplay.

`audio-owner.c` holds software queue, accepted transfers and device observation
under one lock. The producer reserves capacity before a core call; paced
admission waits until software backlog plus observed playable PCM is at most
the 64ms target. Hardware consumption can advance between observations, making
that estimate conservative. Device-space poll and an owner eventfd carry useful
wakes. SYNC_PTR/HWSYNC updates `avail_min` without overwriting `appl_ptr`.
Independent intended 1ms sleeps and the second frame-deadline gate are removed
from the physical game path. Kernel clocks remain for input waits and telemetry.

This reserve trades audio latency for jitter tolerance. It does not make
average emulation faster or prove 64ms covers every real stall. With accepted
32040Hz, callbacks enqueue native PCM directly; a different negotiated rate
retains the continuous fractional converter. Requested ALSA rates do not prove
the underlying DAC clock or absence of a vendor conversion stage.

Pause/normal exit flush queued audio, DRAIN to SETUP, then join before reset or
close. A full device that never progresses gets a two-second software-flush
deadline, observed within the 500ms fault-poll interval; PCM drain has a separate
one-second bound. Admission has one fixed two-second deadline, not a deadline
extended by wakes. Thirty-two consecutive writable wakes without transfer are
a protocol fault. XRUN is surfaced as EPIPE. Intentional failed-run cancellation
wakes/joins the worker; discarded software frames remain explicitly counted.
These bounds do not guarantee cancellation of a wedged vendor kernel syscall.

## Earlier core PCM without changing emulation

The pinned Plus core already finalizes/mixes audio at its existing APU callback
points inside `S9xMainLoop`, but previously retained those samples until the
frame ended. The source transform now publishes already-mixed frames during
that loop. It removes only the accepted prefix and keeps any remainder for the
end-frame flush. CPU/APU ordering, mixing/finalization points and rendered
pixels are unchanged. It does not emulate APU time on another thread.

Against the exact original, 1200 intro/snapshot frames retain exact visible
pixels, concatenated native PCM, geometry and periodic logical state. Named
host process pointers alone are normalized. In 1196 frames the identical PCM
arrives through multiple earlier batches. This proves bytes/state for the
tested workload, not physical delivery deadlines or all-game compatibility.
The final core CRC is `42df1bbe`, size 665040 bytes.

## Verification and deployment

Actual ARM checks execute the client against an independent constrained PCM
provider, including fixed ARM32 ioctl values, 44100Hz/512-frame fallback,
partial/EAGAIN transfers, START failure after accepted frames, asynchronous
DRAIN and visible XRUN. The actual owner is tested against independently
generated PCM, partial transfers, readiness/consumption, 30ms production bursts,
cancellation, false readiness, blocked flush and fixed admission deadlines.
Mocks are contract checks, not measurements of this handheld.

The final runner passes 180 unpaced and 30 paced mock frames, snapshot resume,
SRAM, menu/input/splash/clock/display ownership and abrupt-exit diagnostics.
Same-rate accounting is 96168 generated/enqueued frames plus 2048 mock priming
frames, with all 98216 accepted, zero holds and no leftover software audio.
`verification.json` pins executable/core/wrapper, source and check-artifact
hashes. QEMU timings are not device performance evidence.
The45 source hashes describe checked working-tree bytes. The publication audit
matches Git source bytes exactly or with only CRLF-to-LF text normalization;
all222 indexed evidence hashes and the new release bytes match exactly.

`package-snes-1.9.py` targets only exact consumed Lab2/1.8 D: bytes. It archives
all returned logs and private progress first, changes four owned payload files,
preserves stock/hook/lab/original-wrapper hashes and all existing private saves,
creates a separately qualified older snapshot for the new core, then arms last.
`verify-snes-1.9-card.py` independently reads the result and every retained
archive/file. `publish-snes-1.9.py` exports only authored runtime/wrapper/test
notes and curated verification. Core/vendor dependencies, ROMs and progress
remain local; historical releases are not rewritten.

Installed/armed after a fresh41-MVP/49-lab collection. Independent readback
verifies the exact payload,20 original private files,49 retained lab files,
stock/hook/older-wrapper hashes and the separate migrated snapshot payload/CRC.
The lab marker is absent; only the game one-shot is armed. Curated
[verification and installation proof](../evidence/verification/snes-mvp-1.9/)
and the [owned release](../releases/snes-mvp-1.9/) are published separately from
local dependencies and progress.

## Physical test

Use FF6 **Continue** for the latest Save Point SRAM. The separately migrated
snapshot is older progress; loading it can later replace SRAM on normal exit.
Play story/map → FF6 party menu → map, save and exit, then return D:. Logs report
accepted rate/period/buffer, observed playable range, XRUN/errors, owner wakes,
worker CPU, core call tails and display waits. Observed zero xruns does not count
every possible analog click or prove every drawing reached the panel.
The legacy device-queue min/max fields are producer samples and may include
priming/drained zero; they do not isolate gameplay starvation. Use native stream
state/error, fresh progress identity and accepted-write gaps together. A
zero-delay normal exit is not an underrun observation.

Full drawing at the core's 59.922743404Hz and continuous accurate sound are the
acceptance target. If initialization fails, retain its settings/error logs.
The consumed marker sends the following reboot to stock. The wider hardware
goal is recorded in [the capability roadmap](hardware-capability-roadmap.md).
