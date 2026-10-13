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

## Pearl: explicit combined planning forecast

Later offline [C workback](snes-pearl-workback.md) identifies two additional
mechanisms and the unit-price threshold needed to reach the capacity target.
It does not retroactively change this prior or provide a fullpaths A7 result.

Pearl is HOLY in the suite, original-ROM spell ID 0x0e. This forecast is written
on request before inspecting any fullpaths return. Existing staged bytes stay
unchanged. Measured ability2 heavy-tail step is 17.6605625 ms; deadline is
16.6881545 ms; proposed 20% target is 13.3505236 ms. These tail means are not an
entire-effect service curve or worst-case bound.

My working point estimate is **1.0 ms additional net saving**, allocated as:

| Path | Planning allowance ms | Basis and uncertainty |
| --- | ---: | --- |
| Fixed-color batching | 0.5 | Historical transfer above, subject to different new costs |
| True-subscreen composition | 0.3 | Engineering assumption over 4,166 eligible rows; no isolated A7 price |
| DSP unused interpolation | 0.2 | Engineering assumption over 1,372.25 zero-envelope calls; no isolated A7 price |

The last two numbers are expressly judgments, not empirical estimates recovered
from successful past tests. They assume effective net credits of about 0.072 us
per eligible row and 0.146 us per omitted interpolation after added predicates on
other work. The C confirms that selections/classification and four-tap Gaussian
work can be removed; it does not supply these microsecond prices. Prior A7 warm
benchmarks price different functions and do not measure these paths. Neither
Confuser's unmatched successful tail nor its coupled BG3/half-add change can
identify either new price. The fixed-color term is better calibrated than the
other two. No extra standalone saving is credited for cache interactions.

A rough **0.7–1.4 ms planning band** expresses uncertainty in added costs and
interaction. It is judgmental, not a confidence interval, observed range or
guaranteed bound; outcomes outside it remain possible. In particular, isolated
gains are not proven additive merely because the point estimate adds allowances.

| Additional saving ms | Conditional remaining step ms | Margin to deadline ms | Budget margin |
| --- | ---: | ---: | ---: |
| 0.7 | 16.961 | -0.272 | -1.63% |
| 1.0 | 16.661 | +0.028 | +0.17% |
| 1.4 | 16.261 | +0.428 | +2.56% |

This calculation assumes saved CPU work translates approximately into reduced
active wall/service time with comparable peripheral work. New intentional pacing
must be separated in the return rather than mistaken for lost savings. The
new observer's included cost and ordinary timing variation can consume the tiny
point-estimate margin; no calibration is subtracted to force a pass.

**Verdict:** borderline for bounded cast completion; do not predict a reliable
repeated-cast fix or comfortable headroom. A finite cast may complete because
reserve absorbs some slow calls, but the whole-effect reserve curve is needed
to predict that confidently. The 20% target needs 4.310 ms saving, leaving this
point forecast about **3.310 ms short** (even the optimistic band is 2.910 ms
short). The test should determine whether the weak assumptions are wrong and
which path supplies or consumes the difference.
