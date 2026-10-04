"""Archive the owned probe output and restore its exact prior boot script."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

workspace = Path(__file__).resolve().parent.parent
package = workspace / 'Hardware-Console-v3'
manifest = json.loads((package / 'installation.json').read_text())
card = Path('D:/retro').resolve(strict=True)
assert str(card).lower() == 'd:\\retro', card
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(card / 'init') == manifest['init_probe_sha256'], 'Boot script changed; preserve it'
assert sha(package / 'init.before') == manifest['init_original_sha256']
assert sha(card / 'hardware_probe_v3') == manifest['probe_sha256']
before = {name: sha(card / name) for name in manifest['critical_after']}
assert before == manifest['critical_after'], 'Working binaries changed; inspect first'
report = card / 'hardware_probe_v3.jsonl'
records = [json.loads(line) for line in report.read_text().splitlines()]
assert records[-1]['kind'] == 'complete' and not records[-1]['report_capped']
assert sum(r['kind'] == 'sample' for r in records) == 45
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
archive = workspace / 'device-evidence' / ('hardware-console-return-' + stamp)
archive.mkdir(exist_ok=False)
owned = ['hardware_probe_v3', 'hardware_probe_v3.once',
         'hardware_probe_v3.once.started', 'hardware_probe_v3.jsonl', 'hardware_probe_v3.err']
archived = {}
for name in ['init'] + owned:
    source = card / name
    if source.exists():
        dest = archive / name
        shutil.copyfile(source, dest)
        assert sha(dest) == sha(source)
        archived[name] = sha(dest)
shutil.copyfile(package / 'init.before', card / 'init')
assert sha(card / 'init') == manifest['init_original_sha256']
for name in owned:
    target = card / name
    assert target.parent == card and target.name == name
    if target.exists():
        assert name in archived
        assert sha(target) == archived[name]
        target.unlink()
after = {name: sha(card / name) for name in before}
assert before == after
assert all(not (card / name).exists() for name in owned)
result = {'archive': str(archive), 'hardware_execution_verified': True,
          'record_count': len(records), 'sample_count': 45,
          'complete': records[-1], 'archived_sha256': archived,
          'restored_init_sha256': sha(card / 'init'),
          'critical_unchanged': after, 'removed_probe_paths': owned,
          'probe_error_bytes': (archive / 'hardware_probe_v3.err').stat().st_size}
(archive / 'cleanup-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
