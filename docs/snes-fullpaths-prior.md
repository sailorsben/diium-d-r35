# Historical A7 calibration before the fullpaths return

The earlier answer overemphasized unknown isolated unit prices. Existing matched
A7 changes support useful conditional forecasts. This forecast uses only older
ability1/ability2/ability3 returns and the new offline work counts; no fullpaths
return was inspected. The staged payload and card are unchanged.

## What measured transitions already constrain

The Window2 generalization removes renderer restarts and associated tile
dispatch/preamble work. Aligned ordinary-frame CPU differences are:

| Context | Removed entries | Net A7 CPU saving us | Saving per removed restart bundle us | Outcome |
| --- | ---: | ---: | ---: | --- |
| Holy | 84 | 1,880.2500 | 22.3839 | Still fails |
| Meteor | 82 | 1,740.1250 | 21.2210 | Still fails |
| Ultima | 85.5 | 2,012.4375 | 23.5373 | Now completes 1,200 calls |
| GrandTrain | 110.875 | 2,571.6875 | 23.1945 | Now completes 1,200 calls |

These are net differences between aligned physical runs, including observers.
The last column is bounded fixture completion, not universal gameplay proof.
Associated tile removals differ: 4,320 Holy, 2,148.75 Meteor, 1,452.0625 combined
full/clipped calls for Ultima, 2,895 GrandTrain. The normalized 21.2210–23.5373 us range therefore
prices a historical mixture of removed work and added costs. It is **not** an
isolated renderer-entry price, cycle count, confidence interval or guaranteed bound.
Unexposed frequency, single paired runs, different work shapes and control
variation remain sources of uncertainty. No inclusive PPU quotient is used.

Conversely, ability3's fixed-math cache removes thousands of counted operations
yet changes whole-call CPU by only about -0.175 to +0.098 ms in the listed failed
tails; controls also move by up to 0.102 ms. That is negative calibration against
assuming inexpensive vector arithmetic removal automatically saves milliseconds.
It supports prioritizing repeated setup and avoiding extra all-row classification.

## A conditional transfer forecast

Apply the observed historical net saving per restart bundle to the new removed
entry population, **assuming similar net work per restart and comparable physical
conditions**. The new fixed-color bookkeeping/row-lookup costs and differences in
tile mix can change or erase this estimate. CPU saving translates to deadline
closure only to the extent that wall/service work falls correspondingly.

`conditional saving us = new removed entries * [21.2210366, 23.5372807]`

| Context | New entries removed | Conditional saving ms | Existing step deficit ms | Saving needed for proposed 20% margin ms |
| --- | ---: | ---: | ---: | ---: |
| Holy | 23 | 0.488–0.541 | 0.972 | 4.310 |
| Meteor | 23 | 0.488–0.541 | 1.778 | 5.116 |
| Siren | 153.5 | 3.257–3.613 | 1.835 | 5.173 |
| Carbunkl | 162.625 | 3.451–3.828 | 0.885 | 4.222 |
| Lullaby Rage | 162.75 | 3.454–3.831 | 2.017 | 5.354 |

This predicts fixed-color batching as the strongest deadline-closure opportunity
for Siren/Carbunkl/Lullaby, conditional on its additional cost. It predicts that
Holy/Meteor still need other savings and does not predict the proposed 20% margin
from this path alone. The transfer is more informative than an arbitrary dispatch
price, while remaining a falsifiable engineering prior rather than a passed gate.

Subscreen and DSP changes target different work. Their isolated A7 gains are not
identified by the Window2 transition. Prior math-cache failure warns against
assuming large net gains from arithmetic removal; silent DSP and classification savings still
require measurement. Combined cache/branch effects prevent summing three assumed
gains. The staged reversed-order crossover tests these hypotheses directly.

After the return, compare measured per-path and combined results against this
forecast, report the miss as well as the match, and update the model. A large miss
should trigger inspection of new overhead/work mix/frequency/service conditions;
it is neither evidence that prediction is useless nor proof of a hardware limit.

Sources: [matched A7 differences](../evidence/2026-10-13/ability2-return/aligned-comparison.json),
[old removed work](../evidence/2026-10-13/ability-regression/qualification.json),
[new aligned populations and deficits](../evidence/2026-10-13/full-fidelity-paths/prediction.json),
[negative math-cache result](snes-ability3-return.md).
