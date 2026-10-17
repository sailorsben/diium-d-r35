"""Historical real-return regression plus refusal controls; host files read-only."""
from pathlib import Path
import copy, importlib.util, json
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

def load(name):
    spec = importlib.util.spec_from_file_location(name,ROOT/'build'/name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    probe = load('analyze-uart-kernel-verify-return.py')
    old = ROOT/'device-evidence/uart-kernel-return-20261017T024017469637Z'
    regression = probe.analyze(old)
    prior = json.loads((old/'powered-analysis.json').read_text())
    for key in ['flash_sha256','kernel_sha256','boot_id','windows','readback_elapsed_seconds']:
        assert regression[key] == prior[key], key
    m = load('analyze-uart-reflash-verification.py')
    current = ROOT/'device-evidence/uart-kernel-return-20261017T101755121139Z'
    valid = m.analyze(current)
    real_read = m.read
    cases = []
    for name in ['changed-protected-file','wrong-consumed-marker']:
        def fixture_read(path):
            value = real_read(path)
            if path == current/'archive.json':
                value = copy.deepcopy(value)
                target = 'retro/adcset.ini' if name == 'changed-protected-file' else m.BASE+'consumed'
                entry = next(e for e in value['all_retro_files'] if e['path'] == target)
                entry['sha256'] = '0'*64
            return value
        with patch.object(m,'read',fixture_read):
            try:
                m.analyze(current)
            except AssertionError:
                cases.append(name)
            else:
                raise AssertionError('Accepted invalid '+name)
    original_text = Path.read_text
    def stale_boot(path,*args,**kwargs):
        if path.is_relative_to(current) and path.name.endswith('-boot-id.txt'):
            return prior['boot_id']+'\n'
        return original_text(path,*args,**kwargs)
    with patch.object(Path,'read_text',stale_boot):
        try:
            m.analyze(current)
        except AssertionError as e:
            assert str(e) == 'Stale physical boot'
            cases.append('stale-boot')
        else:
            raise AssertionError('Accepted stale boot')
    assert len(cases) == 3 and valid['fresh_boot_verified']
    print('PASS unchanged historical physical-result regression; current return; protected-file, consumed-marker and stale-boot refusal controls. No card writes.')

if __name__ == '__main__':
    main()
