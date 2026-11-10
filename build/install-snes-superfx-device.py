"""Arm or independently verify the Super FX timing package on I:."""
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys

from attempt_archive import digest


raster = import_module('install-snes-raster-device')
ROOT, MVP, FROZEN, INIT = raster.ROOT, raster.MVP, raster.FROZEN, raster.INIT
fix = raster.fix
TARGET = 'retro/snes-superfx-test1'
BASELINE = 'retro/snes-raster-test1/cores/raster-offset-full.so'
OUT = ROOT/'build/superfx-device-private-v1'
EVIDENCE = ROOT/'evidence/2026-11-10/snes-raster-batches'
INSTALLATION = 'superfx-device-installation.json'
LIVE = 'superfx-device-live-verification.json'


def stage(card, archive, inventory):
    assert not fix.git('status', '--porcelain')
    commit = fix.git('rev-parse', 'HEAD')
    assert commit == fix.git('rev-parse', 'origin/codex/snes-mvp-foundation')
    qualified = json.loads((OUT/'qualification.json').read_text())
    assert qualified['measurement_only'] and not qualified['physical']
    assert set(qualified['pairs']) == {'fx-batch', 'fx-batch-toggle'}
    assert set(qualified['wrapper_cases']) == {'normal', 'mismatch', 'splash-busy', 'unarmed'}
    assert qualified['frozen_receipt_sha256'] == digest(raster.FROZEN_RECEIPT)
    assert qualified['superfx_evidence_sha256'] == digest(EVIDENCE/'superfx-experiment.json')
    for name, sha in qualified['sources'].items():
        assert digest(ROOT/'build'/name) == sha, name
    for name, sha in qualified['payloads'].items():
        assert digest(OUT/name) == sha, name
    previous = json.loads((EVIDENCE/'device-installation.json').read_text())
    assert inventory[MVP+'/launch.sh'] == previous['dispatch_sha256']
    assert inventory['retro/init'] == INIT
    assert inventory[BASELINE] == qualified['baseline_sha256']
    pinned = json.loads(raster.FROZEN_RECEIPT.read_text())['payload_hashes']
    for name, sha in pinned.items():
        if name.startswith('cases/003/'):
            assert inventory[FROZEN+'/'+name] == sha
    raster.verify_inventory(card, inventory)
    health = lambda label: fix.health(archive, 'superfx-device-'+label)
    health('before')
    payload = {n: (OUT/n).read_bytes() for n in [*qualified['payloads'], 'qualification.json']}
    payload['previous-launch.sh'] = (card/MVP/'launch.sh').read_bytes()
    payload_hashes = {n: sha256(data).hexdigest() for n, data in payload.items()}
    dispatch = f'#!/bin/sh\nexec /bin/sh /usr/{TARGET}/launch.sh superfx\n'.encode()
    marker = f'D-R35 core-only A7 Super FX measurement once {commit}\n'.encode()
    with_payload = {**inventory, **{TARGET+'/'+n: sha for n, sha in payload_hashes.items()}}
    raster.activate(card, payload, dispatch, marker,
                    lambda: raster.verify_inventory(card, with_payload), health, target_path=TARGET)
    receipt = {
        'source_commit': commit, 'target': TARGET, 'measurement_only': True,
        'physical_result': 'PENDING', 'pairs_armed': 2, 'prior_archive': archive.name,
        'prior_files': len(inventory), 'baseline_path': BASELINE, 'baseline_sha256': inventory[BASELINE],
        'dispatch_sha256': sha256(dispatch).hexdigest(), 'marker_sha256': sha256(marker).hexdigest(),
        'payload_hashes': payload_hashes, 'normal_init_sha256': INIT,
        'qualification_sha256': digest(OUT/'qualification.json'),
        'new_device_firmware': False, 'full_backup_created': False,
    }
    (archive/INSTALLATION).write_text(json.dumps(receipt, indent=2)+'\n')


def verify(card, archive, inventory):
    receipt = json.loads((archive/INSTALLATION).read_text())
    markers = [MVP+'/armed', TARGET+'/armed']
    expected = {**inventory, MVP+'/launch.sh': receipt['dispatch_sha256']}
    expected.update({TARGET+'/'+n: h for n, h in receipt['payload_hashes'].items()})
    expected.update({n: receipt['marker_sha256'] for n in markers})
    raster.verify_inventory(card, expected)
    assert sorted(p.relative_to(card).as_posix() for p in card.rglob('armed')) == sorted(markers)
    assert not list(card.rglob('Code.bkp')) and digest(card/'retro/init') == INIT
    fix.health(archive, 'superfx-device-independent')
    result = {**receipt, 'exact_card_files': len(expected), 'protected_existing_files': len(inventory)-1,
              'armed_markers': markers, 'FAT_clean': True, 'one_shot_verified': True}
    text = json.dumps(result, indent=2)+'\n'
    (archive/LIVE).write_text(text)
    print(text)


if __name__ == '__main__':
    archive = Path(sys.argv[1]).resolve()
    assert archive.is_relative_to(ROOT/'device-evidence')
    card = Path('I:/').resolve()
    assert str(card).lower() in ('i:/', 'i:\\')
    inventory = raster.archived_inventory(archive)
    if sys.argv[2:] == ['--verify']:
        verify(card, archive, inventory)
    else:
        assert len(sys.argv) == 2
        stage(card, archive, inventory)
