"""Plot physical prices and partial reserve; no calibration subtraction."""
from pathlib import Path
import csv
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
source = ROOT / 'evidence/2026-10-10/snes-a7-cost1-return'
analysis = json.loads((source / 'return-analysis.json').read_text())
model = analysis['scorecard']['conditional_warm_scenarios']['mean']
with (source / 'reserve-curve.csv').open() as f:
    reserve = list(csv.DictReader(f))
fig, axes = plt.subplots(2, 1, figsize=(10, 8), layout='constrained')
ax = axes[0]
labels = ['Warm setup credit', 'Extra row debit', 'Short helper debit', 'Net saving', 'Saving required']
values = [model['setup_credit_us'], -model['extra_row_debit_us'], -model['b_short_shadow_us'],
          model['S_with_short_shadow_us'], 1514.283]
bars = ax.barh(labels, values, color=['#26797b', '#a54a3c', '#a54a3c', '#a54a3c', '#505661'])
for bar, value in zip(bars, values):
    ax.text(value + (18 if value >= 0 else -18), bar.get_y() + bar.get_height()/2,
            f'{value:+.1f}', ha='left' if value >= 0 else 'right', va='center', fontsize=9)
ax.axvline(0, color='black', linewidth=.6)
ax.set(xlabel='Microseconds per call', xlim=(-340, 1710),
       title='Conditional warm model: measured parts do not earn the deadline')
ax.invert_yaxis()
ax.grid(axis='x', alpha=.2)
ax = axes[1]
for name in ('pass-00-mode-0', 'pass-04-mode-0', 'pass-08-mode-0'):
    rows = [r for r in reserve if r['capture'] == name and r['pointer_trusted'] == '1']
    ax.plot([float(r['elapsed_ms']) / 1000 for r in rows],
            [int(r['accepted_minus_hw']) for r in rows], linewidth=.8, label=name)
ax.axhline(864, color='#a54a3c', linestyle='--', linewidth=1, label='Provisional one-call + period margin')
ax.axhline(0, color='black', linewidth=.6)
ax.set(xlabel='Seconds since first RUNNING PCM observation', ylabel='Stereo frames',
       title='Controls: trusted reserve before pointer divergence; effect/recovery truncated')
ax.legend(fontsize=8, ncol=2)
ax.grid(alpha=.2)
target = ROOT / 'docs/assets/snes-a7-cost-return.png'
fig.savefig(target, dpi=150, bbox_inches='tight')
print(target)
