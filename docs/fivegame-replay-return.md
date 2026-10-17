# Replay-aware five-game physical return — 2026-10-17

Strict sparse archive `uart-kernel-return-20261017T110843219457Z` hashes 1,881
files, retains 32,453,489 new evidence bytes and passes read-only FAT checking.
No card writes or full backup. Both markers are consumed; the next boot is stock.
Normal init, payloads, saves, stock binaries and prior evidence verify. Compared
with preinstallation, only the expected dispatcher/last-launch marker and stock
settings/swap changed. Returned settings are preserved rather than restored.

All 20 windows were attempted, with safe display/worker teardown, child reaping,
no supervisor force, no abort and no replay stall. Mario, Metroid, F-Zero and
Rendering Ranger each pass four 1,200-call bounded windows with exact PCM final
accounting and complete histories. All 16 report NOT_MET for the conservative
20% headroom target. This does not establish sustained or human audio/panel acceptance.

Star Fox completes all four 8,656-call cold replays in 136.017–136.494 seconds,
using 135.149–135.616 seconds of main-thread CPU. Each measured window then
fails after exactly four rendered/submitted calls, under both policies:
`SYNC_OBSERVE errno=77 state=1`, reported as "File descriptor in bad state".
The retained stream state is SETUP, with 5,030 transferred frames including
2,823 priming frames, no explicit START calls and the same terminal pointers.
The four calls consume 122.186–122.702 ms of core-thread CPU, versus about
66.753 ms of nominal console time. This short failed prefix is insufficient
for a sustained cost estimate, but clearly cannot support a full-speed claim.

This is a reproducible native PCM failure after successful replay, not a proven
Super FX replay stall, process crash or battery shutdown. The exact kernel
transition causing errno 77 remains unresolved; do not label it a confirmed
underrun solely from this terminal record. Next work should inspect the complete
PCM history and vendor state transition, reproduce that seam independently,
then evaluate emulation versus presentation costs. Do not hide the failure with
automatic reprime or repeat this unchanged physical suite.

Passive UART IRQ19 brackets are 85.389–86.383/sec before and 85.188–86.158/sec
after, with one boot identity and no runtime patch module/endpoint. This supports
continued UART flood correction; there is no new flash readback in this suite.

User observed a red charging light while powered. No ADC/charging telemetry was
collected. This observation cannot distinguish incomplete charge, load-dependent
charging or a charge fault and does not demonstrate a firmware regression.

Reproduction: run `build/report-fivegame-replay.py` on the immutable return once,
then `build/evaluate-fivegame-replay-return.py`. The latter checks retained bytes,
complete protected inventory and independent passive UART windows. Its initial
outside-retro manifest adaptation omitted the sparse schema; analysis stopped
on a hash-only path rather than copying static files. Preserving the schema
fixed it. A strict inventory check also surfaced returned stock settings changes;
these are explicitly reported, not silently treated as unchanged.

The card remains untouched and unarmed. Kernel UART fix and boot screens are
preserved. Emulator promotion remains rejected because all four Star Fox
windows fail and the other windows lack the required headroom.
