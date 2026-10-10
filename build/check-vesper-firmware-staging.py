"""Exercise SD staging/rollback against private temporary folders, never D:."""
from pathlib import Path
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import patch
import importlib.util, json, os, tempfile

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('staging', ROOT / 'build/manage-vesper-firmware.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def run():
    original, package, expected = m.artifacts()
    passed = ['exact qualified package, baseline and vendor-mutated expected image']
    try:
        m.card_guard(ROOT)
    except AssertionError:
        passed.append('unknown card path refused before access')
    else:
        raise AssertionError('Unknown card accepted')
    with tempfile.TemporaryDirectory(prefix='firmware-stage-check-', dir=m.PRIVATE) as directory:
        home = Path(directory).resolve()
        assert home.is_relative_to(m.PRIVATE.resolve())
        for label, health_failure, preexisting in [('success', False, False),
                                                   ('rollback', True, False),
                                                   ('already-staged', False, True)]:
            card, archive = home / label / 'card', home / label / 'archive'
            (card / 'retro/update').mkdir(parents=True)
            archive.mkdir(parents=True)
            protected = card / 'retro/save.srm'
            protected.write_bytes(b'private progress must remain exact')
            if preexisting:
                (card / 'retro/update/Code.bkp').write_bytes(b'unknown preexisting package')
            before = m.inventory(card)
            calls = []

            def write_new(path, data):
                with path.open('xb') as f:
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())
                assert path.read_bytes() == data

            def healthy():
                calls.append('health')
                if health_failure and len(calls) == 2:
                    raise AssertionError('injected poststage health failure')
                return 'fixture healthy'

            survey = SimpleNamespace(write_new=write_new, healthy=healthy,
                                     verify_protected=lambda *args: None)
            # Substitute only the D: identity/archive seams. Actual file writes,
            # rename, full inventory comparison and owned rollback execute here.
            with patch.object(m, 'card_guard', lambda *args: None), \
                 patch.object(m, 'baseline', lambda *args: (archive, survey)):
                try:
                    receipt = m.stage(card)
                except AssertionError:
                    assert health_failure or preexisting
                    assert m.inventory(card) == before
                    if preexisting:
                        assert not (archive / 'firmware-staging.json').exists()
                    else:
                        assert json.loads((archive / 'firmware-staging.json').read_text())['status'].startswith('staging-failed')
                    passed.append(label + ': unrelated files preserved; no replacement left')
                else:
                    assert not health_failure and not preexisting
                    assert receipt['status'] == 'staged-and-verified'
                    assert m.digest(card / 'retro/update/Code.bkp') == m.PACKAGE
                    after = m.inventory(card)
                    assert after.pop('retro/update/Code.bkp')['sha256'] == m.PACKAGE and after == before
                    assert (archive / 'baseline-spi-nor.bin').read_bytes() == original
                    assert (archive / 'expected-after-vendor.bin').read_bytes() == expected
                    passed.append('success: exact package only, backup and expected full image retained')
        # Actual identity/profile guard against controlled files, no real device.
        card = home / 'guard'
        (card / 'retro/update').mkdir(parents=True)
        (card / 'retro/snes-mvp').mkdir()
        (card / 'retro/snes-mvp/armed').write_bytes(b'other active test')
        with patch.object(m, 'INIT', 'fixture-init'), patch.object(m, 'VENDOR', 'fixture-vendor'), \
             patch.object(m, 'digest', lambda p: 'fixture-init' if p.name == 'init' else 'fixture-vendor'), \
             patch.object(Path, 'resolve', lambda p: Path('D:/')):
            try:
                m.card_guard(card)
            except AssertionError as error:
                assert 'snes-mvp is armed' in str(error)
                passed.append('competing armed runtime refused')
            else:
                raise AssertionError('Armed runtime accepted')
    report = {'all_checks_passed': True, 'checks': passed, 'device_access': False,
              'limits': 'Host staging/rollback only; physical flashing/recovery remain unqualified.'}
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    run()
