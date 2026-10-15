# FFVI48-epoch repeat with persistent UART correction

Installed and armed once on I: from pushed source
`46ddf9a81ca83cefac820fe6e4ceabb98d5b96f1`. The fresh strict archive
`device-evidence/a7-pair-before-20261015T065323Z` preserves7,829 prior files;
all7,827 outside the authorized init/dispatcher changes, stock/ROM/progress and
new payload readbacks verify. FAT is clean before/after correction installation,
after retest payloads and after arming. Physical results remain pending.
[Retest installation](../evidence/2026-10-15/uart-spells1/installation.json),
[persistent fix installation](../evidence/2026-10-15/uart-fix1/installation.json).

This repeats the last draw-order ability test with `uart-fix1` active throughout.
The controller, all three emulator cores, plan, states, expected effect data and
inputs are byte-identical to the qualified and physically returned suite. A new
`retro/snes-draw-uart1` destination preserves every earlier result.

The first36 epochs run the draw-order candidate across18 contexts, then repeat
in reverse order. The final12 price raw demand-v3, fixed-APU-only and draw-order
on Meteor/Quasar in forward/reverse orders. Each epoch requests1,200 calls.
The previous [physical return](snes-draw-order-return.md) had all40 candidate
windows clean but a Quasar regression; raw/boundary Meteor controls failed or
drifted. Those controls are deliberately retained unchanged.

The only suite-wrapper changes are the destination and UART status reads before
hardware startup and after child exit. Each requires attached1, no faults/bypass
and cap0. No new reads, clocks, SD writes or samplers run inside the child.
The normal init first loads the persistent correction, then invokes the armed
test. The marker is consumed once; the following reboot uses stock with the
UART correction still enabled. No firmware update is staged.

Qualification rechecks all frozen source/proof/payload hashes, actual firmware
shell syntax and five UART status guard cases. The unchanged ARM controller
completes one bounded epoch under its existing mock mode in the new destination;
full48-epoch qualification is reused by exact payload hashes. This proves
retargeted paths and retains prior coverage, not physical performance. Private mock
results are excluded from installation payloads.

Measured A7 CPU saving and added correction cost are unknown. The measured idle
IRQ reduction is98.994%; the break-even condition is IRQ time avoided greater
than added correction service/dispatch time. No remaining audio-deficit estimate
is invented. The physical prediction is that UART remains attached/fault-free,
the candidate retains its clean histories, and some combination of wall service,
valid running reserve/recovery, deadline margin or control failures improves.
No improvement is also a valid result.

On return, archive before writes. Verify this installation receipt, consumed
marker, all payloads/old protected data, normal-init hash and persistent module;
inspect `uart-before.txt`, `uart-after.txt`, boot log, and wrapper pre/post IRQ
snapshots. Assess the same valid frame intervals, all PCM pointers and complete
cumulative reserve before any drift, rather than just nominal completion.
Compare with the prior archived return. Different boots/environment and IRQ
accounting limit causal CPU pricing; thread CPU alone may not expose IRQ cost.

Safely eject, boot once, allow20–25minutes, and wait for the stock launcher.
Select+Start aborts. Then power down and return I:. If no launcher appears after
30minutes, power down and return the card without another rearm. The UART fix
has its own [rollback switch and installer](uart-persistent-fix.md).
