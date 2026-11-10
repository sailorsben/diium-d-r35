"""Run the existing strict comparators on held-out APU states and Ranger boot."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT/'build/multigame-fixes-private-v1'
QEMU = ['qemu-arm', '-cpu', 'cortex-a7', '-L', 'build/sysroot', '-E', 'LD_LIBRARY_PATH=build/sysroot/lib']


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main(out, candidate):
    out.mkdir()
    reference = ROOT/'build/fivegame-kernel-private-v2/plus-a7.so'
    assert digest(reference)=='d7988b2861500eb923b827ad412c14ae841c03dd44e4099f2616a637bf88f62a'
    ability = ROOT/'build/ability-regression-private-v1'
    plan = json.loads((ability/'plan.json').read_text())
    compare = FIXTURES/'ffvi-v2/compare'
    tests = []
    for case in plan['cases']:
        if case['name'] not in ('METEOR', 'QUASAR'):
            continue
        name = case['name'].lower()
        folder = ability/'cases'/f"{case['seq']:03d}"
        state, inputs = folder/'scene.state', folder/'input.txt'
        assert digest(state)==case['state_sha256'] and digest(inputs)==case['input_sha256']
        rom = ROOT/'build/plus-a7-out/ff6.sfc'
        tests.append((name, [compare,reference,candidate,rom,state,inputs,str(case['observed_effect_id']),'1200'],
                      'PASS 1200 calls: exact graphics/PCM/state', 1200))
    assert len(tests)==2

    # Cold boot exercises the existing Ranger-specific port ordering before
    # the already-inspected gameplay save can mask a boot handshake failure.
    boot = out/'ranger'
    boot.mkdir()
    buttons = boot/'input.txt'
    buttons.write_text('2400 0\n', newline='\n')
    tests.append(('ranger', [FIXTURES/'gameplay-check',reference,candidate,
                  ROOT/'build/fivegame-kernel-private-v2/cases/004/game.sfc',boot/'frames.csv',buttons,boot],
                  'PASS calls=2400', 2400))

    def run(test):
        name, args, token, count = test
        log = out/(name+'.log')
        with log.open('w') as f:
            subprocess.run([*QEMU,*args], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, timeout=420, check=True)
        assert token in log.read_text(), name
        print(name, 'passed', flush=True)
        return {'scenario':name,'calls':count,'normalized_state_and_output_match':True,
                'log_sha256':digest(log),'comparator_sha256':digest(args[0])}

    with ThreadPoolExecutor(max_workers=3) as pool:
        checks = list(pool.map(run, tests))
    (out/'checks.json').write_text(json.dumps({'core_sha256':digest(candidate),'baseline_sha256':digest(reference),
                                               'tests':checks,'device_executed':False}, indent=2)+'\n')


if __name__=='__main__':
    main(*(Path(arg).resolve() for arg in sys.argv[1:]))
