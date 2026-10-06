"""Archive and retire only the exact unconsumed intermediate 1.14 candidate."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import importlib.util, json

ROOT = Path(__file__).resolve().parent.parent
card = Path('D:/').resolve()
assert str(card).lower() in ('d:\\', 'd:/')
target = card / 'retro/snes-mvp'
expected = b'SNES-MVP-v1.14 A7 execution-budget one-shot\n'
assert (target / 'armed').read_bytes() == expected, 'Only the unconsumed intermediate candidate'
manifest = json.loads((ROOT / 'releases/snes-mvp-1.14/manifest.json').read_text(encoding='utf-8'))
for name, key in (('snes-mvp', 'binary_sha256'), ('launch.sh', 'wrapper_sha256'), ('plus-a7.so', 'core_sha256')):
    assert sha256((target / name).read_bytes()).hexdigest() == manifest[key]
assert not (card / 'retro/platform-lab/armed').exists()
spec = importlib.util.spec_from_file_location('collector', ROOT / 'build/collect-platform-lab.py')
collector = importlib.util.module_from_spec(spec); spec.loader.exec_module(collector)
archive = collector.collect(card)
assert (archive / 'snes-mvp/armed').read_bytes() == expected
assert (target / 'armed').read_bytes() == expected
(target / 'armed').unlink()
result = {'version': '1.14', 'retired_utc': datetime.now(timezone.utc).isoformat(),
          'reason': 'retain sampled phase records across long unsampled stretches before final test delivery',
          'unconsumed_marker_archived': True, 'physical_run': False,
          'payload_and_progress_unchanged': True, 'one_shot_armed': False}
(archive / 'retirement.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
