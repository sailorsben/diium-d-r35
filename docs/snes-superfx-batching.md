# Batch Super FX fill and plot loops

The full-tile renderer plus Super FX batching saves 9.23% mean core CPU
in the paired Star Fox QEMU replay. Toggling the two fast paths inside
identical binaries saves 5.76% mean and 6.80% on the tick IDs that
exceeded the budget on the A7. Those are host measurements. The baseline
of the standalone comparison is the exact full-tile build timed on the
handheld.
[Replay evidence](../evidence/2026-11-10/snes-raster-batches/superfx-experiment.json).

## Work removed

The loop census finds two hot sites that repeatedly write the same word
to consecutive RAM addresses. A four-instruction loop can update a
contiguous run of words at once. The counted build uses 796 fill batches
in place of 17,114,000 instruction dispatches.

A second path groups the plot operations in four-bit pixel loops. It
computes masks for up to eight pixels in a tile row and updates each
bitplane byte once for the group. It preserves dither and transparent
color behavior. The counted build uses 153,658 plot batches in place of
3,701,960 dispatches. Together the paths batch 20.82 million of the
81.14 million Super FX guest instructions in the replay.

The fast paths check the live instruction bytes and target and operate
within the existing guest budget. The normal interpreter handles the
final loop iteration, small batches, RAM-backed program code and
unsupported cases. The fill path preserves odd-address word order and
splits at the RAM bank boundary. Both paths preserve the instruction
pipeline, flags and observable register state.

## Exactness and timing

The ARM differential test compares the entire GSU state and RAM with
the original interpreter in 5,580 cases. It varies the instruction
budget, address alignment and wrap, counter values, color, dither, and
RAM-backed code. The replay also passes all 1,200 per-tick pixel and PCM
checks in each of the five fixtures with the combined build. Star Fox
passes independently with each fast path and with the timing toggle
enabled. Callback layout and PCM sample counts match.

| Host comparison | Mean CPU saved | p95 saved | Slow tick cohort mean saved |
|---|---:|---:|---:|
| RAM fill batching | 6.98% | 4.68% | 6.02% |
| Pixel plot batching | 2.51% | 2.32% | 2.86% |
| Combined build | 9.23% | 7.11% | 8.53% |
| Combined paths, identical binaries toggled | 5.76% | 7.05% | 6.80% |

The timing uses 1,080 gameplay ticks after excluding the first 120.
The slow cohort is the 358 tick IDs in that window whose full-tile core
time exceeded 16.688 ms on the A7. Each host pair alternates call order
on one pinned CPU lane. Linked layout changes can affect the standalone
comparison. The toggle controls for the executable bytes. Neither
comparison measures milliseconds saved on the A7.

The next physical comparison is full-tile versus full-tile plus the
combined Super FX paths, with particular attention to the opening and
slow ticks. The new A7 saving, native presentation cost and PCM reserve
are unmeasured. Use the [physical raster baseline](snes-raster-device-test.md)
and retain exact pixels, PCM and sample counts during the comparison.
[Device test procedure](snes-superfx-device-test.md).

To reproduce the offline checks, build the full-tile control and the
Super FX arms with `build/build-snes-throughput.sh`, run
`build/check-snes-superfx-batch.sh` and the `fx-verify` mode of
`build/run-snes-throughput.py`, and use `--superfx` in
`build/run-snes-throughput-pair.py`. Run the single replay harness
with the `fx-profile` and `fx-batch-count` cores to capture counts.
`build/report-snes-superfx.py` aggregates the logs and binds the slow
tick cohort to the private physical return.
