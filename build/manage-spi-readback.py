"""Guarded two-pass read-only SPI capture; all flash contents stay private."""
from pathlib import Path
from hashlib import sha256
import argparse, importlib.util, json, uuid, zlib
ROOT = Path(__file__).resolve().parent.parent
RELEASE = ROOT / 'releases/spi-readback-1'
CAPACITY = 8 * 1024 * 1024
HOOK = b'# D35 SPI readback: synchronous two-pass fixed read-only capture.\nif [ -f /usr/retro/spi-readback/armed ]; then\n  /bin/sh /usr/retro/spi-readback/launch.sh\nfi\n'


def module():
    spec = importlib.util.spec_from_file_location('identification_manager', ROOT / 'build/manage-spi-identify.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def baseline(card, identity, survey):
    archive = identity.baseline(card, survey)
    records = survey.archive_tree(card / 'retro/spi-readback', archive / 'spi-readback')
    (archive / 'readback-extra-collection.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    return archive


def analyze(base):
    errors = []
    installation = read(base / 'installation.json')
    marker = (base / 'consumed').exists() and not (base / 'armed').exists() and (base / 'consumed').read_text().strip() == installation['run_id']
    report = base / 'results/report.jsonl'
    if not report.exists():
        return {'complete': False, 'marker_matches': bool(marker), 'errors': ['No report; inspect marker/startup']}
    if report.stat().st_size > 1024 * 1024:
        return {'complete': False, 'marker_matches': bool(marker), 'errors': ['Report exceeds budget']}
    records = []
    for number, line in enumerate(report.read_text().splitlines(), 1):
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                errors.append('Invalid record shape on line ' + str(number))
            else:
                records.append(record)
        except json.JSONDecodeError:
            errors.append('Invalid JSON line ' + str(number))
    starts = [r for r in records if r.get('kind') == 'start']
    ends = [r for r in records if r.get('kind') == 'result']
    result = ends[-1] if ends else {}
    if len(starts) != 1 or starts[0].get('capacity_bytes') != CAPACITY or starts[0].get('passes') != 2 or starts[0].get('expected_jedec') != 'c84017':
        errors.append('Start contract differs')
    if len(ends) != 1 or result.get('errno') != 0 or result.get('stage') != 'readback-complete' or result.get('timed_out') is not False or result.get('reap_pending') is not False:
        errors.append('Readback did not finish successfully')
    if result.get('bytes') != [CAPACITY, CAPACITY] or result.get('capacity_bytes') != CAPACITY or result.get('block_bytes') != 4096 or result.get('operations') != 4111 or result.get('byte_compared') is not True:
        errors.append('Length, operation count or comparison differs')
    statuses = [result.get(k) for k in ['status_before', 'status_after']]
    if result.get('ids') != ['c84017c84017'] * 3 or any(not isinstance(s, int) or s & 1 for s in statuses):
        errors.append('Identity/status differs')
    if result.get('flash_writes') is not False or result.get('global_config_writes') is not False:
        errors.append('Read-only flags differ')
    startup = (base / 'startup.log').read_text(errors='replace') if (base / 'startup.log').exists() else ''
    if not marker or 'readback_exit=0\n' not in startup:
        errors.append('Marker identity or wrapper exit differs')
    bundle = base / 'results/captures.bin'
    hashes = []
    if not bundle.is_file() or bundle.stat().st_size != CAPACITY * 2:
        errors.append('Returned bundle length differs')
    else:
        data = bundle.read_bytes()
        first, second = data[:CAPACITY], data[CAPACITY:]
        crcs = [f'{zlib.crc32(p):08x}' for p in [first, second]]
        hashes = [sha256(p).hexdigest() for p in [first, second]]
        if crcs != result.get('crc32') or first != second:
            errors.append('Returned CRCs or full passes differ')
        if any(first == bytes([byte]) * CAPACITY for byte in [0, 0xff, 0xa5]):
            errors.append('Blank/floating/unchanged-sentinel image')
    return {'complete': not errors, 'marker_matches': bool(marker), 'errors': errors,
            'result': result, 'pass_sha256': hashes,
            'limits': 'Two matching 8-MiB SPI reads only; layout, boot-image ownership, writes and recovery are not qualified.'}


def install(card, identity, survey):
    base, target = card / 'retro/spi-readback', card / 'retro/init'
    assert not base.exists(), 'Fresh profile only; preserve prior results before any repeat'
    assert digest(target) == survey.INIT and digest(card / 'retro/showlogo') == survey.SPLASH
    assert digest(card / 'retro/vrtemu') == '8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
    for name in ['snes-mvp', 'platform-lab', 'device-survey', 'vesper-boot', 'vesper-boot-probe', 'spi-identify']:
        assert not (card / 'retro' / name / 'armed').exists(), name + ' armed'
    found = identity.analyze(card / 'retro/spi-identify')
    assert found['complete'] and found['result']['ids'] == ['c84017c84017'] * 3
    assert digest(card / 'retro/spi-identify/spi-identify') == 'c461aceae2706f58e9571d27744141605d7f7be63c88330fab6de16a5fefaaa6'
    qualified = read(RELEASE / 'manifest.json')
    assert qualified['software_checks_passed'] and qualified['physical_execution'] == 'pending'
    assert qualified['fixed_commands'] == ['05', '9f', '03'] and qualified['flash_writes'] is False and qualified['global_config_writes'] is False
    for name, h in qualified['source_hashes'].items():
        assert digest(ROOT / name) == h, name
    for name, h in qualified['release_hashes'].items():
        assert digest(RELEASE / name) == h, name
    health = survey.healthy()
    archive = baseline(card, identity, survey)
    (archive / 'chkdsk-prereadback.txt').write_text(health, encoding='utf-8')
    original = target.read_bytes()
    assert original.startswith(b'#!/bin/sh\n') and HOOK not in original
    candidate = b'#!/bin/sh\n' + HOOK + original[len(b'#!/bin/sh\n'):]
    assert candidate.replace(HOOK, b'', 1) == original
    (archive / 'init.before-readback').write_bytes(original)
    (archive / 'init.with-readback').write_bytes(candidate)
    receipt = {'version': 1, 'run_id': uuid.uuid4().hex, 'archive': archive.name,
        'init_before_sha256': survey.INIT, 'init_readback_sha256': sha256(candidate).hexdigest(),
        'binary_sha256': qualified['release_hashes']['spi-readback'], 'wrapper_sha256': qualified['release_hashes']['launch.sh'],
        'capacity_bytes': CAPACITY, 'passes': 2, 'hook': 'synchronous before stock main',
        'fixed_commands': ['05', '9f', '03'], 'flash_writes': False, 'global_config_writes': False,
        'physical_execution': 'pending'}
    base.mkdir()
    try:
        for name in ['spi-readback', 'launch.sh', 'manifest.json']:
            survey.write_new(base / name, (RELEASE / name).read_bytes())
        survey.write_new(base / 'init.before', original)
        survey.write_new(base / 'installation.json', (json.dumps(receipt, indent=2) + '\n').encode())
        survey.atomic_replace(target, candidate)
        survey.verify_protected(card, archive, receipt['init_readback_sha256'])
        survey.write_new(base / 'armed', (receipt['run_id'] + '\n').encode())
    except BaseException:
        if (base / 'armed').exists():
            (base / 'armed').unlink()
        if target.read_bytes() != original:
            survey.atomic_replace(target, original)
        raise
    (archive / 'readback-installation.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))
    return archive


def collect(card, identity, survey, restore=False):
    base = card / 'retro/spi-readback'
    assert base.is_dir()
    archive = baseline(card, identity, survey)
    result = analyze(archive / 'spi-readback')
    (archive / 'readback-analysis.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if restore:
        health = survey.healthy()
        (archive / 'chkdsk-prerestore.txt').write_text(health, encoding='utf-8')
        assert result['marker_matches'], 'Resolve consumed marker identity before restoration'
        installation = read(base / 'installation.json')
        assert digest(card / 'retro/init') == installation['init_readback_sha256']
        assert digest(base / 'init.before') == installation['init_before_sha256'] == survey.INIT
        survey.atomic_replace(card / 'retro/init', (base / 'init.before').read_bytes())
        survey.verify_protected(card, archive, survey.INIT)
        (archive / 'readback-restoration.json').write_text(json.dumps({'init_restored': True, 'init_sha256': survey.INIT}, indent=2) + '\n')
    print(json.dumps({'archive': archive.name, 'analysis': result, 'init_restored': restore}, indent=2))
    return archive


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['install', 'collect', 'restore'])
    p.add_argument('--card', type=Path, default=Path('D:/'))
    args = p.parse_args()
    card = args.card.resolve()
    assert str(card).lower() in ['d:\\', 'd:/']
    identity = module()
    survey = identity.module()
    if args.action == 'install':
        install(card, identity, survey)
    else:
        collect(card, identity, survey, args.action == 'restore')
