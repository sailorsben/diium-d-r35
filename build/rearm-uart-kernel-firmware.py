"""Rearm the exact qualified kernel fix from an unarmed card; no new firmware."""
from pathlib import Path
import importlib.util, json, shutil, sys
from attempt_archive import digest, verify_saved

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT/'device-evidence/uart-kernel-firmware1'
REARM = ROOT/'evidence/2026-10-17/uart-kernel-reflash'
NORMAL = 'b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
CARD_UART = '24280b658d52702848901df258c9e3e9c4a1c4ba876cdad03534bee67d0343fe'

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'build'/name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def stage(card, package, normal, expected_init, atomic, health, verify, inject=lambda _:None):
    init = card/'retro/init'
    trigger = card/'retro/update/Code.bkp'
    assert init.read_bytes() == expected_init and not trigger.exists()
    assert not list(card.rglob('Code.bkp')) and not list(card.rglob('armed'))
    health('before')
    try:
        atomic(init, normal)
        inject('init')
        verify(False)
        health('init')
        atomic(trigger, package)  # Activation last, after normal boot readback.
        inject('trigger')
        verify(True)
        health('armed')
    except BaseException:
        health('before-rollback')
        if trigger.exists():
            assert trigger.read_bytes() == package
            trigger.unlink()
        assert init.read_bytes() in (expected_init, normal)
        if init.read_bytes() != expected_init:
            atomic(init, expected_init)
        raise

def main(archive):
    original = load('stage-uart-kernel-firmware.py')
    p, q, package, normal, _, _ = original.artifacts()
    assert digest(OUT/'normal-init') == NORMAL
    heap = json.loads((OUT/'boot-heap-qualification.json').read_text())
    assert heap['passed'] and heap['heap_bytes'] == 65536
    assert heap['zImage_sha256'] == digest(OUT/'zImage.bin')
    assert heap['original_source_sha256'] == digest(ROOT/'build/check-kernel-decompressor.c')
    iq = json.loads((REARM/'staging-qualification.json').read_text())
    assert iq['passed'] and iq['installer_sha256'] == digest(Path(__file__))
    assert iq['firmware_qualification_sha256'] == digest(OUT/'qualification.json')
    fix = load('install-uart-fix.py')
    assert not fix.git('status','--porcelain')
    assert fix.git('branch','--show-current') == 'codex/snes-mvp-foundation'
    commit = fix.git('rev-parse','HEAD')
    assert commit == fix.git('rev-parse','origin/codex/snes-mvp-foundation')
    archive = archive.resolve()
    assert archive.is_relative_to((ROOT/'device-evidence').resolve())
    a = json.loads((archive/'archive.json').read_text())
    outside = json.loads((archive/'outside-retro.json').read_text())
    assert a['fat_clean'] and a['card_writes'] == outside['card_writes'] == 0
    verify_saved(archive,a)
    entries = a['all_retro_files'] + outside['files']
    card = Path('I:/').resolve()
    assert str(card).lower() in ('i:/','i:\\')
    baseline = {e['path']:e['sha256'] for e in entries}
    assert baseline['retro/init'] in (CARD_UART, NORMAL)
    assert baseline['retro/vrtemu'] == '8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
    assert not (card/'retro/uart-fix1/disabled').exists()
    for e in entries:
        assert digest(card/e['path']) == e['sha256'], e['path']
        if e['stored']:
            assert digest(archive/e['path']) == e['sha256'], e['path']
    assert {x.relative_to(card).as_posix() for x in card.rglob('*') if x.is_file()} == set(baseline)
    assert shutil.disk_usage(card).free > len(package) + 64*1024*1024
    oldinit = (card/'retro/init').read_bytes()
    protected = {n:h for n,h in baseline.items() if n != 'retro/init'}
    def verify(armed):
        expected = {**protected, 'retro/init':NORMAL}
        if armed:
            expected['retro/update/Code.bkp'] = p['package_sha256']
        assert {x.relative_to(card).as_posix() for x in card.rglob('*') if x.is_file()} == set(expected)
        for name, h in expected.items():
            assert digest(card/name) == h, name
        assert not list(card.rglob('armed'))
    stage(card,package,normal,oldinit,fix.atomic,
          lambda label:fix.health(archive,'kernel-reflash-'+label),verify)
    report = {'version':'uart-kernel1-reflash', 'source_commit':commit, 'archive':archive.name,
              'armed_vendor_update':True, 'package_sha256':p['package_sha256'],
              'package_bytes':len(package), 'candidate_sha256':p['candidate_sha256'],
              'expected_after_vendor_sha256':p['expected_after_vendor_sha256'],
              'normal_init_sha256':NORMAL, 'prior_init_sha256':baseline['retro/init'],
              'changed_existing_files':['retro/init'] if baseline['retro/init'] != NORMAL else [],
              'added_update_file':'retro/update/Code.bkp', 'protected_existing_files':len(protected),
              'all_existing_files':len(entries), 'FAT_clean':True,
              'no_emulator_test_armed':True, 'runtime_UART_loader_invoked':False,
              'both_Vesper_screens_and_rootfs_preserved':True, 'no_full_backup':True,
              'battery_observation':'User reports fully charged, green indicator, unplugged behavior now normal; ADC fault not observed',
              'physical_reflash':'PENDING'}
    text = json.dumps(report,indent=2)+'\n'
    (archive/'uart-kernel-installation.json').write_text(text)
    (REARM/'installation.json').write_text(text)
    print(text)

if __name__ == '__main__':
    main(Path(sys.argv[1]))
