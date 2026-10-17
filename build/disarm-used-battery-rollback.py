"""Remove only the archived, exact used firmware trigger; no flash or rearm."""
from pathlib import Path
import json, subprocess, sys
from attempt_archive import digest, verify_saved, PROGRESS

ROOT = Path(__file__).resolve().parent.parent
TRIGGER = 'retro/update/Code.bkp'
PACKAGE = '2b78853155c087cfaf3dab730cabbb2dabc757982626da53ddb04cb9dc7bc389'

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

def health(archive, label):
    r = subprocess.run(['chkdsk','I:'],capture_output=True,text=True)
    (archive/('chkdsk-battery-trace-'+label+'.txt')).write_text(r.stdout+r.stderr)
    assert r.returncode == 0 and '11EB-1465' in r.stdout
    assert 'Windows has scanned the file system and found no problems.' in r.stdout

def verify(card, expected):
    assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()} == set(expected)
    for name, h in expected.items():
        assert digest(card/name) == h, name
    assert not list((card/'retro').rglob('armed'))

def is_save(name):
    p = Path(name)
    base = p.name.lower()
    while base.endswith(('.bak','.bkp')):
        base = base.rsplit('.',1)[0]
    return Path(base).suffix in PROGRESS or bool({'saves','states','snapshots'} & {x.lower() for x in p.parts})

def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to((ROOT/'device-evidence').resolve())
    assert not git('status','--porcelain')
    commit = git('rev-parse','HEAD')
    assert commit == git('rev-parse','origin/codex/snes-mvp-foundation')
    a = json.loads((archive/'archive.json').read_text())
    o = json.loads((archive/'outside-retro.json').read_text())
    assert a['fat_clean'] and a['card_writes'] == 0
    verify_saved(archive,a)
    for entry in o['files']:
        if entry['stored']:
            assert digest(archive/entry['path']) == entry['sha256']
    entries = a['all_retro_files']+o['files']
    expected = {e['path']:e['sha256'] for e in entries}
    assert expected[TRIGGER] == PACKAGE
    host = ROOT/'device-evidence/vesper-wings-firmware-20261015/fixture-compatible.bkp'
    assert digest(host) == PACKAGE
    card = Path('I:/').resolve()
    assert str(card).lower() in ('i:/','i:\\')
    target = (card/TRIGGER).resolve()
    assert target == card/'retro/update/Code.bkp' and target.is_relative_to(card/'retro/update')
    health(archive,'before')
    verify(card,expected)
    target.unlink()  # Sole card mutation: exact, preserved used update trigger.
    del expected[TRIGGER]
    health(archive,'after')
    verify(card,expected)
    assert not list(card.rglob('Code.bkp'))
    report = {'source_commit':commit, 'archive':archive.name,
              'only_removed_path':TRIGGER, 'removed_package_sha256':PACKAGE,
              'host_package_verified':True, 'remaining_files_unchanged':len(expected),
              'progress_and_save_directory_files_preserved':sum(is_save(e['path']) for e in entries),
              'all_returned_evidence_preserved':True, 'UART_boot_files_unchanged':True,
              'ADC_config_and_stock_frontend_unchanged':True,
              'FAT_clean':True, 'no_update_trigger':True, 'no_test_armed':True,
              'no_flash':True, 'no_full_backup':True}
    text = json.dumps(report,indent=2)+'\n'
    (archive/'disarm-used-rollback.json').write_text(text)
    (ROOT/'evidence/2026-10-16/stock-battery-trace/card-preservation.json').write_text(text)
    print(text)

if __name__ == '__main__':
    main(Path(sys.argv[1]))
