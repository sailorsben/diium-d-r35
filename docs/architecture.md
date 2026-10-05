# Userspace platform architecture

The implemented MVP is SNES-only. [MVP1.6](snes-mvp-1.6.md) implements full
rendering with a tailored A7 core and corrected peripheral ownership; its
physical run failed with severe lag/choppy sound and whole-device power-off;
see the [failure review](snes-mvp-1.6-failure.md). The longer [platform review](reference/platform-redesign/proposal.txt) is a design proposal, not a completed multi-emulator product or a speed claim.

[MVP1.7](snes-mvp-1.7.md) retains that exact core and pipeline for the user's
requested logging retry. Fresh RAM progress and bounded wrapper persistence
repair the lost-final-report gap; physical performance remains unqualified.

The [1.7 physical return](snes-mvp-1.7-return.md) confirms zero holds and normal
save/exit, but only ~54.63 emulation calls/sec of active-loop time. FF6 party
menu relief and the expensive-call distribution point toward workload-dependent
cost. Producer display blocking and audio-lead control are separately priced;
overlapping scaler/flip wall must not be mistaken for additional CPU. The
source diagnostic command correction is incorporated in1.8.

[MVP1.8](snes-mvp-1.8.md) moves forward on A7 at the user's direction: emitted
tile-mode specialization, cheaper palettes, vector backdrop/window passes and
less shell logging during play. Its [physical return](snes-mvp-1.8-return.md)
records clicking and whole-device power-off; the retained interval has zero
holds and ~57.93 calls/sec. Mean core wall13.33ms plus3.00ms producer audio-lead
wait makes production control a concrete next target. Some wait is legitimate
throttling; a bounded audio-headroom controller must preserve native average
speed and ordered full drawing. Crash cause remains unknown. Current source
fixes capture without head/sed but is not installed; shipped1.8 is unchanged.

## Implemented owners

[Hardware lab1](platform-lab.md) is a separate supervised executable, dispatched
through the existing one-shot /bin/sh entry. It preserves the original1.8 game
wrapper byte-for-byte and does not change the game runner/core. This lab's
whole-run deadline and raw single-owner OSS observations are not yet changes
to gameplay scheduling or supervision. Full rendering at native cadence remains
the game runtime's acceptance target.
The [physical lab return](platform-lab-1-return.md) demonstrates peripheral
service under substantial synthetic CPU load, while exposing wake lateness
and OSS staging. Coherent consumption-based admission and in-frame PCM
publication remain proposals for gameplay, not changes already installed.

[Lab2](platform-lab2.md) exercises timer/device wakeups and coherent single-owner
audio admission in an isolated synthetic workload. Exported ARM32 observers
price the vendor scaler/display calls and retain actual arguments/status without
changing their sequence. Neither its controller nor scaler lifecycle changes
are installed in the game runtime. Its [physical return](platform-lab-2-return.md)
completes all phases but retains audible clicks. Coarse short timer wakes,
insufficient burst reserve and OSS staging/drain semantics identify concrete
audio-controller work. The suspected scaler fallback never fires.

```text
boot wrapper
  consume one-shot -> archive/log -> finish showlogo -> start one child

main/UI
  scan library -> first paint -> suppress held inputs -> navigate
  release library allocations -> runner -> pause UI -> library/exit

runner
  bounded ROM/ZIP loading -> exact core -> environment/input callbacks
  continuous resampler -> bounded PCM queue -> OSS transport
  native-FPS scheduling + every drawing -> reserved board video submit
  ROM/core-qualified SRAM/snapshot -> explicit unload

board + timing
  GPIO/mixer -> chunk source slots -> owned display worker -> vendor driver
  kernel clock -> relative waits -> durable bounded lifecycle diagnostics
```

This is one executable with separated C modules. Menu/library allocations are released during gameplay; the core's synchronous load-from-memory ownership permits reclaiming duplicate ROM input after load. The existing vendor kernel, board initialization and driver remain bring-up dependencies.

The producer reserves one of three source slots plus FIFO credit before the
core. The worker releases a source after scaling, holds output through flip,
and completes jobs in order. No core-owned pointer is retained or READY image
superseded. Shutdown drains/joins before display/chunk teardown.

Audio callbacks enqueue every converted frame. One audio worker owns nonblocking
transport, preserving unsent frames and partial stereo-frame tails. Reserve
capacity before the core; stop/join before transitions reset/clear the stream.
Priming, clears and remainder are accounted separately. Snapshot operations
qualify core/ROM and roll back on failed load.

## What is retained deliberately

Plus's accurate sound and continuous conversion remain. 1.6 removes adaptive
suppression and publishes audio before video. Kernel-monotonic native timing
remains the clock; a qualified audio-led production controller is not yet
implemented. The stock driver/kernel remain dependencies; lifecycle/queue
semantics beyond the known backend need qualification.

The vendor already has asynchronous display work and CPU-specific emulator paths. Adding more threads on one CPU does not add compute. The design seeks correct ownership, bounded memory, useful overlap and measurable policy rather than assuming fewer layers alone are faster.

## Next audio owner: researched contract, not another guessed gate

[Interface research](platform-interface-research.md) establishes upstream Linux
4.19 OSS/native PCM behavior and identifies defects in current source. The game
producer's ring count does include the audio worker queue through `pump_audio`;
it combines that count with separately sampled board delay rather than one
coherent snapshot, and GETODELAY excludes OSS partial-fragment staging. Intended
1ms polling/backoff sleeps and a separate frame deadline can then gate useful
work. Lab2 independently establishes about 10ms wakes for those short timeouts.

Replace this with one native PCM owner using the existing playback node. Query
and read back constrained rate/format/period/buffer settings; prime before START;
refill on device readiness or meaningful control/new-data events; expose coherent
generated/queued/transferred/playable/consumed accounting and stream state.
Ordinary interleaved writes are the initial transfer mode. Negotiated mmap is
optional and requires correct pointer commits and vendor qualification. A rate
mismatch retains continuous conversion. Explicit DRAIN and DROP serve different
transition policies; zero reported delay is not the complete drain contract.
Upstream ARM does not provide the usual mapped PCM status/control pages; support
SYNC_PTR/HWSYNC independently of any negotiated audio-data mapping.

Use one admission policy with playable reserve sized against long core calls,
refill and scheduling margin. Lab2's 23.22ms queue cannot bridge roughly 30ms of
bursty production. Capacity in an empty software ring cannot supply sound.
Publish already-emulated PCM at valid in-frame synchronization points to shorten
the blackout; keep CPU/APU logical ordering intact. More reserve trades latency
for jitter tolerance. Keep input sampling late and preserve bounded ordered
display ownership and every drawing. This proposal does not guarantee 60FPS or
resolve the previous whole-device poweroffs.

The next physical acceptance should exercise this repaired game path and its
reported PCM state under real FF6 tails. Tests should qualify vendor behavior
and sustained output, after source research supplies the standard interface.
No new payload is installed or armed by the lab2 return/research commit.

## Full-speed implementation and remaining qualification

MVP1.5's controls were physically confirmed; its run recorded 11.838% held
drawings alongside reported occasional lag and rare crackles. MVP1.6 removes
that suppression, implements exact A7 NEON tile/color kernels, releases source
buffers after scaling, queues display jobs in order, and services PCM through
an independent worker. Source reservation happens before the core runs. The
[implementation record](snes-mvp-1.6.md) documents exactness and ownership checks;
the [full-speed plan](full-speed-snes-plan.md) retains the proposed acceptance
criteria and remaining backend work. Physical full-speed acceptance failed;
the return lacks fresh phase totals, so no individual change is exonerated.

Kernel-monotonic pacing and accurate Blargg behavior remain. A hardware audio
cursor, audio-led production control, and persistent scaler ownership require
device qualification before replacing the known transport/backend. The first
full-render test records core, scaler, flip, queue and audio-worker measurements
in memory. From 1.7, it publishes coherent checkpoints outside callbacks and
the wrapper persists them periodically during a bounded diagnostic window,
as well as retaining final reports after play. These measurements decide which
remaining extension is justified; undocumented hardware queues are not assumed.

Reproducible minimal userspace around the known kernel remains the broader
product direction. A new kernel/GPU/bare-metal port requires matching
source/build/recovery and an established useful acceleration path.

The source prototypes the main plumbing. It does not yet provide a general core catalog, broad content support, final audio clock, GPU path, battery/suspend design or complete Buildroot image.
