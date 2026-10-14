# Demand v3 separate physical gameplay qualification

**Returned:** opening-scene run completed cleanly, Confuser reported working;
I: now unarmed. No late-game coverage or matched A7-saving measurement.
See [the physical return](snes-demand-gameplay-return.md) for preserved logs,
timing, reserve and acceptance limits. Installation details below are historical.

Ben explicitly requested “Push it to I:” after the offline implementation was
completed and pushed at d26f64c. This authorizes a separate experimental manual
gameplay install and one-shot boot, with no promotion of the production core.
The 72-epoch automatic measurement plan is not staged or armed by this request.

The payload reuses the qualified ordinary v3 core, SHA256
`1eaf05f36adcbc8286de5777cc47f1cf24a588856a2b0a85e48a9bfa0984e6f8`, and
owned-output runner, SHA256
`e31fbccd50b3e0d71215e789e8cfdb8df6f24cfc9741cfe5b796f732918c4065`.
Neither qualified binary nor older artifact tree is modified. Runtime reports
retain 1.19; wrapper identity and core CRC `02bb090e` identify this experiment.

Installed and one-shot armed on I: from pushed source `9a0340f`. All nine
payloads read back exactly;6316 original retro files and the ROM remain exact.
Read-only FAT checks before installation, after payload and after arm are clean.
The [installation receipt](../evidence/2026-10-14/demand-gameplay/installation.json)
records identities and the pre-install archive.

Fresh private staging uses `build/demand-gameplay-private-v1`; the card target is
`retro/snes-demand-gameplay1`. All existing retro files are archived and checked
before writes. Only `retro/snes-mvp/launch.sh` changes to dispatch the separate
wrapper, with one `retro/snes-mvp/armed` marker. It is consumed before hardware
initialization. The existing boot hook, production binaries, emu_sfc adapter,
ROM and all original progress remain exact. A following reboot starts stock.

The latest separate Confuser-gameplay SRAM is copied. Its state payload is
retained byte-for-byte, with only the separate new core identity header changed.
Qualification compares the original and new cores from that archived progress,
then exercises actual gameplay-runner PCM accounting and a consuming native
provider with two migrated state loads, direct output, fault/retry and drain.
The actual new wrapper is checked for one-shot consumption, splash exclusion,
startup timeout, absence of head/sed/tail, and no live-child card diagnostics.
QEMU verifies these seams, not physical display/input/audio or A7 throughput.

## Prediction and acceptance boundary

The [saving model](../evidence/2026-10-14/demand-optimization/saving-model.json)
remains symbolic: every new A7 saving, added producer/guard cost, interaction,
chunk-access cost and migration cost is unmeasured. Break-even requires the
sum of removed costs to exceed all added costs; deadline acceptance additionally
requires net saving above the matched cycle-derived gap. Prior failing control
windows suggest roughly 1.31/0.80 ms for Meteor/Quasar deadline closure and
4.65/4.14 ms for 20% margin. These are required savings, not achieved savings.
Predicted remaining audio deficit is unknown; complete healthy cumulative
reserve is unavailable. No frequency assumption or timer-overhead subtraction
is permitted. Existing ordinary sparse timing overhead remains included.

Falsifiable manual result: movement, effects, resolution transitions, state load
and exit remain visually correct, with no missing frames/effects or PCM loss;
record whether the known effect faults/stutter persist. Owned chunk coherency
and driver compatibility remain physical questions. Even smooth manual play
does not certify the timing/reserve gate. Production gate remains false.
The baseline synthetic 239-line HDMA state defect described in
[offline qualification](snes-demand-optimization.md) remains unchanged.

Follow [the test sequence](snes-demand-gameplay-test.txt). Archive the return
before any rearm. Full card data, SRAM/state and vendor dependencies stay private.
