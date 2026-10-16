# Ranger and Star Fox fixes; five-game gameplay return — 2026-10-16

The isolated corrected candidate gets all five backup games into inspected
gameplay and passes the rerun. Rendering Ranger's black screen is resolved;
Star Fox's frame150 state divergence is resolved. Testing then exposed a
separate Star Fox compact-target pixel failure at frame178, now avoided by a
SuperFX full-layout compatibility guard.

This supersedes the unresolved findings in the [first evaluation](multigame-evaluation.md).
The candidate has **not** been installed or physically qualified. All results
below are ARM/QEMU software checks, not A7 throughput, panel or speaker proof.

## Changes and causal checks

**Rendering Ranger R2:** the CPU and SPC deadlock during the sound driver's
SYNC exchange. The bounded port trace shows CPU acknowledgements53,59,4e,
then43; after4e is observed, the CPU writes43 while the SPC is still at its
comparison with4e. CPU later waits for port0=ff; SPC waits for the previous
port3 value indefinitely. This is upstream instruction-granular timing, not
an absent ROM or a presentation-worker failure.

For ROM ID `AVCJ`, complete the in-progress SPC instruction before publishing
the next CPU port-write value, temporarily using the APU's existing
allow-time-overflow mechanism. Restore the prior flag immediately afterward.
Reset the compatibility selection on every ROM load. Other ROMs retain their
previous emulated APU timing. This is a scoped compatibility rule, not a claim
to implement cycle-perfect SPC bus timing. No ROM edits or forced PC/game-state
jumps are involved. The original ROM now passes the handshake and reaches
stage1 with visible movement, enemies and shooting.

**Star Fox state:** `S9xDoHDMA` already advances `IndirectAddress` on every
transfer. At termination it adds a cached host-pointer difference a second
time. `S9xStartHDMA` invalidates the memory pointer while its old base pointer
can remain, letting host addresses contaminate emulated DMA registers. Remove
the redundant addition. Keep the actual serialized register bytes in the
comparison; do not normalize them away. The extracted full old function fails
all160 logical-address contract cases; the corrected function passes all160:
eight channels, eight modes, direct/indirect termination and stale-cache cases.

**Star Fox pixels:** strict testing past the fixed state divergence exposes
a pixel mismatch at frame178. Two copies of the identical corrected core also
fail when one uses supplied output targets; the full-layout control passes.
The candidate now declines compact direct output for SuperFX and uses the
established full-layout rendering/callback-copy path. This is a compatibility
guard for an unqualified optimization, not proof of the exact internal PPU
mechanism. The presentation policy still operates; every emulated refresh,
render and audio quantum remains. The guard adds no new framebuffer allocation
but loses the direct-output copy saving for SuperFX. Its A7 cost is unmeasured.

The upstream implementation remains available for comparison in
[Libretro's DMA source](https://github.com/libretro/snes9x2005/blob/master/source/dma.c).
The causal conclusions above come from this workspace's exact source and
negative/positive tests, not the upstream issue list.

## Inspected gameplay and strict rerun

| Game | Reached scene | Accepted comparison |
| --- | --- | --- |
| Super Mario World, PAL backup | Yoshi's Island2 course, movement/jumping and respawn | 1200 calls from private gameplay checkpoint |
| Super Metroid, translation-labeled backup | Ceres station, Samus moving/jumping | 1200 calls from private gameplay checkpoint |
| F-Zero | Starting grid into an active race | 1200 calls from private gameplay checkpoint |
| Star Fox | Corneria first mission, flight/combat | 9856 calls from cold boot, including1200 after the inspected gameplay prefix |
| Rendering Ranger R2 | Stage1, movement/shooting/enemies | 1200 calls from private gameplay checkpoint |

The checkpoints were obtained through recorded ordinary buttons in the
unmodified backed-up ROMs. The explorer supports advancing inputs and saving
images/state; it has no memory-poke command. Some exploration stages continue
from private snapshots to avoid replaying long menus/prologues. The Star Fox
test deliberately uses the complete cold-boot button sequence because GSU
snapshot continuation remains unqualified.

All **14,656 compared calls** pass full visible pixel bytes, PCM sample bytes
and counts, callback geometry and strict periodic normalized state:489 checks
at frames0,30,... . Normalization is unchanged and strips only the previously
named host-pointer fields. Each game includes1200 gameplay calls. The test
cycles distinct aligned direct/scratch target allocations and no-acquisition
fallback requests, with prefix/tail canaries. For SuperFX, accepted acquisition
requests now resolve to full-layout fallback inside the core.

The harness's printed state-check count uses integer floor division, which
understates Star Fox by one; the public receipt computes the actual number
from its0,30,... schedule. This does not affect acceptance or omit a check.
Scripted deaths/respawns occur; this is functional scene coverage, not level
completion or a sustained playability endorsement.

Mario correctly retains the backup's50.319739654 Hz timing; the other four
report59.922743404 Hz. Presentation and emulation rates are not conflated.

## Other verification and evidence

- All18 original FFVI contexts pass1200 calls each:21,600 comparisons with
  exact pixels/PCM/geometry and periodic normalized state, using the corrected
  common-band reference and corrected demand-visible candidate. The reference
  shares the scoped compatibility fixes; it is not original-console truth.
- The unchanged qualified gameplay frontend passes all ten mock cold-boot
  cells under policies0/1 with the new core:600 calls per ordinary cell and
  2400 per Ranger cell,9600 calls total. Render/submission counts and software
  PCM accounting are exact; no errors, remaining or cleared audio. Native ALSA,
  physical display contention and live GPIO are not exercised by those cells.
- The final changed source files reconstruct exactly from the immutable base
  sources plus `prepare-multigame-fixes.py`; no diagnostic tracing remains.
- All five backup ZIPs still hash identically. ROMs, snapshots, images, binaries
  and raw logs remain private; the public receipt contains hashes and metrics.
  No card access/writes, rearm, firmware change or new full backup occurred.

Candidate core SHA256:
`d7988b2861500eb923b827ad412c14ae841c03dd44e4099f2616a637bf88f62a`.

[Qualification and input/evidence hashes](../evidence/2026-10-16/gameplay-fixes/qualification.json).

The final source-producing entry points are
`build/prepare-multigame-fixes.py` and `build/build-multigame-fixes.sh`.
They isolate a new candidate and corrected reference; they do not mutate the
frozen physical FFVI core. `explore-five-games.py` supplies the initial cold
navigation, and the qualification receipt retains subsequent ordinary-button
recipes. Private fixture hashes identify the exact inspected checkpoints.
`qualify-five-gameplay.py v2`, `check-multigame-ffvi.py v2`,
`check-hdma-termination.py`, `check-fixed-gameplay-runner.py` and
`publish-gameplay-fixes.py` produce/check the final receipts. Existing result
directories are guarded against accidental overwrite.

## Remaining acceptance boundary

The two reported failures are fixed in the local tests and all five games now
have actual gameplay coverage. The new binary still needs a matched physical
A7 run. Before installation, quantify its new costs and expected reserve under
the project's performance-candidate gate; SuperFX now pays callback-copy costs
and Ranger has a scoped synchronization change. The FFVI physical result for
the older binary does not qualify this rebuilt one. GSU save/restore, sustained
headroom, real input/presentation cadence and speaker acceptance remain open.
