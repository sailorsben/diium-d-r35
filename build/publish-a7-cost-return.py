"""Publish cost counters/curves only; preserve every prior evidence hash."""
from pathlib import Path
from hashlib import sha256
import importlib.util
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
archive = ROOT / 'device-evidence' / sys.argv[1]
suite = archive / 'snes-cost1'
analysis = json.loads((suite / 'return-analysis.json').read_text())
proof = json.loads((archive / 'independent-cost-return.json').read_text())
assert proof['passed'] and proof['card_writes'] == 0 and proof['clean_fat']
assert analysis['gate'] == 'NOT MET' and len(analysis['captures']) == 13
spec = importlib.util.spec_from_file_location('cost_return_publisher', ROOT / 'build/publish-snes-1.19.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
manifest = ROOT / 'evidence/manifest.json'
raw = manifest.read_bytes()
previous = json.loads(raw)
for entry in previous['entries']:
    assert sha256((ROOT / entry['published']).read_bytes()).hexdigest() == entry['published_sha256']
prefix = ROOT / 'evidence/2026-10-10/snes-a7-cost1-return'
if prefix.exists():
    # Review-time regeneration is allowed only while this return is uncommitted.
    committed_raw = subprocess.check_output(['git', 'show', 'HEAD:evidence/manifest.json'], cwd=ROOT)
    committed = json.loads(committed_raw)
    assert not any(e['published'].startswith(prefix.relative_to(ROOT).as_posix() + '/')
                   for e in committed['entries']), 'Preserve committed return evidence'
    assert previous['entries'][:len(committed['entries'])] == committed['entries']
    assert all(e['published'].startswith(prefix.relative_to(ROOT).as_posix() + '/')
               for e in previous['entries'][len(committed['entries']):])
    raw, previous = committed_raw, committed
else:
    prefix.mkdir(parents=True)
sources = {suite / 'return-analysis.json': 'return-analysis.json',
           suite / 'reserve-curve.csv': 'reserve-curve.csv',
           archive / 'independent-cost-return.json': 'independent-cost-return.json',
           archive / 'chkdsk-cost-return.txt': 'chkdsk-cost-return.txt'}
sources.update({p: p.parent.name + '-unit-cost.csv' for p in sorted(suite.glob('pass-*/unit-cost.csv'))})
additions = []
for source, name in sources.items():
    original = source.read_bytes()
    clean = base.public_text(original)
    target = prefix / name
    target.write_bytes(clean)
    additions.append(dict(source=source.relative_to(ROOT).as_posix(), published=target.relative_to(ROOT).as_posix(),
                          source_sha256=sha256(original).hexdigest(), published_sha256=sha256(clean).hexdigest(),
                          bytes=len(clean), normalized=original != clean))
manifest.write_bytes(base.append_manifest(raw, additions))
print(json.dumps(dict(historical_entries_preserved=len(previous['entries']), new_evidence_files=len(additions),
                      private_rom_core_snapshot_sram_or_backup_published=False), indent=2))
