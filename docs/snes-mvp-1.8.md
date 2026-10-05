# MVP1.8: smarter Cortex-A7 renderer

**Returned result:** clicking and confirmed whole-device power-off. The card is
unarmed; see the [return review](snes-mvp-1.8-return.md) for fresh measurements,
preserved progress and next work. This implementation record describes shipped
1.8. Its firmware-supported-sed assumption below proved false; current source
uses shell builtins, passes without head/sed and has not been installed.

Ben requested a forward optimized A7 build instead of another paired device
comparison. This release changes the actual renderer and reduces gameplay
observer work. It retains the SNES library/pause UI, full drawing, accurate
Blargg sound, continuous PCM conversion and ordered display ownership.
Physical native speed and uninterrupted playback are the next acceptance test.

Installed and armed on D: after read-only return collection and a fresh
pre-install archive. All19 pre-existing private files, stock binaries and boot
hook remain byte-identical. A separate older qualified snapshot was added;
the new Save Point SRAM was not replaced. The next boot consumes this one-shot.

## Concrete changes

The compiler emitted one generic `d35_render_tile` in1.6/1.7 even though its
source said inline. Every row carried a mode dispatcher and general register
requirements. Force inlining at the seven ordinary tile entry points so the
compiler specializes plain, add, add-half, subtract, subtract-half and the two
fixed-half modes. The emitted-code check requires the generic helper to
disappear and all seven functions to contain NEON palette lookup.

Prepare separate low/high palette-byte tables once per tile. Four-bit palettes
use deinterleaving `vld2`; each row uses two `vtbl2` lookups with the original
index. Remove the old per-row doubled index and high-byte index increment.
Two-bit palettes read exactly eight bytes, including the final palette at a
page boundary. No colored-tile cache or invalidation state is introduced;
palette/VRAM mutation and state reconstruction retain their existing rules.

Skip rows with no visible pixels and directly store fully covered colors.
Color math skips active lanes with disabled subscreen math; fixed-only rows
avoid subscreen reads. Half-blend rows without active fixed-color lanes compute
only half math. Mixed lanes preserve the original full-versus-half selection.

Add eight-pixel NEON spans for color-window copying and backdrop fill/blending,
including fixed-color selection and depth masking. These were scalar passes
in `S9xUpdateScreen`. Process complete spans and leave clipped tails upstream.
Eight-bit/direct-color/clipped tile and Mode7 paths retain scalar implementations.
Compiler optimization remains O2 with Cortex-A7/NEON-VFPv4 hard-float targeting.

## Regression caught before installation

The first game-level check faulted at intro frame87. Some plain-backdrop clip
intervals are reversed or empty; the original `while (d < e)` does zero work.
Casting `e-d` directly to unsigned gave the vector helper an enormous span.
Clamp the call-site count to zero unless `d < e`. The real intro and returned
snapshot now pass. Arithmetic-only kernel tests had passed before the fault;
they were not sufficient to qualify integration. Preserve this seam in future
renderer changes.

## Lean gameplay diagnostics

The prior capture-plus-global-sync windows averaged234.4ms elapsed. That was
not proof of main-thread stall or equivalent CPU consumption, but repeated
process/kernel discovery and filesystem flushes were unnecessary observer work.
The wrapper now takes one platform/kernel capture two seconds after readiness,
then only small progress/stderr checkpoints every30 seconds for five minutes.
No global sync occurs during checkpoints. Startup/final-exit sync, the one-shot
marker and splash ownership handshake remain.

Runner counters still refresh atomically in RAM once a second, with final
totals on normal exit. Sudden power loss can lose the latest buffered card
checkpoint; this trades durability for less gameplay I/O. The first platform
capture remains observer work and is recorded. Use firmware-supported `sed`
instead of missing `head`. The actual wrapper test observes sync calls while
its child is alive and verifies CPU/memory capture with a PATH lacking `head`.

## Verification and deployment

[Published verification](../evidence/verification/snes-mvp-1.8/) covers8,388,608
independent scalar/vector color checks,280,000 tile rows,60,000 backdrop/window
spans with clipping tails/canaries, an inaccessible page after the last2bpp
palette, and1,200 real-core frames with exact visible pixels, native PCM,
geometry and periodic normalized state. The pinned original is an output
oracle, not another physical performance experiment.

Runner checks cover partial/EAGAIN PCM preservation, priming, state/SRAM
roundtrip and rollback,180 unpaced plus30 paced calls,120-frame snapshot/menu
integration, GPIO/clock/splash/first-paint, display FIFO lifetime/order/join and
abrupt-exit RAM checkpoints. QEMU does not establish device FPS or audible gaps.

Reproduce with owner-supplied inputs as in [1.6](snes-mvp-1.6.md#reproduce-locally):

```sh
sh build/build-plus-a7.sh
python3 build/prepare-plus-inputs.py --rom build/ff3.zip --snapshot YOUR_ORIGINAL_5ba71d2a_STATE
sh build/build-snes-mvp.sh
sh build/check-plus-a7.sh
sh build/check-snes-mvp.sh
python3 build/verify-snes-mvp.py
python3 build/publish-snes-1.8.py
```

`package-snes-1.8.py --card D:/` requires the exact returned, unarmed1.7 card
and qualified final1.8 bytes. Archive private progress, verify stock/hook hashes,
update only owned files and add a separate qualified older snapshot for the new
core identity. Verify every pre-existing private file byte for byte and arm
last. ROMs, SRAM, states, device dependencies and full card archives stay local.
Release hashes are in the [owned manifest](../releases/snes-mvp-1.8/manifest.json).

## Physical test

Launch FF6, not Rev1. Use **Continue** to resume the new Save Point; installation
preserves that SRAM. The migrated pause-menu snapshot is an older location and
loading it can restore older SRAM when the game exits. Play story/map, open
FF6's party menu, return to the map, then save/exit. Observe movement speed,
random crackles and picture correctness. This is one forward build with zero
intentional held, skipped or superseded drawings.

The target remains native59.9227Hz emulation with full sound. The earlier
power-off cause remains unexplained. Display completion is not optical panel
presentation; accepted PCM is not uninterrupted DAC playback. These changes
reduce concrete CPU work; their device speedup is still to be measured.
