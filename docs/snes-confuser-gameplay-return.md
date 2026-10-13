# Confuser gameplay1 physical return — 2026-10-12

Ben reports that the candidate worked beautifully in two fights. The returned
ordinary runtime session completes without a native PCM failure: 7,119 calls,
7,119 game drawings, no intentional holds or duplicate callbacks, zero write
errors and zero recorded XRUNs. Active gameplay takes 118.662 seconds, or
59.994 calls/sec; the nominal core rate is 59.923. This is one successful manual
session, not exhaustive game/effect or production performance qualification.

Strict private archive `device-evidence/a7-pair-before-20261013T013316Z` captures
577 files, all verified by source/copy/source hashes. UTC date is October13;
collection is October12 in America/Chicago. Readonly FAT/serial11EB-1465 checks
pass. Exact candidate core CRC5cb51346/SHA d5761eac… and regular1.19 runner,
wrapper and dispatch match the release. Marker is consumed; the card is unarmed.
552 prior files remain exact. The sole changed prior protected file is the
runtime swapfile, which legitimately changes across boots. Original progress
and stock/production binaries remain unchanged; separate test progress is archived.
No card writes, rearm or new hardware test occur during this collection.

All 5,239,102 generated converted frames equal accepted output after excluding
8,469 priming-silence frames. Native generation averages534.678 frames/call,
consistent with the534.688 cycle contract and finite endpoints. Three pauses
and one successful snapshot load are recorded. The minimum reported running
PCM reserve is1,313 frames (29.773ms at44,100Hz). Final epoch application pointer
equals accepted frames, without the prior384-frame excess. The zero reserve
and SETUP state in the final report follow normal drained shutdown; neither
establishes a fault. B/library exit, display worker join and wrapper exit0 survive.

The last24 calls average13.173ms core wall and12.559ms thread CPU. Retained sparse
PPU samples range0.328..5.095ms. These are unmatched end-of-session costs; they
cannot be subtracted from the earlier Confuser failure to claim an aligned
speedup. The logs retain no cast IDs or full input/effect reserve timeline.
User observation establishes the two fights' perceived behavior; the logs
establish full-frame/lossless-output accounting and a clean lifecycle in that run.
Incremental A7 dispatch/blend/window costs remain unmeasured.

Reproduce with `python build/analyze-confuser-gameplay-return.py <archive>`.
The bounded numeric analysis is published separately from private ROM/state/SRAM
and raw card contents. Next authorized work is systematic offline screening of
other effects and fixes for shared rendering mechanisms. Preserve this working
binary and its private progress as the rollback/reference; archive before any
future card change. Do not call this an all-effects guarantee or silently promote
the experimental core to production.
