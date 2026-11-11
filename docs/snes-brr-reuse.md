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

Recommend a small adaptive BRR cache: sample reuse and bypass low-hit workloads,
then periodically resample so a new song or game can qualify without training.
That adaptive policy is a proposal, not implemented or measured here. Preserve
the exact decoder fallback, reset/load handling and all DSP scheduling. First
repeat matched timing and full-state/reload regressions on the actual PGO core;
then measure A7 lookup/miss cost, net saving and complete native reserve. No
A7 saving, break-even margin or remaining audio deficit is established, so the
installation gate is unmet. No card or production binary was changed.

Raw census/qualification logs and timings: [results](../evidence/2026-11-11/brr-census/results.json).
`build/prepare-brr-census.py` patches a scratch source copy; `D35_BRR_REUSE=1`
enables the shortcut and `D35_BRR_CENSUS_SKIP=8656` excludes Star Fox warmup.
`build/run-brr-census.sh` uses existing private fixture paths and refuses to
overwrite its scratch directory. Timing logs interleave stderr diagnostics;
remove each complete `BRR_CENSUS...\n` record before parsing the 1,200 rows.
