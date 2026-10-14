# Fullpaths1 A7 return, archived 2026-10-14 UTC

Private archive `device-evidence/a7-pair-before-20261014T003316Z` preserves
5,834 files before card writes. All 91 installed payloads and dispatch verify;
clean FAT serial 11EB-1465. Of 5,020 prior protected files, only runtime swapfile
changed. Original binaries, ROM and gameplay progress remain unchanged. The
one-shot marker was consumed. Analysis uses archived logs only.

All 100 planned runs were attempted; 55 reported runtime failure, 45 completed.
Prior combined completed both 1,200-call windows for Meltdown, Siren, Bahamut,
Carbunkl, Lullaby, Bio Blast and Confuser. Holy, Meteor and Quasar still failed.
Bahamut's historical failure was not reproduced by these baseline repeats.
Completion alone is not valid pointer accounting or a 20% headroom pass.

Matched expensive-call main-thread CPU saving versus ability2, microseconds
(mean for each repeat; 16 aligned calls per interval):

| Context | Repeat 0 | Repeat 1 |
|---|---:|---:|
| Holy/Pearl | 556.813 | 356.313 |
| Meteor | 115.813 | 31.188 |
| Meltdown | 332.125 | 362.750 |
| Siren | 3016.125 | 2939.188 |
| Bahamut | 327.938 | 349.125 |
| Carbunkl | 3755.875 | 3632.938 |
| Quasar | 315.688 | 206.500 |
| Lullaby Rage004 | 3730.438 | 3648.313 |
| Bio Blast control | 385.375 | 350.500 |
| Confuser control | 387.563 | 285.563 |

These are whole-combination costs, not per-entry prices. Holy repeat0 isolated
fixed/subscreen/DSP savings 533.625/300.438/176.813 us sum to 1010.876 us, but
combined saves only 556.813 us. Meteor's two combined gains are 115.813/31.188 us;
subscreen and DSP paths can regress there. Prior arithmetic forecasts therefore
cannot be treated as measured transferable or additive A7 savings.

Conservative prior-combined heavy service proxy (step - pure pacing + all worker
CPU) ranges: Holy18.222-18.244 ms, Meteor19.572-19.632, Meltdown18.074-18.288,
Siren16.683-16.865, Bahamut17.695-17.806, Carbunkl14.648-14.679,
Quasar18.291-18.670, Lullaby15.953-15.987. Against the proposed13.3505 ms
20% target, every context still needs additional savings in this proxy.
Worker overlap may be counted twice; these are not pure core requirements or
hardware impossibility bounds. Fullpaths1 did not capture final worker residual
CPU, so final accounting is extended in combined1. Existing invalid pointer
cases (including completed Meltdown repeat0) remain invalid. All sampled CPU
frequency fields are unavailable; no MHz or native-cycle conversion is inferred.

No production gate pass. New common-band code remains offline-qualified only;
measurement must compare it directly against both baseline and prior combined,
with matched interval, complete effect/recovery, every frame and valid PCM
reserve. New suite avoids attributing logging or incomplete audio work as gain.
