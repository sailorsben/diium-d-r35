# SNES MVP1.11: coherent PCM pacing and resume

The [1.10 return](snes-mvp-1.10-return.md) reaches emulation but fails on WRITEI.
The software queue is not full; its error label hid the native worker failure.
This repair keeps the exact early-audio A7 core and requested PCM configuration.
It adds no drawing suppression, silent reset or automatic underrun recovery.

## Changes

- Paced admission waits for a generation-matched worker observation before
  deciding whether to run the next core call. A wake request alone is not
  freshness. Source reproduces the old defect with an independently changed
  actual PCM lead; the repaired owner blocks until the fresh eligible reading.
- Native observations use SYNC_PTR with post-HWSYNC state and both GET flags.
  Application pointers and readiness controls are preserved. Queued frames use
  the returned boundary, including wrap. Fault observation reads state without
  another hardware update and never converts an invalid stream into success.
- Pause drains and joins before reset; reset restores the period refill
  threshold left at full-buffer by DRAIN. A drain fault stops the pause path
  before snapshot/reset work. Failed writes retain a fresh post-fault snapshot.
- Publication distinguishes an actual ENOBUFS from EBADFD or another worker
  error. Reports add paced-admission lead bounds, native stream epoch/accepted
  counts and snapshot load/rejection counters, with RAM phase checkpoints.

The reserve and hardware candidates remain 64ms and the existing rate/period/
buffer negotiation. This prices coherent actual consumption rather than adding
another timer gate. Lower sampled lead still records a risk; the repair does
not guarantee a floor when production or scheduling exceeds the available PCM.
No compatible GPU, persistent scaler queue or higher clock is inferred.

## Qualification

The unchanged core retains its exact-output qualification. Independent ARM
fixtures cover priming, partial/EAGAIN frames, state faults, pointer wrap, GET
control preservation, drain threshold restoration, fixed deadlines and fresh
admission. The old owner demonstrably fails the same admission counterexample.

The new real FF6 test combines runner, owner and native PCM client with a
separately consuming 44100Hz/128-period/3712-buffer provider. It injects WRITEI
EBADFD, verifies the truthful failure and clean relaunch, then performs two
snapshot loads/re-primes with 120 full drawings and 25ms producer stalls.
Successful accepted/enqueued PCM matches exactly, with zero cleared/remaining
frames. GPIO/splash/display ownership, ARM180/30-frame runs and save rollback
remain checked. These establish software/lifecycle contracts, not handheld
timing, continuous sound or a vendor-driver fix.

The exact consumed 1.10 updater archives all logs/private progress before
changing only runner/wrapper/test notes. It preserves newly updated SRAM,
snapshots, core, stock/hook and all lab files. Independent readback precedes
selected publication; vendor binaries, ROMs and private progress stay local.
Use [test notes](snes-mvp-1.11-test.txt), including our snapshot load/resume.
The following reboot takes stock after the game one-shot is consumed.

Installation and independent card readback complete at 2026-10-05 19:09 UTC.
Before writes, all 43 MVP and 49 lab files are archived and hash verified.
After writes, all 22 current private files, 49 lab files, original snapshots,
core, stock binaries, boot hook and older game wrapper match their protected
hashes. Only the runner, wrapper and test notes change. Game one-shot is armed;
lab remains unarmed. Physical playback and snapshot resume are still pending.
