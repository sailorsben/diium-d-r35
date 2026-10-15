# Unchanged-core PC diagnostic return

The sampler works on the A7 and points to general rendering work as the first
optimization target. Quasar is clean in both bounded windows. Meteor still loses
valid audio pointers, including a control that reports completion. This diagnostic
does not establish a hardware ceiling or an optimization speedup. I: is unarmed;
no card writes, emulator changes or rearm occurred during evaluation.

Strict private archive `device-evidence/a7-pair-before-20261015T002114Z` preserves
7,359 files / 1,848,513,197 bytes with clean FAT. All 88 installed payloads,
dispatcher and consumed marker verify against the installation receipt. Of the
7,225 protected prior files, 7,224 remain exact and only the stock swapfile changes.
Stock binaries, adapter, production core, boot hook, original progress and live
ROM hash verify. Both diagnostic cores remain byte-identical ordinary demand-v3.
All four epochs ran; workers joined and the display was freed. No independent
panel/speaker observation was supplied for this diagnostic.

| Run | Effect / sampling | Calls | Qualification |
| --- | --- | ---: | --- |
| 0 | Meteor / off | 1,200 | Invalid: first frame-pointer drift at 532; final bias 384 frames |
| 1 | Meteor / on | 509 | Invalid: first drift at 488; native PCM errno77, final bias 384 frames |
| 2 | Quasar / on | 1,200 | Clean bounded window: every frame, exact PCM, complete trace, valid pointers |
| 3 | Quasar / off | 1,200 | Clean bounded window: every frame, exact PCM, complete trace, valid pointers |

Frame indices are zero-based. Run0's zero reported errors/XRUNs and complete
drawings do not override its pointer failure. Run1 submits508 of509 calls before
the audio error. Every successful submission uses owned direct output; copied
payload bytes remain0. Both Quasar runs have1,200 scaled/flipped frames, no holds
or duplicates, zero pointer bias and minimum valid running reserve2,059 frames
(46.69ms at the negotiated44,100Hz). Their complete running-sync histories grow
reserve from2,823 to3,016 frames, with exact cumulative accepted-minus-HW-pointer
accounting. This is vendor logical accounting, not an independently measured DAC.

Meteor's complete retained running-sync prefixes show cumulative reserve loss:
2,823 ->747 frames over8.919s in control, and2,823 ->748 over8.186s with sampling.
Accepted growth minus HW-pointer growth is exactly-2,076/-2,075 frames. Minimum
valid running observations fall to170/141 frames (3.85/3.20ms). No later apparent
reserve is certified after the first invalid pointer. The control's worst valid
16-call recorded main+audio/display-worker CPU is16.954ms against16.688ms nominal
quota:0.266ms recorded excess. Reaching the20% target would require3.604ms reduction
over that interval before uncounted system costs. Neither is a guaranteed fix
budget or a complete-system price.

PC sampling reports error0 and dropped0 in both runs:613 Meteor and1,333 Quasar
active samples. Only583 Meteor samples from frames0–487 qualify; all1,333 Quasar
samples qualify. Their timers also report7/24 idle deliveries and5,519/12,158
coalesced expirations, maximum overrun19/21. Observed CPU per delivered notification
is9.92/9.97ms, despite a requested1ms. Expirations are not extra samples and are
never used as weights. The later Meteor heavy window496–535 is unavailable under
valid sampled pointers; its zero selected samples are not evidence of zero work.

The table uses the same broader heavy interval384–487, entirely valid in both
sampled runs, with164/142 delivered samples. These are observed sample shares,
not exact time shares or independent random observations.

| Named symbol group | Meteor samples | Quasar samples |
| --- | ---: | ---: |
| PPU render + PPU registers | 87 /164 (53.0%) | 66 /142 (46.5%) |
| DSP + SPC/APU | 29 /164 (17.7%) | 38 /142 (26.8%) |
| 65C816 operations/memory | 18 /164 (11.0%) | 16 /142 (11.3%) |
| Mixed core scheduler | 12 /164 (7.3%) | 9 /142 (6.3%) |
| DMA | 5 /164 (3.0%) | 4 /142 (2.8%) |
| Other core / main host or libraries | 13 /164 (7.9%) | 9 /142 (6.3%) |

PPU counts are conservative: the frozen classifier leaves `RenderLine`,
`RenderScreen`, some window/geometry helpers and pixel writers in other core.
Every symbol count is retained for audit; one Quasar sample in the full run is
explicitly unmapped in the extended census. No worker instruction sampling occurs.
Meteor's largest heavy-interval named functions are `d35_geometry_draw_0` (19),
`d35_fused_band_1_0` (15), `DrawTile16` (14), `retro_run` (12, mixed) and
`d35_fused_band_3_0` (12). Quasar's are `d35_fused_band_1_0` (27), `DrawTile16`
(16), `dsp_run.part.0` (14), `retro_run` (8) and `dsp_voice_V3` (8). The full
valid-prefix DSP share is about22% in each effect, so audio synthesis remains a
substantial general secondary target. SPC loop unswitching is already present in
this baseline; compiler isolation prevents a future regression rather than
supplying an established new baseline saving.

Sampling has a measurable disturbance. Over common valid warm frames, sampled
minus control recorded thread CPU is+0.159ms/call for Meteor and+0.105ms for Quasar;
core CPU alone is+0.132/+0.109ms. In fixed frames384–415 the thread-CPU difference
is+0.146/+0.129ms. There is one pair per effect with reversed order across effects,
so these include run/order variation. Do not subtract them from samples as an
exact calibration. Sampling may contribute to earlier Meteor failure; that
causal share is not isolated. The unprofiled control also fails pointer qualification.

The strongest existing lead remains state-based draw priority and avoidance of
hidden color production, with the compiler boundary held stable. The local
priority prototype removes32.5% of Meteor main RGB writes and3,407 vector
expansions per heavy call under exact replay; this physical census now places
related geometry, band and tile producers in the hot path. Extra traversal and
guards still require net A7 pricing. Sample fractions cannot price those costs
or convert32.5% fewer writes into32.5% faster emulation. Independent priority,
transparency, clipping and OBJ tests and a production-form exact qualification
remain necessary before another optimized candidate. Further progress should
target work avoidance there, followed by exact DSP improvements if needed.

Reproduce with `python build/evaluate-pc-profile-return.py <strict-archive>`;
`--verify-live` additionally reads I: to verify current protected files/payloads
and ROM. The evaluator checks complete retained PCM transaction counts, valid
prefixes, cumulative reserve identities, exact ELF owners and matched control
intervals. Frozen sampler/preparation proofs and all prior published hashes
remain exact. The [published analysis](../evidence/2026-10-14/pc-profile-return/analysis.json)
contains counts, comparisons, limits and raw-input hashes. The earlier
[installation record](snes-pc-profile-installation.md) remains historical.
