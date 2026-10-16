# Matched physical FFVI presentation-policy test

This is a separately installed measurement test, not production promotion.
It preserves normal `retro/init`, the permanent UART correction, stock adapter,
all prior tests, evidence, ROMs, SRAM and snapshots. Only the owned SNES
dispatcher changes; two consumed one-shot markers activate the new directory
`retro/snes-presentation-ffvi1`. No firmware update is staged.

## Run on the handheld

Safely eject I:, insert the card and cold boot once. The test is automatic.
Expect roughly **27–35 minutes** for all 80 epochs, often less if a control
fails early. Repeated effects are intentional. Watch movement/effect cadence
and listen for clicks, gaps or distortion; note the effect and approximate
point if something looks or sounds wrong. Counters alone cannot establish
panel cadence, DAC continuity or comfortable input response.

Let the suite finish and wait for the stock launcher. Then power off and
return the card for collection. **Select+Start aborts** the replay and requests
normal owned cleanup. If stock has not returned after 36 minutes, or the
wrapper reports an unsafe/forced shutdown, power off and return the card.
Do not repeatedly run the experiment: both markers are consumed before display
ownership. The following boot is stock, with the permanent UART fix retained.

The automatic replay validates fresh physical abort input, not arbitrary live
gameplay controls. Sustained interactive gameplay, save/menu/state cycles and
subjective cadence/audio acceptance remain a later acceptance step after this
matched return. Do not treat automatic effect completion as that acceptance.

## What is matched

One ARM executable, one byte-identical demand-visible v3 core, the same original
ROM, private fixture payloads, original input sequences, effect criteria,
1,200-frame bounds, native PCM negotiation/priming/admission and instrumentation
are used in every pair. `D35_PRESENTATION_POLICY=0` blocks on display credit;
`1` tries credit and renders to private aligned scratch when unavailable,
retaining every core call/render/audio sample while intentionally skipping
only that presentation. No READY replacement or SCALER-source modification.

The first 72 epochs cover all 18 established FFVI contexts four times:

| Repeat | Policy | Fixture order |
| --- | --- | --- |
| 0 | Blocking | Forward |
| 1 | Candidate | Reverse |
| 2 | Candidate | Forward |
| 3 | Blocking | Reverse |

Thus every effect has ABBA coverage with reversed order, including Meteor,
Quasar, Bio Blast, Confuser and the retained conditional/Rage contexts.
Frame-property matches retain their bounded interpretation; they do not prove
every possible branch or replace original effect identity requirements.

The last eight epochs use the unchanged HOLY fixture, in ABBA order for each
of +24 ms and +48 ms main-thread CPU. Each executes seven burns at zero-based
frames 239, 359, 479, 599, 719, 839 and 959. Each has a long recovery window,
including 240 frames after the final burn. The load schedule, actual executed
event count and CPU duration are recorded for both policies. A failing cell
may stop before all seven burns; no unexecuted burst or missing recovery
interval is counted as successful.

The isolated measurement runner uses the production presentation-policy code
inside the established full-frame observer/controller. It retains the prior
diagnostic native PCM history collector and pacing/worker accounting in both
arms, with flush after audio join/display idle. This diagnostic collector
differs from production's immediate durable-fault persistence. No claim of an
uninstrumented production speedup is made from its elapsed time. No nested
core phase clocks, PC sampler or instruction hooks are enabled; observer costs
are included and never subtracted as an unrelated calibration.

## Ownership and evidence

The wrapper checks healthy attached UART status before and after the child,
signals `/tmp/vrtemu.log` and waits for active showlogo owners to exit before
the test opens its display. A kernel-monotonic supervisor owns the test child
with a 35-minute deadline and bounded TERM/KILL/reap. Forced, signaled, unknown
or unreaped termination returns unsafe status72; the wrapper withholds stock
until reboot. A normally returned diagnostic failure is distinct from a crash.

Each boot gets a new `results/run-<boot-id>-<pid>` directory. Each epoch has
its own `run-NNN` directory. Per-frame/PCM/effect observations stay in bounded
RAM until audio is joined and display idle; console output stays in `/tmp`
until child exit. Flush/sync occurs between epochs, never as a live periodic
wrapper monitor. A power cut can lose the current RAM history; preceding
flushed epochs and all earlier test directories remain intact.

`frames.csv` retains all 1,200 produced-frame boundaries, generated audio,
rendered/submitted/skipped counts, reservation/try wall time, worker CPU,
pointer/accounting samples and executed load events/CPU. `pcm-full.txt` retains
the complete bounded native trace from entry0 where available. A full history
is required for acceptance; truncation, pointer drift and post-error reserve
values cannot be relabeled as clean evidence. `animation.csv` retains the
original effect/property/input observations. Normal close joins the display
worker before source/display destruction.

## Measured gate and falsifier

Pressure3 measured 0.004 ms try/reservation wall versus 11.480 ms blocking wall
after a synthetic 48 ms event; its first five recovery intervals restored
primed lead within 19.5–20.0 ms after observed minima. Those are wall/recovery
measurements for a different synthetic workload. They are not 11.48 ms of CPU
saving. Its steady samples recorded approximately 0.022–0.039 ms extra mean
main CPU per quantum, with ordering and duration limitations.

This actual-core candidate's A7 saving, added try/scratch/cache/observer cost
and remaining FFVI deficit are **unmeasured**. The test is explicitly intended
to measure those missing terms. Known product scratch allocation is 123,008
bytes; the test adds bounded observer/PCM-history storage. The necessary
inequality is:

`avoided display-credit wall wait > added policy cost + scratch-render delta
+ downstream recovery cost`.

The nominal cycle-derived quantum remains 16.688153 ms. Complete cumulative
valid reserve and matched heavy/recovery intervals determine whether a bounded
audio deficit closed. Zero skips can mean this path had no opportunity to
help; it is not a failure of the comparison. This policy cannot repair sustained
CPU overload, and no 80 ms tolerance or 20% headroom is promised.

Reject a claimed improvement if a matched control passes and candidate fails,
if effect/state/render/PCM work changes, valid lead does not recover when credit
is the constraint, added costs consume the avoided wait, ownership/teardown
fails, or visible/audio behavior is unacceptable. Compare exact common valid
indices; failed prefixes cannot pass a full 1,200-frame cell. Do not infer a
hardware ceiling from these workloads.

## Collection and reproducibility

Archive all returned files before any mutation/rearm. Use
`build/archive-a7-pair-card.py`, then supplement with
`build/archive-presentation-extra.py <archive>` to preserve the rest of I:.
Keep the installation receipt from the pre-install archive. Analyze the new
return only:

```sh
python build/report-presentation-ffvi.py <return-archive> --installation <pre-install-archive>/presentation-ffvi-installation.json
```

The reporter verifies archived payload hashes against the installation,
rejects mock telemetry as physical, checks complete windows/effects/presentation
and PCM identities, censors invalid prefixes and reports matched CPU data
separately from wall wait. Detailed burst recovery is interpreted from the
retained full reserve history and frame/event timestamps; sampled minima are
not exact continuous minima. Physical visual/audio judgment remains required.

Preparation and qualification commands are:

```sh
python build/prepare-presentation-ffvi.py
wsl --exec python3 build/qualify-presentation-ffvi.py
python build/check-presentation-install.py
```

They create a fresh private tree, execute all 80 actual controller epochs
(96,000 real-core calls), test both native-policy paths and firmware
guard/abort/replay/forced-child cases. They establish software contracts,
not hardware performance. Publication contains authored source and metadata
hashes only; ROMs, private fixture/SRAM/state bytes, vendor libraries and
full-card content stay private.

The initial O3/LTO consuming-provider fixture hit an admission timeout during
its retry. That result is preserved privately. The fixture's established O2
build passes both policies, including 40 forced presentation skips, fault/retry,
single drain and sustained-deficit rejection. The deployable controller remains
O3/LTO. This does not establish why the preliminary fixture timed out or claim
that a compiler change repaired a hardware fault.
