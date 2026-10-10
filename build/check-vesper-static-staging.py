"""Host staging rollback/refusal checks in private fixtures; never D:."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import importlib.util, json, os, shutil, tempfile, zlib

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('static_manager', ROOT / 'build/manage-vesper-static.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def check():
    image, package, expected = m.artifacts()
    passed = ['exact hash-bound candidate/package, qualified sources and vendor-mutated expected image']
    try:
        m.card_guard(ROOT)
    except AssertionError:
        passed.append('wrong card refused before access')
    else:
        raise AssertionError('Wrong card accepted')
    with tempfile.TemporaryDirectory(prefix='static-staging-check-', dir=m.PRIVATE) as directory:
        home = Path(directory).resolve()
        assert home.is_relative_to(m.PRIVATE.resolve()) and home.parent == m.PRIVATE.resolve()
        for label in ['success', 'health-rollback', 'existing-update']:
            card, archive = home / label / 'card', home / label / 'archive'
            (card / 'retro/update').mkdir(parents=True)
            archive.mkdir(parents=True)
            (card / 'retro/progress.srm').write_bytes(b'keep this private progress exact')
            if label == 'existing-update':
                (card / 'retro/update/Code.bkp').write_bytes(b'unknown staged package')
            before = m.inventory(card)
            calls = []

            def write_new(path, data):
                with path.open('xb') as f:
                    f.write(data); f.flush(); os.fsync(f.fileno())
                assert path.read_bytes() == data

            def healthy():
                calls.append('health')
                if label == 'health-rollback' and len(calls) == 2:
                    raise AssertionError('injected poststage health failure')
                return 'fixture healthy'

            survey = SimpleNamespace(write_new=write_new, healthy=healthy, verify_protected=lambda *args: None)
            with patch.object(m, 'card_guard', lambda *args: None), \
                 patch.object(m, 'baseline', lambda *args: (archive, survey)):
                try:
                    receipt = m.stage(card)
                except AssertionError:
                    assert label != 'success' and m.inventory(card) == before
                    if label == 'existing-update':
                        assert not (archive / 'static-staging.json').exists()
                    else:
                        assert json.loads((archive / 'static-staging.json').read_text())['status'].startswith('staging-failed')
                    passed.append(label + ': original bytes preserved; no owned update left')
                else:
                    assert label == 'success' and receipt['first_static_screen'] == 'Vesper replacement'
                    assert receipt['second_animation'] == 'verified Vesper preserved'
                    after = m.inventory(card)
                    assert after.pop('retro/update/Code.bkp')['sha256'] == m.PACKAGE and after == before
                    assert (archive / 'baseline-installed-spi.bin').read_bytes() == image
                    assert (archive / 'expected-after-vendor.bin').read_bytes() == expected
                    passed.append('success: exact package only, current installed backup and expected image retained')
        # Exercise the new baseline/run guard using an actual returned complete
        # reader profile, while replacing only the known-D: identity seam.
        card = home / 'baseline-guard'
        shutil.copytree(m.PRIVATE / 'snes-mvp-return-20261010T052230Z/spi-readback', card / 'retro/spi-readback')
        with patch.object(m.old, 'card_guard', lambda *args: None):
            m.card_guard(card)
            base = card / 'retro/spi-readback'
            raw = bytearray((base / 'results/captures.bin').read_bytes())
            raw[0] ^= 1; raw[8388608] ^= 1
            (base / 'results/captures.bin').write_bytes(raw)
            p = base / 'results/report.jsonl'
            records = [json.loads(line) for line in p.read_text().splitlines()]
            for r in records:
                if r['kind'] == 'result':
                    r['crc32'] = [f'{zlib.crc32(raw[:8388608]):08x}', f'{zlib.crc32(raw[8388608:]):08x}']
            p.write_text(''.join(json.dumps(r) + '\n' for r in records), encoding='utf-8')
            try:
                m.card_guard(card)
            except AssertionError as error:
                assert 'latest verified installed baseline' in str(error)
                passed.append('complete but different flash baseline refused')
            else:
                raise AssertionError('Different complete baseline accepted')
        # Existing guard checks competing marker before reading a reader profile.
        card = home / 'competing-test'
        (card / 'retro/update').mkdir(parents=True)
        (card / 'retro/snes-mvp').mkdir()
        (card / 'retro/snes-mvp/armed').write_bytes(b'other test')
        with patch.object(m.old, 'digest', lambda p: m.old.INIT if p.name == 'init' else m.old.VENDOR), \
             patch.object(Path, 'resolve', lambda p: Path('D:/')):
            try:
                m.card_guard(card)
            except AssertionError as error:
                assert 'snes-mvp is armed' in str(error)
                passed.append('competing armed runtime refused')
            else:
                raise AssertionError('Competing marker accepted')
    result = {'all_checks_passed': True, 'checks': passed, 'device_access': False,
              'source_sha256': {name: m.digest(ROOT / name) for name in
                                ['build/manage-vesper-static.py', 'build/check-vesper-static-staging.py']},
              'limits': 'Host staging/baseline/refusal/rollback checks, separate from physical flashing and display acceptance.'}
    m.save(m.QUALIFIED / 'staging-checks.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    check()
