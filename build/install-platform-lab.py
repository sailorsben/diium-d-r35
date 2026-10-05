"""Publish and optionally install lab1 on the exact unarmed MVP1.8 card."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import os
import shutil

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / 'build/platform-lab-out'
RELEASE = ROOT / 'releases/platform-lab-1'
RUNNER = '46c65c39f7a5a1ec354367dcf94e4af997c4c4f6783fa7393813393f4ba89a19'
WRAPPER = '339cc5c4131f66a97869b9ef933ca889d2552a8f8dce0c1b5c6e7429339a3351'
HOOK = 'b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
EXPECTED = {
    'retro/main': 'ace334d88d013240e2b93eb8cb691f1f09e4109d6d509648a5518cbae0b25873',
    'retro/vrtemu': '8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72',
    'retro/driver.so': '2c0134b3fc425f5b65c271c014e291824590c773190014f4e50c3ed33c2f13f9',
    'retro/showlogo': '436d8018808b150c926274575a195f664e61db646f44713371019e9ae10caf3b',
    'retro/libs/emu_sfc.so': '3a0ceb3cfde5148cecec0fb7cf5cf4c57229f9c6040626f79de3a520ae38c00e',
    'retro/libs/emu_sfc_plus.so': '1812b19b50270c625b43126253f687edc46bb9ba3cf0c4ccaaf3e2c29bef6657',
}

def digest(p): return sha256(p.read_bytes()).hexdigest()

def publish():
    checks = json.loads((BUILD / 'verification.json').read_text())
    assert checks['passed'] and not checks['hardware_qualified']
    assert checks['binary_sha256'] == digest(BUILD / 'platform-lab')
    assert all(digest(ROOT / p) == h for p, h in checks['source_hashes'].items()), 'Qualified source changed'
    payload = {'platform-lab': BUILD / 'platform-lab',
               'launch.sh': ROOT / 'build/launch-platform-lab.sh',
               'dispatch.sh': ROOT / 'build/dispatch-platform-lab.sh',
               'verification.json': BUILD / 'verification.json',
               'abi.txt': BUILD / 'abi.txt',
               'selftest.log': BUILD / 'selftest.log',
               'TEST-ME.txt': ROOT / 'docs/platform-lab-test.txt'}
    RELEASE.mkdir(exist_ok=True)
    # Never silently replace a published release with different bytes.
    for name, source in payload.items():
        target = RELEASE / name
        assert not target.exists() or digest(target) == digest(source), target
        shutil.copy2(source, target)
    manifest = {name: digest(RELEASE / name) for name in payload}
    (RELEASE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest

def install(card, arm):
    card = card.resolve()
    assert str(card).lower() in ('d:\\', 'd:/'), 'Exact inspected D: card only'
    mvp = card / 'retro/snes-mvp'; lab = card / 'retro/platform-lab'
    assert not lab.exists(), 'Archive and deliberately qualify an update; this is a first-install guard'
    assert not (mvp / 'armed').exists(), 'Collect the existing armed test first'
    assert digest(card / 'retro/init') == HOOK
    assert digest(mvp / 'snes-mvp') == RUNNER and digest(mvp / 'launch.sh') == WRAPPER
    for p, h in EXPECTED.items(): assert digest(card / p) == h, p
    assert shutil.disk_usage(card).free > 8 * 1024 * 1024
    spec = importlib.util.spec_from_file_location('card_collection', ROOT / 'build/collect-snes-mvp.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    archive = mod.collect(card)  # Logs and all private progress, before any writes.
    protected = {str(p.relative_to(card)).replace('\\', '/'): digest(p)
                 for folder in ('retro/snes-mvp/saves', 'retro/saves', 'retro/states')
                 for p in (card / folder).rglob('*') if p.is_file()}
    mvp_core = {str(p.relative_to(card)).replace('\\', '/'): digest(p)
                for p in mvp.glob('*.so')}
    saved_wrapper = mvp / 'launch-game-1.8.sh'
    assert not saved_wrapper.exists()
    (archive / 'lab-protected.json').write_text(json.dumps(protected, indent=2) + '\n')
    lab.mkdir(); (lab / 'results').mkdir()
    shutil.copy2(mvp / 'launch.sh', saved_wrapper)
    try:
        for name in ('platform-lab', 'launch.sh', 'TEST-ME.txt', 'manifest.json'):
            shutil.copy2(RELEASE / name, lab / name)
            assert digest(lab / name) == digest(RELEASE / name)
        # This file is invoked with /bin/sh; the original wrapper is byte exact.
        staged = mvp / 'launch.sh.lab-tmp'
        shutil.copy2(RELEASE / 'dispatch.sh', staged)
        os.replace(staged, mvp / 'launch.sh')
        assert digest(saved_wrapper) == WRAPPER
        assert digest(mvp / 'snes-mvp') == RUNNER
        assert digest(card / 'retro/init') == HOOK
        for p, h in {**EXPECTED, **protected, **mvp_core}.items(): assert digest(card / p) == h, p
        if arm:
            marker = lab / 'armed.tmp'; marker.write_text('platform-lab-1 one shot\n', newline='\n')
            os.replace(marker, lab / 'armed')
            marker = mvp / 'armed.lab-tmp'; marker.write_text('dispatch platform-lab-1 only\n', newline='\n')
            os.replace(marker, mvp / 'armed')  # Qualified boot hook's entry gate, last.
    except BaseException:
        (lab / 'armed').unlink(missing_ok=True); (mvp / 'armed').unlink(missing_ok=True)
        shutil.copy2(saved_wrapper, mvp / 'launch.sh')
        raise
    result = {'version': 'lab1', 'installed_utc': datetime.now(timezone.utc).isoformat(),
              'archive': str(archive), 'armed': arm, 'protected_private_count': len(protected),
              'stock_and_private_unchanged': True, 'hook_unchanged': True,
              'game_runner_and_core_unchanged': True, 'original_wrapper_sha256': digest(saved_wrapper),
              'lab_sha256': digest(lab / 'platform-lab')}
    (archive / 'lab-installation.json').write_text(json.dumps(result, indent=2) + '\n')
    (BUILD / 'installation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--arm', action='store_true')
    parser.add_argument('--card', default='D:/')
    args = parser.parse_args()
    assert not args.arm or args.install
    manifest = publish()
    print(json.dumps(install(Path(args.card), args.arm) if args.install else manifest, indent=2))
