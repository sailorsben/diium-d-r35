"""Independent read-only proof after installation; no arm/update operations."""
from pathlib import Path
from hashlib import sha256
import argparse, importlib.util, json, struct, zlib

ROOT = Path(__file__).resolve().parent.parent
def digest(path): return sha256(path.read_bytes()).hexdigest()

def verify(card, archive):
    card = card.resolve(); archive = archive.resolve()
    assert str(card).lower() in ('d:\\', 'd:/')
    assert archive.is_relative_to(ROOT / 'device-evidence')
    spec = importlib.util.spec_from_file_location('qualified_release', ROOT / 'build/publish-snes-1.14.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    checks = mod.qualified()
    installation = json.loads((archive / 'installation.json').read_text())
    for name, key in (('snes-mvp', 'binary_sha256'), ('launch.sh', 'wrapper_sha256'), ('plus-a7.so', 'core_sha256')):
        assert digest(card / 'retro/snes-mvp' / name) == checks[key] == installation[key]
    assert (card / 'retro/snes-mvp/TEST-ME.txt').read_bytes() == (ROOT / 'docs/snes-mvp-1.14-test.txt').read_bytes()
    protected = json.loads((archive / 'protected.json').read_text())
    for name, wanted in protected.items(): assert digest(card / name) == wanted, name
    returned = ROOT / 'device-evidence' / installation['archive_before_writes']
    assert returned.is_relative_to(ROOT / 'device-evidence')
    old = json.loads((returned / 'collection.json').read_text())
    changed = {'retro/snes-mvp/' + name for name in ('snes-mvp', 'launch.sh', 'TEST-ME.txt', 'plus-a7.so')}
    for entry in old['copied_and_hash_verified']:
        assert digest(returned / entry['archive_path']) == entry['sha256']
        if entry['card_path'] not in changed:
            assert digest(card / entry['card_path']) == entry['sha256'], entry['card_path']
    for entry in json.loads((returned / 'lab-collection.json').read_text())['copied']:
        assert digest(card / 'retro/platform-lab' / entry['relative_path']) == entry['sha256']
        assert digest(returned / 'platform-lab' / entry['relative_path']) == entry['sha256']
    original = card / 'retro/snes-mvp/saves/game-a27f1c7a-3145728-core-5ba71d2a-656816.state'
    assert digest(original) == checks['qualified_snapshot_sha256']
    state = card / 'retro/snes-mvp/saves' / f"game-a27f1c7a-3145728-core-{checks['core_crc32']}-{checks['core_bytes']}.state"
    expected = bytearray(original.read_bytes())
    struct.pack_into('<II', expected, 20, int(checks['core_crc32'], 16), checks['core_bytes'])
    assert state.read_bytes() == expected
    assert zlib.crc32(expected[40:]) & 0xffffffff == struct.unpack_from('<I', expected, 32)[0]
    assert (card / 'retro/snes-mvp/armed').read_bytes() == b'SNES-MVP-v1.14 A7 execution-budget one-shot\n'
    assert not (card / 'retro/platform-lab/armed').exists()
    result = {'passed': True, 'version': '1.14', 'card_writes': 0,
        'one_shot_armed': True, 'lab_unarmed': True,
        'payload_matches_qualified_build': True, 'original_private_files_unchanged': installation['original_private_files_unchanged'],
        'retained_lab_files_verified': installation['retained_lab_files'],
        'all_original_nonpayload_files_and_archives_verified': True,
        'stock_and_hook_unchanged': True, 'older_game_wrapper_unchanged': True,
        'separate_snapshot_payload_and_crc_verified': True,
        'hardware_audio_and_speed': 'pending physical qualification'}
    (archive / 'independent-readback.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--card', default='D:/')
    parser.add_argument('--archive', type=Path, required=True)
    args = parser.parse_args(); verify(Path(args.card), args.archive)
