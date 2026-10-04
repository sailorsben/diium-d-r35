"""Read-only card collection: preserve a returned MVP and all private progress."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
import shutil

ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def collect(card):
    card = card.resolve()
    target = card / 'retro/snes-mvp'
    assert target.is_dir() and (target / 'snes-mvp').is_file(), 'No MVP at this card path'
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    archive = ROOT / 'device-evidence' / ('snes-mvp-return-' + stamp)
    archive.mkdir(parents=True, exist_ok=False)
    files = []
    for relative in ('retro/snes-mvp', 'retro/saves', 'retro/states'):
        folder = card / relative
        if folder.is_dir():
            files.extend(p for p in folder.rglob('*') if p.is_file())
    files.append(card / 'retro/init')
    entries = []
    for source in sorted(files):
        assert not source.is_symlink(), source
        relative = source.relative_to(card)
        assert not any(part == '..' for part in relative.parts), relative
        destination = archive / ('snes-mvp' if relative.parts[:2] == ('retro', 'snes-mvp')
                                 else 'card')
        destination = (destination.joinpath(*relative.parts[2:])
                       if relative.parts[:2] == ('retro', 'snes-mvp')
                       else destination / relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        before = digest(source)
        shutil.copy2(source, destination)
        assert digest(destination) == before == digest(source), source
        entries.append({'card_path': relative.as_posix(),
                        'archive_path': destination.relative_to(archive).as_posix(),
                        'sha256': before, 'bytes': source.stat().st_size})
    production = {}
    for relative in ('retro/main', 'retro/vrtemu', 'retro/driver.so',
                     'retro/libs/emu_sfc.so', 'retro/libs/emu_sfc_plus.so'):
        source = card / relative
        if source.is_file():
            production[relative] = digest(source)
    result = {'collected_utc': datetime.now(timezone.utc).isoformat(),
              'card': str(card), 'archive': str(archive), 'card_writes': 0,
              'armed_present': (target / 'armed').exists(),
              'copied_and_hash_verified': entries, 'production_hashes': production}
    (archive / 'collection.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'archive': str(archive), 'copied_files': len(entries),
                      'card_writes': 0, 'armed_present': result['armed_present']}, indent=2))
    return archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--card', default='D:/')
    collect(Path(parser.parse_args().card))
