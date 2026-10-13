# Ability3: exact fixed-operand palette reuse

This explicitly requested experimental test follows the measured
[ability2 return](snes-ability2-return.md). It uses a separate owned counter-free
core and version1.19-ability3 at `retro/snes-ability3`. The ROM and original
game progress remain exact. Installation is not production promotion.

## Common mechanism and implementation

`d35_render_tile` previously gathered palette colors and repeated packedRGB565
fixed-color arithmetic for every visible eight-pixel row. When every active
lane has subscreen depth1, that operand is identical across the palette: move
the exact add/subtract/half operation into a small derived palette once, then
reuse its lookup table. This targets repeated computation, without deferring
genuine fixed-color register writes or caching framebuffer/depth output.

The80-entry cache keys palette pointer, color epoch,2/4bpp, fixed RGB565 value
and operation. Modes1/2 use full add for depth1,3/4 full subtract,5/6 their
original fixed-half operators. Half-subtract preserves the pinned Plus packed
borrow semantics. Palette/brightness/load invalidation follows the existing
epoch; epoch wrap clears both caches.2bpp reads exactlyfour colors. Each tile
entry lazily obtains its derived table only when an eligible row exists. Mixed
depths, true subscreen colors, clipping,8bpp and direct color retain the prior
path. Plain-mode eligibility compiles away. No effect or game ID is in the core.

## Evidence and prediction

Two million cache/palette checks compare against the original pinned scalar
arithmetic, including changed fixed operands/operations/palette epochs, epoch
wrap and inaccessible guard pages. All18 real cast contexts must compare exact
graphics/PCM/normalized emulated state against original1.19. A separate counted
core records applicable rows and cache hits/builds; it is never installed.
The first counted replay lacked an exported symbol and is preserved as invalid;
mandatory final-frame counter checks prevent missing data becoming zero work.

Let c be saved math cost per eligible row, p added palette-build cost, h cache-hit
cost, q eligibility overhead per active row, u other cache/contention effects,
all ultimately measured A7 microseconds. For the current physical failure tail:

`S = eligible_rows*c - palette_builds*p - palette_hits*h - active_rows*q - u`

The [prediction receipt](../evidence/2026-10-13/ability3/predictions.json) records
each precise tail, optimistic break-even and explicitly assumed sensitivity.
No inclusive CPU/count quotient is presented as a unit price. QEMU durations
are excluded from performance evidence. Broad eligible-row counting gives a
conservative eligibility-overhead bound because plain paths compile away.
Production cadence under assumptions is `735.94752e6/(tail_us-S)`; remaining
deficit is `max(0,44100-cadence)`. Real cost distributions and net A7 results
remain missing, so the installation gate is **NOT MET** for production.

Falsifiable test: complete all18 windows with1,200 drawings each, requested
properties, exact software PCM accounting and zero native errors. Compare the
same expensive emulated frames against ability2, including effect/recovery
reserve where pointer accounting is valid. Cases with no eligible work cannot
be credited to this cache. A partial improvement is a measured partial result;
average60FPS alone is insufficient. No silent reprime or failure suppression.

## Hardware protocol

Automatic18-case sequence lasts about6–7 minutes; MENU ends it. Audio/display
workers stay live, coarse kernel wall/thread CPU clocks and existing RAM
observers stay included. Sysfs frequency is inspected; unexposed frequency is
reported instead of assuming666MHz. Logs stay in RAM until audio join/display
idle; no new hot-path logging is added. Private fixture payloads are unchanged;
only separately copied core identity headers migrate. Production adapters,
ROMs and actual progress are hash-protected. One-shot consumption makes the
following reboot stock. See [instructions](snes-ability3-test.txt).

Fresh archive/FAT/boot/source/proof/payload guards precede staging and readback.
The [installation receipt](../evidence/2026-10-13/ability3/installation.json)
records arming only after protected-file checks and clean final FAT.
