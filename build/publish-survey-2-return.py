"""Publish curated survey2/ID-install evidence; preserve all historical manifest bytes."""
from pathlib import Path
from hashlib import sha256
import importlib.util
import json

ROOT = Path(__file__).resolve().parent.parent
BEFORE = ROOT / 'device-evidence/snes-mvp-return-20261009T182253Z'
RETURN = ROOT / 'device-evidence/snes-mvp-return-20261009T232801Z'
RESTORE = ROOT / 'device-evidence/snes-mvp-return-20261009T232840Z'
INSTALL = ROOT / 'device-evidence/snes-mvp-return-20261009T234340Z'
PREFIX = 'evidence/2026-10-09/device-survey-2-return/'
SPI_PREFIX = 'evidence/2026-10-09/spi-identify-install/'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def protected():
    before = read(BEFORE / 'collection.json')
    returned = read(RETURN / 'collection.json')
    assert returned['complete'] and not returned['read_errors'] and returned['card_writes'] == 0
    old = {e['card_path']: e for e in before['copied_and_hash_verified']}
    new = {e['card_path']: e for e in returned['copied_and_hash_verified']}
    assert old.keys() == new.keys() and len(old) == 51
    for name, e in new.items():
        assert digest(RETURN / e['archive_path']) == e['sha256']
        if name != 'retro/init':
            assert e['sha256'] == old[name]['sha256']
    assert new['retro/init']['sha256'] == 'bbc24d21c400044e2dd9bd979b53940db06f354980ddb324f893ba53ac4d3751'
    assert before['production_hashes'] == returned['production_hashes']
    old_lab = {e['relative_path']: e for e in read(BEFORE / 'lab-collection.json')['copied']}
    new_lab = {e['relative_path']: e for e in read(RETURN / 'lab-collection.json')['copied']}
    assert old_lab == new_lab and len(old_lab) == 49
    for name, e in new_lab.items():
        assert digest(RETURN / 'platform-lab' / name) == e['sha256']
    return {'mvp_progress_archive_files': 51, 'lab_files_unchanged': 49,
            'intended_exception': 'Installed survey init hook; exact original restored after health check',
            'production_hashes_unchanged': True, 'collection_card_writes': 0}


def publish():
    spec = importlib.util.spec_from_file_location('survey_analysis', ROOT / 'build/analyze-device-survey.py')
    analyzer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analyzer)
    base = RETURN / 'device-survey'
    result = analyzer.analyze(base)
    assert result['complete'] and len(result['captured']) == 905
    assert result['identity']['expected_run_id'] == '8fc1bcb371894ef0a4b7e75bdc52909d'
    assert not result['failed_captures'] and not result['parse_errors']
    records = [json.loads(line) for line in (base / 'results/report.jsonl').read_text().splitlines()]

    def captured(source):
        matches = [r for r in records if r.get('kind') == 'capture' and r['source'] == source]
        assert len(matches) == 1 and not matches[0]['errno']
        return analyzer.capture_bytes(base / 'results', matches[0])

    assert captured('/proc/521/comm').strip() == b'vrtemu'
    # Link targets and rdev come from metadata records rather than dereferencing devices.
    ownership = [r for r in records if r.get('source') in ['/proc/521/exe', '/proc/521/fd/8', '/dev/spidev0.0']]
    assert any(r.get('link') == '/usr/retro/vrtemu' for r in ownership), ownership
    assert any(r.get('link') == '/dev/spidev0.0' for r in ownership), ownership
    assert any(r.get('rdev') == 39168 for r in ownership), ownership
    model = captured('/sys/firmware/devicetree/base/model').rstrip(b'\0').decode()
    assert model == 'Generalplus EMU Board'
    restoration = read(RESTORE / 'survey-restoration.json')
    assert restoration == {'init_restored': True, 'init_sha256': 'b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'}
    assert 'found no problems' in (RETURN / 'chkdsk-survey-2-return.txt').read_text()
    assert 'found no problems' in (RESTORE / 'chkdsk-prerestore.txt').read_text()
    installation = read(INSTALL / 'spi-installation.json')
    verification = read(INSTALL / 'spi-verification.json')
    assert installation['run_id'] == '42401fa0056c4cfda90da165e2ad851f'
    assert installation['flash_writes'] is False and installation['global_config_writes'] is False
    assert verification['only_spi_identification_armed'] and verification['release_init_and_marker_readback']
    assert 'found no problems' in (INSTALL / 'chkdsk-postspi.txt').read_text()
    q = read(ROOT / 'releases/spi-identify-1/qualification.json')
    assert q['software_checks_passed'] and len(q['checks']) == 11
    summary = {k: result[k] for k in ['complete', 'version', 'identity', 'consumed', 'wrapper_exit', 'end', 'groups']}
    summary.update({'verified_capture_ranges': 905, 'failed_captures': 0,
        'protected': protected(), 'init_restoration': restoration, 'returned_fat_clean': True,
        'board_model': model, 'stock_spi_owner': {'pid': 521, 'comm': 'vrtemu',
            'exe': '/usr/retro/vrtemu', 'fd': 8, 'device': '/dev/spidev0.0', 'major': 153, 'minor': 0},
        'offline_elf_review_count': len(read(base / 'offline-review/index.json')['entries']),
        'vendor_execution': False, 'physical_spi_identification': 'pending',
        'shutdown_control': 'Physical power button; only device shutdown control, no launcher menu option',
        'limit': 'One intact survey return through the normal button; not general media/driver/shutdown qualification. No flash write, recovery, original splash replacement or audio fix.'})
    source = RETURN / 'public-analysis.json'
    source.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8', newline='\n')
    selected = {
        PREFIX + 'analysis.json': source,
        PREFIX + 'chkdsk-return.txt': RETURN / 'chkdsk-survey-2-return.txt',
        PREFIX + 'chkdsk-prerestore.txt': RESTORE / 'chkdsk-prerestore.txt',
        PREFIX + 'restoration.json': RESTORE / 'survey-restoration.json',
        SPI_PREFIX + 'installation.json': INSTALL / 'spi-installation.json',
        SPI_PREFIX + 'verification.json': INSTALL / 'spi-verification.json',
        SPI_PREFIX + 'chkdsk-postinstall.txt': INSTALL / 'chkdsk-postspi.txt',
    }
    manifest = ROOT / 'evidence/manifest.json'
    original = manifest.read_bytes()
    existing = json.loads(original)['entries']
    assert not any(e['published'].startswith((PREFIX, SPI_PREFIX)) for e in existing)
    for e in existing:
        assert digest(ROOT / e['published']) == e['published_sha256'], e['published']
    additions = []
    for published, path in selected.items():
        raw = path.read_bytes()
        normalized = raw.decode('utf-8-sig').replace('\r\r\n', '\n').replace('\r\n', '\n').replace('\r', '\n').encode()
        for bad in [b'Bearer ', b'github_pat_', b'ghp_', b'C:\\Users', b'.codex/attachments']:
            assert bad not in normalized
        target = ROOT / published
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(normalized)
        additions.append({'source': path.relative_to(ROOT).as_posix(), 'published': published,
            'source_sha256': sha256(raw).hexdigest(), 'published_sha256': digest(target),
            'bytes': len(normalized), 'normalized': raw != normalized})
    closing = b'\r\n  ]\r\n}\r\n'
    assert original.endswith(closing)
    encoded = b',\r\n'.join(('\r\n'.join('    ' + line for line in json.dumps(e, indent=2).splitlines())).encode() for e in additions)
    updated = original[:-len(closing)] + b',\r\n' + encoded + closing
    assert json.loads(updated)['entries'] == existing + additions
    manifest.write_bytes(updated)
    print(json.dumps({'published_files': len(additions), 'raw_vendor_or_private_files_published': False,
                      'verified_capture_ranges': 905}, indent=2))


if __name__ == '__main__':
    publish()
