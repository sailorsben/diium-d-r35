"""Independent source/trace arithmetic checks for the actual archived Focus1 budget."""
from pathlib import Path
from fractions import Fraction
from hashlib import sha256
import argparse
import importlib.util
import json
import math
import re
import tempfile

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive', type=Path)
archive = parser.parse_args().archive.resolve()
budget = json.loads((archive / 'effect-budget.json').read_text())
header = (ROOT / 'build/snes9x2005/source/snes9x.h').read_text()
apu = (ROOT / 'build/snes9x2005/source/apu_blargg.c').read_text()


def constant(text, name):
    return int(re.search(r'^#define\s+' + name + r'\s+\(?([0-9]+)', text, re.M)[1])


master = constant(header, 'SNES_CLOCK_SPEED') * 6
scanline_time = Fraction(re.search(r'^#define SNES_SCANLINE_TIME \(([^)]+)\)', header, re.M)[1])
scanline_clocks = int(scanline_time * master + Fraction(1, 2))
frame_clocks = scanline_clocks * constant(header, 'SNES_MAX_NTSC_VCOUNTER')
spc_ratio = Fraction(constant(apu, 'APU_NUMERATOR_NTSC'), constant(apu, 'APU_DENOMINATOR_NTSC'))
native = frame_clocks * spc_ratio / 32
cycles = budget['cycles']
assert cycles['master_clocks_per_call'] == frame_clocks == 358416
assert math.isclose(cycles['nominal_fps'], master / frame_clocks, rel_tol=1e-12)
assert math.isclose(cycles['expected_native_frames_per_call'], float(native), rel_tol=1e-12)
assert math.isclose(cycles['expected_sink_frames_per_call'], float(native * Fraction(44100, 32040)), rel_tol=1e-12)
trace = []
for line in (archive / 'snes-mvp/last-pcm-fault.txt').read_text().splitlines():
    if line.startswith('seq='):
        r = dict(p.split('=', 1) for p in line.split())
        if r['op'] == 'SYNC_OK':
            trace.append({k: int(v) for k, v in r.items() if k != 'op'})
stop = next(i for i, r in enumerate(trace) if r['appl'] != r['xfer'])
trusted = trace[:stop]
assert all(r['state'] == 3 and r['queued'] == r['xfer'] - r['hw'] for r in trusted)
# Independently compute every possible chronological reserve loss, rather than
# repeating the analyzer's rolling minimum implementation.
drawdown = max(a['queued'] - b['queued'] for i, a in enumerate(trusted) for b in trusted[i:])
assert drawdown == budget['reserve']['retained_trusted_peak_drawdown'] == 1407
assert max(trusted[0]['queued'] - r['queued'] for r in trusted) == budget['reserve']['retained_trusted_peak_prefix_deficit'] == 672
running = [r for r in trace if r['state'] == 3]
nominal = max(Fraction(44100 * (b['ns'] - a['ns']), 10**9) - (b['xfer'] - a['xfer'])
              for i, a in enumerate(running) for b in running[i:])
assert math.isclose(float(nominal), budget['reserve']['running_nominal_peak_drawdown'], abs_tol=1e-8)
assert not budget['reserve']['complete_effect_requirement_measured'] and not budget['reserve']['recovery_captured']
assert budget['window_candidate']['installation_gate'] == 'NOT MET'
assert budget['window_candidate']['expected_net_saving_us'] is None
session = archive / 'snes-mvp/saves/last-session.txt'
assert budget['source_sha256'] == sha256(session.read_bytes()).hexdigest()
spec = importlib.util.spec_from_file_location('check_focus_parser', ROOT / 'build/analyze-snes-focus.py')
analyzer = importlib.util.module_from_spec(spec); spec.loader.exec_module(analyzer)
with tempfile.TemporaryDirectory(dir=ROOT / 'build') as directory:
    malformed = Path(directory) / 'duplicate.txt'
    malformed.write_bytes(session.read_bytes() + b'focus_profile=1\n')
    try:
        analyzer.analyze(malformed)
    except AssertionError as error:
        assert 'Duplicate report field' in str(error)
    else:
        raise AssertionError('Duplicate fields accepted')
print('PASS: independent source-clock fractions, actual PCM peak-loss pairs, pointer trust boundary, missing-recovery and candidate-gate invariants, archived report hash and duplicate-field refusal')
