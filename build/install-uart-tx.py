"""Install only the qualified snapshot preflight on the designated I: card."""
from pathlib import Path
from hashlib import sha256
import importlib.util
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/uart-tx-private'
MARKER = b'UART TX1 reversible pending correction FIFO8 one-byte limit\n'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def health(archive, name):
    run = subprocess.run(['chkdsk', 'I:'], capture_output=True, text=True)
    (archive / name).write_text(run.stdout + run.stderr, encoding='utf-8')
    assert run.returncode == 0 and '11EB-1465' in run.stdout and 'Windows has scanned the file system and found no problems.' in run.stdout


def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to(ROOT / 'device-evidence')
    baseline = json.loads((archive / 'archive.json').read_text())
    q = json.loads((OUT / 'package-qualification.json').read_text())
    module_q = json.loads((OUT / 'qualification.json').read_text())
    assert baseline['fat_clean'] and baseline['card_writes'] == 0
    assert q['reversible_TX_correction'] and len(q['owner_checks']) == 21 and len(module_q['checks']) == 17
    assert not q['production_gate'] and not module_q['live_module_load_unload_qualified']
    assert digest(OUT / 'qualification.json') == q['compiled_module_qualification_sha256']
    for proof in [q, module_q]:
        for name, expected in proof['sources'].items():
            assert digest(ROOT / name) == expected, name
    for name, expected in q['payloads'].items():
        assert digest(OUT / 'package' / name) == expected, name
    assert not git('status', '--porcelain') and git('branch', '--show-current') == 'codex/snes-mvp-foundation'
    commit = git('rev-parse', 'HEAD')
    assert commit == git('rev-parse', 'origin/codex/snes-mvp-foundation')
    spec = importlib.util.spec_from_file_location('uart_card_guard', ROOT / 'build/package-snes-1.19.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    card = Path('I:/').resolve()
    assert str(card).lower() in ('i:/', 'i:\\')
    target = card / 'retro/uart-tx1'
    trigger = card / 'retro/snes-mvp'
    assert target.resolve().is_relative_to(card) and not target.exists()
    assert not list((card / 'retro').rglob('armed')) and not (card / 'retro/update/Code.bkp').exists()
    for entry in baseline['all_retro_files']:
        assert digest(card / entry['path']) == entry['sha256'], entry['path']
    for name, expected in guard.BOOT_EXPECTED.items():
        assert digest(card / name) == expected, name
    assert digest(card / 'retro/init') == guard.baseline.HOOK
    rom = card / '002/Final Fantasy VI.zip'
    rom_hash = digest(rom)
    assert rom_hash == 'f61af2bd9e3f9b6a2bd543fb176af0b81fd9e5ba4ea0fa0f453371ccb45d3911'
    health(archive, 'chkdsk-before-uart-tx.txt')
    protected = {e['path']: e['sha256'] for e in baseline['all_retro_files'] if e['path'] != 'retro/snes-mvp/launch.sh'}
    original = (trigger / 'launch.sh').read_bytes()
    payload = {n: (OUT / 'package' / n).read_bytes() for n in q['payloads'] if n != 'dispatch.sh'}
    payload['qualification.json'] = (OUT / 'package-qualification.json').read_bytes()
    assert shutil.disk_usage(card).free > sum(map(len, payload.values())) + 512 * 1024 * 1024
    created, dispatch = [], False
    target.mkdir()
    def verify():
        for name, expected in protected.items():
            assert digest(card / name) == expected, name
        for name, raw in payload.items():
            assert (target / name).read_bytes() == raw, name
        assert digest(rom) == rom_hash
    try:
        for name, raw in payload.items():
            path = target / name
            guard.atomic(path, raw, target)
            created.append(path)
        verify()
        health(archive, 'chkdsk-after-uart-tx-payload.txt')
        guard.atomic(trigger / 'launch.sh', (OUT / 'package/dispatch.sh').read_bytes(), trigger)
        dispatch = True
        guard.atomic(trigger / 'armed', MARKER, trigger)
        assert sorted(p.relative_to(card).as_posix() for p in (card / 'retro').rglob('armed')) == ['retro/snes-mvp/armed']
        assert (trigger / 'armed').read_bytes() == MARKER
        health(archive, 'chkdsk-after-uart-tx-arm.txt')
        verify()
    except Exception:
        health(archive, 'chkdsk-before-uart-tx-rollback.txt')
        marker = trigger / 'armed'
        if marker.exists():
            assert marker.read_bytes() == MARKER
            marker.unlink()
        if dispatch:
            guard.atomic(trigger / 'launch.sh', original, trigger)
        for path in reversed(created):
            assert path.resolve().is_relative_to(target.resolve())
            path.unlink()
        assert target.resolve().is_relative_to(card) and target.name == 'uart-tx1'
        target.rmdir()
        raise
    report = {'version': 'uart-tx1', 'source_commit': commit, 'archive': archive.name,
              'card': 'I:', 'one_shot_armed': True, 'clean_FAT': True,
              'protected_files': len(protected), 'reversible_TX_correction': True, 'physical_result': 'PENDING',
              'production_gate': False, 'ROM_unchanged': True, 'original_progress_unchanged': True,
              'payload_hashes': {n: sha256(raw).hexdigest() for n, raw in payload.items()},
              'dispatch_sha256': digest(trigger / 'launch.sh')}
    (archive / 'uart-tx-installation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
