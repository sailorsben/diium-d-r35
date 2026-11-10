"""Publish compact raster evidence from the verified private scratch runs."""
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT/'build/fivegame-kernel-private-v2/plus-a7.so'
THROUGHPUT = ROOT/'evidence/2026-11-10/snes-throughput/analysis.json'
report = import_module('report-snes-throughput')


def checked_replays(directories):
    verification = {}
    layout = {}
    hashes = {}
    for directory in directories:
        batch = report.replay(directory/'raster-verify')
        for name, sha in batch['meta']['core_sha256'].items():
            assert hashes.setdefault(name, sha) == sha
        for row in batch['results']:
            assert row['verified'] == 1200 and row['mismatch'] == 0, row
            assert row['rendered'] == 1200
            key = (row['game'], row['core'])
            if key not in verification:
                verification[key] = row
            sig = (row['callback_layout_crc32'], row['audio_frames'])
            assert layout.setdefault(row['game'], sig) == sig, row
    return verification, hashes


def main(first, full, isolated, timing, ablation, output, *heldout):
    verification, hashes = checked_replays((first, full, isolated))
    assert hashes['physical'] == report.sha(BASE)
    baseline = first/'baseline/snes9x2005_plus_libretro.so'
    text_hash = report.elf_text(BASE)
    assert text_hash == report.elf_text(baseline)
    paired = {'builds': report.paired(timing), 'ablation': report.paired(ablation)}
    for series in paired.values():
        for name, sha in series['meta']['core_sha256'].items():
            if name == 'baseline':
                assert sha == report.sha(baseline)
            elif name.endswith('-disabled'):
                assert sha == series['meta']['core_sha256'][name.removesuffix('-disabled')]
            else:
                assert sha in {hashes.get(name), hashes.get(name+'-toggle')}, name
        assert all(r['rendered'] == [1200, 1200] for r in series['results'])
        series['results'].sort(key=lambda row: (row['game'], row['candidate']))
    assert heldout
    fixture_checks = [json.loads((path/'checks.json').read_text()) for path in heldout]
    for check in fixture_checks:
        assert check['baseline_sha256'] == hashes['physical']
        assert check['core_sha256'] in hashes.values()
        assert all(r['normalized_state_and_output_match'] for r in check['tests'])
    keys = ('core', 'game', 'mode', 'verified', 'mismatch', 'callback_layout_crc32',
            'rendered', 'audio_frames', 'log_sha256', 'raster')
    replays = [{k: row[k] for k in keys if k in row} for _, row in sorted(verification.items())]
    physical = json.loads(THROUGHPUT.read_text())['physical_baseline']
    physical_keys = ('run', 'game', 'policy', 'period_ns', 'valid_prefix', 'rendered', 'service_p95_ns',
                     'target_p95_gap_ns', 'first_valid_prefix_core_cpu_mean_ns',
                     'first_valid_prefix_core_only_excess_ns', 'nominal_final_deficit_frames')
    geometry = subprocess.check_output(
        [sys.executable, ROOT/'build/check-snes-raster-offset.py'], text=True).strip()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        'new_device_execution': False,
        'baseline_text_sha256': text_hash,
        'prior_physical_source_sha256': report.sha(THROUGHPUT),
        'prior_physical': [{k: row[k] for k in physical_keys if k in row} for row in physical],
        'verified_core_sha256': hashes,
        'verified_replays': replays,
        'mode2_geometry_check': geometry,
        'paired_qemu': paired,
        'held_out_strict': fixture_checks,
    }, indent=2)+'\n', newline='\n')


if __name__ == '__main__':
    main(*(Path(p).resolve() for p in sys.argv[1:]))
