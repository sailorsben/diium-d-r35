"""Stage and verify the one-shot, core-only A7 raster measurement on I:."""
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from attempt_archive import digest, verify_saved


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT/'build/raster-device-private-v1'
TARGET = 'retro/snes-raster-test1'
MVP = 'retro/snes-mvp'
FROZEN = 'retro/snes-fivegame-kernel2'
INIT = 'b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
FROZEN_RECEIPT = ROOT/'evidence/2026-10-17/fivegame-replay/qualification.json'
RASTER = ROOT/'evidence/2026-11-10/snes-raster-batches/analysis.json'
fix = import_module('install-uart-fix')


def card_files(card):
    return {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}


def verify_inventory(card, inventory):
    assert card_files(card) == set(inventory)
    for name, sha in inventory.items():
        assert digest(card/name) == sha, name


def activate(card, payload, dispatch, marker, verify_payload, health, inject=lambda _: None):
    target, launcher = card/TARGET, card/MVP/'launch.sh'
    markers = [target/'armed', card/MVP/'armed']
    previous = launcher.read_bytes()
    assert not target.exists() and not list(card.rglob('armed')) and not list(card.rglob('Code.bkp'))
    target.mkdir()
    try:
        for name, data in payload.items():
            path = Path(name)
            assert not path.is_absolute() and '..' not in path.parts
            p = target/path
            p.parent.mkdir(parents=True, exist_ok=True)
            fix.atomic(p, data)
        verify_payload()
        health('payload')
        fix.atomic(launcher, dispatch)
        inject('dispatcher')
        for p in markers:
            fix.atomic(p, marker)
            inject(p.parent.name)
        health('armed')
    except BaseException:
        # Remove only markers from this attempt and restore the exact dispatcher.
        health('before-rollback')
        for p in reversed(markers):
            if p.exists():
                assert p.read_bytes() == marker
                p.unlink()
        assert launcher.read_bytes() in (dispatch, previous)
        if launcher.read_bytes() != previous:
            fix.atomic(launcher, previous)
        raise


def self_test():
    for fail in (None, 'dispatcher', 'snes-raster-test1', 'snes-mvp'):
        with TemporaryDirectory() as temp:
            card = Path(temp)
            launcher = card/MVP/'launch.sh'
            launcher.parent.mkdir(parents=True)
            launcher.write_bytes(b'old')

            def inject(step):
                if step == fail:
                    raise RuntimeError(step)

            try:
                activate(card, {'pair': b'test'}, b'new', b'once', lambda: None,
                         lambda _: None, inject)
            except RuntimeError:
                assert fail and launcher.read_bytes() == b'old' and not list(card.rglob('armed'))
            else:
                assert not fail and launcher.read_bytes() == b'new' and len(list(card.rglob('armed'))) == 2
    print('PASS staging success and rollback at three activation boundaries')


def archived_inventory(archive):
    a = json.loads((archive/'archive.json').read_text())
    o = json.loads((archive/'outside-retro.json').read_text())
    assert a['fat_clean'] and a['card_writes'] == o['card_writes'] == 0
    verify_saved(archive, a)
    verify_saved(archive, {'schema': o['schema'], 'all_retro_files': o['files']})
    return {e['path']: e['sha256'] for e in a['all_retro_files']+o['files']}


def stage(card, archive, inventory):
    assert not fix.git('status', '--porcelain')
    commit = fix.git('rev-parse', 'HEAD')
    assert commit == fix.git('rev-parse', 'origin/codex/snes-mvp-foundation')
    q = json.loads((OUT/'qualification.json').read_text())
    assert q['measurement_only'] and not q['production_gate'] and not q['device_execution']
    assert len(q['pairs']) == 12 and len(q['wrapper_cases']) == 4
    assert q['frozen_receipt_sha256'] == digest(FROZEN_RECEIPT)
    assert q['raster_receipt_sha256'] == digest(RASTER)
    for name, sha in q['sources'].items():
        assert digest(ROOT/'build'/name) == sha, name
    for name, sha in q['payloads'].items():
        assert digest(OUT/name) == sha, name
    pinned = json.loads(FROZEN_RECEIPT.read_text())['payload_hashes']
    for name, sha in pinned.items():
        if name == 'plus-a7.so' or name.startswith('cases/'):
            assert inventory[FROZEN+'/'+name] == sha, name
    assert inventory['retro/init'] == INIT
    assert inventory[MVP+'/launch.sh'] == sha256(
        f'#!/bin/sh\nexec /bin/sh /usr/{FROZEN}/launch.sh\n'.encode()).hexdigest()
    verify_inventory(card, inventory)
    health = lambda label: fix.health(archive, 'raster-device-'+label)
    health('before')
    payload = {n: (OUT/n).read_bytes() for n in [*q['payloads'], 'qualification.json']}
    payload['previous-launch.sh'] = (card/MVP/'launch.sh').read_bytes()
    payload_hashes = {n: sha256(b).hexdigest() for n, b in payload.items()}
    dispatch = f'#!/bin/sh\nexec /bin/sh /usr/{TARGET}/launch.sh\n'.encode()
    marker = f'D-R35 core-only A7 raster measurement once {commit}\n'.encode()
    new_files = {TARGET+'/'+n: sha for n, sha in payload_hashes.items()}
    activate(card, payload, dispatch, marker,
             lambda: verify_inventory(card, {**inventory, **new_files}), health)
    receipt = {
        'source_commit': commit, 'target': TARGET, 'measurement_only': True,
        'physical_result': 'PENDING', 'pairs_armed': 12, 'candidate_cores_staged': 6,
        'prior_archive': archive.name, 'prior_files': len(inventory),
        'dispatch_sha256': sha256(dispatch).hexdigest(), 'marker_sha256': sha256(marker).hexdigest(),
        'payload_hashes': payload_hashes, 'normal_init_sha256': INIT,
        'qualification_sha256': digest(OUT/'qualification.json'),
        'new_device_firmware': False, 'full_backup_created': False,
    }
    (archive/'raster-device-installation.json').write_text(json.dumps(receipt, indent=2)+'\n')


def verify(card, archive, inventory):
    receipt = json.loads((archive/'raster-device-installation.json').read_text())
    markers = [MVP+'/armed', TARGET+'/armed']
    expected = dict(inventory)
    expected[MVP+'/launch.sh'] = receipt['dispatch_sha256']
    expected.update({TARGET+'/'+n: h for n, h in receipt['payload_hashes'].items()})
    expected.update({n: receipt['marker_sha256'] for n in markers})
    verify_inventory(card, expected)
    assert sorted(p.relative_to(card).as_posix() for p in card.rglob('armed')) == sorted(markers)
    assert not list(card.rglob('Code.bkp')) and digest(card/'retro/init') == INIT
    fix.health(archive, 'raster-device-independent')
    result = {**receipt, 'exact_card_files': len(expected), 'protected_existing_files': len(inventory)-1,
              'armed_markers': markers, 'FAT_clean': True, 'one_shot_verified': True}
    text = json.dumps(result, indent=2)+'\n'
    (archive/'raster-device-live-verification.json').write_text(text)
    print(text)


if __name__ == '__main__':
    if sys.argv[1:] == ['--self-test']:
        self_test()
    else:
        archive = Path(sys.argv[1]).resolve()
        assert archive.is_relative_to(ROOT/'device-evidence')
        card = Path('I:/').resolve()
        assert str(card).lower() in ('i:/', 'i:\\')
        inventory = archived_inventory(archive)
        if sys.argv[2:] == ['--verify']:
            verify(card, archive, inventory)
        else:
            assert len(sys.argv) == 2
            stage(card, archive, inventory)
