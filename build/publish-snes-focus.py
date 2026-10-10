"""Publish the qualified owned diagnostic runner and bounded evidence, without dependencies."""
from pathlib import Path
from hashlib import sha256
import importlib.util
import json

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/snes-focus-out'
ARCHIVE = ROOT / 'device-evidence/snes-mvp-return-20261010T144407Z'
RELEASE = ROOT / 'releases/snes-focus-1'
PREFIX = 'evidence/verification/snes-focus-1/'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def publish():
    spec = importlib.util.spec_from_file_location('focus_public_baseline', ROOT / 'build/publish-snes-1.19.py')
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    q = json.loads((OUT / 'verification.json').read_text())
    assert q['version'] == '1.19-focus1' and q['passed'] and not q['hardware_qualified']
    for group in ('source_hashes', 'check_artifact_hashes'):
        for name, wanted in q[group].items():
            assert digest(ROOT / name) == wanted, name
    assert digest(OUT / 'snes-mvp') == q['binary_sha256']
    old = json.loads((ROOT / 'releases/snes-mvp-1.19/manifest.json').read_text())
    for key in ('core_sha256', 'core_bytes', 'core_crc32', 'wrapper_sha256'):
        assert q[key] == old[key]
    installation = json.loads((ARCHIVE / 'focus-installation.json').read_text())
    readback = json.loads((ARCHIVE / 'independent-focus-readback.json').read_text())
    assert readback['passed'] and readback['fat_clean'] and readback['one_shot_armed']
    assert readback['lab_unarmed'] and readback['firmware_trigger_absent']
    assert readback['unchanged_files_independently_verified'] == installation['unchanged_files_verified'] == 138
    for key in ('binary_sha256', 'core_sha256', 'wrapper_sha256'):
        assert readback[key] == installation[key] == q[key]
    review = json.loads((OUT / 'budget-review.json').read_text())
    smoke = json.loads((OUT / 'smoke-analysis.json').read_text())
    guard = json.loads((OUT / 'analyzer-check.json').read_text())
    assert review['returned_session'] == '502-9771840000'
    assert smoke['mock_backend'] and smoke['retained_frame_count'] == 64
    assert guard['passed'] and guard['checks'] == 4
    public = dict(q)
    public['release_kind'] = 'Runner-only diagnostics; physical focus result pending; no audio fix claimed'
    public['dependencies'] = 'Use the unchanged locally qualified1.19 core/wrapper and owner-supplied device runtime; no dependency binaries published'
    helpers = ['analyze-bio-blast-budget.py', 'analyze-snes-focus.py', 'install-snes-focus.py',
               'verify-snes-focus-card.py', 'publish-snes-focus.py']
    public['support_source_hashes'] = {('build/' + name): digest(ROOT / 'build' / name) for name in helpers}
    public['test_instructions_sha256'] = digest(ROOT / 'docs/snes-focus-1-test.txt')
    payload = {'snes-mvp': (OUT / 'snes-mvp').read_bytes(),
               'TEST-ME.txt': (ROOT / 'docs/snes-focus-1-test.txt').read_bytes(),
               'manifest.json': (json.dumps(public, indent=2) + '\n').encode()}
    for name, raw in payload.items():
        path = RELEASE / name
        assert not path.exists() or path.read_bytes() == raw, 'Immutable release: ' + name
    manifest_path = ROOT / 'evidence/manifest.json'
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    assert not any(entry['published'].startswith(PREFIX) for entry in manifest['entries']), 'Already published'
    for entry in manifest['entries']:
        assert digest(ROOT / entry['published']) == entry['published_sha256']
    sources = {OUT / name: name for name in ('focus-check.log', 'native-check.log', 'abi.txt',
                                            'budget-review.json', 'smoke-analysis.json', 'analyzer-check.json')}
    sources[OUT / 'smoke/last-session.txt'] = 'smoke-session.txt'
    sources[OUT / 'verification.json'] = 'verification.json'
    for name in ('focus-installation.json', 'independent-focus-readback.json',
                 'chkdsk-before-focus.txt', 'chkdsk-after-focus-payload.txt',
                 'chkdsk-after-focus-arm.txt', 'chkdsk-independent-focus.txt'):
        sources[ARCHIVE / name] = name
    prepared = []
    for source, name in sources.items():
        raw = source.read_bytes()
        output = payload['manifest.json'] if name == 'verification.json' else baseline.public_text(raw)
        target = ROOT / PREFIX / name
        assert not target.exists() or target.read_bytes() == output, 'Existing evidence differs: ' + name
        prepared.append((source, target, raw, output))
    RELEASE.mkdir(parents=True, exist_ok=True)
    for name, raw in payload.items():
        (RELEASE / name).write_bytes(raw)
    additions = []
    for source, target, raw, output in prepared:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output)
        additions.append({'source': source.relative_to(ROOT).as_posix(),
                          'published': target.relative_to(ROOT).as_posix(),
                          'source_sha256': sha256(raw).hexdigest(), 'published_sha256': sha256(output).hexdigest(),
                          'bytes': len(output), 'normalized': raw != output})
    manifest_path.write_bytes(baseline.append_manifest(manifest_raw, additions))
    print(json.dumps({'version': q['version'], 'owned_release_files': len(payload),
                      'curated_evidence_files': len(prepared), 'historical_hashes_preserved': len(manifest['entries']),
                      'dependency_or_private_progress_published': False}, indent=2))


if __name__ == '__main__':
    publish()
