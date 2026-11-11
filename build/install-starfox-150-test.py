"""Prepare, arm and independently verify the one-shot Star Fox PCM test."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from importlib import import_module
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from attempt_archive import inventory, write_manifest


previous = import_module('install-stock-shell-display-test')
probe = import_module('prepare-snes-pcm-audit')
ROOT, SUP = previous.ROOT, previous.SUPERVISOR
OUT = ROOT / 'build/starfox-150-private-v1'
TARGET = 'retro/snes-starfox-150'
RECEIPT = 'starfox-150-installation.json'
FILES = ('display-runner', 'plus-a7.so', 'launch.sh')
WINDOWS = ('pcm-cache', 'lcd-control', 'lcd-cache')
BASE = ROOT / 'evidence/2026-11-10/snes-throughput/stock-shell-display-installation.json'


def wrapper():
    path = ROOT / 'build/launch-stock-shell-display-test.sh'
    s = path.read_text()
    s = s.replace('snes-shell-display1', 'snes-starfox-150').replace('stock-shell-display1', 'starfox-150')
    s = probe.replace_once(s, 'shell-display-$$-$name', 'starfox-150-$$-$name')
    s = probe.replace_once(s, 'D35_IDENTICAL_VIDEO_REUSE="$3"',
                           'D35_IDENTICAL_VIDEO_REUSE=1 D35_AUDIT_MODE2_MEMO="$3" D35_PCM_DIAGNOSTIC_RESERVE=150')
    s = probe.replace_once(s, "printf 'begin %s pcm=%s reuse=%s\\n'", "printf 'begin %s silent=%s cache=%s\\n'")
    begin = s.index('run_window display-control')
    end = s.index("printf 'complete\\n'", begin)
    return s[:begin] + '''run_window pcm-cache 0 1
handle_result "$?"
run_window lcd-control 1 0
handle_result "$?" || exit 1
run_window lcd-cache 1 1
handle_result "$?" || exit 1
''' + s[end:]


def check_wrapper(launch):
    busybox = ROOT / 'build/uart-fix-private/firmware-busybox'
    shell = ['qemu-arm', '-0', 'busybox', '-L', ROOT / 'build/sysroot', busybox, 'sh']
    subprocess.run([*shell, '-n', launch], check=True)
    for rc, windows in ((0, WINDOWS), (1, WINDOWS), (5, WINDOWS[:1])):
        with TemporaryDirectory() as path:
            base = Path(path)
            lab, mvp, proc = (base / name for name in ('lab', 'mvp', 'proc'))
            for directory in (lab, mvp, proc):
                directory.mkdir()
            runner = lab / 'display-runner'
            runner.write_text('''#!/bin/sh
[ "$D35_PCM_DIAGNOSTIC_RESERVE" = 150 ] && [ "$D35_IDENTICAL_VIDEO_REUSE" = 1 ] || exit 72
[ ! -e "$D35_DISPLAY_LAB/armed" ] && [ ! -e "$D35_DISPLAY_MVP/armed" ] || exit 72
[ -f "$D35_DISPLAY_STOP" ] && [ -z "$D35_ABILITY_MOCK$D35_MVP_NO_PACING$D35_FIVE_ORACLE" ] || exit 72
printf '%s %s %s\\n' "${2##*/}" "$D35_MEASURE_DISPLAY" "$D35_AUDIT_MODE2_MEMO" >> "$D35_DISPLAY_LAB/calls"
[ "${2##*/}" != pcm-cache ] || exit "$PCM_RC"
''')
            runner.chmod(0o755)
            env = dict(os.environ, D35_DISPLAY_LAB=str(lab), D35_DISPLAY_MVP=str(mvp),
                       D35_DISPLAY_PROC=str(proc), D35_DISPLAY_STOP=str(base / 'stop'),
                       D35_ABILITY_MOCK='1', D35_MVP_NO_PACING='1', D35_FIVE_ORACLE='1', PCM_RC=str(rc))
            subprocess.run([*shell, launch], env=env, check=True, timeout=30)
            assert not (lab / 'calls').exists()
            for directory in (lab, mvp):
                (directory / 'armed').write_text('test\n')
            subprocess.run([*shell, launch], env=env, check=True, timeout=30)
            calls = (lab / 'calls').read_text().splitlines()
            assert calls == ['pcm-cache 0 1', 'lcd-control 1 0', 'lcd-cache 1 1'][:len(windows)]
            subprocess.run([*shell, launch], env=env, check=True, timeout=30)
            assert (lab / 'calls').read_text().splitlines() == calls


def build():
    subprocess.run(['sh', 'build/check-snes-pcm-audit.sh', OUT], cwd=ROOT, check=True)
    launch = OUT / 'launch.sh'
    launch.write_text(wrapper(), encoding='utf-8', newline='\n')
    check_wrapper(launch)
    (OUT / 'candidate').rename(OUT / 'display-runner')
    print('PASS PCM reserve, display ownership and exact firmware shell sequence')


def qualify(training):
    core = training / 'core/snes9x2005_plus_libretro.so'
    for game in ('000', '001', '003'):
        assert 'verified=1200 mismatched=0' in (training / f'train-{game}.log').read_text(), game
    assert 'Werror=coverage-mismatch' in (training / 'use.log').read_text()
    symbols = subprocess.check_output(['arm-linux-gnueabihf-nm', '-S', core], text=True)
    memo = [line.split() for line in symbols.splitlines() if ' d35_memo' in line]
    assert len(memo) == 1 and int(memo[0][1], 16) == 0x13b800
    assert ' d35_mode2_read' in symbols and ' d35_raster_set_enabled' in symbols
    pinned = previous.read_json(SUP.FROZEN_RECEIPT)['payload_hashes']
    fixture = ROOT / 'build/fivegame-kernel-private-v2'
    for name in previous.FIXTURE_FILES:
        assert previous.digest(fixture / name) == pinned[name], name
    shutil.copyfile(core, OUT / 'plus-a7.so')
    check_wrapper(OUT / 'launch.sh')

    def replay(cache):
        result = OUT / ('replay-cache' if cache else 'replay-control')
        result.mkdir(exist_ok=False)
        env = {k: v for k, v in os.environ.items() if not k.startswith('D35_')}
        env.update(D35_ABILITY_MOCK='1', D35_MVP_NO_PACING='1', D35_FULL_HOST_FIXTURE='1',
                   D35_FIVE_ORACLE='1', D35_IDENTICAL_VIDEO_REUSE='1', D35_MEASURE_DISPLAY='1',
                   D35_DISPLAY_FIXTURES=str(fixture), D35_AUDIT_MODE2_MEMO=str(cache),
                   D35_PCM_DIAGNOSTIC_RESERVE='150')
        with (result / 'console.log').open('w') as log:
            subprocess.run(['qemu-arm', '-cpu', 'cortex-a7', '-L', ROOT / 'build/sysroot',
                            '-E', f'LD_LIBRARY_PATH={ROOT / "build/sysroot/lib"}', OUT / 'display-runner',
                            '--supervise', result, OUT, 'unused'], env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=420)
        trace = result / 'run-000'
        assert '#oracle_checks=1200' in (trace / 'input.csv').read_text()
        assert 'cold_boot_calls=8656' in (trace / 'warmup.txt').read_text()
        assert 'final_PCM_software_accounting_exact=1' in (trace / 'headroom.txt').read_text()
        assert 'reaped=1\nforced=0' in (result / 'supervisor.txt').read_text()
        counts = trace / 'mode2-cache.txt'
        if cache:
            assert 'reused_rows=165006' in counts.read_text()
        else:
            assert not counts.exists()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(replay, (0, 1)))
    sources = (Path(__file__), ROOT / 'build/launch-stock-shell-display-test.sh',
               ROOT / 'build/check-snes-pcm-audit.sh', ROOT / 'build/prepare-snes-pcm-audit.py',
               ROOT / 'build/snes-mode2-dependencies.h', ROOT / 'build/prepare-snes-stack-audit.py',
               ROOT / 'build/build-snes-core-pgo.sh')
    previous.write_json(OUT / 'qualification.json', dict(measurement_only=True, physical_runs=0,
        entries=16, reserve_ms=150, prime_frames=6615, rate_hz=44100, windows=WINDOWS,
        replay_oracle_calls=2400, frameskip=0, payloads={name: previous.digest(OUT / name) for name in FILES},
        sources={p.relative_to(ROOT).as_posix(): previous.digest(p) for p in sources},
        fixtures={name: pinned[name] for name in previous.FIXTURE_FILES}))
    print('PASS exact 16-entry profile-guided core and both supervised Star Fox output checks')


def archive(card):
    assert previous.digest(card / 'retro/init') == SUP.INIT
    assert previous.digest(card / 'retro/vrtemu') == previous.STOCK
    assert not list(card.rglob('armed')) and not list(card.rglob('Code.bkp'))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = ROOT / 'device-evidence' / f'starfox-150-before-{stamp}'
    output.mkdir()
    previous.health(output, 'starfox-150-archive')
    retro = inventory(card, output)
    write_manifest(output / 'archive.json', retro, card='I:', all_retro_files=retro, card_writes=0, fat_clean=True)
    other = inventory(card, output, outside=True)
    write_manifest(output / 'outside-retro.json', other, card_writes=0, files=other)
    previous.card_state(output)
    print(output)


def stage(card, archive):
    inventory = previous.card_state(archive)
    q = previous.read_json(OUT / 'qualification.json')
    assert q['measurement_only'] and q['physical_runs'] == 0 and q['replay_oracle_calls'] == 2400
    assert (q['entries'], q['reserve_ms'], q['prime_frames'], q['frameskip']) == (16, 150, 6615, 0)
    assert tuple(q['windows']) == WINDOWS and (OUT / 'launch.sh').read_text() == wrapper()
    for name, checksum in q['sources'].items():
        assert previous.digest(ROOT / name) == checksum, name
    for name, checksum in q['fixtures'].items():
        assert inventory[previous.FIXTURES + '/' + name] == checksum, name
    assert inventory['retro/init'] == SUP.INIT and inventory['retro/vrtemu'] == previous.STOCK
    assert inventory[previous.BOOT] == previous.read_json(BASE)['dispatcher_sha256']
    git = SUP.fix.git
    assert not git('status', '--porcelain')
    commit = git('rev-parse', 'HEAD')
    assert commit == git('rev-parse', 'origin/codex/snes-mvp-foundation')
    SUP.verify_inventory(card, inventory)
    previous.health(archive, 'starfox-150-before')
    payload = {name: (OUT / name).read_bytes() for name in FILES}
    assert {name: sha256(data).hexdigest() for name, data in payload.items()} == q['payloads']
    payload['previous-launch.sh'] = (card / previous.BOOT).read_bytes()
    payload['qualification.json'] = (OUT / 'qualification.json').read_bytes()
    dispatch = f'#!/bin/sh\nexec /bin/sh /usr/{TARGET}/launch.sh\n'.encode()
    marker = f'starfox-150 {commit}\n'.encode()
    hashes = {name: sha256(data).hexdigest() for name, data in payload.items()}
    expected = {**inventory, **{TARGET + '/' + name: checksum for name, checksum in hashes.items()}}
    SUP.activate(card, payload, dispatch, marker, lambda: SUP.verify_inventory(card, expected),
                 lambda label: previous.health(archive, 'starfox-150-' + label), target_path=TARGET)
    previous.write_json(archive / RECEIPT, dict(commit=commit, target=TARGET, physical_result='pending',
        measurement_only=True, production_gate=False, original_files=len(inventory), windows=WINDOWS,
        entries=q['entries'], reserve_ms=q['reserve_ms'], prime_frames=q['prime_frames'], payload_hashes=hashes,
        dispatcher_sha256=sha256(dispatch).hexdigest(), marker_sha256=sha256(marker).hexdigest()))


def verify(card, archive):
    receipt = previous.read_json(archive / RECEIPT)
    expected = previous.card_state(archive)
    markers = (TARGET + '/armed', SUP.MVP + '/armed')
    expected.update({TARGET + '/' + name: checksum for name, checksum in receipt['payload_hashes'].items()})
    expected.update(dict.fromkeys(markers, receipt['marker_sha256']))
    expected[previous.BOOT] = receipt['dispatcher_sha256']
    SUP.verify_inventory(card, expected)
    assert sorted(p.relative_to(card).as_posix() for p in card.rglob('armed')) == sorted(markers)
    assert not list(card.rglob('Code.bkp'))
    previous.health(archive, 'starfox-150-readback')
    report = dict(**receipt, verified_files=len(expected), clean_fat=True, armed=markers)
    previous.write_json(archive / 'starfox-150-readback.json', report)
    print(f'PASS {len(expected)} files, clean FAT32, both one-shot markers, cache and 150 ms reserve')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('build', 'qualify', 'archive', 'stage', 'verify'))
    parser.add_argument('path', nargs='?', type=Path)
    args = parser.parse_args()
    if args.operation == 'build':
        build()
    elif args.operation == 'qualify':
        qualify(args.path.resolve())
    else:
        card = Path('I:/').resolve()
        assert os.name == 'nt' and str(card).lower() in ('i:/', 'i:\\')
        if args.operation == 'archive':
            archive(card)
        else:
            snapshot = args.path.resolve()
            assert snapshot.is_relative_to(ROOT / 'device-evidence')
            (stage if args.operation == 'stage' else verify)(card, snapshot)
