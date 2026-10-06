# Userspace platform architecture

The current [MVP1.13](snes-mvp-1.13.md) retains the native PCM owner,
consumption-driven producer admission, earlier mixed core audio and every
drawing. The [1.9 return](snes-mvp-1.9-return.md) qualifies44100Hz/128-period/
3712-buffer settings and one priming transfer, then fails before emulation.
Startup now uses observed state: acknowledge write-driven RUNNING after full
priming, START only from PREPARED and verify afterward. Precise operation/state/
pointer diagnostics survive failures. The 1.10 return starts playback but later
fails on WRITEI. 1.11 waits for fresh worker admission, reads post-HWSYNC pointers/
state, restores drain readiness and distinguishes transport errors from queue
capacity. A consuming real-core/native-client fixture exercises retry and two
snapshot resumes. Sustained native consumption, audible continuity
and sustained full speed remain physically unqualified. The
[hardware roadmap](hardware-capability-roadmap.md) preserves the broader
platform goal and remaining opportunities beyond smooth FF6.

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
fixes capture without head/sed in1.9 and without tail in1.10; shipped1.8 is unchanged.

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
  earlier mixed PCM -> native-rate bypass/continuous conversion -> PCM owner
  consumption admission + every drawing -> reserved board video submit
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

Audio callbacks enqueue every generated/converted frame. One worker owns
nonblocking native frame transfers and the software/playable observation under
one lock. Producer admission reserves capacity and bounds observed lead; PCM
readiness/eventfd notifications replace short polling gates. Priming precedes
playback; kernel WRITEI may start it at the threshold. Explicit START is valid
only from PREPARED, followed by a RUNNING check. Flush/DRAIN/join precede normal
reset/close; failure cancellation
and clears remain counted. Snapshot operations qualify core/ROM and roll back
on failed load. Historical `audio-pipe.c` retains the1.8 OSS implementation;
current gameplay builds `audio-owner.c` and `native-pcm.c`.

## What is retained deliberately

Plus's accurate sound remains.1.6 removes adaptive suppression;1.9 additionally
publishes already-mixed PCM within the core call. The physical production clock
is native PCM consumption; direct kernel clocks serve timing telemetry/input
waits. A negotiated rate mismatch retains continuous conversion. The stock
driver/kernel remain dependencies; lifecycle/queue semantics beyond the known
backend need qualification.

The vendor already has asynchronous display work and CPU-specific emulator paths. Adding more threads on one CPU does not add compute. The design seeks correct ownership, bounded memory, useful overlap and measurable policy rather than assuming fewer layers alone are faster.

## Research basis for the1.9 owner

[Interface research](platform-interface-research.md) establishes upstream Linux
4.19 OSS/native PCM behavior and identifies defects in current source. The game
producer's ring count does include the audio worker queue through `pump_audio`;
it combines that count with separately sampled board delay rather than one
coherent snapshot, and GETODELAY excludes OSS partial-fragment staging. Intended
1ms polling/backoff sleeps and a separate frame deadline can then gate useful
work. Lab2 independently establishes about 10ms wakes for those short timeouts.

MVP1.9 replaces this with one native PCM owner using the playback node. Query
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

The1.9 return fails before emulation;1.10 repairs startup state handling. The
next acceptance should first establish RUNNING, then exercise FF6 tails and
reported consumption/playable state. Source research supplies the standard
interface; the device qualifies vendor behavior and sustained output.

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

Accurate Blargg behavior remains.1.9 implements audio-led production using
native PCM state/availability rather than an assumed raw hardware cursor.
Native settings and persistent scaler ownership still require device
qualification. The first
full-render test records core, scaler, flip, queue and audio-worker measurements
in memory. From 1.7, it publishes coherent checkpoints outside callbacks and
the wrapper persists them periodically during a bounded diagnostic window,
as well as retaining final reports after play. These measurements decide which
remaining extension is justified; undocumented hardware queues are not assumed.

Reproducible minimal userspace around the known kernel remains the broader
product direction. A new kernel/GPU/bare-metal port requires matching
source/build/recovery and an established useful acceleration path.

The source prototypes the main plumbing. It does not yet provide a general core
catalog, broad content support, physically qualified native audio clock, GPU
path, battery/suspend design or complete Buildroot image.

The 1.12 physical return still fails in SETUP and does not preserve the PCM
flight history. 1.13 writes that first-fault transaction/kernel capture directly
to the card with file/directory sync before error return and explicit capture
status. Core, settings and admission remain unchanged; no driver fix is claimed.
See [latest return](snes-mvp-1.12-return.md) and [capture](snes-mvp-1.13.md).
