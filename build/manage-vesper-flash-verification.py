"""Archived rearm of the unchanged read-only reader; compare installed Vesper bytes.

Never stages Code.bkp, invokes the vendor updater, or implements flash writes.
Old card reader profiles are retained by a guarded rename, not deleted.
"""
from pathlib import Path
from hashlib import sha256
import argparse, importlib.util, json, os, time, uuid

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = ROOT / 'device-evidence/snes-mvp-return-20261010T044231Z/expected-after-vendor.bin'
EXPECTED_SHA = 'd20301be923288e6ace49b43dd8cce306855ded8cd961643e5ee14854d9e6f03'


def manager():
    spec = importlib.util.spec_from_file_location('readback_manager', ROOT / 'build/manage-spi-readback.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def save(path, record):
    path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')


def expected_image():
    data = EXPECTED.read_bytes()
    assert len(data) == 8388608 and sha256(data).hexdigest() == EXPECTED_SHA
    return data


def move_owned(source, destination, parent):
    # Check final absolute targets before any directory move on Windows.
    source, destination, parent = source.resolve(), destination.resolve(), parent.resolve()
    assert source.parent == destination.parent == parent
    assert source.is_dir() and not source.is_symlink() and not destination.exists()
    assert source.name.startswith('spi-readback') and destination.name.startswith('spi-readback')
    os.rename(source, destination)


def arm(card, m, identity, survey):
    expected_image()
    base, target = card / 'retro/spi-readback', card / 'retro/init'
    assert not (card / 'retro/update/Code.bkp').exists(), 'Remove update trigger first'
    assert m.digest(target) == survey.INIT and m.digest(card / 'retro/showlogo') == survey.SPLASH
    assert m.digest(card / 'retro/vrtemu') == '8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
    for name in ['snes-mvp', 'platform-lab', 'device-survey', 'vesper-boot',
                 'vesper-boot-probe', 'spi-identify', 'spi-readback']:
        assert not (card / 'retro' / name / 'armed').exists(), name + ' armed'
    prior = m.analyze(base)
    assert prior['complete'] and prior['marker_matches'], 'Resolve prior reader return first'
    assert m.digest(base / 'init.before') == survey.INIT
    qualified = m.read(m.RELEASE / 'manifest.json')
    assert qualified['software_checks_passed'] and qualified['fixed_commands'] == ['05', '9f', '03']
    assert qualified['flash_writes'] is False and qualified['global_config_writes'] is False
    for path, expected in qualified['source_hashes'].items():
        assert m.digest(ROOT / path) == expected, path
    for path, expected in qualified['release_hashes'].items():
        assert m.digest(m.RELEASE / path) == expected, path
    # Preserve first; no card mutation until a fresh successful health gate.
    archive = m.baseline(card, identity, survey)
    (archive / 'chkdsk-preverification-rearm.txt').write_text(survey.healthy(), encoding='utf-8')
    entries = m.read(archive / 'readback-extra-collection.json')
    for entry in entries:
        assert m.digest(base / entry['path']) == entry['sha256']
    assert len(entries) == sum(p.is_file() for p in base.rglob('*'))
    original = target.read_bytes()
    patched = b'#!/bin/sh\n' + m.HOOK + original[len(b'#!/bin/sh\n'):]
    identifier = uuid.uuid4().hex
    parked = base.with_name('spi-readback.pre-vesper-' + identifier)
    receipt = {'version': 1, 'archive': archive.name,
               'retained_prior_profile': parked.relative_to(card).as_posix(),
               'expected_full_image_sha256': EXPECTED_SHA,
               'read_only_commands': ['05', '9f', '03'], 'flash_writes': False,
               'global_config_writes': False, 'status': 'preparing'}
    save(archive / 'vesper-verification-rearm.json', receipt)
    move_owned(base, parked, card / 'retro')
    try:
        for entry in entries:
            assert m.digest(parked / entry['path']) == entry['sha256']
        # The unchanged legacy collector names archives with second precision.
        time.sleep(1.05)
        installation_archive = m.install(card, identity, survey)
        for entry in entries:
            assert m.digest(parked / entry['path']) == entry['sha256']
        receipt.update({'status': 'armed', 'installation_archive': installation_archive.name,
                        'installation': m.read(base / 'installation.json')})
        save(archive / 'vesper-verification-rearm.json', receipt)
    except BaseException:
        # Restore only bytes and paths this operation owns; keep partial files.
        if target.read_bytes() == patched:
            survey.atomic_replace(target, original)
        assert target.read_bytes() == original, 'Unexpected init; preserve and inspect'
        if base.exists():
            if (base / 'armed').exists():
                install = m.read(base / 'installation.json')
                assert (base / 'armed').read_text().strip() == install['run_id']
                (base / 'armed').unlink()
            partial = base.with_name('spi-readback.incomplete-' + identifier)
            move_owned(base, partial, card / 'retro')
        move_owned(parked, base, card / 'retro')
        receipt['status'] = 'failed; normal init and prior profile restored; partial files retained'
        save(archive / 'vesper-verification-rearm.json', receipt)
        raise
    return receipt


def collect(card, m, identity, survey, restore):
    expected = expected_image()
    archive = m.collect(card, identity, survey, restore)
    analysis = m.read(archive / 'readback-analysis.json')
    result = {'version': 1, 'archive': archive.name, 'capture_complete': analysis['complete'],
              'expected_full_image_sha256': EXPECTED_SHA, 'full_image_matches': False,
              'normal_init_restored': restore, 'flash_writes': False}
    if analysis['complete']:
        raw = (archive / 'spi-readback/results/captures.bin').read_bytes()
        passes = [raw[:8388608], raw[8388608:]]
        result['pass_sha256'] = [sha256(data).hexdigest() for data in passes]
        result['both_passes_match_expected'] = [data == expected for data in passes]
        result['full_image_matches'] = all(result['both_passes_match_expected'])
        if not result['full_image_matches']:
            result['differing_64k_blocks'] = [[hex(i) for i in range(0, 8388608, 65536)
                                              if data[i:i+65536] != expected[i:i+65536]] for data in passes]
    save(archive / 'vesper-flash-verification.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['arm', 'collect', 'restore'])
    parser.add_argument('--card', type=Path, default=Path('D:/'))
    args = parser.parse_args()
    card = args.card.resolve()
    assert str(card).lower() in ('d:\\', 'd:/')
    m = manager()
    identity = m.module()
    survey = identity.module()
    result = arm(card, m, identity, survey) if args.action == 'arm' else collect(card, m, identity, survey, args.action == 'restore')
    print(json.dumps(result, indent=2))
