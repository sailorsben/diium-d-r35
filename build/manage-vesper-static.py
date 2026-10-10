"""Guarded SD staging/return for the exact first-splash Vesper package.

Reuses established card/archive/health and read-only verification helpers.
Never implements or directly invokes a flash writer. Normal SD init stays exact.
"""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse, importlib.util, io, json, os, struct, uuid, zipfile, zlib

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / 'device-evidence'
QUALIFIED = PRIVATE / 'vesper-static-qualified-20261010'
BASELINE = 'd20301be923288e6ace49b43dd8cce306855ded8cd961643e5ee14854d9e6f03'
CANDIDATE = '9f99ec3984f19b38d216cef2cad38eacb2bad9792046900d8fa91262a6e772b9'
EXPECTED = '509cdc305deca2654fbf48184eb16d523b4b6cae0effffc4a3cba6845622d9fd'
PACKAGE = '0012b1016df784ff92d92691d1740b3215bfda005a58b6382aaabffaf5c18b4c'


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'build' / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


old = load('manage-vesper-firmware.py')
digest, save, inventory = old.digest, old.save, old.inventory


def artifacts():
    baseline = (QUALIFIED / 'baseline-installed.bin').read_bytes()
    candidate = (QUALIFIED / 'spi-vesper-static.bin').read_bytes()
    expected = (QUALIFIED / 'expected-after-vendor.bin').read_bytes()
    package = (QUALIFIED / 'fixture-compatible.bkp').read_bytes()
    for data, h in [(baseline, BASELINE), (candidate, CANDIDATE), (expected, EXPECTED), (package, PACKAGE)]:
        assert sha256(data).hexdigest() == h
    assert len(baseline) == len(candidate) == len(expected) == 8388608 and len(package) == 5713655
    assert candidate[:0x8854] == baseline[:0x8854]
    assert candidate[0x9e854:] == baseline[0x9e854:]
    assert expected[:0x100] == candidate[:0x100] and expected[0x108:] == candidate[0x108:]
    assert struct.unpack_from('<II', expected, 0x100) == (0x17e40b24, 0x5d4a6000)
    with zipfile.ZipFile(io.BytesIO(package[3:])) as z:
        assert package[:3] == b'WQW' and z.namelist() == ['SPI_ROM.bin']
        member = z.infolist()[0]
        assert member.date_time == (2026, 10, 10, 12, 0, 0)
        assert member.CRC == zlib.crc32(candidate) == 0x17e40b24 and z.read(member) == candidate
    qualification = json.loads((QUALIFIED / 'qualification.json').read_text())
    assert qualification['all_checks_passed'] and len(qualification['checks']) == 10
    assert all(c['passed'] for c in qualification['checks'])
    assert qualification['baseline_sha256'] == BASELINE and qualification['candidate_sha256'] == CANDIDATE
    assert qualification['expected_after_vendor_sha256'] == EXPECTED and qualification['package_sha256'] == PACKAGE
    assert qualification['vendor_sha256'] == old.VENDOR
    assert qualification['ram_erase_blocks'] == 10 and qualification['ram_page_programs'] == 2560
    assert qualification['ram_result_matches_vendor_mutated_candidate']
    for name, h in qualification['source_sha256'].items():
        assert digest(ROOT / name) == h, name
    return baseline, package, expected


def card_guard(card):
    old.card_guard(card)
    reader = load('manage-spi-readback.py')
    result = reader.analyze(card / 'retro/spi-readback')
    assert result['complete'] and result['marker_matches']
    assert result['pass_sha256'] == [BASELINE, BASELINE], 'Use the latest verified installed baseline'
    assert reader.read(card / 'retro/spi-readback/installation.json')['run_id'] == 'c4a59205933b4459a9d88ed6aafe5dd2'


def baseline(card):
    archive, survey = old.baseline(card)
    parked = {}
    for path in sorted((card / 'retro').glob('spi-readback.pre-vesper-*')):
        assert path.is_dir() and not path.is_symlink()
        parked[path.name] = survey.archive_tree(path, archive / 'retained-reader-profiles' / path.name)
    save(archive / 'retained-reader-collection.json', parked)
    return archive, survey


def stage(card):
    image, package, expected = artifacts()
    card_guard(card)
    destination = card / 'retro/update/Code.bkp'
    assert not destination.exists(), 'Update already staged; collect instead'
    archive, survey = baseline(card)
    (archive / 'chkdsk-prestage.txt').write_text(survey.healthy(), encoding='utf-8')
    before = inventory(card)
    save(archive / 'card-before.json', before)
    survey.write_new(archive / 'baseline-installed-spi.bin', image)
    survey.write_new(archive / 'Code.bkp', package)
    survey.write_new(archive / 'expected-after-vendor.bin', expected)
    receipt = {'version': 1, 'run_id': uuid.uuid4().hex, 'stage_utc': datetime.now(timezone.utc).isoformat(),
               'archive': archive.name, 'card_path': 'retro/update/Code.bkp',
               'package_sha256': PACKAGE, 'package_bytes': len(package), 'baseline_sha256': BASELINE,
               'candidate_sha256': CANDIDATE, 'expected_after_vendor_sha256': EXPECTED,
               'normal_init_sha256': old.INIT, 'vendor_sha256': old.VENDOR,
               'protected_card_files': len(before), 'card_inventory_exclusions': ['System Volume Information'],
               'first_static_screen': 'Vesper replacement', 'second_animation': 'verified Vesper preserved',
               'authorization': 'User requests replacing first static screen via established SD update path; prior no-programmer risk acceptance retained.',
               'external_recovery_available': False, 'recovery_qualified': False,
               'physical_update': 'pending', 'physical_animation': 'pending', 'status': 'preparing'}
    save(archive / 'static-staging.json', receipt)
    temporary = destination.with_name('Code.vesper-static-' + receipt['run_id'] + '.tmp')
    try:
        survey.write_new(temporary, package)
        card_guard(card)
        assert not destination.exists()
        os.rename(temporary, destination)
        assert digest(destination) == PACKAGE
        survey.verify_protected(card, archive, old.INIT)
        after = inventory(card)
        assert after.pop('retro/update/Code.bkp') == {'bytes': len(package), 'sha256': PACKAGE}
        assert after == before, 'Unrelated card bytes changed'
        (archive / 'chkdsk-poststage.txt').write_text(survey.healthy(), encoding='utf-8')
        receipt['status'] = 'staged-and-verified'
        save(archive / 'static-staging.json', receipt)
    except BaseException:
        for owned in [temporary, destination]:
            if owned.exists() and digest(owned) == PACKAGE:
                owned.unlink()
        receipt['status'] = 'staging-failed; inspect archive/card'
        save(archive / 'static-staging.json', receipt)
        raise
    return receipt


def collect(card, unstage=False):
    assert str(card.resolve()).lower() in ('d:\\', 'd:/')
    archive, survey = baseline(card)
    path = card / 'retro/update/Code.bkp'
    result = {'archive': archive.name, 'update_present': path.exists(), 'card_writes': 0,
              'update_sha256': digest(path) if path.exists() else None,
              'physical_update': 'Require physical startup report and subsequent full SPI comparison'}
    if unstage and path.exists():
        assert result['update_sha256'] == PACKAGE, 'Preserve unexpected update image'
        (archive / 'chkdsk-preunstage.txt').write_text(survey.healthy(), encoding='utf-8')
        survey.verify_protected(card, archive, old.INIT)
        path.unlink()
        assert not path.exists()
        result['card_writes'] = 1
        (archive / 'chkdsk-postunstage.txt').write_text(survey.healthy(), encoding='utf-8')
    save(archive / 'static-return.json', result)
    return result


def verify(card, action):
    # Keep original scripts/qualification unchanged; bind this new run to only
    # the new expected first-splash image, including vendor CRC/time mutations.
    artifacts()
    v = load('manage-vesper-flash-verification.py')
    v.EXPECTED = QUALIFIED / 'expected-after-vendor.bin'
    v.EXPECTED_SHA = EXPECTED
    m = v.manager()
    identity = m.module()
    survey = identity.module()
    if action == 'verify-arm':
        return v.arm(card, m, identity, survey)
    return v.collect(card, m, identity, survey, action == 'verify-restore')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['check', 'stage', 'collect', 'unstage', 'verify-arm', 'verify-collect', 'verify-restore'])
    p.add_argument('--card', type=Path, default=Path('D:/'))
    args = p.parse_args()
    card = args.card.resolve()
    assert str(card).lower() in ('d:\\', 'd:/')
    if args.action == 'check':
        artifacts()
        result = {'qualified_package_sha256': PACKAGE, 'expected_after_vendor_sha256': EXPECTED, 'device_access': False}
    elif args.action == 'stage':
        result = stage(card)
    elif args.action.startswith('verify-'):
        result = verify(card, args.action)
    else:
        result = collect(card, args.action == 'unstage')
    print(json.dumps(result, indent=2))
