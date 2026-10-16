"""Sparse attempt evidence: hashes for everything, content only for progress/logs.

The private object store owns immutable saved generations. Per-attempt paths are
hard links to those objects, so existing log readers can use ordinary paths.
No full-copy fallback is allowed when hard linking is unavailable.
"""
from pathlib import Path
from hashlib import sha256
import json
import os
import shutil
import uuid

SCHEMA = 'sparse-attempt-v1'
PROGRESS = {'.srm', '.sram', '.sav', '.save', '.state', '.sta', '.frz', '.rtc', '.eep', '.fla'}
LOGS = {'.log', '.csv', '.jsonl', '.trace'}


def digest(path):
    h = sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def retain(relative):
    """Only mutable progress and diagnostic output, never whole test packages."""
    p = Path(relative)
    parts = {part.lower() for part in p.parts}
    name = p.name.lower()
    # Backups retain the classification of their original filename.
    while name.endswith(('.bak', '.bkp')):
        name = name.rsplit('.', 1)[0]
    suffix = Path(name).suffix
    if parts & {'cases', 'fixtures', 'targeted-cases'} or suffix in {'.so', '.zip', '.sfc', '.smc', '.nes', '.gba', '.rom'}:
        return False
    return (bool(parts & {'saves', 'states', 'snapshots', 'results', 'logs', 'captures'})
            or suffix in PROGRESS or suffix in LOGS
            or name.startswith(('last-', 'latest-', 'fault', 'crash'))
            or name in {'report.txt', 'supervisor.txt', 'suite-result.txt'})


def inventory(card, out, outside=False):
    card, out = Path(card).resolve(), Path(out).resolve()
    store = out.parent / 'attempt-objects'
    entries = []
    scan = card if outside else card / 'retro'
    def failed(error):
        raise error
    for parent, dirs, names in os.walk(scan, followlinks=False, onerror=failed):
        if outside and Path(parent) == card:
            dirs[:] = [d for d in dirs if d.lower() != 'retro']
        for d in dirs:
            if (Path(parent) / d).is_symlink():
                raise ValueError('Linked card directory: ' + str(Path(parent) / d))
        for name in sorted(names):
            source = Path(parent) / name
            if source.is_symlink():
                raise ValueError('Linked card file: ' + str(source))
            relative = source.relative_to(card)
            before = source.stat()
            h = digest(source)
            saved = retain(relative)
            entry = {'path': relative.as_posix(), 'bytes': before.st_size,
                     'sha256': h, 'stored': saved, 'new_content_bytes': 0}
            if saved:
                store.mkdir(parents=True, exist_ok=True)
                obj = store / h
                if obj.exists():
                    if digest(obj) != h:
                        raise ValueError('Corrupt attempt object: ' + str(obj))
                else:
                    temp = store / (h + '.' + uuid.uuid4().hex + '.tmp')
                    try:
                        shutil.copyfile(source, temp)
                        if digest(temp) != h or digest(source) != h:
                            raise ValueError('Card changed during collection: ' + str(source))
                        os.replace(temp, obj)
                    finally:
                        temp.unlink(missing_ok=True)
                    entry['new_content_bytes'] = before.st_size
                target = out / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                os.link(obj, target)
                if digest(target) != h:
                    raise ValueError('Archive readback mismatch: ' + str(target))
            after = source.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError('Card changed during collection: ' + str(source))
            entries.append(entry)
    return entries


def verify_saved(archive, metadata):
    """Verify only retained bytes; hash-only entries are explicitly not backups."""
    for entry in metadata['all_retro_files']:
        if metadata.get('schema') != SCHEMA or entry['stored']:
            if digest(Path(archive) / entry['path']) != entry['sha256']:
                raise ValueError('Archive mismatch: ' + entry['path'])


def write_manifest(path, entries, **metadata):
    value = dict(schema=SCHEMA, storage_policy='changed-progress-and-logs; static-files-hash-only',
                 new_content_bytes=sum(e['new_content_bytes'] for e in entries), **metadata)
    Path(path).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
