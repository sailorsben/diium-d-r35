"""Qualify the adaptive decoder with frozen outputs and paired CPU timing."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / 'build/fivegame-kernel-private-v2/cases'
QEMU = ['qemu-arm', '-cpu', 'cortex-a7', '-L', 'build/sysroot',
        '-E', 'LD_LIBRARY_PATH=build/sysroot/lib']
GAMES = ('Super Mario World', 'Super Metroid', 'F-Zero', 'Star Fox', 'Rendering Ranger')


def compile_replay(name, output):
    subprocess.run([
        'arm-linux-gnueabihf-gcc', '-std=gnu11', '-O2', '-mcpu=cortex-a7',
        '-mfpu=neon-vfpv4', '-mfloat-abi=hard', '-marm', '-fno-stack-protector',
        '-D_TIME_BITS=32', '-D_FILE_OFFSET_BITS=32', '-DD35_AUDIT_STATE', '-DUSE_BLARGG_APU',
        '-Wall', '-Wextra', '-Werror', '-no-pie', '-nostdlib',
        '-Ibuild/snes9x2005/libretro-common/include', '/usr/arm-linux-gnueabihf/lib/crt1.o',
        f'build/snes-throughput-{name}.c', '-Lbuild/sysroot/lib', '-Wl,--no-as-needed',
        '-l:libdl-2.30.so', '-l:libz.so.1', '-l:libc-2.30.so', '-l:libgcc_s.so.1',
        '-o', output,
    ], cwd=ROOT, check=True)


def run(argv, path):
    with path.open('w') as log:
        subprocess.run(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=420)
    return path.read_text().splitlines()


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main(out, reference, core, repeats):
    out.mkdir()
    same = out / 'disabled.so'
    same.write_bytes(core.read_bytes())
    compile_replay('pair', out / 'pair')
    compile_replay('replay', out / 'replay')
    # Spread simultaneous pairs over distinct physical host cores where possible.
    lanes = list(dict((Path(f'/sys/devices/system/cpu/cpu{cpu}/topology/thread_siblings_list').read_text(), cpu)
                      for cpu in sorted(os.sched_getaffinity(0))).values())

    def verify(task):
        index, heldout, control = task
        case = FIXTURES / f'{index:03}'
        cold = '8656' if index == 3 else '0'
        mode = 'cold-poison' if index == 3 else 'full'
        env = ['-E', 'D35_AUDIT_STATE=1']
        if heldout:
            env += ['-E', 'D35_AUDIT_HELDOUT=1']
        if control:
            env += ['-E', 'D35_BRR_CONTROL=1']
        label = 'off' if control else 'auto'
        log = out / f'{index:03}-{"heldout-" if heldout else ""}{label}.log'
        lines = run([*QEMU, *env, out / 'replay', core, case, cold, mode, 'verify'], log)
        verified = 0 if heldout else 1200
        assert f'verified={verified} mismatched=0' in lines[-1], log
        return [line for line in lines if line.startswith(('audit_', 'callback_layout='))]

    def time_game(index):
        case = FIXTURES / f'{index:03}'
        cold = '8656' if index == 3 else '0'
        prefix = 'both-cold-off' if index == 3 else 'full'
        qemu = ['taskset', '-c', str(lanes[index % len(lanes)]), *QEMU]
        measurements = []
        for repeat in range(repeats):
            for mode, baseline in [('toggle', same), ('compare', reference)]:
                log = out / f'{index:03}-{mode}-{repeat}.csv'
                lines = run([*qemu, out / 'pair', baseline, core, case, cold,
                             prefix + '-brr-' + mode], log)
                rows = [tuple(map(int, line.split(','))) for line in lines if line.split(',')[0].isdigit()]
                assert [row[0] for row in rows] == list(range(1200)), log
                first = statistics.mean(row[1] for row in rows)
                second = statistics.mean(row[2] for row in rows)
                stats, = [line for line in lines if line.startswith('brr ')]
                measurements.append(dict(comparison=mode, repeat=repeat, control_ns=first, auto_ns=second,
                                         saving_percent=100 * (1 - second / first),
                                         profile={k: int(v) for k, v in (part.split('=') for part in stats.split()[1:])},
                                         log_sha256=digest(log)))
        print(GAMES[index], 'paired timings finished', flush=True)
        return dict(game=GAMES[index], measurements=measurements)

    checks = [(3, True), (3, False), *((index, False) for index in (0, 1, 2, 4))]
    exact = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        tasks = [(index, heldout, control) for index, heldout in checks for control in (True, False)]
        signatures = list(pool.map(verify, tasks))
        for n, (index, heldout) in enumerate(checks):
            first, second = signatures[2*n:2*n+2]
            assert first == second and len(first) == (1242 if heldout else 42)
            exact.append(dict(game=GAMES[index], heldout=heldout, ticks=1200, matched_records=len(first)))
            print(GAMES[index], 'held-out input and reloads passed' if heldout else 'exact replay passed', flush=True)
        timings = list(pool.map(time_game, range(len(GAMES))))
    result = dict(physical=False, reference_sha256=digest(reference), core_sha256=digest(core),
                  exact=exact, timings=timings)
    (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main(*(Path(arg).resolve() for arg in sys.argv[1:4]), int(sys.argv[4]))
