"""Read-only live stock/ROM/probe checks against a completed private archive."""
from pathlib import Path
from hashlib import sha256
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to(ROOT / 'device-evidence')
    metadata = json.loads((archive / 'archive.json').read_text())
    assert metadata['fat_clean'] and metadata['card_writes'] == 0
    spec = importlib.util.spec_from_file_location('card_guard', ROOT / 'build/package-snes-1.19.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    card = Path('I:/').resolve()
    assert str(card).lower() in ('i:/', 'i:\\')
    assert not list((card / 'retro').rglob('armed'))
    assert not (card / 'retro/update/Code.bkp').exists()
    checks = {name: digest(card / name) == expected for name, expected in guard.BOOT_EXPECTED.items()}
    checks['retro/init'] = digest(card / 'retro/init') == guard.baseline.HOOK
    checks['FFVI_ROM'] = digest(card / '002/Final Fantasy VI.zip') == 'f61af2bd9e3f9b6a2bd543fb176af0b81fd9e5ba4ea0fa0f453371ccb45d3911'
    assert all(checks.values()), checks
    entries = [e for e in metadata['all_retro_files'] if e['path'].startswith('retro/uart-pair1/')]
    assert len(entries) == 8
    for entry in entries:
        assert digest(card / entry['path']) == digest(archive / entry['path']) == entry['sha256']
    result = {'read_only': True, 'card': 'I:', 'checks': checks,
              'probe_payload_and_logs_match_archive': True, 'probe_files_verified': len(entries),
              'one_shot_consumed': True, 'firmware_trigger_absent': True}
    (archive / 'live-protected-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
