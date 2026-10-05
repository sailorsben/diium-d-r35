# Platform interfaces: what source already tells us — 2026-10-05

Ben challenges the investigation flow: documented contracts should be researched
before using another physical run to rediscover them. This review separates
upstream Linux 4.19 behavior, this project's implementation defects, recovered
vendor calls and remaining device qualification. No new card payload or test is
installed by this review.

## OSS facts available without another device run

The primary reference is Linux 4.19's
[pcm_oss.c](https://raw.githubusercontent.com/torvalds/linux/v4.19/sound/core/oss/pcm_oss.c).
The device exposes matching `snd_pcm_oss_*` symbols, but its vendor kernel is
4.19.128; upstream source is an interpretation reference, not recovered vendor
kernel text.

| Contract in upstream source | Consequence for this project |
|---|---|
| `snd_pcm_oss_write1` can accept a partial fragment into `runtime->oss.buffer` before transferring it to PCM | A successful write does not prove those samples are in the playable PCM buffer |
| `snd_pcm_oss_get_odelay` returns PCM delay without adding `oss.buffer_used`; an EPIPE can become zero delay | GETODELAY alone is neither total accepted backlog nor an xrun detector |
| Non-mmap GETOPTR `bytes` derives from `runtime->oss.bytes - delay`, masked with INT_MAX; `blocks` is backlog-related | Do not treat it as an unconditional raw hardware cursor, a modulo-2^32 clock, or interrupt count |
| GETOSPACE subtracts the OSS staging fixup from PCM availability | Negative free space is compatible with staging; do not cast it to unsigned capacity |
| `snd_pcm_oss_post` issues START; it does not flush the partial fragment and ignores start errors | Lab2's POST/zero-delay/RESET sequence was an insufficient drain contract |
| `snd_pcm_oss_sync` pads/flushes staging and drains; RESET drops PCM and clears staging | Use an owned, supervised completion path for a graceful stop; keep deliberate discard/reset separate |

These are source findings. [Lab2's return](platform-lab-2-return.md) supplies
corresponding observations: accepted/pointer/delay residue, negative free space,
partial writes, and residual bytes at nominal zero-delay shutdown. The record
cannot identify every audible click or prove the physical fate of each residual
sample.

## A documented native PCM route exists

The return identifies `/dev/snd/pcmC0D0p` (116:16), `controlC0` and ALSA timer
nodes. Missing `/proc/asound` does not negate these character devices. The
Linux 4.19 [native PCM implementation](https://raw.githubusercontent.com/torvalds/linux/v4.19/sound/core/pcm_native.c)
and [driver guide](https://www.kernel.org/doc/html/v4.19/sound/kernel-api/writing-an-alsa-driver.html)
define the contract; a pinned
[TinyALSA implementation](https://android.googlesource.com/platform/external/tinyalsa/+/e0f4106198318a8f16467428c5a4c3ad24f7d4cc/src/pcm.c)
demonstrates a small userspace client.

| Interface | Use |
|---|---|
| PVERSION / INFO / HW_REFINE | Query protocol, identity and feasible format/rate/period/buffer combinations |
| HW_PARAMS | Select actual constrained stream parameters and read back what was accepted |
| SW_PARAMS | Set start threshold, stop threshold, timestamps and `avail_min` explicitly |
| PREPARE / START | Prime an owned stream before playback starts |
| STATUS / SYNC_PTR / DELAY | Observe PCM state, positions and queued frames, including XRUN state |
| poll on PCM plus an owner eventfd | Wake for meaningful device space or new/control data |
| WRITEI_FRAMES, or negotiated mmap plus pointer commit | Transfer generated PCM with explicit acceptance/ownership |
| DRAIN versus DROP | Graceful completion versus an intentional stream discard |

Native poll registers on the PCM waitqueue and tests availability against
`avail_min`; error states produce an error indication. It does not require a
separate short sleep to keep time. An mmap mode requires negotiated support and
correct application-pointer commits; neither an advertised capability nor an
existing device node proves it works on this board.

An ARM-specific source boundary is already known: upstream 4.19 compiles the
usual mapped PCM status/control records only for X86/PPC/ALPHA. Its other-arch
path rejects those maps with ENXIO; PCM **data** mapping has a separate negotiated
driver/DMA contract. Therefore an ARM client must support SYNC_PTR/HWSYNC rather
than assuming x86-style shared status/control pages. The pinned TinyALSA client
demonstrates the SYNC_PTR fallback. This is an upstream design fact; the vendor
kernel may differ. No physical run is needed to design that fallback correctly.

This supports a concrete next implementation: one small native PCM owner with
read-back parameters, explicit priming, interrupt-driven refill and visible
stream state. Start with ordinary interleaved transfer; mmap is an optional
extension with a real ownership contract. Use ARM32/device-compatible headers
and ABI, not host ioctl sizes. A negotiated hardware rate may differ from the
core's 32,040Hz; preserve continuous conversion when required. There is no need
to invent an audio interface or infer its commands from scratch.

## Defects identifiable directly in our game source

`build/snes-mvp/runner.c` combines a separately sampled board delay with
`s.ring_count`, which **does include the audio worker's queue**: `pump_audio`
copies `audio_pipe_stats.remaining`. The two observations are not one snapshot;
an intervening transfer can produce an incorrect sum. GETODELAY also excludes
OSS staging. An earlier reading wrongly called the worker queue omitted; this
source trace corrects that claim. These are accounting risks, not a reproduced
attribution of every click. The runner polls
lead with intended 1ms sleeps and then applies a separate frame deadline.
`audio-pipe.c` also polls software capacity and adds intended 1ms backoff after
fast readiness. Lab2 establishes coarse timer wakes on this device, but the
split accounting and multiple gates are visible in source without that test.

Replace this with one audio owner's coherent accounting and one production
admission policy. Track generated, queued, transferred, playable and consumed
positions in their proper units. Reserve future sink capacity without mistaking
software capacity for playable sound. Keep input sampling late, bounded display
credits and every drawing. Condition/event notifications should carry meaningful
progress; control wakeups must not trigger arbitrary extra 10ms sleeps.

The reserve must cover a long core call plus refill/scheduling margin. A 23.22ms
reported PCM queue cannot cover a roughly 30ms producer blackout by arithmetic.
More playable reserve has an audio-latency tradeoff. Publishing already-emulated
PCM at correct in-frame synchronization points can shorten the blackout;
parallelizing emulated CPU/APU time incorrectly is not an acceptable shortcut.
The budget comes from actual core tails, not a fixed average-frame assumption.

## What remains vendor-specific

Bounded searches for exact `gp_pscaler_ioctl`, `pscaler_wait`, GPA7XXXA and
matching Generalplus kernel/SDK sources did not locate an applicable source
tree. This is a search limit, not proof that no source exists. Older ARM7/ARM9,
camera-app and different-Sunplus sources do not establish this A7 board's ABI.
The saved module map is useful provenance, but the matching display/audio module
bytes are not presently in the collected local inputs; only the board module is
available in the inspected card export. Do not pretend a symbol list is code.

Use the pinned userspace driver's DWARF/disassembly for exact call arguments and
the returned trace for costs/status. Its 973 successful statuses all include
FRAME_DONE, making the ten-sleep fallback a negative result for this workload.
Persistent scaler/A+B operation still needs a kernel completion/release contract.

Physical qualification should now answer concrete remaining questions: accepted
native PCM settings, stable refill under real FF6 tails, audible output and
sustained full drawing. It should validate the implementation produced from
these contracts rather than supply basic API documentation one run at a time.
