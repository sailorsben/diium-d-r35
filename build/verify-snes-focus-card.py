"""Independent read-only verification of the installed focus runner and preserved card."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import importlib.util
import json
import subprocess

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / 'device-evidence/snes-mvp-return-20261010T144407Z'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify():
    card = Path('D:/').resolve()
    assert str(card).lower() in ('d:/', 'd:\\')
    spec = importlib.util.spec_from_file_location('focus_baseline_verify', ROOT / 'build/package-snes-1.19.py')
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    q = json.loads((ROOT / 'build/snes-focus-out/verification.json').read_text())
    receipt = json.loads((ARCHIVE / 'focus-installation.json').read_text())
    assert q['passed'] and receipt['version'] == q['version'] == '1.19-focus1'
    for key, name in [('binary_sha256', 'snes-mvp'), ('core_sha256', 'plus-a7.so'),
                      ('wrapper_sha256', 'launch.sh')]:
        assert digest(card / 'retro/snes-mvp' / name) == q[key] == receipt[key]
    assert (card / 'retro/snes-mvp/TEST-ME.txt').read_bytes() == (ROOT / 'docs/snes-focus-1-test.txt').read_bytes()
    collection = json.loads((ARCHIVE / 'collection.json').read_text())
    lab = json.loads((ARCHIVE / 'lab-collection.json').read_text())
    protected = {}
    for entry in collection['copied_and_hash_verified']:
        assert digest(ARCHIVE / entry['archive_path']) == entry['sha256']
        if entry['card_path'] not in ('retro/snes-mvp/snes-mvp', 'retro/snes-mvp/TEST-ME.txt'):
            protected[entry['card_path']] = entry['sha256']
    protected.update({'retro/platform-lab/' + entry['relative_path']: entry['sha256'] for entry in lab['copied']})
    protected.update(baseline.BOOT_EXPECTED)
    prior = json.loads((ROOT / 'device-evidence/snes-mvp-1.19-install-20261010T064616Z/protected.json').read_text())
    readers = {name: value for name, value in prior.items() if name.startswith('retro/spi-readback')}
    assert len(readers) == 27
    protected.update(readers)
    for name, wanted in protected.items():
        assert digest(card / name) == wanted, name
    assert digest(card / 'retro/init') == baseline.baseline.HOOK
    assert sorted(path.relative_to(card).as_posix() for path in (card / 'retro').rglob('armed')) == ['retro/snes-mvp/armed']
    assert (card / 'retro/snes-mvp/armed').read_bytes() == b'SNES-focus-1 runner diagnostics; unchanged1.19 core one-shot\n'
    assert not (card / 'retro/update/Code.bkp').exists()
    health = subprocess.run(['chkdsk', 'D:'], capture_output=True, text=True)
    assert health.returncode == 0 and '11EB-1465' in health.stdout
    assert 'Windows has scanned the file system and found no problems.' in health.stdout
    (ARCHIVE / 'chkdsk-independent-focus.txt').write_text(health.stdout, encoding='utf-8')
    proof = {'passed': True, 'version': q['version'], 'verified_utc': datetime.now(timezone.utc).isoformat(),
             'card_writes': 0, 'archive_files_verified': len(collection['copied_and_hash_verified']),
             'unchanged_files_independently_verified': len(protected), 'spi_reader_files_verified': len(readers),
             'binary_sha256': q['binary_sha256'], 'core_sha256': q['core_sha256'],
             'wrapper_sha256': q['wrapper_sha256'], 'one_shot_armed': True,
             'lab_unarmed': True, 'firmware_trigger_absent': True, 'fat_clean': True,
             'private_progress_and_boot_preserved': True, 'physical_focus_result': 'pending'}
    (ARCHIVE / 'independent-focus-readback.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    verify()
