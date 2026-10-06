# SNES MVP1.15: retain sampled costs through a long run

This is the final test candidate for the [A7 execution-budget rewrite](snes-mvp-1.14.md).
The core, converter and PCM changes are those locally qualified in1.14.
Before handing the card back, review found that the24-call recent history
could age sampled APU/PPU costs out after an unsampled stretch.1.15 retains
the most recent eight sampled calls separately, including epoch, call number,
CPU/wall/frontend/admission costs. Recent ordinary calls remain separate.
Both histories are bounded RAM and are included in checkpoints/final reports.
No additional clock sampling or gameplay card I/O is introduced.

The1.14 payload and public check files remain immutable. It was an installed,
locally qualified intermediate candidate and was retired without a physical
run. The exact core is unchanged in1.15. The runner, native lifecycle,
starvation, boot/input/display/snapshot and retained-sample checks were rerun.
QEMU output and timings still do not prove handheld speed or sound.

`build/package-snes-1.15.py` requires the exact unarmed1.14 owned payload.
The1.14 one-shot is archived and retired before that update; all original
private progress, historical snapshots, stock/hook and lab files are preserved.
The separate snapshot qualified for the unchanged new core is retained.
Independent readback and immutable publication are required before delivery.
Use [the gameplay instructions](snes-mvp-1.15-test.txt) for one meaningful run:
Continue, expensive scene/party menu/map, pause/resume, optionally load the older
snapshot, then save and exit. Native cadence, complete sound and stability
remain pending physical qualification.

Installed and independently read back at2026-10-06 05:48 UTC (October5
America/Chicago). Archive45 MVP/49 lab files before final writes. All23
existing private files remain byte exact, including the separate new-core
snapshot, and stock/hook/older wrapper match. Game one-shot armed; lab
unarmed. Curated qualification/install/readback evidence is in
`evidence/verification/snes-mvp-1.15/`; owner-only archives remain local.
