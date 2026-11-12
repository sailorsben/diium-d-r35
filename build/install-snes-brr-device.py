"""Qualify, archive, arm and verify the one-shot five-game BRR measurement."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory

from attempt_archive import digest, inventory, write_manifest


raster = import_module('install-snes-raster-device')
replay = import_module('check-snes-raster-device')
ROOT, MVP, FROZEN, INIT = raster.ROOT, raster.MVP, raster.FROZEN, raster.INIT
OUT = ROOT / 'build/brr-device-private-v1'
TARGET = 'retro/snes-brr-test1'
CURRENT = 'retro/d35-launcher1/libs/d35-snes.so'
CURRENT_SHA = '70d885151b7d3cac05ae69fc9653974c420b49d5cb20f95b09af547f319a8936'
PRIOR_DISPATCH = 'f8d3acb00e8a5506a2f885b57d63010f35cd8983668a41ae5c274eeaf2bd8244'
LAUNCHER_MARKER = 'retro/d35-launcher1/armed'
MARKERS = (MVP + '/armed', TARGET + '/armed')
MATRIX = [(game, arm) for game in ('000', '001', '002', '004', '003') for arm in ('auto', 'off')]
WRAPPER_CASES = ('normal', 'mismatch', 'splash-busy', 'unarmed')
SOURCES = ('build-snes-core-pgo.sh', 'snes-brr-adaptive.h', 'prepare-snes-brr-adaptive.py',
           'snes-throughput-pair.c', 'snes-throughput-replay.c', 'build-snes-raster-device.sh',
           'snes-raster-device-launch.sh', 'check-snes-raster-device.py',
           'install-snes-raster-device.py', 'attempt_archive.py', Path(__file__).name)


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def fixtures():
    return {name: h for name, h in read(raster.FROZEN_RECEIPT)['payload_hashes'].items()
            if name.startswith('cases/')}


def pair_args(game, arm, lab=OUT, frozen=replay.FROZEN):
    warm = game == '003'
    mode = 'brr-toggle-device' if arm == 'auto' else 'brr-disabled-device'
    control = 'off' if arm == 'auto' else 'current'
    return [lab/'cores'/f'{control}.so', lab/'cores'/f'{arm}.so', frozen/'cases'/game,
            '8656' if warm else '0', ('both-cold-off-' if warm else '') + mode]


def check_pair(csv, log, reference, arm, game):
    lines = csv.read_text().splitlines()
    assert len(lines) == 1205 and lines[0].startswith('cold,')
    assert lines[-4] == 'published,1200,1200' and lines[-2].startswith('brr ')
    assert lines[-3] == f"audio,{reference['audio_frames']},{reference['audio_frames']}"
    layout = reference['callback_layout_crc32']
    assert lines[-1] == f'oracle,1200,1200,{layout},{layout}'
    progress = log.read_text().splitlines()
    assert progress[-1] == 'gameplay_calls_per_arm=1200'
    if game == '003':
        assert 'cold_calls_per_arm=8656 gameplay_started' in progress
    last = (0, 0, 0, 0)
    for tick, line in enumerate(lines[1:1201]):
        frame, a, b, wa, wb, oa, ob, *stats = map(int, line.split(','))
        assert frame == tick and 0 <= oa < a and 0 <= ob < b and wa > 0 and wb > 0
        assert len(stats) == 4 and all(n >= p for n, p in zip(stats, last))
        assert stats[2] - last[2] in (0, 1)
        last = stats
    total = {k: int(v) for k, v in (s.split('=') for s in lines[-2].split()[1:])}
    assert list(last) == [total[k] for k in ('probes', 'passes', 'active_ticks', 'profile_cpu_ns')]
    if arm == 'off':
        assert not any(total.values()), total
    return dict(game=game, arm=arm, oracle_ticks_per_arm=1200, callback_layout=layout,
                profile=total, csv_sha256=digest(csv), log_sha256=digest(log))


def qualify(training):
    candidate = training/'core/snes9x2005_plus_libretro.so'
    current = ROOT/'build/starfox-150-private-v1/plus-a7.so'
    assert digest(current) == CURRENT_SHA and digest(candidate) != CURRENT_SHA
    for game in ('000', '001', '003'):
        assert 'verified=1200 mismatched=0' in (training/f'train-{game}.log').read_text()
    assert '-fprofile-use' in (training/'use.log').read_text()
    assert 'brr_trial_pass' in (training/'core/source/snes-brr-adaptive.h').read_text()
    assert digest(training/'core/source/snes-brr-adaptive.h') == digest(ROOT/'build/snes-brr-adaptive.h')
    for name, h in fixtures().items():
        assert digest(replay.FROZEN/name) == h, name
    subprocess.run(['sh', 'build/build-snes-raster-device.sh', OUT], cwd=ROOT, check=True)
    (OUT/'cores').mkdir()
    for name, path in (('current', current), ('auto', candidate), ('off', candidate)):
        shutil.copyfile(path, OUT/'cores'/f'{name}.so')
    for path in [OUT/'pair', *sorted((OUT/'cores').glob('*.so'))]:
        versions = subprocess.check_output(['arm-linux-gnueabihf-readelf', '-V', path], text=True)
        imports = re.findall(r'GLIBC_(\d+)\.(\d+)', versions)
        assert imports and all(tuple(map(int, v)) <= (2, 30) for v in imports)
    with TemporaryDirectory() as temp:
        tmp = Path(temp)
        (tmp/'bin').mkdir()
        for name in ('sleep', 'sync'):
            path = tmp/'bin'/name
            path.write_text('#!/bin/sh\nexit 0\n')
            path.chmod(0o755)
        for case in WRAPPER_CASES:
            matrix = replay.wrapper_check(tmp, case, out=OUT, profile='brr')
            assert matrix == {'normal': MATRIX, 'mismatch': MATRIX[:1],
                              'splash-busy': [], 'unarmed': []}[case]
        lab = tmp/'brr-normal'
        run, = (lab/'results').glob('run-*')
        for game, arm in MATRIX:
            assert (run/f'{game}-{arm}.csv').read_text().splitlines() == [
                str(p) for p in pair_args(game, arm, lab, Path('/usr')/FROZEN)]

    refs = {row['game']: row for row in read(replay.RASTER)['verified_replays'] if row['core'] == 'physical'}
    results = OUT/'mock-pairs'
    results.mkdir()

    def check(row):
        game, arm = row
        csv = results/f'{game}-{arm}.csv'
        log = csv.with_suffix('.log')
        with csv.open('w') as data, log.open('w') as trace:
            subprocess.run([*replay.QEMU, '-E', 'LD_LIBRARY_PATH=build/sysroot/lib', OUT/'pair',
                            *pair_args(game, arm)], cwd=ROOT, stdout=data, stderr=trace,
                           check=True, timeout=420)
        result = check_pair(csv, log, refs[int(game)], arm, game)
        print(game, arm, 'verified', flush=True)
        return result

    # Start both long Star Fox warmups alongside the short cases.
    with ThreadPoolExecutor(max_workers=6) as pool:
        pairs = list(pool.map(check, reversed(MATRIX)))
    write(OUT/'qualification.json', dict(measurement_only=True, device_execution=False,
        previous_core_sha256=CURRENT_SHA, candidate_core_sha256=digest(candidate),
        frozen_receipt_sha256=digest(raster.FROZEN_RECEIPT), wrapper_cases=WRAPPER_CASES,
        pairs=pairs, payloads={name: digest(OUT/name) for name in
                              ('pair', 'launch.sh', 'cores/current.so', 'cores/auto.so', 'cores/off.so')},
        sources={name: digest(ROOT/'build'/name) for name in SOURCES}))


def archive_card(card):
    assert digest(card/'retro/init') == INIT and digest(card/CURRENT) == CURRENT_SHA
    assert not any(card.rglob('Code.bkp'))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    archive = ROOT/'device-evidence'/f'brr-device-before-{stamp}'
    archive.mkdir()
    raster.fix.health(archive, 'brr-archive')
    retro = inventory(card, archive)
    outside = inventory(card, archive, outside=True)
    write_manifest(archive/'archive.json', retro, card='I:', all_retro_files=retro, card_writes=0, fat_clean=True)
    write_manifest(archive/'outside-retro.json', outside, files=outside, card_writes=0)
    for name in ('retro/recent.lst', MVP+'/launch.sh', MVP+'/armed', LAUNCHER_MARKER):
        if (card/name).is_file():
            path = archive/'boot-context'/name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(card/name, path)
            assert digest(path) == digest(card/name)
    raster.archived_inventory(archive)
    print(archive)


def stage(card, archive):
    before = raster.archived_inventory(archive)
    q = read(OUT/'qualification.json')
    assert q['measurement_only'] and not q['device_execution']
    assert {(p['game'], p['arm']) for p in q['pairs']} == set(MATRIX)
    assert set(q['wrapper_cases']) == set(WRAPPER_CASES)
    assert q['frozen_receipt_sha256'] == digest(raster.FROZEN_RECEIPT)
    for name, h in q['sources'].items():
        assert digest(ROOT/'build'/name) == h, name
    for name, h in q['payloads'].items():
        assert digest(OUT/name) == h, name
    assert q['payloads']['cores/current.so'] == CURRENT_SHA
    assert q['payloads']['cores/off.so'] == q['payloads']['cores/auto.so'] == q['candidate_core_sha256']
    for name, h in fixtures().items():
        assert before[FROZEN+'/'+name] == h, name
    assert before['retro/init'] == INIT and before[CURRENT] == CURRENT_SHA
    assert before[MVP+'/launch.sh'] == PRIOR_DISPATCH
    assert not any(card.rglob('Code.bkp')) and not (card/TARGET).exists()
    raster.verify_inventory(card, before)
    commit = raster.fix.git('rev-parse', 'HEAD')
    assert not raster.fix.git('status', '--porcelain')
    assert commit == raster.fix.git('rev-parse', 'origin/codex/snes-mvp-foundation')
    health = lambda label: raster.fix.health(archive, 'brr-'+label)
    health('before')

    armed = {p.relative_to(card).as_posix() for p in card.rglob('armed')}
    assert armed in (set(), {MVP+'/armed', LAUNCHER_MARKER}), armed
    prior = {name: (archive/'boot-context'/name).read_bytes() for name in armed}
    if prior:
        assert prior[MVP+'/armed'] == prior[LAUNCHER_MARKER]
        assert re.fullmatch(rb'd35-launcher1 [0-9a-f]{40}\n', prior[LAUNCHER_MARKER])
        assert all(digest(card/name) == sha256(data).hexdigest() == before[name] for name, data in prior.items())
    payload = {name: (OUT/name).read_bytes() for name in (*q['payloads'], 'qualification.json')}
    payload['previous-launch.sh'] = (card/MVP/'launch.sh').read_bytes()
    hashes = {name: sha256(data).hexdigest() for name, data in payload.items()}
    dispatch = f'#!/bin/sh\nexec /bin/sh /usr/{TARGET}/launch.sh brr\n'.encode()
    marker = f'D-R35 core-only A7 BRR measurement once {commit}\n'.encode()
    expected = {name: h for name, h in before.items() if name not in prior}
    expected.update({TARGET+'/'+name: h for name, h in hashes.items()})
    try:
        for name in (MVP+'/armed', LAUNCHER_MARKER):
            if name in prior:
                (card/name).unlink()
        raster.activate(card, payload, dispatch, marker, lambda: raster.verify_inventory(card, expected),
                        health, target_path=TARGET)
    except BaseException:
        assert digest(card/MVP/'launch.sh') == PRIOR_DISPATCH
        for name in (LAUNCHER_MARKER, MVP+'/armed'):
            if name in prior and not (card/name).exists():
                raster.fix.atomic(card/name, prior[name])
        raise
    write(archive/'brr-installation.json', dict(source_commit=commit, target=TARGET, measurement_only=True,
        physical_result='pending', pairs_armed=10, prior_archive=archive.name, prior_files=len(before),
        superseded_markers=sorted(prior), payload_hashes=hashes, dispatch_sha256=sha256(dispatch).hexdigest(),
        marker_sha256=sha256(marker).hexdigest(), full_backup_created=False))


def verify(card, archive):
    before = raster.archived_inventory(archive)
    receipt = read(archive/'brr-installation.json')
    expected = {name: h for name, h in before.items() if name not in receipt['superseded_markers']}
    expected.update({TARGET+'/'+name: h for name, h in receipt['payload_hashes'].items()})
    expected.update(dict.fromkeys(MARKERS, receipt['marker_sha256']))
    expected[MVP+'/launch.sh'] = receipt['dispatch_sha256']
    raster.verify_inventory(card, expected)
    assert {p.relative_to(card).as_posix() for p in card.rglob('armed')} == set(MARKERS)
    assert not any(card.rglob('Code.bkp'))
    raster.fix.health(archive, 'brr-independent')
    result = dict(**receipt, exact_card_files=len(expected), FAT_clean=True, armed_markers=MARKERS,
                  verified_unchanged_prior_files=sum(expected.get(name) == h for name, h in before.items()))
    write(archive/'brr-readback.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('qualify', 'archive', 'stage', 'verify'))
    parser.add_argument('path', type=Path, nargs='?')
    args = parser.parse_args()
    if args.action == 'qualify':
        qualify(args.path.resolve())
    else:
        card = Path('I:/').resolve()
        assert os.name == 'nt' and str(card).lower() in ('i:/', 'i:\\')
        if args.action == 'archive':
            archive_card(card)
        else:
            path = args.path.resolve()
            assert path.is_relative_to(ROOT/'device-evidence')
            (stage if args.action == 'stage' else verify)(card, path)
