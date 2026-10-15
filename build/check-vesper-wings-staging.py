"""Exercise actual staging filesystem seam on private fixture cards only."""
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import importlib.util
import json
import tempfile

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('wings_stage', ROOT / 'build/stage-vesper-wings-firmware.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def main():
    _, _, package = m.artifacts()
    checks = ['exact qualified package, sources and firmware baseline hashes']
    try:
        m.guard(ROOT)
    except AssertionError:
        checks.append('wrong-card refusal before card reads')
    else:
        raise AssertionError('Wrong card accepted')
    with tempfile.TemporaryDirectory(prefix='wings-stage-check-', dir=ROOT / 'device-evidence') as directory:
        home = Path(directory).resolve()
        assert home.parent == (ROOT / 'device-evidence').resolve()
        for case in ['normal', 'health-failure', 'existing-trigger']:
            card = home / case / 'card'
            archive = home / case / 'archive'
            (card / 'retro/update').mkdir(parents=True)
            archive.mkdir()
            (card / 'retro/progress.srm').write_bytes(b'private progress preserved exactly')
            if case == 'existing-trigger':
                (card / 'retro/update/Code.bkp').write_bytes(b'unknown existing trigger')
            before = m.inventory(card)
            calls = []
            def health(*args):
                calls.append(args[-1])
                if case == 'health-failure' and len(calls) == 1:
                    raise AssertionError('Injected poststage health failure')
            with patch.object(m, 'healthy', health):
                try:
                    m.stage_payload(card, archive, package, before)
                except AssertionError:
                    assert case != 'normal' and m.inventory(card) == before
                    if case == 'health-failure':
                        assert calls == ['poststage', 'before-rollback']
                    checks.append(case + ': protected progress and original trigger state preserved')
                else:
                    assert case == 'normal'
                    after = m.inventory(card)
                    assert after.pop('retro/update/Code.bkp')['sha256'] == m.PACKAGE and after == before
                    checks.append('actual write/rename/readback adds only exact qualified update')
    # Exercise the real physical capture parser against the retained full reads.
    m.verify_installed_capture(ROOT / 'device-evidence/a7-pair-before-20261015T052954Z/retro/spi-readback')
    fake = SimpleNamespace(analyze=lambda base: {'complete': True, 'marker_matches': True, 'pass_sha256': ['0' * 64] * 2})
    with patch.object(m, 'load', lambda name: fake):
        try:
            m.verify_installed_capture(ROOT)
        except AssertionError:
            pass
        else:
            raise AssertionError('Different complete flash capture accepted')
    checks.append('actual retained full flash capture accepted; complete different firmware refused')
    assert len(checks) == 6
    result = {'all_checks_passed': True, 'checks': checks, 'card_access': False,
        'sources': {name: m.digest(ROOT / name) for name in
                    ['build/stage-vesper-wings-firmware.py', 'build/check-vesper-wings-staging.py']}}
    m.save(m.QUALIFIED / 'staging-checks.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
