"""Build and arm the isolated Star Fox LCD/PCM measurement on I:."""
import argparse
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path
import shutil
import subprocess

from attempt_archive import digest, verify_saved


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT/'build/stock-shell-display-private-v2'
TARGET = 'retro/snes-shell-display1'
FIXTURES = 'retro/snes-fivegame-kernel2'
CORE = '0974965d71640d391cb5fdbc3f474d5056b72ae834a2fe8c6b8e66600a39cf86'
STOCK = '8e5c3185244b3a1ca50f377728a0af6ad5e808c09db9d1749d1183014b8ade72'
FIXTURE_FILES = [f'cases/003/{name}' for name in ('game.sfc', 'warmup.txt', 'input.txt', 'expected.bin')]
RECEIPT = 'stock-shell-display-installation.json'
SUPERVISOR = import_module('install-snes-raster-device')
BOOT = SUPERVISOR.MVP+'/launch.sh'
FILES = ('display-runner', 'plus-a7.so', 'launch.sh')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')


def prepare(source, core):
    assert os.name == 'posix' and digest(core) == CORE
    assert digest(source/'candidate') == '4dbcf3269eaa4f02256af6d67c16ca2c1cf4a2f70136215f09b985842d7be767'
    prepare_reuse = import_module('prepare-snes-native-reuse')
    prepare_reuse.prepare(source, OUT)
    main = OUT/'main.c'
    text = main.read_text()
    point = ' unsigned count=0,failed=0,limit='
    text = prepare_reuse.replace_once(text, point, ' const char *fixtures=getenv("D35_DISPLAY_FIXTURES");\n'
                                     ' if(!fixtures || !*fixtures)fixtures=argv[3];\n'+point)
    for filename in ('scene.state', 'input.txt', 'expected.bin', 'game.sfc', 'warmup.txt'):
        text = prepare_reuse.replace_once(text, f'/cases/%03u/{filename}",argv[3]',
                                         f'/cases/%03u/{filename}",fixtures')
    main.write_text(text, encoding='utf-8', newline='\n')
    subprocess.run(['sh', 'build/check-snes-native-reuse.sh', OUT], cwd=ROOT, check=True)
    (OUT/'candidate').rename(OUT/'display-runner')
    shutil.copyfile(core, OUT/'plus-a7.so')
    shutil.copyfile(ROOT/'build/launch-stock-shell-display-test.sh', OUT/'launch.sh')
    busybox = ROOT/'build/uart-fix-private/firmware-busybox'
    subprocess.run(['qemu-arm', '-0', 'busybox', '-L', ROOT/'build/sysroot', busybox,
                    'sh', '-n', OUT/'launch.sh'], check=True)
    fixture = ROOT/'build/fivegame-kernel-private-v2'
    pinned = read_json(SUPERVISOR.FROZEN_RECEIPT)['payload_hashes']
    for name in FIXTURE_FILES:
        assert digest(fixture/name) == pinned[name], name
    for label, mode in [('control', '0'), ('reuse', '1')]:
        result = OUT/label
        result.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith('D35_')}
        env.update(D35_ABILITY_MOCK='1', D35_MVP_NO_PACING='1', D35_FULL_HOST_FIXTURE='1',
                   D35_FIVE_ORACLE='1', D35_IDENTICAL_VIDEO_REUSE=mode, D35_MEASURE_DISPLAY='1',
                   D35_DISPLAY_FIXTURES=str(fixture))
        with (OUT/f'{label}.log').open('w') as log:
            subprocess.run(['qemu-arm', '-cpu', 'cortex-a7', '-L', ROOT/'build/sysroot',
                            '-E', f'LD_LIBRARY_PATH={ROOT / "build/sysroot/lib"}', OUT/'display-runner',
                            '--supervise', result, OUT, 'unused'], env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=420)
        trace = result/'run-000'
        assert '#oracle_checks=1200' in (trace/'input.csv').read_text()
        assert 'cold_boot_calls=8656' in (trace/'warmup.txt').read_text()
        assert 'final_PCM_software_accounting_exact=1' in (trace/'headroom.txt').read_text()
        assert 'reaped=1\nforced=0' in (result/'supervisor.txt').read_text()
    sources = [Path(__file__), ROOT/'build/launch-stock-shell-display-test.sh',
               ROOT/'build/prepare-snes-native-reuse.py', ROOT/'build/check-snes-native-reuse.sh']
    write_json(OUT/'qualification.json', dict(measurement_only=True, hardware_runs=0, frameskip=0,
               replay_oracle_calls=2400, payloads={name: digest(OUT/name) for name in FILES},
               sources={p.relative_to(ROOT).as_posix(): digest(p) for p in sources},
               fixtures={name: pinned[name] for name in FIXTURE_FILES}))
    print('PASS board reuse fixture, firmware shell syntax and both supervised replay oracles')


def health(archive, label):
    SUPERVISOR.fix.health(archive, 'shell-display-'+label)
    checked = subprocess.run(['fsutil', 'dirty', 'query', 'I:'], capture_output=True, text=True, check=True)
    (archive/f'fsutil-shell-display-{label}.txt').write_text(checked.stdout, encoding='utf-8')
    assert 'is not dirty' in checked.stdout.lower(), checked.stdout


def card_state(archive):
    original = read_json(archive/'archive.json')
    outside = read_json(archive/'outside-retro.json')
    assert original['card_writes'] == outside['card_writes'] == 0
    verify_saved(archive, original)
    verify_saved(archive, {'schema': outside['schema'], 'all_retro_files': outside['files']})
    return {row['path']: row['sha256'] for row in original['all_retro_files']+outside['files']}


def stage(card, archive):
    inventory = card_state(archive)
    qualification = read_json(OUT/'qualification.json')
    assert qualification['measurement_only'] and qualification['hardware_runs'] == 0
    assert qualification['replay_oracle_calls'] == 2400 and qualification['frameskip'] == 0
    for name, checksum in qualification['sources'].items():
        assert digest(ROOT/name) == checksum, name
    for name, checksum in qualification['fixtures'].items():
        assert inventory[FIXTURES+'/'+name] == checksum, name
    assert inventory['retro/init'] == SUPERVISOR.INIT and inventory['retro/vrtemu'] == STOCK
    assert inventory[BOOT] == sha256(b'#!/bin/sh\nexec /bin/sh /usr/retro/snes-superfx-native1/launch.sh\n').hexdigest()
    git = SUPERVISOR.fix.git
    assert not git('status', '--porcelain')
    commit = git('rev-parse', 'HEAD')
    assert commit == git('rev-parse', 'origin/codex/snes-mvp-foundation')
    SUPERVISOR.verify_inventory(card, inventory)
    health(archive, 'before')
    payload = {name: (OUT/name).read_bytes() for name in FILES}
    assert {name: sha256(data).hexdigest() for name, data in payload.items()} == qualification['payloads']
    payload['previous-launch.sh'] = (card/BOOT).read_bytes()
    payload['qualification.json'] = (OUT/'qualification.json').read_bytes()
    dispatch = f'#!/bin/sh\nexec /bin/sh /usr/{TARGET}/launch.sh\n'.encode()
    marker = f'stock-shell-display1 {commit}\n'.encode()
    hashes = {name: sha256(data).hexdigest() for name, data in payload.items()}
    expected = {**inventory, **{TARGET+'/'+name: checksum for name, checksum in hashes.items()}}
    SUPERVISOR.activate(card, payload, dispatch, marker,
                        lambda: SUPERVISOR.verify_inventory(card, expected),
                        lambda label: health(archive, label), target_path=TARGET)
    write_json(archive/RECEIPT, dict(commit=commit, target=TARGET, physical_result='pending',
               measurement_only=True, production_gate=False, prototype_installed=False,
               core_sha256=CORE, payload_hashes=hashes, original_files=len(inventory),
               dispatcher_sha256=sha256(dispatch).hexdigest(), marker_sha256=sha256(marker).hexdigest()))


def verify(card, archive):
    receipt = read_json(archive/RECEIPT)
    expected = card_state(archive)
    expected.update({TARGET+'/'+name: checksum for name, checksum in receipt['payload_hashes'].items()})
    markers = (TARGET+'/armed', SUPERVISOR.MVP+'/armed')
    expected.update(dict.fromkeys(markers, receipt['marker_sha256']))
    expected[BOOT] = receipt['dispatcher_sha256']
    SUPERVISOR.verify_inventory(card, expected)
    assert sorted(p.relative_to(card).as_posix() for p in card.rglob('armed')) == sorted(markers)
    assert not list(card.rglob('Code.bkp'))
    health(archive, 'readback')
    print(json.dumps(dict(**receipt, verified_files=len(expected), clean_fat=True, armed=markers), indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('prepare', 'stage', 'verify'))
    parser.add_argument('path', type=Path)
    parser.add_argument('--core', type=Path)
    args = parser.parse_args()
    path = args.path.resolve()
    if args.operation == 'prepare':
        prepare(path, args.core.resolve())
    else:
        card = Path('I:/').resolve()
        assert os.name == 'nt' and str(card).lower() in ('i:/', 'i:\\')
        assert path.is_relative_to(ROOT/'device-evidence')
        (stage if args.operation == 'stage' else verify)(card, path)


if __name__ == '__main__':
    main()
