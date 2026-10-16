"""Independent read-only card readback after the explicit pressure-lab install."""
from pathlib import Path
from hashlib import sha256
import json, sys

ROOT = Path(__file__).resolve().parent.parent

def digest(path):
    with path.open('rb') as stream:
        h = sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to(ROOT / 'device-evidence')
    baseline = json.loads((archive / 'archive.json').read_text())
    receipt = json.loads((archive / 'render-pressure-installation.json').read_text())
    assert baseline['fat_clean'] and receipt['one_shot_armed'] and receipt['clean_FAT']
    card = Path('I:/')
    protected = [e for e in baseline['all_retro_files'] if e['path'] != 'retro/snes-mvp/launch.sh']
    for entry in protected:
        assert digest(card / entry['path']) == entry['sha256'], entry['path']
    for name, expected in receipt['payload_hashes'].items():
        assert digest(card / 'retro/render-pressure3' / name) == expected, name
    assert digest(card / 'retro/snes-mvp/launch.sh') == receipt['dispatch_sha256']
    markers = sorted(p.relative_to(card).as_posix() for p in (card / 'retro').rglob('armed'))
    assert markers == ['retro/render-pressure3/armed', 'retro/snes-mvp/armed']
    for name in markers:
        assert (card / name).read_bytes() == b'Render pressure3 ROM-free77-phase device lab\n'
        assert digest(card / name) == receipt['marker_sha256']
    rom_hash = digest(card / '002/Final Fantasy VI.zip')
    assert rom_hash == 'f61af2bd9e3f9b6a2bd543fb176af0b81fd9e5ba4ea0fa0f453371ccb45d3911'
    assert not (card / 'retro/update/Code.bkp').exists()
    assert not (card / 'retro/uart-fix1/disabled').exists()
    fat_reports = {}
    for label in ['before', 'payload', 'armed']:
        path = archive / ('chkdsk-uart-fix-pressure-' + label + '.txt')
        report = path.read_text()
        assert '11EB-1465' in report and 'Windows has scanned the file system and found no problems.' in report
        fat_reports[label] = digest(path)
    result = dict(version='render-pressure3', archive=archive.name,
                  installation_sha256=digest(archive / 'render-pressure-installation.json'),
                  archive_sha256=digest(archive / 'archive.json'),
                  source_sha256=digest(Path(__file__).resolve()),
                  protected_prior_files=len(protected), all_protected_exact=True,
                  payloads_exact=True, markers=markers, marker_bytes_exact=True,
                  ROM_sha256=rom_hash, UART_fix_preserved=True,
                  flash_update_absent=True, clean_FAT_reports=fat_reports,
                  card_writes=0, physical_result='PENDING')
    (archive / 'render-pressure-live-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main(Path(sys.argv[1]))
