"""Unarmed-card staging success/failure fixtures. No physical card access."""
from pathlib import Path
import importlib.util, json, tempfile
from attempt_archive import digest

ROOT = Path(__file__).resolve().parent.parent

def main():
    spec = importlib.util.spec_from_file_location('rearm',ROOT/'build/rearm-uart-kernel-firmware.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    cases = ['success','init','trigger','health-before','health-init','health-armed',
             'changed-init','existing-trigger','armed-test','verify-init','verify-trigger']
    for fault in cases:
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as tmp:
            card = Path(tmp)
            (card/'retro/update').mkdir(parents=True)
            init = card/'retro/init'
            trigger = card/'retro/update/Code.bkp'
            init.write_bytes(b'foreign' if fault == 'changed-init' else b'old init')
            (card/'retro/save.srm').write_bytes(b'progress')
            (card/'retro/evidence.log').write_bytes(b'prior evidence')
            if fault == 'existing-trigger':
                trigger.write_bytes(b'foreign update')
            if fault == 'armed-test':
                (card/'retro/armed').write_bytes(b'competing test')
            before = {p.relative_to(card):p.read_bytes() for p in card.rglob('*') if p.is_file()}
            def atomic(path,data):
                part = path.with_name(path.name+'.fixture-tmp')
                part.write_bytes(data)
                part.replace(path)
                assert path.read_bytes() == data
            def health(label):
                if fault == 'health-'+label:
                    raise RuntimeError('injected FAT failure')
            def inject(label):
                if fault == label:
                    raise RuntimeError('injected interruption')
            def verify(armed):
                assert init.read_bytes() == b'normal'
                assert trigger.exists() == armed
                if armed:
                    assert trigger.read_bytes() == b'package'
                if fault == ('verify-trigger' if armed else 'verify-init'):
                    raise RuntimeError('injected readback failure')
            try:
                m.stage(card,b'package',b'normal',b'old init',atomic,health,verify,inject)
            except (AssertionError,RuntimeError):
                assert fault != 'success'
                assert {p.relative_to(card):p.read_bytes() for p in card.rglob('*') if p.is_file()} == before
            else:
                assert fault == 'success' and init.read_bytes() == b'normal'
                assert trigger.read_bytes() == b'package'
            assert (card/'retro/save.srm').read_bytes() == b'progress'
            assert (card/'retro/evidence.log').read_bytes() == b'prior evidence'
    m.REARM.mkdir(parents=True,exist_ok=True)
    report = {'passed':True,'cases':cases,'card_access':False,
              'installer_sha256':digest(ROOT/'build/rearm-uart-kernel-firmware.py'),
              'checker_sha256':digest(Path(__file__)),
              'firmware_qualification_sha256':digest(m.OUT/'qualification.json')}
    (m.REARM/'staging-qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS 11 unarmed-card staging success/refusal/interruption/FAT/readback cases')

if __name__ == '__main__':
    main()
