"""Publish verified physical diagnostic metadata; retain every prior proof."""
from pathlib import Path
from hashlib import sha256
import json, sys

ROOT = Path(__file__).resolve().parent.parent

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def main(archive):
    archive = archive.resolve()
    assert archive.is_relative_to(ROOT / 'device-evidence')
    source = archive / 'pc-profile-return-evaluation.json'
    r = json.loads(source.read_text())
    assert r['FAT_clean'] and r['card_writes'] == 0 and r['marker_consumed']
    assert r['installed_payloads_verified'] == 88 and r['same_exact_core_both_variants']
    assert r['ROM_live_sha256'] == 'f61af2bd9e3f9b6a2bd543fb176af0b81fd9e5ba4ea0fa0f453371ccb45d3911'
    assert len(r['epochs']) == 4 and len(r['PC_attribution']['runs']) == 2
    assert not r['production_gate_passed'] and not r['emulator_runtime_changes']
    for n, h in r['inputs'].items():
        assert digest(ROOT / n) == h, n
    out = ROOT / 'build/current-pc-profile-private-v1'
    q = json.loads((out / 'verification.json').read_text())
    ready = json.loads((out / 'ready.json').read_text())
    for group in ('source_hashes', 'payload_hashes', 'proof_hashes'):
        for n, h in q[group].items():
            assert digest(ROOT / n if group == 'source_hashes' else out / n) == h, n
    for n, h in ready['additional_sources'].items():
        assert digest(ROOT / n) == h, n
    assert ready['verification_sha256'] == digest(out / 'verification.json')
    for n, h in json.loads((ROOT / 'build/demand-visible-private-v3/frozen.json').read_text()).items():
        assert digest(ROOT / n) == h, n
    manifest = ROOT / 'evidence/manifest.json'
    m = json.loads(manifest.read_text())
    for e in m['entries']:
        assert digest(ROOT / e['published']) == e['published_sha256'], e['published']
    target = ROOT / 'evidence/2026-10-14/pc-profile-return/analysis.json'
    assert not target.exists()
    target.parent.mkdir(parents=True, exist_ok=False)
    target.write_text(json.dumps(r, indent=2) + '\n')
    assert digest(target) == digest(source)
    m['entries'].append({'source': source.relative_to(ROOT).as_posix(), 'published': target.relative_to(ROOT).as_posix(),
                         'source_sha256': digest(source), 'published_sha256': digest(target),
                         'bytes': target.stat().st_size, 'normalized': False})
    manifest.write_text(json.dumps(m, indent=2) + '\n')
    print(json.dumps({'physical_epochs': 4, 'prior_published_hashes_verified': len(m['entries']) - 1,
                      'frozen_preparation_exact': True, 'card_writes': 0, 'published': str(target)}))

if __name__ == '__main__':
    main(Path(sys.argv[1]))
