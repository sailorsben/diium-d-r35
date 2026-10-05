# SNES MVP1.6: full rendering on Cortex-A7

Implemented and installed as a one-shot on the tested card, 2026-10-04 local.
**Physical performance is pending.** This changes real rendering and host
ownership; it does not establish 60 FPS from QEMU timing.

## What changed

- Pinned Plus now has ARMv7 NEON kernels for ordinary 2/4bpp eight-pixel tile rows
  across plain/add/subtract/half/fixed-color modes. Four-D-register palette lookup
  with VTBL, vector transparency/priority masks and horizontal reversal replace
  scalar branches/loads. Palette data is reloaded per tile call. Half subtraction
  computes the exact old table result without the table access in these kernels.
- Eight-bit/direct-color, clipped, widened, backdrop and Mode7 reference paths
  remain scalar. Blargg numerical behavior and serialization layout are unchanged.
  No APU shortcut, frameskip, emulated overclock or global fast-math is enabled.
- Plus delivers completed native PCM before video. The host callback only
  resamples/enqueues; a joined audio worker owns writes/partial tails/poll.
  Pause/reset joins that worker before clearing/resetting, preventing old PCM
  from arriving in a resumed stream. Software clears/remainder are counted.
- Three chunk source slots and a two-job FIFO retain every submitted image.
  Buffer and publication credit are reserved before retro_run. Callback copy
  does not wait for previous scanout. The worker frees the source after DrawVFB,
  then flips while the core can produce ahead; output stays exclusively owned by
  that worker. Queue full means backpressure before the core, never superseding.
- Drawing suppression is removed. A null video callback is a visible failure.
  GPIO is sampled once per core step. Kernel-monotonic native timing remains the
  production clock; total PCM lead is bounded using available OSS occupancy.
  Audio-led cursor control and drift correction are not claimed as qualified.
- The known vendor scaler backend remains. Persistent-fd/reset semantics and
  hardware A/B queueing are not yet qualified; no guessed ioctl behavior was
  added. Scaler/flip/copy/producer wait and both workers' CPU are now reported.

## Verification and evidence limits

[Selected verification](../evidence/verification/snes-mvp-1.6/verification.json):
8,388,608 scalar/vector color comparisons; 280,000 randomized tile rows; 1,200
actual pinned/candidate core frames from intro and the latest private snapshot,
with exact visible-pixel/native-PCM/geometry matches. Periodic emulated state
matches after normalizing named host-pointer fields in the upstream snapshot.

**New discovery:** Plus memcpy-serializes raw CPU/ICPU/SA1 host pointers; raw
snapshot bytes across two loaded libraries are not all expected to match.
The oracle compares logical CPU offsets and other state, normalizes only named
pointer fields, and separately resumes the same input snapshot in both cores.
This is not a blanket exemption for arbitrary serialization differences.

Actual runner pause-menu integration resumes a separately migrated snapshot for
120 frames, with zero held drawings and private SRAM save/clean exit. The final
binary's 180-frame smoke and 30-frame paced smoke render every frame and account
for every produced/priming PCM frame in the mock sink. Fragmented/EAGAIN transport
preserves the reference checksum. Real board-queue fixtures gate scanout, fill
the FIFO, check owned copies/order/credit and require join before teardown.
Splash/input/clock/watchdog/UI/state regressions also pass. ARM requirements
remain compatible with device glibc 2.30 (runner max required GLIBC 2.17).

These checks do not measure physical speed, DAC continuity or optical presents.
`display_flipped` is completed vendor flip calls. Display counters include pause
UI jobs; compare FIFO submitted/scaled/flipped totals accordingly. Audio accepted
frames are logical complete frames, including the existing retained partial-byte
tail mechanism. Device queue/reset-clear numbers are estimates, not XRUN counts.
Maximum write gap excludes deliberate paused-worker intervals. Active wall time
excludes pause UI; kernel/preemption and queue waits are included during play.

## Isolated deployment and next test

The new core lives at `retro/snes-mvp/plus-a7.so`; stock libraries, init and all 18
pre-existing private progress files were hash-verified unchanged. The latest FF6
snapshot has an additional core-bound copy, qualified by the equivalence and
actual runner tests. No original state is retagged or overwritten. Boot still
consumes one armed marker; the next reboot takes stock.

Launcher SHA256: `330cf1a544b6a2b499f96ec6c0c01afbb229ea9ef80003e9857f7776d39ef278`.
Core SHA256: `2e88db49c18c9aa2c96f6806882e78acf9feb3da5e235109f13d1699a8e12766`;
CRC32 `90fbcc4e`, 660,912 bytes. Wrapper SHA256:
`46ca120709e30935716a2e892eff922430bfc28189f8c75c07191fdb0d31a707`.

Play FF6: load the migrated snapshot, map→party menu→map and normal story/gameplay
for about five minutes; Save/Load and Exit. Report lag, crackles, corruption or
freeze. On return collect all progress first. Success needs native speed, zero
omitted drawings, bounded FIFO/audio queues and uninterrupted physical sound.
The current logs can distinguish core CPU, worker CPU and device waits; no
fallback silently restores adaptive holding.

## Reproduce locally

Follow [device dependencies](build-and-test.md), retaining the exact baseline
core and supplying your own known FF6 ROM and MVP1.5 snapshot. New core changes
are reproducibly applied from the pinned upstream source; no dependency binary
or private game data is distributed here.

```sh
sh build/build-plus-a7.sh
python3 build/prepare-plus-inputs.py --rom build/ff3.zip --snapshot /path/to/owned-mvp1.5.state
sh build/build-snes-mvp.sh
sh build/check-plus-a7.sh
sh build/check-snes-mvp.sh
python3 build/verify-snes-mvp.py
```

`build/package-snes-1.6.py` is guarded for the exact tested D: card/hook/binaries
and hash-qualified FF6 state. It archives private progress, atomically writes
owned files, verifies originals, creates only the separate migrated copy, then
arms last. It is not a universal firmware installer. The old 1.5 publisher now
refuses a 1.6 live build; `publish-snes-1.6.py` appends new evidence and retains
historical release bytes/hashes.
