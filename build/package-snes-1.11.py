"""Guarded consumed 1.10 to 1.11 PCM observation/resume repair; unchanged core/progress."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import argparse, importlib.util, json, os, shutil

ROOT = Path(__file__).resolve().parent.parent

def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'build' / filename)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value

baseline = module('lab_baseline', 'install-platform-lab.py')
release = module('native_release', 'publish-snes-1.11.py')
collector = module('lab_collector', 'collect-platform-lab.py')
digest = release.digest

def atomic(path, raw, target):
    path = path.resolve(); target = target.resolve()
    assert path.is_relative_to(target), 'Owned folder only: ' + str(path)
    temporary = path.with_name(path.name + '.v111-tmp')
    assert not temporary.exists()
    try:
        with temporary.open('xb') as handle:
            handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        assert digest(temporary) == sha256(raw).hexdigest()
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)

def update(card):
    card = card.resolve(); assert str(card).lower() in ('d:\\', 'd:/'), 'Exact inspected D: only'
    target = card / 'retro/snes-mvp'; lab = card / 'retro/platform-lab'
    assert target.is_dir() and lab.is_dir()
    assert not (target / 'armed').exists() and not (lab / 'armed').exists(), 'Collect consumed test first'
    checks = release.qualified()
    old = json.loads((ROOT / 'releases/snes-mvp-1.10/manifest.json').read_text())
    assert digest(target / 'snes-mvp') == old['binary_sha256']
    assert digest(target / 'plus-a7.so') == old['core_sha256']
    assert digest(target / 'launch-game-1.8.sh') == baseline.WRAPPER
    assert digest(target / 'launch.sh') == old['wrapper_sha256']
    assert checks['core_sha256']==old['core_sha256'], 'This repair must retain the qualified core'
    for name in ('platform-lab', 'launch.sh', 'TEST-ME.txt', 'manifest.json'):
        assert digest(lab / name) == digest(ROOT / 'releases/platform-lab-2' / name), name
    assert digest(card / 'retro/init') == baseline.HOOK
    assert digest(target / 'init.stock') == '6d65bf756183f37c19a542703c8d50193d5c137e7d0d45be4ac980fcdcb8efbd'
    for name, wanted in baseline.EXPECTED.items(): assert digest(card / name) == wanted, name
    assert shutil.disk_usage(card).free > 8 * 1024 * 1024
    original = target / 'saves/game-a27f1c7a-3145728-core-5ba71d2a-656816.state'
    assert digest(original) == checks['qualified_snapshot_sha256']
    # Every returned log/private file is archived with source/copy/source hashes.
    returned = collector.collect(card)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    archive = ROOT / 'device-evidence' / ('snes-mvp-1.11-install-' + stamp)
    archive.mkdir()
    protected = {p.relative_to(card).as_posix(): digest(p) for folder in
                 ('retro/snes-mvp/saves', 'retro/saves', 'retro/states')
                 for p in (card / folder).rglob('*') if p.is_file()}
    retained = {p.relative_to(card).as_posix(): digest(p) for p in lab.rglob('*') if p.is_file()}
    retained['retro/snes-mvp/launch-game-1.8.sh'] = baseline.WRAPPER
    retained['retro/snes-mvp/init.stock'] = digest(target / 'init.stock')
    unchanged = {**baseline.EXPECTED, 'retro/init': baseline.HOOK, **protected, **retained}
    (archive / 'protected.json').write_text(json.dumps(unchanged, indent=2) + '\n')
    sources = {'snes-mvp': ROOT / 'build/snes-mvp/out/snes-mvp',
               'launch.sh': ROOT / 'build/snes-mvp/launch.sh',
               'TEST-ME.txt': ROOT / 'docs/snes-mvp-1.11-test.txt'}
    payload = {name: path.read_bytes() for name, path in sources.items()}
    before = {name: (target / name).read_bytes() for name in payload}
    changed = []; marker_created = False
    try:
        for name, raw in payload.items():
            atomic(target / name, raw, target); changed.append(name)
            assert (target / name).read_bytes() == raw
        for name, wanted in unchanged.items(): assert digest(card / name) == wanted, name
        assert not (lab / 'armed').exists()
        atomic(target / 'armed', b'SNES-MVP-v1.11 native PCM one-shot\n', target)
        marker_created = True
        assert (target / 'armed').read_bytes() == b'SNES-MVP-v1.11 native PCM one-shot\n'
    except BaseException:
        if marker_created: (target / 'armed').unlink(missing_ok=True)
        for name in reversed(changed): atomic(target / name, before[name], target)
        raise
    result = {'version': '1.11', 'installed_utc': datetime.now(timezone.utc).isoformat(),
        'one_shot_armed': True, 'lab_unarmed': True, 'archive_before_writes': returned.name,
        'stock_binaries_unchanged': True, 'boot_hook_unchanged': True,
        'original_private_files_unchanged': len(protected), 'retained_lab_files': len(retained) - 2,
        'original_game_wrapper_unchanged': True, 'new_save_point_sram_preserved': True,
        'snapshot_migration': 'unchanged qualified core; all existing snapshots retained',
        'binary_sha256': digest(target / 'snes-mvp'), 'wrapper_sha256': digest(target / 'launch.sh'),
        'core_sha256': digest(target / 'plus-a7.so'), 'hardware_result': 'pending'}
    (archive / 'installation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return archive

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--card', default='D:/')
    update(Path(parser.parse_args().card))
