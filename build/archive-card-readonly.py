"""Salvage readable card files before filesystem repair. Never writes to card.

The incomplete archive is evidence, not an installation baseline. Full card
contents stay private under device-evidence and must never be published.
"""
from pathlib import Path
from hashlib import sha256
import argparse, json, os

ROOT = Path(__file__).resolve().parent.parent

def archive_card(card, destination):
    card = card.resolve(); destination = destination.resolve()
    assert str(card).lower() in ('d:\\', 'd:/')
    assert destination.is_relative_to(ROOT / 'device-evidence')
    destination.mkdir(parents=True, exist_ok=False)
    entries = []; errors = []
    def error(path, operation, exc):
        errors.append({'path': str(Path(path).relative_to(card)).replace('\\', '/'),
                       'operation': operation, 'error': str(exc),
                       'winerror': getattr(exc, 'winerror', None)})
    def digest(path):
        h = sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
        return h.hexdigest()
    for parent, folders, names in os.walk(card, onerror=lambda e: error(e.filename, 'enumerate', e)):
        for name in sorted(names):
            source = Path(parent) / name; relative = source.relative_to(card)
            target = destination / 'files' / relative
            try:
                assert not source.is_symlink(), source
                target.parent.mkdir(parents=True, exist_ok=True)
                h = sha256()
                with source.open('rb') as src, target.open('xb') as dst:
                    for block in iter(lambda: src.read(1024 * 1024), b''):
                        h.update(block); dst.write(block)
                wanted = h.hexdigest()
                assert digest(target) == wanted == digest(source), source
                entries.append({'path': relative.as_posix(), 'bytes': target.stat().st_size,
                                'sha256': wanted})
            except OSError as exc:
                error(source, 'copy-and-readback', exc)
    result = {'card_writes': 0, 'complete': not errors, 'errors': errors,
              'copied_and_hash_verified': entries}
    (destination / 'collection.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'archive': str(destination), 'files': len(entries),
                     'bytes': sum(e['bytes'] for e in entries), 'errors': errors,
                     'card_writes': 0}, indent=2))

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--card', type=Path, default=Path('D:/'))
    p.add_argument('--destination', type=Path, required=True)
    a = p.parse_args(); archive_card(a.card, a.destination)
