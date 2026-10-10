"""Publish only verified Focus1 text diagnostics and derived budgets; no card access."""
from pathlib import Path
from hashlib import sha256
import argparse
import importlib.util
import json

ROOT = Path(__file__).resolve().parent.parent
PREFIX = 'evidence/2026-10-10/snes-focus-1-return/'


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'build' / file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def publish(archive):
    archive = archive.resolve()
    budget = module('publish_focus_budget', 'analyze-snes-effect-budget.py').analyze(archive)
    baseline = module('publish_focus_text', 'publish-snes-1.19.py')
    mvp = archive / 'snes-mvp'
    selected = {name: archive / name for name in ('independent-readback.json', 'chkdsk-return.txt',
                                                 'focus-analysis.json', 'pcm-analysis.json',
                                                 'effect-budget.json', 'reserve-curve.csv')}
    selected.update({'session-failure.txt': mvp / 'saves' / ('failure-' + budget['session_id'] + '-session.txt'),
                     'pcm-failure.txt': mvp / 'last-pcm-fault.txt',
                     'startup.log': mvp / 'startup.log', 'last-run.log': mvp / 'last-run.log',
                     'diagnostic-flush.log': mvp / 'diagnostic-flush.log'})
    manifest = ROOT / 'evidence/manifest.json'
    raw = manifest.read_bytes()
    entries = json.loads(raw)['entries']
    for entry in entries:
        assert sha256((ROOT / entry['published']).read_bytes()).hexdigest() == entry['published_sha256'], entry['published']
    additions = []
    for name, source in selected.items():
        original = source.read_bytes()
        output = baseline.public_text(original)
        for forbidden in (b'GITHUB_TOKEN', b'Bearer ', b'github_pat_', b'ghp_', b'C:\\Users', b'.codex/attachments', b'D35MVP01', b'D35PLUS1'):
            assert forbidden not in output, name
        target = ROOT / PREFIX / name
        existing = next((e for e in entries if e['published'] == PREFIX + name), None)
        if existing:
            assert target.read_bytes() == output, 'Published evidence is immutable'
            continue
        assert not target.exists()
        additions.append((target, output, dict(source=source.relative_to(ROOT).as_posix(), published=PREFIX + name,
                                               source_sha256=sha256(original).hexdigest(),
                                               published_sha256=sha256(output).hexdigest(), bytes=len(output),
                                               normalized=original != output)))
    for target, output, _ in additions:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output)
    if additions:
        manifest.write_bytes(baseline.append_manifest(raw, [entry for _, _, entry in additions]))
    print(json.dumps(dict(published_files=len(additions), historical_entries_verified=len(entries),
                          card_writes=0, private_progress_or_dependencies_published=False), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    publish(parser.parse_args().archive)
