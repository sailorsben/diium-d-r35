# Five-game handheld BRR cache measurement

This one-boot measurement uses the Super Mario World,
Super Metroid, F-Zero, Star Fox and Rendering Ranger replay fixtures. The
existing launcher PGO core is the baseline. The new PGO build includes the
32-frame live CPU gate and the same 16-entry Mode 2 renderer cache.

Each game runs two paired comparisons over the same 1,200 gameplay ticks.

| Pair | Control | Candidate | Measures |
| --- | --- | --- | --- |
| `auto` | New PGO with BRR profiling disabled | Byte-identical new PGO with adaptation enabled | Net cost of profiling, trials and sustained caching |
| `off` | Current launcher PGO | New PGO with BRR profiling disabled | Cost of carrying the change in the core when it is disabled |

The runner alternates the two cores' call order on the single Cortex-A7.
It checks every frame's pixels, native PCM bytes, sample counts and callback
layout against the frozen fixtures. It records wall time, thread CPU time
and time spent in the verification callbacks so analysis can subtract the
observer. The `auto` CSV also shows when the runtime probes, accepts a trial
and uses sustained caching. A zero sustained count still allows the cost
of probes and short trials. The `off` CSV must have zero BRR activity.

## Physical acceptance

Subtract callback CPU from each measured frame. Compare the mean and p95,
including the whole 1,200-tick window and the four chronological quarters.
Use the `auto` pair to price all adaptation work and separately inspect
ticks using sustained caching. Use the `off` pair to detect regressions
from the rebuilt core itself. A useful result lowers adjusted CPU across
enabled windows. Use 1% mean and 2% p95 as practical tolerances for the
disabled comparison. A result near measurement variation needs another
physical pair before it supports a claim of equivalence. Frequency and
thermal snapshots are collected where the kernel exposes them. Oracle or
accounting mismatches invalidate a pair.

This is the measurement for the installation gate. Mean break-even is
`net saving > baseline service time −
emulated tick period`. The exact source period is about 16.688 ms for the
NTSC fixtures and about 19.87 ms for the PAL Mario fixture. A production
claim would also need full native PCM acceptance, drawdown and reserve
recovery. Those costs and the remaining reserve deficit are unknown here
because the diagnostic uses in-process output checks and does not open the
LCD or PCM device.

## Boot and return

Safely eject I:, insert the card, and boot the handheld once. The test stops
the splash to remove its CPU load. The screen can stay dark and silent
until the stock menu appears. The two Star Fox pairs each do a full cold
replay before timing. Allow roughly 15–20 minutes for the suite, based on
earlier physical replay times. The two markers are consumed before the
first pair, so the next boot follows the normal stock route.
The BRR test supersedes the pending launcher art test. Its old dispatcher
and both marker contents are retained in the private pre-test archive.

After the stock menu appears, shut the handheld down and reconnect I:.
Archive the new `retro/snes-brr-test1/results/run-*` directory and all private
progress before touching the card. The wrapper writes a completion line
only after all ten pairs pass. Partial runs retain the completed pair data
and the latest failure or warmup progress. Run the report on the archived
directory with `python build/report-snes-brr-device.py ARCHIVED_RUN`.

Each CSV tick has the tick number, two core CPU times, two wall times, two
callback CPU times, and cumulative probes, admissions, sustained ticks and
probe CPU. Times are in nanoseconds. No per-frame CSV writes occur during
timing. Logs are synced after each pair. Qualification checks the same
runner with the ARM fixture and exercises the exact firmware BusyBox wrapper
for normal, oracle failure, active splash and unarmed cases.

The PGO core passed all ten exact ARM replay pairs, or 24,000 measured
core calls across both arms. It also passed the independent FFVI Meteor,
Quasar and Ranger state checks. [Replay qualification](../evidence/2026-11-11/brr-adaptive/device-qualification.json).

I: was armed from source `48bd5f3`. Independent readback verified both
one-shot markers, all 2,169 card files, 2,159 unchanged prior file hashes
and clean FAT32. The QEMU arms completed with no sustained caching in these
windows. The handheld will make its own timing decisions.
[Card readback](../evidence/2026-11-11/brr-adaptive/device-arming.json).

## Handheld return

All ten pairs completed on the Cortex-A7. The 24,000 measured core calls
match the frozen pixels, PCM, sample counts and callback layout. Both
Star Fox pairs completed their cold replay. None of the five adaptive
windows recorded a successful admission or sustained cache tick. Thirteen
decode probes used 8.624 ms of thread CPU in total. The logs do not price
cache hits in sustained use because no gameplay window reached that state.

The table shows change in callback-adjusted core CPU. A positive number
means the candidate used more CPU.

| Game | Auto vs. same build forced off, mean | New build forced off vs. prior core, mean | New build forced off vs. prior core, p95 |
| --- | ---: | ---: | ---: |
| Super Mario World | −0.01% | +1.71% | +1.94% |
| Super Metroid | −0.14% | +0.55% | +0.60% |
| F-Zero | −0.05% | +0.45% | +0.50% |
| Star Fox | −0.13% | −0.64% | −1.36% |
| Rendering Ranger | −0.18% | +1.12% | +1.66% |

The adaptive checks were within 0.19% of the identical build forced off
on mean CPU in all five scenes. The larger disabled-core comparison missed
the 1% mean tolerance in Mario and Ranger. Their extra cost was 0.161 ms and
0.139 ms per tick, respectively, with higher CPU in every quarter. All five
passed the 2% p95 tolerance. This run shows no sustained cache savings and
does not qualify the new core to replace the existing launcher core. The
diagnostic measured core CPU and left native audio reserve unmeasured.

Both one-shot markers were consumed. The sparse archive contains the logs,
private progress and hashes for all 2,192 returned files. Only the swapfile
changed among the retained pre-test files. FAT32 returned dirty and the
read-only CHKDSK found no filesystem problems. No writes or repair were
made on return. [Measured return](../evidence/2026-11-11/brr-adaptive/device-return.json).
