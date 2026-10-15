"""Publish interpreted UART metadata only, preserving every prior evidence hash."""
from pathlib import Path
from hashlib import sha256
import json

ROOT = Path(__file__).resolve().parent.parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    source = ROOT / 'device-evidence/uart-kernel-offline/research.json'
    report = json.loads(source.read_text())
    assert report['card_access'] is False and report['live_irq_cause_proven'] is False
    assert report['a7_irq_duration_measured'] is False and len(report['checks']) == 6
    assert report['retained_builtin_runtime_symbols_matched'] == 242
    assert report['latest_draw_order_suite']['irq19_delta'] == 6730129
    for name, expected in report['inputs'].items():
        assert digest(ROOT / name) == expected, name
    manifest = ROOT / 'evidence/manifest.json'
    data = json.loads(manifest.read_text())
    for entry in data['entries']:
        assert digest(ROOT / entry['published']) == entry['published_sha256'], entry['published']
    target = ROOT / 'evidence/2026-10-14/uart-kernel/research.json'
    assert not target.exists(), 'Refuse to overwrite published evidence'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
    data['entries'].append({'source': source.relative_to(ROOT).as_posix(),
        'published': target.relative_to(ROOT).as_posix(), 'source_sha256': digest(source),
        'published_sha256': digest(target), 'bytes': target.stat().st_size, 'normalized': False})
    manifest.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'prior_published_hashes_verified': len(data['entries']) - 1,
                      'published': target.relative_to(ROOT).as_posix(), 'card_access': False}))


if __name__ == '__main__':
    main()
