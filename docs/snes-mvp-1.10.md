# SNES MVP1.10 — PCM startup-state repair

The [1.9 return](snes-mvp-1.9-return.md) fails before any emulation: native PCM
accepts44100Hz/128-period/3712-buffer settings and2823 priming frames, then
EBADFD prevents startup. It exposes a client state assumption and missing
after-write diagnostics.1.10 repairs that seam while retaining the exact
qualified early-audio A7 core, display ownership, UI, input and every drawing.
Physical startup, sound, full speed and stability remain pending; prior
whole-device poweroffs remain unresolved.

## Startup contract

Set `start_threshold` to the playable priming target (ceil(rate×64ms)), verify
software-parameter return fields, and allow the documented native write path
to start only once that target is available. After each priming write, observe
state and pointers. A RUNNING stream is acknowledged only after at least the
target priming frames have transferred. A PREPARED stream with sufficient
queued PCM receives explicit START, followed by a fresh RUNNING check.

If START returns EBADFD, accept it only if a fresh observation proves RUNNING
after the priming target. This handles a state transition race; it does not
turn EBADFD into unconditional success. Early auto-start, nonrunning bad-state
results, XRUN and suspended/protocol failures remain visible errors. A failure
after a positive transfer still returns the accepted frame count and exposes
the sticky error separately. There is no replay, silent reset or lost prefix.

The native client preserves operation/errno, last state, availability,
application/hardware pointers, priming transferred and START calls/races.
The owner copies those fields even on failed observation, before cleanup can
erase them. Session/progress reports retain them plus running-stream playable
min/max, distinct from the legacy producer samples and final drained zero.
Successful startup depends on real state, not merely an accepted write count.

Configuration/error messages remain in the RAM runtime log. The wrapper copies
its first192 lines using shell builtins; the historical byte-tail outputs were
empty. No tail/head/sed dependency can suppress startup errors. The compatible
`kernel-tail.txt` filename now holds a labelled first128-line kernel snapshot,
not a claimed kernel tail. Sparse-PATH tests verify actual error/runtime capture
with all three utilities absent. Neither this nor the return establishes why
the old byte-tail captures were empty.

## Qualification and deployment

Independent actual ARM client tests use the observed44100/128/3712 fallback
and compare every transferred byte under partial/EAGAIN writes. They exercise
write-driven auto-start with no duplicate START, healthy explicit START and
explicit-start failure after acceptance, a fresh-state-verified EBADFD race,
rejected early/nonrunning starts and software-threshold mismatch, SYNC_PTR, asynchronous drain and visible XRUN. Actual owner,
final180/30-frame runner, snapshot/SRAM, display/input/splash and abrupt-exit
checks pass. The unchanged core remains exact for1200 frames,1196 with earlier
byte-equivalent PCM batches. QEMU timings are not handheld performance data.

`package-snes-1.10.py` requires exact consumed1.9 bytes, archives all logs/private
progress first and changes only runner/wrapper/test notes. Core, every snapshot,
stock binaries, boot hook,49 lab files and original1.8 wrapper remain intact.
Independent card readback precedes selected immutable publication; no games,
private progress or vendor/core dependency binaries are published.

Use FF6 **Continue** for the latest Save Point, then story/map → party menu →
map, save and exit normally. If startup fails again, the returned report should
identify the precise PCM operation and state rather than just strerror.
The following reboot takes stock after the game one-shot is consumed.

Installation completes after a fresh 43-MVP/49-lab archive. Independent readback
verifies the exact 1.10 payload, all 22 current private files, 49 lab files and
unchanged core/stock/hook/original-wrapper hashes. No snapshot migration or core
replacement occurs. Game one-shot is armed; lab remains unarmed. Physical
startup, playback, speed and stability are pending.
