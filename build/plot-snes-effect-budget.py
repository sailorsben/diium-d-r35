"""Plot published Focus1 measurements; no device access or inferred recovery."""
from pathlib import Path
import csv
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / 'evidence/2026-10-10/snes-focus-1-return'
budget = json.loads((EVIDENCE / 'effect-budget.json').read_text())
focus = json.loads((EVIDENCE / 'focus-analysis.json').read_text())
with (EVIDENCE / 'reserve-curve.csv').open() as stream:
    curve = list(csv.DictReader(stream))
fig, axes = plt.subplots(2, 1, figsize=(10, 7.5), layout='constrained')
ax = axes[0]
for sampled, marker, label in [(0, '.', 'Ordinary successful call'), (1, 'D', 'Profiled call (overhead included)')]:
    rows = [r for r in focus['frames'] if r['sampled'] == sampled and r['run'] < focus['runs']]
    ax.scatter([r['run'] for r in rows], [r['wall_ns'] / 1e6 for r in rows], marker=marker, label=label)
ax.axhline(budget['cycles']['native_budget_ms'], color='black', linestyle='--', linewidth=1, label='Core-model frame budget: 16.688 ms')
samples = budget['sampled_frames']
ax.plot([r['run'] for r in samples], [r['ppu_cpu_ns'] / 1e6 for r in samples], '-o', label='Sampled PPU CPU')
ax.plot([r['run'] for r in samples], [r['apu_inclusive_cpu_ns'] / 1e6 for r in samples], '-o', label='Sampled APU-inclusive CPU')
ax.set(xlabel='Core call number (effect onset is not marked)', ylabel='Milliseconds', title='Retained rising cost; terminal fault-handling call excluded')
ax.legend(fontsize=8, ncol=2)
ax.grid(alpha=.2)
ax = axes[1]
trusted = [r for r in curve if r['reserve_trusted'] == 'True']
running = [r for r in curve if r['state'] == '3']
ax.step([float(r['elapsed_ms']) for r in trusted], [float(r['accepted_minus_hw']) for r in trusted], where='post', label='Accepted minus reported hardware (before divergence)')
ax.plot([float(r['elapsed_ms']) for r in running], [float(r['nominal_deficit']) for r in running], label='44.1 kHz elapsed-time demand minus accepted writes')
first_divergence_seq = budget['pcm']['application_pointer_difference_changes'][0]['seq']
divergence_ms = float(next(r['elapsed_ms'] for r in curve if int(r['seq']) == first_divergence_seq))
ax.axvline(divergence_ms, color='firebrick', linestyle='--', label='First unexplained application-pointer increment')
ax.axhline(0, color='black', linewidth=.7)
ax.set(xlabel='Milliseconds since first retained PCM observation', ylabel='Stereo audio frames', title='Partial PCM window: onset and recovery absent; connecting lines are visual guides')
ax.legend(fontsize=8)
ax.grid(alpha=.2)
target = ROOT / 'docs/assets/snes-focus-1-budget.png'
fig.savefig(target, dpi=160)
print(target)
