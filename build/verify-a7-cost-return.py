"""Independent read-only return verification against the pre-install archive."""
from pathlib import Path
from hashlib import sha256
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
before = ROOT / 'device-evidence' / sys.argv[1]
returned = ROOT / 'device-evidence' / sys.argv[2]
card = Path('D:/')

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

proof = json.loads((before / 'cost-installation.json').read_text())
for name, wanted in proof['payload_hashes'].items():
    assert digest(card / 'retro/snes-cost1' / name) == wanted, name
    assert digest(returned / 'snes-cost1' / name) == wanted, name
assert digest(card / 'retro/snes-mvp/launch.sh') == proof['dispatch_sha256']
records = json.loads((before / 'collection.json').read_text())['copied_and_hash_verified']
protected = {r['card_path']: r['sha256'] for r in records
             if r['card_path'] != 'retro/snes-mvp/launch.sh'}
lab = json.loads((before / 'lab-collection.json').read_text())
protected.update({'retro/platform-lab/' + r['relative_path']: r['sha256'] for r in lab['copied']})
previous = json.loads((ROOT / 'device-evidence/snes-mvp-1.19-install-20261010T064616Z/protected.json').read_text())
protected.update({p: h for p, h in previous.items() if p.startswith('retro/spi-readback')})
spec = importlib.util.spec_from_file_location('cost_return_baseline', ROOT / 'build/package-snes-1.19.py')
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
protected.update(baseline.BOOT_EXPECTED)
assert len(protected) == proof['protected_hashes_verified']
for name, wanted in protected.items():
    assert digest(card / name) == wanted, name
assert not list((card / 'retro').rglob('armed'))
assert not (card / 'retro/update/Code.bkp').exists()
assert (card / 'retro/snes-cost1/last-launch').read_bytes() == (
    b'SNES-cost1 diagnostic measurement suite; baseline renderer only; no production candidate\n')
collection = json.loads((returned / 'cost-collection.json').read_text())
assert collection['clean_fat'] and collection['marker_consumed'] and collection['identity_verified']
result = {'passed': True, 'card_writes': 0, 'protected_hashes_verified': len(protected),
          'payloads_exact': True, 'production_runner_core_adapter_stock_progress_unchanged': True,
          'measurement_dispatch_exact': True, 'marker_consumed': True, 'all_tests_unarmed': True,
          'clean_fat': True, 'candidate_installed': False}
(returned / 'independent-cost-return.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
