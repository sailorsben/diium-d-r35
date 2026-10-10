"""Stage the exact privately qualified SD update; never implement a flash writer.

The human explicitly accepted proceeding without an external recovery device.
Only D:/retro/update/Code.bkp is changed. Normal init stays byte-identical.
Vendor-containing packages, backups, logs and inventories remain private.
"""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse, importlib.util, io, json, os, shutil, struct, uuid, zipfile, zlib

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT / 'device-evidence'
CAPTURE = PRIVATE / 'snes-mvp-return-20261010T003708Z/spi-readback'
QUALIFIED = CAPTURE / 'firmware-qualified-candidate'
BASELINE = '5c4ea86ca5c497a26136ee9a59d8a31085e15c8d1dc5f063b874a20c400d9e2b'
CANDIDATE = '246a46afa5cda655b47db787dff94e430bbf7f8a897b751cfca28ddc79f68ff7'
PACKAGE = '5263abf58bdfd161e90811e6cc0ecd233657ac8328a924185234c98af2ad8499'
VENDOR = '8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
INIT = 'b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
PROFILES = ['snes-mvp', 'platform-lab', 'device-survey', 'vesper-boot',
            'vesper-boot-probe', 'spi-identify', 'spi-readback']


def digest(path):
    h = sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'build' / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def artifacts():
    image = (CAPTURE / 'offline-review/spi-nor.bin').read_bytes()
    candidate = (QUALIFIED / 'spi-vesper-offline.bin').read_bytes()
    package = (QUALIFIED / 'fixture-compatible.bkp').read_bytes()
    assert len(image) == len(candidate) == 8388608
    assert sha256(image).hexdigest() == BASELINE
    assert sha256(candidate).hexdigest() == CANDIDATE
    assert len(package) == 5683533 and sha256(package).hexdigest() == PACKAGE
    assert package[:3] == b'WQW'
    with zipfile.ZipFile(io.BytesIO(package[3:])) as archive:
        members = archive.infolist()
        assert len(members) == 1 and members[0].filename == 'SPI_ROM.bin'
        assert members[0].date_time == (2026, 10, 9, 12, 0, 0)
        assert members[0].CRC == zlib.crc32(candidate) == 0xf2914d07
        assert archive.read(members[0]) == candidate
    report = json.loads((QUALIFIED / 'qualification.json').read_text())
    assert report['all_checks_passed'] and len(report['checks']) == 9
    assert all(item['passed'] for item in report['checks'])
    assert report['flash_baseline_sha256'] == BASELINE
    assert report['candidate_sha256'] == CANDIDATE and report['vendor_sha256'] == VENDOR
    for name, expected in report['source_sha256'].items():
        assert digest(ROOT / name) == expected, name
    assert report['updater_ram_dry_run']['all_simulated_flash_bytes_match_mutated_candidate']
    assert report['updater_ram_dry_run']['erase_blocks'] == 55
    assert report['updater_ram_dry_run']['page_programs'] == 14080
    expected = bytearray(candidate)
    struct.pack_into('<II', expected, 0x100, 0xf2914d07, 0x5d496000)
    return image, package, bytes(expected)


def card_guard(card):
    assert str(card.resolve()).lower() in ('d:\\', 'd:/'), 'Only the known D: card'
    assert digest(card / 'retro/init') == INIT, 'Inspect unexpected init; do not overwrite'
    assert digest(card / 'retro/vrtemu') == VENDOR, 'Updater identity differs'
    for name in PROFILES:
        assert not (card / 'retro' / name / 'armed').exists(), name + ' is armed'
    assert (card / 'retro/update').is_dir() and not (card / 'retro/update').is_symlink()


def inventory(card):
    entries = {}
    def failed(error):
        raise error
    for parent, folders, files in os.walk(card, onerror=failed):
        # Windows owns this directory; it is never a device runtime/progress path.
        if Path(parent) == card:
            folders[:] = [name for name in folders if name != 'System Volume Information']
        for name in files:
            path = Path(parent) / name
            assert not path.is_symlink(), path
            relative = path.relative_to(card).as_posix()
            entries[relative] = {'bytes': path.stat().st_size, 'sha256': digest(path)}
    return entries


def baseline(card):
    manager = load('manage-spi-readback.py')
    identity = manager.module()
    survey = identity.module()
    archive = manager.baseline(card, identity, survey)
    survey.archive_tree(card / 'retro/update', archive / 'firmware-update')
    survey.archive_tree(card / 'retro/display', archive / 'display')
    for source in (card / 'retro').iterdir():
        if source.is_file() and source.suffix in ('.log', '.err'):
            target = archive / 'root-logs' / source.name
            target.parent.mkdir(exist_ok=True)
            before = digest(source)
            shutil.copy2(source, target)
            assert before == digest(source) == digest(target)
    return archive, survey


def stage(card):
    image, package, expected = artifacts()
    card_guard(card)
    destination = card / 'retro/update/Code.bkp'
    assert not destination.exists(), 'An update is already staged; collect instead'
    # Preserve returned logs/private progress before the fresh health gate.
    archive, survey = baseline(card)
    health = survey.healthy()
    (archive / 'chkdsk-prestage.txt').write_text(health, encoding='utf-8')
    before = inventory(card)
    save(archive / 'card-before.json', before)
    survey.write_new(archive / 'baseline-spi-nor.bin', image)
    survey.write_new(archive / 'Code.bkp', package)
    survey.write_new(archive / 'expected-after-vendor.bin', expected)
    run_id = uuid.uuid4().hex
    receipt = {'version': 1, 'run_id': run_id, 'stage_utc': datetime.now(timezone.utc).isoformat(),
               'archive': archive.name, 'card_path': 'retro/update/Code.bkp',
               'package_sha256': PACKAGE, 'package_bytes': len(package),
               'baseline_sha256': BASELINE, 'candidate_sha256': CANDIDATE,
               'expected_after_vendor_sha256': sha256(expected).hexdigest(),
               'normal_init_sha256': INIT, 'vendor_sha256': VENDOR,
               'authorization': 'Proceed via SD now; obtain external programmer if boot fails.',
               'external_recovery_available': False, 'recovery_qualified': False,
               'physical_update': 'pending', 'physical_animation': 'pending',
               'first_static_screen': 'preserved', 'second_animation': 'Vesper replacement',
               'card_inventory_exclusions': ['System Volume Information'],
               'protected_card_files': len(before), 'status': 'preparing'}
    save(archive / 'firmware-staging.json', receipt)
    temporary = destination.with_name('Code.vesper-' + run_id + '.tmp')
    try:
        survey.write_new(temporary, package)
        card_guard(card)
        assert not destination.exists()
        os.rename(temporary, destination)
        assert digest(destination) == PACKAGE
        survey.verify_protected(card, archive, INIT)
        after = inventory(card)
        assert after.pop('retro/update/Code.bkp') == {'bytes': len(package), 'sha256': PACKAGE}
        assert after == before, 'Unrelated card file changed'
        (archive / 'chkdsk-poststage.txt').write_text(survey.healthy(), encoding='utf-8')
        receipt['status'] = 'staged-and-verified'
        save(archive / 'firmware-staging.json', receipt)
    except BaseException:
        # Exact owned paths only. Never remove a changed/unknown update image.
        for owned in [temporary, destination]:
            if owned.exists() and digest(owned) == PACKAGE:
                owned.unlink()
        receipt['status'] = 'staging-failed; inspect card and archive'
        save(archive / 'firmware-staging.json', receipt)
        raise
    return receipt


def collect(card, unstage=False):
    archive, survey = baseline(card)
    path = card / 'retro/update/Code.bkp'
    result = {'archive': archive.name, 'update_present': path.exists(), 'card_writes': 0,
              'physical_update': 'not established by SD logs; require full SPI readback',
              'update_sha256': digest(path) if path.exists() else None}
    if unstage and path.exists():
        assert result['update_sha256'] == PACKAGE, 'Preserve unexpected package before removal'
        (archive / 'chkdsk-preunstage.txt').write_text(survey.healthy(), encoding='utf-8')
        survey.verify_protected(card, archive, INIT)
        path.unlink()
        assert not path.exists()
        result['card_writes'] = 1
        (archive / 'chkdsk-postunstage.txt').write_text(survey.healthy(), encoding='utf-8')
    save(archive / 'firmware-return.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'stage', 'collect', 'unstage'])
    parser.add_argument('--card', type=Path, default=Path('D:/'))
    args = parser.parse_args()
    assert str(args.card.resolve()).lower() in ('d:\\', 'd:/'), 'Only the known D: card'
    if args.action == 'check':
        original, package, expected = artifacts()
        print(json.dumps({'artifacts_match_offline_qualification': True, 'package_sha256': PACKAGE,
                          'expected_after_vendor_sha256': sha256(expected).hexdigest(),
                          'device_access': False}, indent=2))
    else:
        print(json.dumps(stage(args.card) if args.action == 'stage'
                         else collect(args.card, args.action == 'unstage'), indent=2))
