"""Qualify off-card in WSL, then arm or verify the isolated native replay on I:."""
import argparse
import csv
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from attempt_archive import digest


raster = import_module('install-snes-raster-device')
ROOT, MVP, FROZEN, INIT = raster.ROOT, raster.MVP, raster.FROZEN, raster.INIT
fix = raster.fix
TARGET = 'retro/snes-superfx-native1'
BASE = ROOT/'build/fivegame-kernel-private-v2'
OUT = ROOT/'build/superfx-native-private-v1'
EVIDENCE = ROOT/'evidence/2026-11-10'
NATIVE = EVIDENCE/'snes-throughput'
SUPERFX = EVIDENCE/'snes-raster-batches'
CORE = 'retro/snes-superfx-test1/cores/fx-batch.so'
CASE = [f'cases/003/{n}' for n in ('game.sfc', 'input.txt', 'warmup.txt', 'expected.bin')]
PAYLOAD = ['fivegame-suite', 'plus-a7.so', 'uart-observe', 'ROM-PATH.txt', 'launch.sh']
HOST_SWITCHES = ('D35_ABILITY_MOCK', 'D35_MVP_NO_PACING', 'D35_FULL_HOST_FIXTURE', 'D35_FIVE_ORACLE')
WRAPPER_CASES = ('normal', 'unarmed', 'active-splash', 'observer-before', 'child-crash')
RECEIPT = 'superfx-native-installation.json'


def load(path):
    return json.loads(path.read_text())


def kv(path):
    return dict(line.split('=', 1) for line in path.read_text().splitlines() if '=' in line)


def checksum(data):
    return sha256(data).hexdigest()


def pinned():
    cold = load(NATIVE/'cold-raster-runner.json')
    previous = load(SUPERFX/'superfx-device-installation.json')
    frozen = load(raster.FROZEN_RECEIPT)['payload_hashes']
    return cold['candidate_sha256'], previous['payload_hashes']['cores/fx-batch.so'], frozen


def wrapper_bytes():
    template = (BASE/'launch.sh').read_bytes()
    assert template.count(b'/usr/retro/snes-fivegame-kernel2') == 1
    assert template.count(b'export LD_LIBRARY_PATH=') == 1
    return template.replace(b'/usr/retro/snes-fivegame-kernel2', f'/usr/{TARGET}'.encode()).replace(
        b'export LD_LIBRARY_PATH=', ('unset '+' '.join(HOST_SWITCHES)+'\nexport LD_LIBRARY_PATH=').encode())


def check_wrapper(work, rom):
    firmware = ROOT/'build/uart-fix-private/firmware-busybox'
    shell = ['qemu-arm', '-0', 'busybox', '-L', 'build/sysroot', firmware, 'sh']
    launcher = OUT/'launch.sh'
    subprocess.run([*shell, '-n', launcher], cwd=ROOT, check=True)
    for name in WRAPPER_CASES:
        lab = work/name
        proc, mvp = lab/'proc', lab/'mvp'
        proc.mkdir(parents=True)
        mvp.mkdir()
        for path in (lab/'armed', mvp/'armed'):
            if name != 'unarmed':
                path.write_text('fixture\n')
        (lab/'ROM-PATH.txt').write_text(f'{rom}\n')
        observer = lab/'uart-observe'
        observer.write_text('#!/bin/sh\n'+('exit 1\n' if name == 'observer-before' else 'mkdir "$2"\n'))
        runner = lab/'fivegame-suite'
        runner.write_text(
            '#!/bin/sh\nset -eu\n'
            + ''.join(f'[ -z "${{{flag}+set}}" ]\n' for flag in HOST_SWITCHES)
            + '[ "$1" = --supervise ] && [ -d "$2" ] && [ "$3" = "$D35_LAB_BASE" ] && [ -f "$4" ]\n'
            + 'printf ran > "$D35_LAB_BASE/ran"\n'
            + ('exit 139\n' if name == 'child-crash' else 'exit 0\n'))
        for executable in (observer, runner):
            executable.chmod(0o755)
        if name == 'active-splash':
            splash = proc/'123'
            splash.mkdir()
            (splash/'comm').write_text('showlogo\n')
            (splash/'status').write_text('State:\tS\n')
        env = {**os.environ, **dict.fromkeys(HOST_SWITCHES, '1'),
               'D35_LAB_BASE': str(lab), 'D35_MVP_BASE': str(mvp), 'D35_LAB_PROC_ROOT': str(proc),
               'D35_LAB_SYS_ROOT': str(lab/'sys'), 'D35_LAB_SPLASH_STOP': str(lab/'stop')}
        args = [*shell, launcher]
        if name == 'child-crash':
            args = ['timeout', '3', *args]
        rc = subprocess.run(args, cwd=ROOT, env=env, timeout=15).returncode
        assert rc == {'active-splash': 1, 'observer-before': 1, 'child-crash': 124}.get(name, 0), name
        assert (lab/'ran').exists() == (name in ('normal', 'child-crash')), name
        assert not (lab/'armed').exists() and not (mvp/'armed').exists()
        logs = list(lab.glob('results/*/wrapper.log'))
        if name == 'normal':
            assert len(logs) == 1 and 'lab_exit=0' in logs[0].read_text()
            subprocess.run(args, cwd=ROOT, env=env, timeout=15, check=True)
            assert list(lab.glob('results/*/wrapper.log')) == logs
        elif name == 'active-splash':
            assert 'splash_timeout' in logs[0].read_text()
        elif name == 'child-crash':
            assert 'next boot is stock' in logs[0].read_text()
        elif name == 'unarmed':
            assert not logs and not (lab/'stop').exists()


def check_replay(result, oracle):
    run = result/'run-000'
    warm, session = kv(run/'warmup.txt'), kv(run/'last-session.txt')
    checks, supervisor = kv(run/'input.csv'), kv(result/'supervisor.txt')
    with (run/'frames.csv').open() as log:
        frames = list(csv.DictReader(line for line in log if not line.startswith('#')))
    assert warm['status'] == 'completed' and warm['cold_boot_calls'] == '8656'
    assert warm['cold_replay_raster_disabled'] == warm['measured_metrics_reset_before_audio'] == '1'
    assert kv(run/'headroom.txt')['physical'] == '0' and len(frames) == 1200
    assert session['runs'] == session['rendered_frames'] == session['video_submitted'] == '1200'
    assert session['audio_remaining_frames'] == session['audio_cleared_frames'] == '0'
    assert not session['error'] and kv(run/'result.txt')['runner_rc'] == '0'
    assert checks['#oracle_enabled'] == str(int(oracle))
    assert checks['#oracle_checks'] == ('1200' if oracle else '0')
    assert supervisor['reaped'] == '1' and supervisor['forced'] == '0'
    assert kv(result/'suite-result.txt')['planned'] == '1' and kv(run/'begin.txt')['policy'] == '0'


def qualify(candidate):
    assert os.name == 'posix'
    controller, combined, frozen = pinned()
    assert digest(candidate) == controller
    source_core = ROOT/'build/superfx-device-private-v1/cores/fx-batch.so'
    assert digest(source_core) == combined
    for name in ['launch.sh', 'uart-observe', *CASE]:
        assert digest(BASE/name) == frozen[name], name
    OUT.mkdir(exist_ok=True)
    shutil.copyfile(candidate, OUT/'fivegame-suite')
    shutil.copyfile(source_core, OUT/'plus-a7.so')
    shutil.copyfile(BASE/'uart-observe', OUT/'uart-observe')
    (OUT/'launch.sh').write_bytes(wrapper_bytes())
    (OUT/'ROM-PATH.txt').write_bytes(f'/usr/{TARGET}/{CASE[0]}\n'.encode())
    with TemporaryDirectory(prefix='d35-native-') as tmp:
        work = Path(tmp)
        check_wrapper(work, BASE/CASE[0])
        trial = work/'replay'
        trial.mkdir()
        for name in ('fivegame-suite', 'plus-a7.so'):
            (trial/name).symlink_to(OUT/name)
        (OUT/'fivegame-suite').chmod(0o755)
        (trial/'cases').symlink_to(BASE/'cases', target_is_directory=True)
        env = {k: v for k, v in os.environ.items() if not k.startswith('D35_')}
        env.update(dict.fromkeys(HOST_SWITCHES[:3], '1'))
        for mode in ('oracle', 'native-flags'):
            result = trial/mode
            result.mkdir()
            oracle = mode == 'oracle'
            active_env = {**env, 'D35_FIVE_ORACLE': '1'} if oracle else env
            with (OUT/f'{mode}.log').open('w') as log:
                subprocess.run(['qemu-arm', '-cpu', 'cortex-a7', '-L', 'build/sysroot',
                                '-E', 'LD_LIBRARY_PATH=build/sysroot/lib', trial/'fivegame-suite',
                                '--supervise', result, trial, 'unused'], cwd=ROOT, env=active_env,
                               stdout=log, stderr=subprocess.STDOUT, check=True, timeout=420)
            check_replay(result, oracle)
            shutil.copyfile(result/'supervisor.txt', OUT/f'{mode}-supervisor.txt')
    proof = dict(source_sha256=digest(Path(__file__)), cold_calls=8656, exact_calls=1200,
                 oracle_disabled_mock_calls=1200, physical=False, policy=0,
                 wrapper_cases=WRAPPER_CASES, firmware_busybox_sha256=digest(ROOT/'build/uart-fix-private/firmware-busybox'),
                 payload_hashes={n: digest(OUT/n) for n in PAYLOAD}, fixture_hashes={n: frozen[n] for n in CASE})
    (OUT/'qualification.json').write_bytes((json.dumps(proof, indent=2)+'\n').encode())
    print('PASS both supervised rehearsals and five exact firmware BusyBox wrapper cases')


def health(archive, label):
    fix.health(archive, 'superfx-native-'+label)
    result = subprocess.run(['fsutil', 'dirty', 'query', 'I:'], capture_output=True, text=True, check=True)
    (archive/f'superfx-native-dirty-{label}.txt').write_text(result.stdout+result.stderr)
    assert 'is not dirty' in result.stdout.lower(), result.stdout


def stage(card, archive, inventory):
    assert not fix.git('status', '--porcelain')
    commit = fix.git('rev-parse', 'HEAD')
    assert commit == fix.git('rev-parse', 'origin/codex/snes-mvp-foundation')
    assert (ROOT/'docs/snes-superfx-native-test.md').is_file()
    controller, combined, frozen = pinned()
    proof = load(OUT/'qualification.json')
    assert proof['source_sha256'] == digest(Path(__file__))
    assert proof['cold_calls'] == 8656 and proof['exact_calls'] == proof['oracle_disabled_mock_calls'] == 1200
    assert proof['policy'] == 0 and not proof['physical'] and tuple(proof['wrapper_cases']) == WRAPPER_CASES
    assert proof['payload_hashes'] == {n: digest(OUT/n) for n in PAYLOAD}
    assert proof['payload_hashes']['fivegame-suite'] == controller
    assert proof['payload_hashes']['plus-a7.so'] == inventory[CORE] == combined
    assert proof['payload_hashes']['uart-observe'] == frozen['uart-observe']
    assert proof['fixture_hashes'] == {n: inventory[FROZEN+'/'+n] for n in CASE} == {n: frozen[n] for n in CASE}
    assert inventory[MVP+'/launch.sh'] == load(SUPERFX/'superfx-device-installation.json')['dispatch_sha256']
    assert inventory['retro/init'] == INIT
    raster.verify_inventory(card, inventory)
    health(archive, 'before')
    payload = {n: (OUT/n).read_bytes() for n in [*PAYLOAD, 'qualification.json']}
    payload.update({n: (card/FROZEN/n).read_bytes() for n in CASE})
    payload['previous-launch.sh'] = (card/MVP/'launch.sh').read_bytes()
    hashes = {n: checksum(data) for n, data in payload.items()}
    assert all(hashes[n] == frozen[n] for n in CASE)
    dispatch = f'#!/bin/sh\nexec /bin/sh /usr/{TARGET}/launch.sh\n'.encode()
    marker = f'D-R35 native Star Fox full-tile + Super FX playback once {commit}\n'.encode()
    expected = {**inventory, **{TARGET+'/'+n: h for n, h in hashes.items()}}
    armed = {**expected, MVP+'/launch.sh': checksum(dispatch),
             MVP+'/armed': checksum(marker), TARGET+'/armed': checksum(marker)}

    def guarded_health(label):
        if label == 'armed':
            raster.verify_inventory(card, armed)
        health(archive, label)

    raster.activate(card, payload, dispatch, marker, lambda: raster.verify_inventory(card, expected),
                    guarded_health, target_path=TARGET)
    receipt = dict(source_commit=commit, target=TARGET, measurement_only=True, physical_result='PENDING',
                   native_lcd=True, native_pcm=True, on_device_crc_oracle=False, policy=0,
                   prior_archive=archive.name, prior_files=len(inventory), normal_init_sha256=INIT,
                   dispatch_sha256=checksum(dispatch), marker_sha256=checksum(marker), payload_hashes=hashes,
                   core_sha256=combined, controller_sha256=controller, full_backup_created=False)
    (archive/RECEIPT).write_text(json.dumps(receipt, indent=2)+'\n')


def verify(card, archive, inventory):
    receipt = load(archive/RECEIPT)
    markers = [MVP+'/armed', TARGET+'/armed']
    expected = {**inventory, MVP+'/launch.sh': receipt['dispatch_sha256']}
    expected.update({TARGET+'/'+n: h for n, h in receipt['payload_hashes'].items()})
    expected.update(dict.fromkeys(markers, receipt['marker_sha256']))
    raster.verify_inventory(card, expected)
    assert sorted(p.relative_to(card).as_posix() for p in card.rglob('armed')) == sorted(markers)
    assert not list(card.rglob('Code.bkp')) and digest(card/'retro/init') == INIT
    health(archive, 'independent')
    result = dict(**receipt, exact_card_files=len(expected), protected_existing_files=len(inventory)-1,
                  armed_markers=markers, FAT_clean=True, one_shot_verified=True)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('qualify', 'stage', 'verify'))
    parser.add_argument('path', type=Path, help='qualified runner ELF for qualify, prior archive otherwise')
    args = parser.parse_args()
    path = args.path.resolve()
    if args.operation == 'qualify':
        qualify(path)
    else:
        assert os.name == 'nt' and path.is_relative_to(ROOT/'device-evidence')
        card = Path('I:/').resolve()
        assert str(card).lower() in ('i:/', 'i:\\')
        inventory = raster.archived_inventory(path)
        (stage if args.operation == 'stage' else verify)(card, path, inventory)
