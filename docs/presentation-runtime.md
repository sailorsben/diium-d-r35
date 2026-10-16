# Real-emulator presentation policy integration

The subsequent [matched physical package](presentation-ffvi-test.md) now covers
the same policy in the actual full-frame measurement runner, with80 ABBA/
reversed epochs and qualified recovery/install guards. [Physical FFVI results](presentation-ffvi-return.md) are now recorded; the
integration-only preparation described below remains preserved.

An isolated candidate now applies pressure3's presentation policy to the actual
owned-output emulator runner. This is offline integration and correctness
qualification. It has not been installed, armed, or physically qualified. The
last verified card state remains the unarmed pressure3 return; this work does
not access the card.

## Behavior and ownership

`build/prepare-presentation-runtime.py` creates the fresh ignored directory
`build/presentation-runtime-private-v1`. It copies the established gameplay
runner from `demand-private-v1/runtime-v1` and imports only `board.c`/`board.h`
from the hash-qualified pressure3 support. Existing production files, earlier
experiments and their evidence remain intact.

After unchanged PCM admission, the runner atomically tries to reserve a FREE
source plus FIFO credit. Available credit retains direct chunk rendering and
the existing ordered worker. Busy credit gives the core a separate aligned
123,008-byte heap allocation, including its renderer prefix/tail. The core
still executes, fully renders and produces every audio sample; its validated
video callback increments the intentional presentation-skip count without
submitting to the board. Unsupported direct-output geometry retains the core's
existing full-layout fallback. The core's output-finish seam releases its
render pointer after the callback. Scratch is retained through core teardown.

No READY job is replaced and no SCALER-owned source is written. Display drain
and join, input polling after admission, menu/state handling, PCM service,
priming, conversion, fault persistence and cleanup retain their established
paths. Production `audio-owner.c`, `audio-pipe.h`, `native-pcm.c` and
`native-pcm.h` remain byte-identical to the original gameplay runner. In
particular, no second audio finish is added.

`D35_PRESENTATION_POLICY=1` is the candidate default; `0` uses blocking reserve
in the same executable. Other values fail before loading the core or opening
PCM. Reports identify `1.19-presentation1`, the policy, rendered frames,
intentional presentation skips and total reservation/try wall time. Successful
full-render accounting is `rendered_frames = video_submitted +
presentation_skipped = runs`. These counters describe callback/submission
activity; they are not optical scanout or DAC evidence.

The pinned core is the existing demand-visible v3 gameplay core, SHA256
`1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8`.
Its binary and serialization ABI are unchanged. This does not promote the
separate draw-order optimization or resolve its performance regression.

## Verification

Run on the installed Linux/WSL toolchain, from the repository root:

```sh
python3 build/prepare-presentation-runtime.py
python3 build/check-presentation-runtime.py
python3 build/check-presentation-controls.py
python3 build/publish-presentation-runtime.py
```

Preparation refuses an existing candidate directory. The ARM executable uses
the production Cortex-A7 hard-float, time32, `-O3 -flto=4` build flags and the
device glibc 2.30 libraries. Functional fixtures use ARM/QEMU and fake hardware;
their timings are not A7 measurements.

The qualification covers:

- All 192 actual board ownership/FIFO combinations, including busy-state
  immutability and closed/stopping/null rejection behavior.
- The actual display worker with gated scanout: unchanged queued pixels,
  direct/copied submission, busy try-reservation, ordered completion and joined
  teardown before source storage is freed.
- The actual runner, real FFVI core, threaded audio owner and native PCM client
  with an independently consuming provider: 120 renders, 80 presentations and
  40 forced intentional skips; no lost/cleared PCM; two snapshot loads/resumes;
  one drain per stream; fault/retry persistence. Sustained underproduction still
  exposes starvation instead of hidden re-priming.
- A same-runner blocking control: 120 renders/presentations, zero skips,
  matching accepted/enqueued PCM identities, two state resumes and three drains.
- Unavailable display fails before the next core call. Invalid policy,
  omitted drawing and invalid video geometry remain errors under skip policy.
- 18 original FFVI effect/input contexts, 1,200 calls each: every rendered pixel,
  PCM byte/sample count and geometry match an independent unchanged-core sink;
  normalized emulated state matches every 30 calls. The candidate alternates
  direct output, scratch and no-acquisition fallback. The original ROM and
  bounded inputs are retained privately. This is 21,600 comparison calls, not
  21,600 physically played frames.

An initial assembly accidentally imported pressure3's diagnostic PCM collector,
which defers capture and therefore failed production's durable-fault assertion.
That attempt is preserved privately. Only the display board is imported in the
qualified candidate; the production PCM path is preserved. An O2 preliminary
build/check tree is also retained privately; final evidence identifies the
production-flag executable explicitly.

[Integration proof](../evidence/2026-10-15/presentation-runtime/qualification.json),
[control/error proof](../evidence/2026-10-15/presentation-runtime/controls-qualification.json).
Public artifacts contain authored source and metadata/hashes, not ROMs,
private states, saves, vendor libraries or card backups.

## Performance gate and next physical test

Pressure3 measured 0.004 ms reservation/try wall versus 11.480 ms blocking wall
after the first 48 ms synthetic burst, with recovery of the first five bursts
within 19.5–20.0 ms after their observed reserve minima. Its passing steady
cells recorded about 0.022–0.039 ms more mean main CPU per quantum. Those are
short, candidate-first synthetic results; they do not price this integration.

For the actual runner, measured A7 CPU saving, try-lock/branch cost, scratch
memory-route delta, cache effects and total added downstream work are **missing**.
The known extra heap allocation is 123,008 bytes, excluding allocator metadata.
ARM text grows from 93,529 to 94,826 bytes (+1,297); data grows 4 bytes and BSS
40 bytes versus the established owned-output runner. Those are footprint
measurements, not cycle costs. Source/binary hashes are retained in the
qualification. No exact remaining FFVI audio deficit or 20% margin can be
predicted from offline work counts or QEMU timing.

The applicable break-even inequality remains:

`avoided display-credit wall wait > added try/policy cost + scratch-versus-chunk
render cost + downstream recovery cost`.

With zero skips, avoided wait may be zero and the policy may add cost. It cannot
repair a sustained core CPU deficit. The existing 16.688153 ms nominal quantum
and complete valid cumulative native reserve, where available, remain the
physical acceptance basis.

Next is a **measurement/qualification test**, not production promotion:

1. Archive all returned card files/private progress before any mutation;
   require clean FAT, protected stock adapter/ROM/saves/UART hashes, clean pushed
   exact source and independent payload/readback/marker verification.
2. Use this one executable and unchanged pinned core/state/input/audio settings
   with policy `0` versus `1`. Retain the complete 1,200-frame windows and all
   workload/effect identity criteria. Use ABBA/reversed ordering, followed by
   sustained gameplay; do not compare different cores or silently shorten
   failed windows. A hardware harness/package remains to be prepared.
3. Collect bounded RAM histories for produced/submitted/skipped frames, actual
   executed load events, fresh input, worker ownership, valid PCM pointer/count
   identities and complete reserve recovery. Flush after owned workers stop.
   Separate CPU from wall wait, and censor invalid/error tails.
4. Establish visible cadence/input response and audible continuity on the
   handheld, normal menu/save/state resume and teardown, plus cold-boot return
   to stock with permanent UART correction. Counters alone cannot accept these.

The falsifier is failure to recover valid audio lead when display credit is the
constraint, equivalent added cost, any changed state/pixel/PCM/input behavior,
ownership/lifecycle fault or unacceptable visible cadence/audio. The 24 ms
and unloaded controls must not regress; 80 ms and sustained overload are not
promised fixes. Hardware acceptance and installation remain outstanding.
