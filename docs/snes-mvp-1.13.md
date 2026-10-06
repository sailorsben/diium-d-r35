# SNES MVP1.13: durable capture before audio error return

The [1.12 return](snes-mvp-1.12-return.md) has a fresh fatal report but no PCM
flight history. Relying on a RAM file plus periodic wrapper copies did not
preserve the needed evidence on this device. This build repairs that seam;
the SETUP transition and 384-frame discrepancy remain unresolved.

## Capture contract

- Keep the existing bounded 96-operation RAM history during normal playback.
  No healthy-transfer file writes or kernel-log reads are added. Its existing
  timestamp syscall/memory overhead remains physically unmeasured.
- On the first sticky fault, snapshot kernel READ_ALL before any card I/O.
  Record the actual returned bytes or errno; a refused read still allows the
  PCM history to be captured. READ_ALL does not clear the ring.
- Write `$BASE/last-pcm-fault.txt.tmp` directly, flush stdio, `fsync` the file,
  close, rename to the final path and `fsync` its containing directory. Complete
  this before returning the error to the audio owner, before DROP/close and
  before the library can report the failure.
- Append `trace_errno`, `trace_synced` and `trace_bytes` to PCM error detail.
  Only a successful file and directory sync gives `trace_synced=1`. Preserve
  the original PCM errno if capture fails. Keep a failed temporary file for
  collection; do not reinterpret capture failure as playback recovery.
- The wrapper clears old final/temporary history at the next armed start and
  retains fresh final/temporary captures on cleanup. Fault capture no longer
  waits for a periodic copy or wrapper exit.

Fault-only card writes can delay the error screen. No playback recovery is
attempted, so this occurs after the stream has already failed. Physical card
sync support, kernel-read access and capture durability still need the test.

## Verification and deployment

The actual ARM native-client fixture verifies bounded history, no healthy log
writes, successful file and directory sync, and explicit injected sync failure
without changing PCM errno. The real runner/owner/native-client test with FF6
proves the fault file exists before the runner returns, then exercises a clean
retry and two snapshot resumes. The actual wrapper passes immediate-error exit
with the direct card path, retained temporary capture, stale-history clearing,
splash handoff and firmware-style absent tools. Existing input/clock/display/
save checks and unchanged-core exact-output checks pass. Software fixtures do
not prove vendor transitions or handheld performance.

`build/package-snes-1.13.py` accepts only the exact consumed 1.12 card, archives
all returned logs/private progress before writes, updates runner/wrapper/test
notes and arms last. Core, PCM settings/admission, full drawing, snapshots,
SRAM/backups, stock/hook and lab files retain protected hashes. Independent
readback is required before publishing the owned release and selected checks.

[Test once](snes-mvp-1.13-test.txt). One audio error is enough; reconnect D:
afterward. Inspect the history and capture status before choosing another
behavioral change. Continuous full sound/rendering remain the goal.

Installation and independent readback complete at 2026-10-06 04:42 UTC
(October 5 in America/Chicago), following another verified 43-MVP/49-lab archive.
All 22 current private files, original snapshots, current SRAM and backup,
49 lab files and stock/hook/core/older wrapper match their protected hashes.
Game one-shot is armed; lab remains unarmed. Physical result is pending.

## Physical return

The [1.13 return](snes-mvp-1.13-return.md) proves durable PCM capture and kernel
READ_ALL, but still fails audio. Reserve erosion precedes period-sized pointer
increments and SETUP. The card is consumed/unarmed. No new build is installed;
the [budget review](execution-budget-review.md) defines the next proposal.
