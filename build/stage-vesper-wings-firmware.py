"""Stage the qualified animation update on I:; device boot performs flashing.

Only the new Code.bkp trigger may change. All backups/vendor bytes stay private.
"""
from pathlib import Path
from hashlib import sha256
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent.parent
QUALIFIED = ROOT / 'device-evidence/vesper-wings-firmware-20261015'
BASELINE = '509cdc305deca2654fbf48184eb16d523b4b6cae0effffc4a3cba6845622d9fd'
PACKAGE = '2b78853155c087cfaf3dab730cabbb2dabc757982626da53ddb04cb9dc7bc389'


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'build' / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


inventory = load('manage-vesper-firmware.py').inventory


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def artifacts():
    q = json.loads((QUALIFIED / 'qualification.json').read_text())
    p = json.loads((QUALIFIED / 'preparation.json').read_text())
    assert q['all_checks_passed'] and len(q['checks']) == 12
    assert q['baseline_sha256'] == p['baseline_sha256'] == BASELINE
    assert q['package_sha256'] == p['package_sha256'] == PACKAGE
    assert q['ram_result_matches_vendor_mutated_candidate'] and q['ram_erase_blocks'] == 52
    assert q['ram_page_programs'] == 13312
    assert digest(QUALIFIED / 'preparation.json') == q['preparation_sha256']
    for name, expected in q['sources'].items():
        assert digest(ROOT / name) == expected, name
    for name, expected in p['files'].items():
        path = QUALIFIED / name
        assert path.name == name and path.stat().st_size == expected['bytes'] and digest(path) == expected['sha256']
    assert p['static_bitmap_preserved'] and p['all_other_cpio_bytes_exact']
    assert p['other_flash_bytes_exact_except_rootfs_and_length']
    return p, q, (QUALIFIED / 'fixture-compatible.bkp').read_bytes()


def guard(card):
    assert str(card.resolve()).lower() in ('i:/', 'i:\\'), 'Only the designated I: card'
    assert not list((card / 'retro').rglob('armed')), 'A competing test is armed'
    assert (card / 'retro/update').is_dir() and not (card / 'retro/update').is_symlink()
    assert not (card / 'retro/update/Code.bkp').exists(), 'An update is already staged'
    stock = load('package-snes-1.19.py')
    for name, expected in stock.BOOT_EXPECTED.items():
        assert digest(card / name) == expected, name
    assert digest(card / 'retro/init') == stock.baseline.HOOK
    assert digest(card / '002/Final Fantasy VI.zip') == 'f61af2bd9e3f9b6a2bd543fb176af0b81fd9e5ba4ea0fa0f453371ccb45d3911'
    verify_installed_capture(card / 'retro/spi-readback')


def verify_installed_capture(base):
    reader = load('manage-spi-readback.py')
    result = reader.analyze(base)
    assert result['complete'] and result['marker_matches']
    assert result['pass_sha256'] == [BASELINE, BASELINE], 'Latest verified installed firmware required'
    assert reader.read(base / 'installation.json')['run_id'] == 'db7079b5f61b4ee5b7d36d22e58472fd'


def healthy(card, archive, label):
    run = subprocess.run(['chkdsk', str(card)], capture_output=True, text=True)
    (archive / ('chkdsk-wings-' + label + '.txt')).write_text(run.stdout + run.stderr, encoding='utf-8')
    assert run.returncode == 0 and '11EB-1465' in run.stdout
    assert 'Windows has scanned the file system and found no problems.' in run.stdout


def write_new(path, data):
    with path.open('xb') as stream:
        assert stream.write(data) == len(data)
        stream.flush()
        os.fsync(stream.fileno())
    assert path.read_bytes() == data


def stage_payload(card, archive, package, before):
    """Small filesystem seam exercised separately against private fixture cards."""
    assert sha256(package).hexdigest() == PACKAGE
    destination = card / 'retro/update/Code.bkp'
    assert not destination.exists()
    temporary = destination.with_name('Code.wings-' + uuid.uuid4().hex + '.tmp')
    assert temporary.resolve().is_relative_to((card / 'retro/update').resolve())
    try:
        write_new(temporary, package)
        assert not destination.exists()
        os.rename(temporary, destination)
        assert digest(destination) == PACKAGE
        after = inventory(card)
        assert after.pop('retro/update/Code.bkp') == {'bytes': len(package), 'sha256': PACKAGE}
        assert after == before, 'Protected card files changed'
        healthy(card, archive, 'poststage')
        assert digest(destination) == PACKAGE
    except BaseException:
        # First establish filesystem health. Remove only exact owned bytes;
        # preserve an unknown/changed trigger for inspection.
        healthy(card, archive, 'before-rollback')
        for owned in [temporary, destination]:
            assert owned.resolve().is_relative_to((card / 'retro/update').resolve())
            if owned.exists() and digest(owned) == PACKAGE:
                owned.unlink()
        raise


def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to(ROOT / 'device-evidence')
    prior = json.loads((archive / 'archive.json').read_text())
    assert prior['fat_clean'] and prior['card_writes'] == 0
    p, q, package = artifacts()
    host_checks = json.loads((QUALIFIED / 'staging-checks.json').read_text())
    assert host_checks['all_checks_passed'] and len(host_checks['checks']) == 6
    for name, expected in host_checks['sources'].items():
        assert digest(ROOT / name) == expected, name
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
    assert not git('status', '--porcelain')
    assert git('branch', '--show-current') == 'codex/snes-mvp-foundation'
    commit = git('rev-parse', 'HEAD')
    assert commit == git('rev-parse', 'origin/codex/snes-mvp-foundation')
    card = Path('I:/').resolve()
    guard(card)
    for entry in prior['all_retro_files']:
        assert digest(card / entry['path']) == digest(archive / entry['path']) == entry['sha256']
    healthy(card, archive, 'prestage')
    before = inventory(card)
    assert shutil.disk_usage(card).free > len(package) + 512 * 1024 * 1024
    save(archive / 'card-before-wings.json', before)
    # Preserve non-retro private progress too; retro is already strictly archived.
    for name, entry in before.items():
        if name.startswith('retro/'):
            continue
        target = archive / 'outer-card' / name
        assert target.resolve().is_relative_to((archive / 'outer-card').resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(card / name, target)
        assert digest(target) == digest(card / name) == entry['sha256']
    for name in ['baseline-installed.bin', 'expected-after-vendor.bin', 'fixture-compatible.bkp']:
        write_new(archive / ('wings-' + name), (QUALIFIED / name).read_bytes())
    guard(card)
    assert inventory(card) == before
    stage_payload(card, archive, package, before)
    result = {'version': 'vesper-wings-2-firmware', 'archive': archive.name, 'source_commit': commit,
        'card': 'I:', 'status': 'staged-and-verified', 'package_sha256': PACKAGE, 'package_bytes': len(package),
        'baseline_sha256': BASELINE, 'candidate_sha256': p['candidate_sha256'],
        'expected_after_vendor_sha256': p['expected_after_vendor_sha256'],
        'protected_card_files': len(before), 'all_prior_files_unchanged': True, 'clean_FAT': True,
        'normal_init_preserved': True, 'first_static_screen': 'preserved', 'second_animation': 'Wings2 feather sweep',
        'only_new_card_path': 'retro/update/Code.bkp', 'armed_markers': 0, 'physical_update': 'PENDING',
        'external_recovery_qualified': False, 'qualification_sha256': digest(QUALIFIED / 'qualification.json')}
    save(archive / 'wings-staging.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
