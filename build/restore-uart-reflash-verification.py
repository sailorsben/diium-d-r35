"""Restore only exact normal init after this reflash's accepted physical return."""
from pathlib import Path
import importlib.util, json, sys
from attempt_archive import digest, verify_saved

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT/'evidence/2026-10-17/uart-kernel-reflash'
NORMAL = 'b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'

def read(path):
    return json.loads(path.read_text())

def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to((ROOT/'device-evidence').resolve())
    spec = importlib.util.spec_from_file_location('fix',ROOT/'build/install-uart-fix.py')
    fix = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fix)
    assert not fix.git('status','--porcelain')
    commit = fix.git('rev-parse','HEAD')
    assert commit == fix.git('rev-parse','origin/codex/snes-mvp-foundation')
    v = read(archive/'reflash-verification-analysis.json')
    assert all(v[k] for k in ['complete','reflash_verification','fresh_boot_verified',
                             'two_pass_flash_exact','runtime_UART_module_absent',
                             'idle_IRQ_flood_acceptance_passed','saves_and_prior_evidence_unchanged'])
    assert v['verification_installation_sha256'] == digest(PUBLIC/'verification-installation.json')
    for name, h in v['analyzer_sources'].items():
        assert digest(ROOT/'build'/name) == h, name
    assert v['archive_manifest_sha256'] == digest(archive/'archive.json')
    assert v['outside_manifest_sha256'] == digest(archive/'outside-retro.json')
    a, o = read(archive/'archive.json'), read(archive/'outside-retro.json')
    assert a['fat_clean'] and a['card_writes'] == o['card_writes'] == 0
    verify_saved(archive,a)
    for e in o['files']:
        if e['stored']:
            assert digest(archive/e['path']) == e['sha256']
    expected = {e['path']:e['sha256'] for e in a['all_retro_files']+o['files']}
    installed = read(PUBLIC/'verification-installation.json')
    assert expected['retro/init'] == installed['init_sha256']
    normal = ROOT/'device-evidence/uart-kernel-firmware1/normal-init'
    assert digest(normal) == NORMAL
    card = Path('I:/').resolve()
    assert str(card).lower() in ('i:/','i:\\')
    def verify():
        assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()} == set(expected)
        for name, h in expected.items():
            assert digest(card/name) == h, name
        assert not list(card.rglob('armed')) and not list(card.rglob('Code.bkp'))
    verify()
    fix.health(archive,'reflash-restore-before')
    fix.atomic(card/'retro/init',normal.read_bytes())
    expected['retro/init'] = NORMAL
    verify()
    fix.health(archive,'reflash-restore-after')
    r = {'source_commit':commit,'archive':archive.name,
         'normal_init_restored_sha256':NORMAL,'only_changed_path':'retro/init',
         'protected_files_unchanged':len(expected)-1,'all_file_count':len(expected),
         'all_probe_results_retained':True,'saves_and_evidence_unchanged':True,
         'no_armed_tests':True,'no_update_trigger':True,'FAT_clean':True,
         'no_full_backup':True,'no_firmware_writes':True}
    text = json.dumps(r,indent=2)+'\n'
    (archive/'reflash-restoration.json').write_text(text)
    (PUBLIC/'restoration.json').write_text(text)
    print(text)

if __name__ == '__main__':
    main(Path(sys.argv[1]))
