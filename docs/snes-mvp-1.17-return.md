# MVP1.17 return: first launch works, Magitek Bio Blast drains audio

The user confirms FF6 started on its first attempt. The one recorded launch
ran 35,763 core calls in 596.266 seconds of active time, about 59.978 calls/sec,
with zero held drawings or duplicate video callbacks. Its snapshot load worked.
Using **Terra's Magitek armor Bio Blast** then produced an audio error and
returned to our library. This was not Edgar's Tools Bio Blaster, a recorded
core segfault, or a reported whole-device power-off.

The final 22 ordinary calls average 17.981 ms wall / 16.638 ms main CPU.
Earlier retained samples put inclusive PPU work near 3–4 ms; the final sampled
call records 8.150 ms PPU / 4.616 ms APU. Sampled regions include their own
measurement overhead. Display reservation averages only 0.00469 ms/call over
the session; that does not assign the entire effect deficit to display waiting.

Matched large audio batches arrive about every 18.37 ms near failure, producing
about 40,066 accepted frames/sec against a 44,100 Hz sink. Reserve erosion
precedes three unexplained 128-frame application-pointer advances and
SETUP/EBADFD. The trace supports a transient production deficit. It does not
identify which vendor component advances the pointer or establish that every
scene runs slowly. We continue to report the fault rather than silently restart
audio or omit emulated frames.

The returned card was unarmed. All 50 MVP / 49 lab archive files verify, the
installed payload matches 1.17, and stock hashes match. Only current SRAM changed
among protected gameplay files; all snapshots and SRAM backup remain intact.
Archive timestamp is 2026-10-09 02:01 UTC, **2026-10-08 America/Chicago**.

The unique native failure report/PCM history and startup log are fresh 1.17.
`last-session.txt.bak` and `last-run.log` are retained 1.16 artifacts. The two
fresh native reports differ only in their checkpoint/elapsed timestamps because
unique failure persistence follows the final report. Native teardown finishes
in startup.log, but no completed wrapper-exit copy is present. Its absence does
not establish why the wrapper did not finish persisting its RAM logs.

The user checked playthroughs and withdrew the expectation of driving snow in
that Narshe section. There is currently no demonstrated snow regression. This
correction does not independently establish every wind sound or clean-core
effect is accurate.

For [1.18](snes-mvp-1.18.md), an offline tool derives a private replay from the
owner's Narshe snapshot: force a grass-background formation, use Terra's normal
Magitek menu, select Bio Blast, and execute its real game script. No attack
parameters, ROM scripts or emulated timing are changed. This reproduces the
effect, not the exact physical encounter/background. Its complete 1,200 frames
match clean-core pixels, PCM, geometry and periodic logical state.

[Verified return and work counts](../evidence/2026-10-08/snes-mvp-1.17-return/analysis.json).
