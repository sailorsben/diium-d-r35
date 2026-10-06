"""Publish qualified native PCM build; never publish games or dependencies."""
from pathlib import Path
from hashlib import sha256
import json

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'build/snes-mvp/out'
RELEASE = ROOT / 'releases/snes-mvp-1.13'
PREFIX = 'evidence/verification/snes-mvp-1.13/'

def digest(path): return sha256(path.read_bytes()).hexdigest()

def append_manifest(raw, entries):
    # Preserve all historical bytes, including mixed LF/CRLF formatting.
    offset = raw.index(b'\n  ]', raw.index(b'"entries"'))
    if raw[offset - 1:offset] == b'\r': offset -= 1
    newline = '\r\n' if b'\r\n' in raw else '\n'
    rendered = [newline.join('    ' + line for line in json.dumps(entry, indent=2).splitlines())
                for entry in entries]
    addition = (',' + newline + (',' + newline).join(rendered)).encode()
    return raw[:offset] + addition + raw[offset:]

def qualified():
    checks = json.loads((OUT / 'verification.json').read_text())
    assert checks['passed'] and checks['version'] == '1.13'
    assert checks['hardware_qualified'] is False
    for group in ('source_hashes', 'check_artifact_hashes'):
        for name, wanted in checks[group].items():
            assert digest(ROOT / name) == wanted, 'Qualified input changed: ' + name
    for source, key in ((OUT / 'snes-mvp', 'binary_sha256'),
                        (ROOT / 'build/snes-mvp/launch.sh', 'wrapper_sha256'),
                        (ROOT / 'build/plus-a7-out/plus-a7.so', 'core_sha256'),
                        (ROOT / 'build/plus-a7-render.h', 'a7_header_sha256')):
        assert digest(source) == checks[key], 'Qualified payload changed: ' + source.name
    assert b'\r' not in (ROOT / 'build/snes-mvp/launch.sh').read_bytes()
    return checks

def publish():
    checks = qualified()
    installs = sorted((ROOT / 'device-evidence').glob('snes-mvp-1.13-install-*/installation.json'))
    assert installs, 'Install and independently verify the exact card payload first'
    installation_path = installs[-1]
    installation = json.loads(installation_path.read_text())
    assert installation['one_shot_armed'] and installation['version'] == '1.13'
    for key in ('binary_sha256', 'wrapper_sha256', 'core_sha256'):
        assert installation[key] == checks[key]
    proof = json.loads((installation_path.parent / 'independent-readback.json').read_text())
    assert proof['passed'] and proof['one_shot_armed'] and proof['lab_unarmed']
    public = {k: v for k, v in checks.items() if k != 'qualified_snapshot_sha256'}
    public['dependencies'] = 'Locally built pinned core and owner-supplied matched driver/runtime; no dependency binaries or private progress published'
    payload = {'snes-mvp': (OUT / 'snes-mvp').read_bytes(),
               'launch.sh': (ROOT / 'build/snes-mvp/launch.sh').read_bytes(),
               'TEST-ME.txt': (ROOT / 'docs/snes-mvp-1.13-test.txt').read_bytes(),
               'manifest.json': (json.dumps(public, indent=2) + '\n').encode()}
    # Reject changed bytes before touching an existing versioned release.
    for name, raw in payload.items():
        existing = RELEASE / name
        assert not existing.exists() or existing.read_bytes() == raw, 'Immutable release: ' + name
    manifest_path = ROOT / 'evidence/manifest.json'
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    assert not any(e['published'].startswith(PREFIX) for e in manifest['entries']), 'Already published'
    for entry in manifest['entries']:
        assert digest(ROOT / entry['published']) == entry['published_sha256']
    sources = [ROOT / name for name in checks['check_artifact_hashes']]
    names = {OUT / 'smoke-final/last-session.txt': 'smoke-session.txt',
             OUT / 'paced-smoke/last-session.txt': 'paced-session.txt'}
    sources += [OUT / 'verification.json', installation_path,
                installation_path.parent / 'independent-readback.json']
    prepared = []
    for source in sources:
        raw = source.read_bytes()
        name = names.get(source, source.name)
        if name == 'verification.json':
            output = (json.dumps(public, indent=2) + '\n').encode()
        else:
            output = raw.decode().replace(str(ROOT), '<workspace>').replace(ROOT.as_posix(), '<workspace>').replace('\r\n', '\n').encode()
        prepared.append((source, name, raw, output))
    assert len({name for _, name, _, _ in prepared}) == len(prepared)
    RELEASE.mkdir(parents=True, exist_ok=True)
    for name, raw in payload.items(): (RELEASE / name).write_bytes(raw)
    additions = []
    for source, name, raw, output in prepared:
        target = ROOT / PREFIX / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output)
        additions.append({'source': source.relative_to(ROOT).as_posix(),
            'published': target.relative_to(ROOT).as_posix(),
            'source_sha256': sha256(raw).hexdigest(), 'published_sha256': sha256(output).hexdigest(),
            'bytes': len(output), 'normalized': raw != output})
    manifest_path.write_bytes(append_manifest(manifest_raw, additions))
    print(json.dumps({'version': '1.13', 'release_files': len(payload),
                      'curated_check_files': len(prepared), 'private_progress_published': False}, indent=2))

if __name__ == '__main__': publish()
