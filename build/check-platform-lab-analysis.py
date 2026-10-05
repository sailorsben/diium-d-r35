"""Hand-calculated counter fixtures: staging, query failures and cursor resets."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('analysis', Path(__file__).with_name('analyze-platform-lab.py'))
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

def sample(time, accepted, delay, free, ptr, delay_rc=0, space_rc=0, ptr_rc=0):
    return {k: str(v) for k, v in {
        'begin_ns': time, 'accepted_bytes': accepted, 'delay_bytes': delay,
        'free_bytes': free, 'ptr_bytes': ptr, 'delay_rc': delay_rc,
        'space_rc': space_rc, 'ptr_rc': ptr_rc}.items()}

samples = [sample(0, 0, 0, 16, 0), sample(10_000_000, 20, 16, -4, 4),
           sample(30_000_000, 20, 8, 4, 12), sample(40_000_000, 20, 0, 0, 0, -1, -1, -1)]
result = module.audio_observations(samples, 1000)
assert result['steady_delay_min_bytes'] == 8  # Startup and failed zero excluded.
assert result['steady_delay_min_ms_at_negotiated_rate'] == 2
assert result['negative_free_space_samples'] == 1  # Retained, never clamped.
assert result['sample_interval_mean_ms'] == 40 / 3
assert result['sample_interval_max_ms'] == 20
assert result['query_errors'] == {'delay': 1, 'space': 1, 'ptr': 1}
assert result['raw_pointer_delta_no_wrap_bytes'] == 12
assert not result['pointer_qualified_as_scheduling_clock']
samples.append(sample(50_000_000, 20, 4, 8, 3))  # Could be reset or a wrap.
result = module.audio_observations(samples, 1000)
assert result['pointer_backward_samples'] == 1
assert result['raw_pointer_delta_no_wrap_bytes'] is None
print('PASS: startup/error exclusion, negative space, sample intervals and unqualified cursor reset')
