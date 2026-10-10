"""Private host fixtures for archived rearm, fail-closed rollback and full comparison."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import importlib.util, json, tempfile

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('verification', ROOT / 'build/manage-vesper-flash-verification.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def run():
    real = v.manager()
    expected = v.expected_image()
    passed = ['exact vendor-mutated expected image hash']
    with tempfile.TemporaryDirectory(prefix='vesper-verification-check-', dir=ROOT / 'device-evidence') as directory:
        home = Path(directory).resolve()
        assert home.is_relative_to((ROOT / 'device-evidence').resolve())
        for label, fail, existing_update in [('success', False, False),
                                              ('install-fails', True, False),
                                              ('update-present', False, True)]:
            card, archive = home / label / 'card', home / label / 'archive'
            base = card / 'retro/spi-readback'
            base.mkdir(parents=True)
            archive.mkdir(parents=True)
            target = card / 'retro/init'
            original = b'#!/bin/sh\n# unchanged baseline\n'
            target.write_bytes(original)
            (base / 'init.before').write_bytes(original)
            (base / 'prior-capture.bin').write_bytes(b'prior private reader contents')
            if existing_update:
                (card / 'retro/update').mkdir()
                (card / 'retro/update/Code.bkp').write_bytes(b'never combine reader with flash trigger')
            prior = {p.name:real.digest(p) for p in base.iterdir()}
            entries = [{'path':name, 'sha256':h} for name,h in prior.items()]
            v.save(archive / 'readback-extra-collection.json', entries)

            def digest(path):
                if path == target or path.name == 'init.before':
                    return real.digest(path)
                if path.name == 'showlogo':
                    return 'fixture-splash'
                if path.name == 'vrtemu':
                    return '8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
                return real.digest(path)

            def atomic_replace(path, data):
                path.write_bytes(data)

            def install(*args):
                base.mkdir()
                installation = {'run_id':'fixture-new-run'}
                v.save(base / 'installation.json', installation)
                (base / 'armed').write_text('fixture-new-run\n')
                (base / 'new-payload').write_bytes(b'new owned reader')
                target.write_bytes(b'#!/bin/sh\n' + real.HOOK + original[len(b'#!/bin/sh\n'):])
                if fail:
                    raise RuntimeError('injected installer failure after arming')
                return archive

            m = SimpleNamespace(digest=digest, read=real.read, analyze=lambda p:{'complete':True,'marker_matches':True},
                                RELEASE=real.RELEASE, HOOK=real.HOOK, baseline=lambda *a:archive, install=install)
            survey = SimpleNamespace(INIT=real.digest(target), SPLASH='fixture-splash', healthy=lambda:'fixture healthy',
                                     atomic_replace=atomic_replace)
            with patch.object(v.time, 'sleep', lambda *a:None):
                try:
                    receipt = v.arm(card,m,None,survey)
                except (RuntimeError, AssertionError):
                    assert fail or existing_update
                    assert target.read_bytes()==original
                    assert {p.name:real.digest(p) for p in base.iterdir()}==prior
                    assert not (base/'armed').exists()
                    if fail:
                        assert len(list((card/'retro').glob('spi-readback.incomplete-*')))==1
                    passed.append(label+': original init/prior profile retained; new marker absent')
                else:
                    assert not fail and not existing_update and receipt['status']=='armed'
                    parked=card/receipt['retained_prior_profile']
                    assert {p.name:real.digest(p) for p in parked.iterdir()}==prior
                    assert (base/'armed').read_text().strip()=='fixture-new-run'
                    passed.append('success: prior profile intact, fresh reader alone armed')
        outside=home/'outside'
        outside.mkdir()
        try:
            v.move_owned(outside,home/'spi-readback-other',home/'different-parent')
        except AssertionError:
            assert outside.exists()
            passed.append('out-of-parent directory move refused')
        else:
            raise AssertionError('Unexpected directory move accepted')
        for label, data, complete, match in [('match',expected+expected,True,True),
                                             ('different',expected+bytes([expected[0]^1])+expected[1:],True,False),
                                             ('incomplete',b'',False,False)]:
            archive=home/label
            (archive/'spi-readback/results').mkdir(parents=True)
            v.save(archive/'readback-analysis.json',{'complete':complete})
            (archive/'spi-readback/results/captures.bin').write_bytes(data)
            m=SimpleNamespace(collect=lambda *a:archive,read=real.read)
            result=v.collect(home,m,None,None,False)
            assert result['full_image_matches'] is match
            if label=='different':
                assert result['differing_64k_blocks']==[[],['0x0']]
            passed.append(label+': complete full-byte comparison result correct')
    print(json.dumps({'all_checks_passed':True,'checks':passed,'device_access':False,
                      'limits':'Host manager/move/rollback/comparison only; unchanged reader already qualified separately.'},indent=2))


if __name__=='__main__':
    run()
