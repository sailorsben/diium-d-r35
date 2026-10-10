# FF6 Bio Blast: ROM-derived cause map and window experiment

The owner ROM rebuilds byte for byte from the pinned annotated disassembly.
Its native CPU instructions now have a private low-level C analysis map, and
Bio Blast has a readable C script/model. That map identifies a concrete renderer
inefficiency: circular-window edge writes repeatedly flush the surrounding scene.
A separate core retains those edges per scanline and reduces actual PPU update
entries by78.97% in the replay's expensive interval. Correctness checks pass;
hardware speed and audio acceptance remain pending. Increased color preparation
is a material cost tradeoff. The installed card still has focus1 diagnostics on
the unchanged1.19 core, not this candidate.

## Reconstruction and its limits

The3,145,728-byte FF6 US1.0 ROM, CRC32 `a27f1c7a`, SHA256
`0f51b4fca41b7fd509e4b8f9d543151f68efa5e97b08493e4b2a0c06f5d8d5e2`,
matches the rebuilt ROM by direct byte comparison. The
[annotated assembly](https://github.com/everything8215/ff6/tree/813013276c952fdd27edcf7b8b86f17291542cbf)
is pinned at `813013276c952fdd27edcf7b8b86f17291542cbf`;
cc65 at `555282497c3ecf8b313d87d5973093af19c35bd5`.
Build SPC first, then the full ROM; preserve extracted assets privately.
The WSL Python adapter takes `D35_FF6_PYTHON`, pointing to an existing Python
environment with numpy. It does not require a published account-specific path.

`build/lift-ff6-code.py` verifies equality before reading assembler debug spans.
It lifts103,538 static native instruction addresses /232,585 instruction bytes
across C0,C1,C2,C3,C5,D4,E5,EE. Source opcode/span checks preserve code/data
boundaries;3,256 non-ROM or unsupported spans are excluded. All eight generated
C files pass syntax checks. They remain under ignored
`build/ff6-cause-private/c-map/`, with symbol and source-line indexes.

This is C for analysis, with explicit effective-address, flags, widths, stack,
control and hardware helpers. Those helpers are declarations, not a completed
native runtime. RAM overlays, broad SPC code, assets and script payloads are
outside that native instruction lift. It is neither recovered original C nor a
runnable game. The readable `build/ff6-bio-blast.c` reconstructs the BG1 script;
its engine interfaces document behavior rather than implement the whole engine.
`build/ff6-bio-blast-model.h` reconstructs wave table generation. Only the focused
copy kernel has been compared directly with execution of the original ROM.

## Function -> register behavior -> emulator consequence

| Original operation | Expected effect | Actual emulation path / finding |
|---|---|---|
| D0/3DB2..3DFE Bio Blast BG1 script | Repeated wave, circle expansion/movement and palette fade |56 then33 update loops. `frame(0)` yields to the game's animation scheduler; it is not a host-clock sleep |
| C1/EE9C initializes waves; C1/ED86 updates; C1/EF34 copies32 samples | Horizontal amplitude8/frequency1; vertical amplitude2/frequency2. Phase rotates a32-sample table; copy uses16-bit stores with stride4 |178 captured C1/EF34 calls produce all32 words expected by the independent C model, zero mismatches |
| C1/EFA3 selects BG1 HDMA table6; NMI installs/copies scroll state | Repeat32-line wave table, combine with base scroll; HDMA writes BG1 H/V scroll (`$210D/$210E`) each line | Scroll values already enter per-scanline `LineData`. Frame320 has448 writes to each register and zero immediate rendered flushes |
| C1/F088 -> C1/1BC7 -> C2/D8DD/D8E1 and C2/D96F | Build and output circular window bounds, then NMI copy / HDMA5 | Window2 edges (`$2128/$2129`) change scanline clipping. Frame320 has91+32 actual pending-render flushes |
| `S9xSetPPU` window cases -> `FLUSH_REDRAW` -> `S9xUpdateScreen` | Preserve all previously elapsed lines before changing a shared clip state | The general renderer repeatedly runs for small vertical slices, preventing batching of otherwise unaffected backgrounds |

The script's scroll-wave operation was an initial suspect. The instruction and
register trace narrows the target to circular clipping. It does not prove the
precise vendor audio-state transition: physical1.19 still supplies sound too
slowly before SETUP/EBADFD, and its final24 calls lack phase samples.

The trace runs the original ROM in an isolated instrumented core. Frame-end
`main/sub/math` values are blanking-time state; they cannot establish which
layers were enabled during active drawing. `rendered_flushes` counts only an
actual pending line range at the original flush site.

## Code change and verification

`build/plus-a7-window.h` captures six bytes per row,1,536 bytes total: validity,
left/right, inside/outside and main/sub masking. Capture occurs with the scroll
line. Earlier rows retain their own bounds after future register writes.
`DrawBackground` uses the recorded BG1 bands and splits vertical batches when
the records change. Other backgrounds can remain batched.

Deferral requires Mode1, normal resolution, no BG1 mosaic, no color window,
only BG1 using Window2 and no BG1 Window1. Unsupported states retain the general
flush path. Missing captured rows refuse deferral; frame-start resets records.
All other PPU register updates, clip invalidation, game code, PCM policy and
frame rendering remain intact. `build/prepare-window-batch.py` applies the change
only to a fresh ignored census core. Shipping source and1.19 core remain exact.

| Check | Result and boundary |
|---|---|
| Independent original `ComputeClipWindows` oracle |524,288 combinations of both edge bytes, inside/outside and main/sub masks; every pixel on both screens matches. Retained rows, reset, missing-row and fallback guards pass |
| Actual ARM core comparison |3,600 frames:1,200 complete Bio Blast replay plus1,200 intro and1,200 returned-snapshot frames. Per-frame visible RGB565/native PCM CRCs, sample counts and geometry match; normalized serialized bytes match every30 frames |
| Same1,200-frame command replay | All command-boundary image/PCM checksums match1.19; traced baseline matches too |
| All eight C banks and readable model | C syntax checks pass; this does not qualify helper execution |

The oracle includes unchanged stock-derived `source/clip.c`, not a second copy
of the candidate's formula. Its original fall-through warning is left intact
and exempted from `-Werror`; owned code retains other warnings as errors.

In162 effect frames (zero-based inclusive census rows277..438):

| Mean work per frame |1.19 | Candidate | Change |
|---|---:|---:|---:|
| Actual `S9xUpdateScreen` entries |134.537 |28.290 |-78.97% |
| Color-row materializations |4,117.290 |5,541.210 |+34.58% |
| Color-row reuse |7,965.222 |6,541.302 |-17.88% |

The other123 counters match in that interval, including tile/depth/NEON work.
Two register-site counters also change with the pending line ranges;
`flush_before_2129` is instrumented before the new deferral condition and must
not be presented as an actual-flush count. The renderer-entry counter is the
appropriate reduction measure. Changed traversal/cache locality is a plausible
explanation for extra color work, not yet a measured cache diagnosis.

These are correctness and work counts from a private derived battle, not the
exact physical encounter or A7 timing. Reduced entry counts cannot outweigh
the color tradeoff by assertion. No speedup or repaired audio is claimed.

## Exact next step and reproduction

The card contains the qualified runner-only
[focus1 test](snes-focus-1.md); its physical result is pending. Collect and hash
the returned session/private progress before any new card changes. Use its
ordinary/sample separation to assess actual expensive-interval costs. A separate
production build of this window patch needs qualification and actual A7 cost
evidence before it becomes an installed replacement. The current candidate is
instrumented and intentionally separate from the release.

Reproduction after privately rebuilding the byte-matched ROM:

```text
python build/lift-ff6-code.py
python build/prepare-ff6-cause.py
sh build/check-ff6-cause.sh
python build/prepare-window-batch.py
sh build/check-render-census.sh render-census-window-batch-private
sh build/check-window-oracle.sh
```

The prepare scripts refuse to overwrite previous experiment directories.
Reuse preserved artifacts for analysis; do not erase them to force reruns.
The existing private command replay uses `build/replay-snes-scene.sh`; the
comparison harness is `build/plus-a7-equivalence.c` with1200-frame Bio Blast and
1200-frame intro/returned-state runs. `build/analyze-ff6-cause.py` verifies actual
inputs, outputs and source hashes. See
[curated analysis](../evidence/verification/ff6-bio-blast-cause/analysis.json)
and [C coverage](../evidence/verification/ff6-bio-blast-cause/c-map-verification.json).
ROMs, extracted assets, generated bank C maps, states, trace binaries and core
dependencies remain private. Only authored tools/models and bounded evidence
are published.
