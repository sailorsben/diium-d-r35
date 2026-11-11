# Exact compressed-audio reuse — five-minute investigation, 2026-11-11

The reviewed DSP experiments optimize interpolation and output staging, but
do not cache BRR decoding. `dsp_decode_brr` produces four samples from the
actual header/filter, two fetched bytes and two previous decoded samples.
An address-only cache would be wrong. An exact value key can preserve timed
RAM reads and all buffer writes while avoiding repeated predictor arithmetic.

A 256-entry, 8 KiB census retains the original decoder and checks every hit.
Across 1,200 gameplay ticks per game it finds 64.66% reuse in Mario, 74.40%
in Metroid, 38.62% in F-Zero, 25.72% in Star Fox and 4.94% in Ranger.
Every hit matches all four original outputs. Zero-input/zero-history cases
are a small minority, so this is not merely a silence shortcut.

The optional shortcut's first alternating-order ARM/QEMU timing pair against
the uninstrumented control saves whole-core mean CPU 4.97% in Mario, 4.46%
in Metroid and 1.89% in F-Zero; Ranger regresses 2.88%. These are one host
timing pair per game, not A7 measurements. The probe retains diagnostic
overhead and uses the bounded-renderer development build, not a newly trained
production PGO binary. All five shortcut replays pass all 1,200 frozen
picture, PCM and sample-count observations, including Star Fox.
The original-decoder key test passes one million varied pairs on both host
and ARM/QEMU, including address wrap and unrelated buffer contents.

Raw census/qualification logs and timings: [results](../evidence/2026-11-11/brr-census/results.json).
`build/prepare-brr-census.py` patches a scratch source copy; `D35_BRR_REUSE=1`
enables the shortcut and `D35_BRR_CENSUS_SKIP=8656` excludes Star Fox warmup.
`build/run-brr-census.sh` uses existing private fixture paths and refuses to
overwrite its scratch directory. Timing logs interleave stderr diagnostics;
remove each complete `BRR_CENSUS...\n` record before parsing the 1,200 rows.

## Runtime profiling

The adaptive build starts with the original decoder. It collects 1,024 actual
BRR requests over at most eight emulated ticks. At the next frame boundary it
runs those same requests through both paths twice in opposite order, using
the kernel thread CPU clock. The cached path uses the same ARM helper in the
probe and gameplay. Each cache timing starts with an empty 256-entry table.
Both pairs must favor the cache by more than 12.5%, and at least a quarter of
the requests must hit. These margins allow for timing noise and work outside
the probe. An unavailable clock or sparse decode leaves the scalar path active.

An enabled cache resamples after about 120 ticks. A failed timing probe waits
240 ticks before retrying, doubling up to 960 on repeated failures. A new
sound sequence can qualify on a later probe. The selector reads audio data
and thread CPU time. It has no title, ROM identity, per-game settings or
persistent profiles. The cache and trace together reserve 14 KiB. Normal
uncached decoding skips their memory accesses between probes.

The key captures both bytes read by the original BRR code, the header's
filter and shift, and both predictor samples. A key match restores all four
outputs and their mirrored writes. The original pointer, address, DSP clock
and PCM scheduling remain in the emulation path. Reset, game changes and
state loads restart profiling. Cache and timer state stay outside save states.

Build an isolated candidate with `sh build/build-snes-core-pgo.sh OUT REPLAY
mode2-memo-bounded brr-adaptive`. Run `python3 build/check-snes-brr-adaptive.py
CHECK_OUT REFERENCE CORE REPEATS` in WSL. The checker compares canonical and
held-out input replays, including two Star Fox reloads, against the scalar
path using the same binary. It also times both an identical-binary pair and
a pair with the previous core. No physical test is run by these tools.

## Validation and cost

The Cortex-A7 development build passed all five 1,200-tick picture, PCM,
sample-count, callback-layout and normalized-state comparisons. Star Fox
also matched 1,200 calls with different inputs, poisoned output buffers and
two reloads. The independent Final Fantasy VI and Ranger comparators passed
another 4,800 calls. [Development results](../evidence/2026-11-11/brr-adaptive/development.json).

In three same-binary QEMU timing pairs per shorter scene, median savings
were −0.84% for Mario, +0.06% for Metroid, +0.07% for F-Zero and −1.13% for
Ranger. The Ranger cache stayed off in all three pairs. These values include
probe cost and measurement variation. Comparing complete development ELFs
produced larger differences, including a Metroid regression. The earlier
always-on prototype's gains do not transfer to this adaptive build.

Physical net A7 savings, probe cost and remaining native audio reserve are
unmeasured. A paired handheld run must show lower net core time in enabled
windows and comparable cost in rejected windows. It must also preserve
exact output and complete PCM reserve recovery with frame skipping disabled.
No card or production binary was updated for this work.
