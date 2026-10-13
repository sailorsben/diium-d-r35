# FF6 ability lab — 2026-10-12

An isolated super-unit battle fixture is built locally. Terra has 9,999 HP,
999 MP and three selectable command profiles. The other two party members also
have 9,999 HP/999 MP, and the lone enemy has 60,000 HP. Original levels,
strength, magic power and ordinary ability rules remain intact. This keeps
damage manageable while exercising the game's own commands and graphics.

The ROM is unchanged. Unlocks, resources and command slots live only in copied
private snapshots, separate from actual gameplay progress. No card access,
installation, renderer change or production promotion occurs in this task.

| Profile | Terra's four command slots | Available choices |
|---|---|---|
| Spellbook | Magic / Lore / Magitek / Item | 54 spells,24 Lores,8 Magitek abilities |
| Skills | Tools / SwdTech / Blitz / Dance | All8 Tools,8 Bushidos,8 Blitzes,8 Dances |
| Rage | Rage / Magic / Lore / Item | 255 non-terminator Rage table IDs,including unusual/boss entries |

FF6 has four command slots and one equipped esper per character. Accordingly,
the lab has three main checkpoints and27 separate summon-menu checkpoints.
Rage table exposure does not mean255 ordinarily learnable or qualified Rages.
One character also cannot supply every enemy-only, item, weapon or scripted
effect; those need separate contexts.

## What has actually passed

Against the original1.19 renderer, the separate generalized-window ARM candidate
passes **124 requested casts** through ordinary menu/button input in the
original ROM. Every qualified cast hits its actual animation-table record,
initialization and completion. Each run compares1,200 nominal calls: graphics
and native PCM every call, and logical serialized state every30 calls with only
the existing named host-pointer fields normalized.

| Family | Requested casts qualified |
|---|---:|
| Magic |54/54|
| Lore |24/24|
| Summons |27/27|
| Magitek |8/8|
| Tools |8/8|
| Blitz |Pummel only; remaining7 unlocked but unqualified|
| Bushido |Dispatch only; remaining7 unlocked but unqualified|
| Dance |Native-terrain Wind Song -> Wind Slash only|
| Rage |Soldier selection/initialization observed; requested Fire not produced|

All126 final scenarios remain graphics/PCM/state equal over **151,200 calls**.
Two scenarios receive `needs_context`, not a passing requested-cast verdict.
Those two are ordinary random/contextual outcomes:

- Soldier Rage sets its monster ID to1 and Rage status. Enemy HP decreases by66
  while no Fire animation initializes. The original `RandRage` chooses between
  Fight and Fire with probability1/2 each. This run follows the physical branch;
  matching outputs alone cannot qualify Fire. Further natural Rage turns/RNG
  contexts must establish that outcome.
- Water Rondo runs on native Wind Song/grass terrain. The game permits a50%
  stumble on mismatched terrain; the end-state retains selected Dance ID5 but
  clears Dance status and never starts El Nino. Conditional on success, Dance
  probabilities are7/16,3/8,1/8,1/16. Thus the first El Nino chance here is7/32
  (21.875%), not certainty. Native Wind Song successfully produces Wind Slash.

These probabilities assume the game's normal RNG distribution. A deterministic
saved state has a deterministic outcome; repeating identical inputs is not a new
random trial. No RNG, damage, terrain or effect-animation substitution bypass is
used to turn those two cases into artificial passes.

The124 passes establish bounded offline correctness, not A7 throughput, reserve
or repeated-cast stability. The original four-command menu, single-enemy normal
battle and Magitek party sprites remain the underlying context. Reflected,
multi-enemy, side/back, field/event, weapon/item, all Rage outcomes and remaining
Blitz/Bushido/Dance choices still need coverage. Target level, immunity, current
HP and status can change hit/miss, revival and conditional effect branches;
casting every menu entry does not qualify all those branches.

## Setup corrections retained as evidence

38 earlier completed receipts are preserved outside the final qualification
population: four passing superseded checks and34 requested-identity misses.
No output/state mismatch occurred in those receipts. The failed setup attempts
remain immutable, together with their snapshots, input streams and logs.

Source analysis corrected the harness, rather than accepting matching pixels
as proof of a chosen ability:

- The English Magic menu uses two columns. English `LORE_SELECT` explicitly
  sets one column; its shared position table is not the language-specific
  cursor algorithm. The final Lore recipe uses the actual `LANG_EN` branch.
- Command-list edits do not automatically redraw cached menu labels.
  `w7e3a58` requests the game's `BTL_GFX_11` redraw; mechanical HP/MP and display
  caches must agree.
- Tools requires the battle inventory as well as persistent inventory and the
  owned-Tools mask. All eight original item targeting records are copied from
  the ROM. Tool mechanics IDs125/126 are not their graphics-table indices329/330;
  the graphics dispatcher uses `NOISEBLASTER + tool index`.
- Bushido requires the actual eligible-weapon flag. Rage/Dance selection proceeds
  through the game's self-target confirmation; Active-mode controls isolate
  Wait-mode pauses without changing natural RNG or terrain rules.

Offsets come from the byte-matched English FF6 linker symbols and source in
the private disassembly at commit813013276c. Relevant routines are
`party.asm`/spell-list construction, `cursor.asm`/language-specific selection,
`anim_cmd.asm`/Tools dispatch, `action_1.asm`/`RandRage`, `RandDance` and
`DanceRateTbl`, and `battle_cmd.asm`/Dance terrain/stumble rules.

This is a deliberately engineered early-Narshe fixture derived from the earlier
owned Magitek test state, including its historical battle-setup edits. It is
not an untouched ordinary save or a guarantee that re-entry into another battle
will preserve these injected command lists. Reload a lab checkpoint for each
new case.

## Private playable package and manual test

`build/ff6-ability-lab-private-v1/playable/` contains30 checksum-verified
checkpoints: `spellbook`, `skills`, `rage` and27 named summons. Each has its own
`saves/` directory and a valid regular-runner snapshot filename/header.
They are compatible with the successful counter-free Confuser gameplay core:

- Core SHA256 `d5761eacc68fbcba91052de19d37ca9f159fb2b40df7c9272f49398b9b4f880a`,
  CRC5cb51346,798296 bytes.
- ROM SHA256 `0f51b4fca41b7fd509e4b8f9d543151f68efa5e97b08493e4b2a0c06f5d8d5e2`,
  CRCa27f1c7a,3,145,728 bytes.

All three main profiles also pass the owned actual runner/PCM-owner consuming
client fixture: six successful snapshot loads and360 full drawings with the
working counter-free core. That fixture deliberately injects PCM faults/stalls
to verify load/re-prime/fault retention/drain behavior. Its clocks and provider
are mock hardware; these results qualify the snapshot-loading seam, not A7 speed.

This package is ready for a separate future hardware stage; no launcher/installer
has been added and it is **not loaded on I:**. Keep each profile's save directory
separate from real progress and other profiles. The regular frontend has one
snapshot slot per ROM/core identity, so future staging must select the profile
directory explicitly; placing all30 identically named states into one directory
would overwrite them.

Once staged under a separate lab entry:

1. Use Select+Start -> Load snapshot. The main profiles open Terra's command menu;
   summon checkpoints open the selected summon menu. Commands use normal controls.
2. Cast one chosen ability. Observe its complete effect and recovery, continuous
   sound and the ability to reopen the menu or resume play. Note the exact name.
3. Reload the checkpoint before the next case. Doom/Death, Warp, self-destruct,
   lasting status effects and summons may end or disrupt battle normally despite
   increased HP. A normal battle ending is not an emulator crash.
4. Use SwdTech's normal charge gauge and Blitz's real input sequence. Dance/Rage
   outcomes remain random; verify the produced effect, not just the menu choice.
5. For repeated-cast stability, repeat a named case from the same checkpoint and
   retain startup/effect/recovery evidence. Sparse end-of-session telemetry alone
   cannot prove every chosen ability occurred or remained within budget.

Highest-value first physical cases are Holy, Meteor, Ultima, GrandTrain, El Nino,
glow-heavy summons and Mode7 controls identified in the
[effect safety screen](ff6-effect-safety-screen.md). This lab provides selectable
real-command contexts for much of that list. A matched-state core comparison
still needs real A7 incremental prices, kernel clocks, actual frequency conditions,
live audio/display workers and full effect/recovery reserve. Previous work-count
savings cannot be transferred as measured milliseconds to these new contexts.

Any future card write requires explicit staging authorization plus a fresh
archive/FAT/protected-hash gate. Preserve `emu_sfc.so`, stock files, current
working core and private gameplay progress. A new checkpoint lab is a new test
context; it does not authorize installing the generalized renderer.

## Reproduce and inspect

Private prerequisites are the owned ROM, byte-matched disassembly, current
counter-free core, original1.19 reference, prior owned replay runner/sysroot,
the earlier private Magitek seed and existing generalized-window screen core.
No ROM, snapshot, SRAM or vendor binary is published.

On a fresh private lab tree, `sh build/build-ff6-ability-lab.sh` bootstraps the
owned seed, prepares/redraws profiles and builds the ARM checker. It refuses
replacing an existing checker. `python3 build/run-ff6-ability-lab.py menus`
creates the normal spell/Lore/Magitek/summon cases; `skills`, `dance`,
`skill-contexts` and `confirmed-skills` prepare the additional profiles/cases.
`qualify` and `qualify-skills` run new cases, or verify completed receipt identities
and reuse them. Historical `correct-magic`, `correct-lore`, `english-lore` modes
preserve this investigation's setup corrections; fresh `menus` uses correct
English layouts directly.

`python3 build/qualify-ff6-ability-lab-runner.py` performs the three new-profile
runner checks in fresh private output folders. It refuses replacing completed
checks. The six main-profile loads are additional to the cast comparison calls.

`python build/analyze-ff6-ability-lab.py` verifies every completed receipt,
original identities and packaged checkpoint CRC/SHA, and regenerates only derived
private analysis. It does not rerun completed emulation or access the card.
The public [analysis](../evidence/2026-10-12/ability-lab/analysis.json),
[coverage](../evidence/2026-10-12/ability-lab/coverage.csv) and
[bounded cast proofs](../evidence/2026-10-12/ability-lab/proof-summary.log) and
[runner loading proof](../evidence/2026-10-12/ability-lab/runner-proof.json)
preserve all764 prior manifest entries and append four bounded files.
