# MVP1.17: keep diagnostics outside playback

The [1.16 return](snes-mvp-1.16-return.md) sustains31,601 complete frames at
about59.99 core calls/sec on its successful retry. Its first launch fails
inside the wrapper's300ms platform-discovery/card-copy window. Main CPU stays
around9ms while wall time rises to18–39ms and PCM reserve drains.

The wrapper now captures static platform evidence and flushes it **before
starting the launcher child**. It performs no routine discovery, diagnostic
card copies, background monitor or global sync during the child lifetime.
Runner progress and phase history stay in `/tmp`/RAM. After child exit/joined
teardown, the wrapper copies final progress/runtime logs, captures a post-child
platform snapshot and syncs. Startup-timeout diagnosis remains available for
a child that never signals ready.

Native PCM faults still write/fsync their bounded history before returning an
audio error. Failed-session report/trace pairs still survive retries. Game
saves and snapshots still persist at their explicit lifecycle points. This
change does not make all storage activity disappear; it removes the wrapper's
unrequested routine diagnostic work from playback.

Abrupt whole-device power loss can now lose the latest RAM progress. The card
then retains startup evidence and any already-persisted fault/session records,
not a fresh periodic gameplay checkpoint. A completed kernel ioctl or changed
`appl_ptr` still requires the native flight history for attribution. Do not
interpret this tradeoff as a solved poweroff cause.

The1.16 core remains byte-identical (`2c04a7ad…`, CRC`4d245ba5`,785,504 bytes).
Full raster rendering, all sound settings, PCM negotiation/priming, A7 kernels,
converter and queue/admission policy remain. Runner report version becomes1.17.
No automatic PCM recovery, larger initial silence, or weather-effect patch is
introduced.

The actual shell fixture observes all wrapper diagnostic files and sync calls
through a ready child's five-second lifetime. Old1.16 is rejected for a live
diagnostic card write;1.17 leaves them unchanged until exit, then retains final
progress, logs and fresh fault history. Splash/ready/watchdog/minimal-firmware
contracts and actual ARM runner audio, snapshot, save and teardown checks pass.
Extended12,000-frame clean-core equivalence and private scene-capture logs
accompany qualification. QEMU checks are correctness evidence, not device
timing or audible-effect qualification.

The guarded installer accepts consumed exact1.16 on inspected D:, archives
all returned files first and preserves current saved progress, original
snapshots, stock/hook and all49 lab files. Independent readback must precede
handoff. [One coherent physical test](snes-mvp-1.17-test.txt) checks cold first
launch and sustained gameplay. Wind/snow fidelity remains separately unresolved.

Installed and independently read back2026-10-06 at13:21 UTC. Pre-write archive
contains48 MVP/49 lab files. All26 original private files and all retained
stock/hook/lab files match. Game armed, lab unarmed; core and snapshot payload
remain unchanged. Runner SHA256`673581b3…`, wrapper`a90b99db…`.
Release: `releases/snes-mvp-1.17/`; qualification and independent readback:
[`evidence/verification/snes-mvp-1.17/`](../evidence/verification/snes-mvp-1.17/independent-readback.json).
