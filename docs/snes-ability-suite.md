# Automated original-ROM ability exercise

Authorized experimental one-shot `1.19-ability1`, separate directory
`retro/snes-ability1` on I:. The original ROM and gameplay saves are unchanged.
The emulator is the same counter-free core that passed the two Confuser fights
(SHA256 d5761eacc68fbcba91052de19d37ca9f159fb2b40df7c9272f49398b9b4f880a).
No generalized renderer candidate or production replacement is installed.

## Scope and success

400 independent cases:54 Magic,27 Espers,8 Magitek,24 Lore,8 Tools,8 Blitz,
8 Bushido,8 Dance and255 Rage entries. These are menu/command cases, not400
distinct animations. Rage includes entries outside ordinary learnable gameplay;
random Fight/Special branches and Dance terrain/stumble rules remain natural.
One seeded outcome does not cover every possible animation of each command.

The user's criterion is that the ability fires and its animation renders and
finishes without a runtime failure. Damage/healing balance is not an acceptance
requirement. Targets must allow the ability to fire: living high-HP enemies,
injured living allies for healing, KO Wedge for revival, curable status for
status cures, existing enemy buffs for Dispel, Reflect for Reflect Lore, and
enemy level60 for level-based Lore. Each case reloads an isolated fixture;
previous cases cannot exhaust MP or kill the next target. Blitz uses the real
button sequences; Bushido uses a prepared charge level and normal confirmation.

Offline targeting checks found Raise/Arise initially aimed at living Terra.
Selecting Down after opening the target cursor revives Wedge in both corrected
cases. Preserve the negative receipts. All16 Blitz/Bushido graphic identities
are observed; their attack numbers are command-local, unlike global graphics
indices. Retort/Stunner share graphics properties, so the local number matters.
The last three Rage cases select IDs252–254, verified from game RAM.

## Timing, evidence and limits

Each case runs at most1,200 nominal calls with normal native audio and display.
At16.6881545ms/call,400 cases require133.505 minutes before load/flush overhead.
Plan for more than2h15 and use power. MENU/Select+Start stops the sweep; B is
not required. Logs are flushed between cases after the audio worker is joined
and the display queue is idle. The display worker remains owned by the suite
until final board cleanup; it is not joined at every case boundary.

`begin.txt` persists case identity before workers run. `frames.csv` records
kernel thread CPU/wall/admission, quota/reserve, display metrics and frequency.
`animation.csv` stores frame-boundary properties, attack number, target masks,
HP/MP/status and Rage/Dance selections. Observer copy/timer cost is reported
separately and remains included in run cost. Frequency is inspected/pinned only
to an exposed existing maximum if permitted, restored afterward, and recorded;
no assumed666MHz conversion. No per-frame SD logging or pixel CRC scanning.
`result.txt`, deferred PCM trace and wrapper logs identify runtime failures.

Frame-boundary property matches are observation evidence, not proof that every
animation thread completed: cached properties can remain and short events can
fall between samples. Analysis must distinguish observed animation, absent/
conditional command, truncated case, PCM failure and missing completion proof.
The visible animation plus logs support qualification; a completed1,200-call
loop alone does not pass an ability. Hard process failure leaves a begin record
without a result and stops the suite; do not manufacture recovery/pass evidence.

## Prediction before installation

The unchanged renderer predicts no saved emulation work. Instrumentation adds
nonnegative overhead; logging is moved outside each active case. Saving S and
incremental renderer unit costs e/r/b are not measured by this suite; the
production installation gate remains false. Its falsifiable physical purpose
is to locate which real command contexts lose cadence/reserve or fail, while
recording which animation actually fired. Offline QEMU timing is excluded from
A7 performance evidence. Earlier124 normal-command passes do not qualify all
400 new contexts or physical speed.

Installation requires a fresh complete archive, known-card serial/clean FAT,
unchanged protected hashes, exact qualified runner/core/wrapper/fixture hashes,
and readback. Only the owned dispatch and one-shot marker change outside the
new versioned folder. The marker is consumed before running; next boot is stock.

See [instructions](snes-ability-suite-test.txt). Physical result is pending.
