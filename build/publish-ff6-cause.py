"""Publish bounded experiment evidence, preserving all historical hashes and private inputs."""
from pathlib import Path
from hashlib import sha256
import importlib.util
import json

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/ff6-window-batch-private'
PREFIX = 'evidence/verification/ff6-bio-blast-cause/'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def publish():
    spec = importlib.util.spec_from_file_location('cause_public_baseline', ROOT / 'build/publish-snes-1.19.py')
    baseline = importlib.util.module_from_spec(spec); spec.loader.exec_module(baseline)
    q = json.loads((OUT / 'analysis.json').read_text())
    assert q['passed'] and not q['hardware_qualified'] and not q['installed_on_card']
    for group in ('source_hashes', 'private_input_hashes'):
        for name, wanted in q[group].items():
            assert digest(ROOT / name) == wanted, name
    raw_manifest = (ROOT / 'evidence/manifest.json').read_bytes()
    manifest = json.loads(raw_manifest)
    assert not any(entry['published'].startswith(PREFIX) for entry in manifest['entries'])
    for entry in manifest['entries']:
        assert digest(ROOT / entry['published']) == entry['published_sha256']
    sources = {OUT / name: name for name in ('analysis.json', 'window-check.log', 'c-map-syntax.log',
                                             'equivalence-bio.log', 'equivalence-general.log')}
    sources[ROOT / 'build/ff6-cause-private/c-map/verification.json'] = 'c-map-verification.json'
    prepared = []
    for source, name in sources.items():
        raw = source.read_bytes(); output = baseline.public_text(raw)
        target = ROOT / PREFIX / name
        assert not target.exists() or target.read_bytes() == output
        prepared.append((source, target, raw, output))
    additions = []
    for source, target, raw, output in prepared:
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(output)
        additions.append({'source': source.relative_to(ROOT).as_posix(),
                          'published': target.relative_to(ROOT).as_posix(),
                          'source_sha256': sha256(raw).hexdigest(), 'published_sha256': sha256(output).hexdigest(),
                          'bytes': len(output), 'normalized': raw != output})
    (ROOT / 'evidence/manifest.json').write_bytes(baseline.append_manifest(raw_manifest, additions))
    print(json.dumps({'curated_experiment_files': len(additions), 'prior_evidence_hashes_preserved': len(manifest['entries']),
                      'ROM_progress_or_dependency_bytes_published': False, 'candidate_installed': False}, indent=2))


if __name__ == '__main__':
    publish()
