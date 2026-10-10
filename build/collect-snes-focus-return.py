"""Strict read-only Focus1 return archival. All writes target the local checkout."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import importlib.util
import json
import struct
import subprocess
import zlib

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / 'device-evidence/snes-mvp-return-20261010T144407Z'


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'build' / file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def collect():
    card = Path('D:/').resolve()
    assert str(card).lower() in ('d:/', 'd:\\')
    health = subprocess.run(['chkdsk.exe', 'D:'], capture_output=True, text=True)
    # Preserve a failed check locally too; never repair or write the card.
    (ROOT / 'build/focus-return-health-private.txt').write_text(health.stdout + health.stderr, encoding='utf-8')
    assert health.returncode == 0 and '11EB-1465' in health.stdout
    assert 'Windows has scanned the file system and found no problems.' in health.stdout
    expected = json.loads((ROOT / 'releases/snes-focus-1/manifest.json').read_text())
    mvp = card / 'retro/snes-mvp'
    identities = {}
    for name, key in [('snes-mvp', 'binary_sha256'), ('plus-a7.so', 'core_sha256'), ('launch.sh', 'wrapper_sha256')]:
        identities[key] = digest(mvp / name)
        assert identities[key] == expected[key], name
    assert not list((card / 'retro').rglob('armed'))
    assert not (card / 'retro/update/Code.bkp').exists()
    assert (mvp / 'last-launch').read_bytes() == b'SNES-focus-1 runner diagnostics; unchanged1.19 core one-shot\n'
    archive = module('focus_return_collector', 'collect-platform-lab.py').collect(card)
    (archive / 'chkdsk-return.txt').write_text(health.stdout + health.stderr, encoding='utf-8')
    collection = json.loads((archive / 'collection.json').read_text())
    lab = json.loads((archive / 'lab-collection.json').read_text())
    old = json.loads((BASELINE / 'collection.json').read_text())
    old_lab = json.loads((BASELINE / 'lab-collection.json').read_text())
    assert collection['complete'] and not collection['read_errors'] and not collection['armed_present']
    assert collection['production_hashes'] == old['production_hashes']
    assert lab['copied'] == old_lab['copied'] and not lab['lab_armed']
    new = {e['card_path']: e for e in collection['copied_and_hash_verified']}
    prior = {e['card_path']: e for e in old['copied_and_hash_verified']}
    assert set(prior) <= set(new), 'Prior file missing'
    for entry in new.values():
        assert digest(archive / entry['archive_path']) == digest(card / entry['card_path']) == entry['sha256']
    for entry in lab['copied']:
        assert digest(archive / 'platform-lab' / entry['relative_path']) == digest(card / 'retro/platform-lab' / entry['relative_path']) == entry['sha256']
    progress = [n for n in prior if n.endswith(('.srm', '.srm.bak', '.state', '.state.bak'))]
    changes = [n for n in progress if prior[n]['sha256'] != new[n]['sha256']]
    states = [n for n in progress if n.endswith(('.state', '.state.bak'))]
    for name in states:
        raw = (archive / new[name]['archive_path']).read_bytes()
        assert raw[:8] == b'D35MVP01' and len(raw) == struct.unpack_from('<I', raw, 28)[0] + 40
        assert zlib.crc32(raw[40:]) & 0xffffffff == struct.unpack_from('<I', raw, 32)[0]
    baseline = module('focus_return_baseline', 'package-snes-1.19.py')
    protected = dict(baseline.BOOT_EXPECTED)
    previous = json.loads((ROOT / 'device-evidence/snes-mvp-1.19-install-20261010T064616Z/protected.json').read_text())
    readers = {n: h for n, h in previous.items() if n.startswith('retro/spi-readback')}
    assert len(readers) == 27
    protected.update(readers)
    for name, wanted in protected.items():
        assert digest(card / name) == wanted, name
    assert digest(card / 'retro/init') == baseline.baseline.HOOK == new['retro/init']['sha256']
    proof = dict(passed=True, version='1.19-focus1', verified_utc=datetime.now(timezone.utc).isoformat(),
                 archive=archive.name, card_writes=0, fat_clean=True, one_shot_consumed=True,
                 all_markers_absent=True, firmware_update_trigger_absent=True,
                 mvp_progress_files_verified=len(new), lab_files_verified=len(lab['copied']),
                 prior_files_retained=len(prior), progress_files_verified=len(progress),
                 owned_snapshot_crc_verified=len(states), changed_progress_files=changes,
                 stock_vesper_init_and_27_reader_files_verified=True, **identities)
    (archive / 'independent-readback.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(proof, indent=2))
    return archive


if __name__ == '__main__':
    collect()
