"""Sparse attempt evidence: hashes for everything, content only for progress/logs.

The private object store owns immutable saved generations. Per-attempt paths are
hard links to those objects, so existing log readers can use ordinary paths.
No full-copy fallback is allowed when hard linking is unavailable.
"""
from errno import EMLINK
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
    diagnostic = (len(p.parts) > 2 and p.parts[0].lower() == 'retro'
                  and (p.parts[1].lower().startswith(('snes-', 'uart-', 'render-pressure', 'spi-'))
                       or p.parts[1].lower() in {'platform-lab', 'device-survey'}))
    run_output = any(part.lower().startswith(('run-', 'pass-', 'epoch-')) for part in p.parts[2:-1])
    root_report = name in {'pcm-full.txt', 'runtime-platform.txt', 'runtime-platform-latest.txt',
                          'kernel-tail.txt', 'startup-platform.txt', 'startup-processes.txt',
                          'suite-identity.json'}
    return ((diagnostic and ((run_output and suffix in {'.txt', '.json'}) or root_report))
            or bool(parts & {'saves', 'states', 'snapshots', 'results', 'logs', 'captures'})
            or suffix in PROGRESS or suffix in LOGS
            or name.startswith(('last-', 'latest-', 'fault', 'crash'))
            or name in {'report.txt', 'supervisor.txt', 'suite-result.txt'})


def retain_object(source, store, target, sha):
    """Link to a verified object, opening a new shard only at the link limit."""
    store.mkdir(parents=True, exist_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    shard = added = 0
    while True:
        obj = store/(sha if shard == 0 else f'{sha}.{shard}')
        if not obj.exists():
            temp = store/(sha + '.' + uuid.uuid4().hex + '.tmp')
            try:
                shutil.copyfile(source, temp)
                if digest(temp) != sha or digest(source) != sha:
                    raise ValueError('Card changed during collection: ' + str(source))
                try:
                    os.link(temp, obj)
                    added += temp.stat().st_size
                except FileExistsError:
                    pass
            finally:
                temp.unlink(missing_ok=True)
        if digest(obj) != sha:
            raise ValueError('Corrupt attempt object: ' + str(obj))
        try:
            os.link(obj, target)
        except OSError as error:
            at_limit = error.errno == EMLINK or getattr(error, 'winerror', None) == 1142
            if not at_limit or obj.stat().st_nlink <= 1:
                raise
            shard += 1
        else:
            if digest(target) != sha:
                raise ValueError('Archive readback mismatch: ' + str(target))
            return added


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
                entry['new_content_bytes'] = retain_object(source, store, out/relative, h)
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
