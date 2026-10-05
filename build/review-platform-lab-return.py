"""Verify/publish selected lab1 return evidence; no card writes or private saves."""
from pathlib import Path
from hashlib import sha256
import argparse
import importlib.util
import json
import shutil

ROOT = Path(__file__).resolve().parent.parent
RELEASE = ROOT / 'releases/platform-lab-1'

def digest(p): return sha256(p.read_bytes()).hexdigest()

def review(archive, before):
    current = json.loads((archive / 'collection.json').read_text())
    original = json.loads((before / 'collection.json').read_text())
    assert current['card_writes'] == 0 and not current['armed_present']
    assert current['production_hashes'] == original['production_hashes']
    files = {e['card_path']: e for e in current['copied_and_hash_verified']}
    protected = json.loads((before / 'lab-protected.json').read_text())
    assert all(files[p]['sha256'] == h for p, h in protected.items())
    for entry in current['copied_and_hash_verified']:
        assert digest(archive / entry['archive_path']) == entry['sha256']
    lab_collection = json.loads((archive / 'lab-collection.json').read_text())
    assert lab_collection['card_writes'] == 0 and not lab_collection['lab_armed']
    for entry in lab_collection['copied']:
        assert digest(archive / 'platform-lab' / entry['relative_path']) == entry['sha256']
    lab = archive / 'platform-lab'
    manifest = json.loads((RELEASE / 'manifest.json').read_text())
    for name in ('platform-lab', 'launch.sh', 'TEST-ME.txt'):
        assert digest(lab / name) == manifest[name]
    assert files['retro/snes-mvp/launch.sh']['sha256'] == manifest['dispatch.sh']
    for relative in ('retro/init', 'retro/snes-mvp/snes-mvp'):
        old = next(e for e in original['copied_and_hash_verified'] if e['card_path'] == relative)
        assert old['sha256'] == files[relative]['sha256']
    old_wrapper = next(e for e in original['copied_and_hash_verified'] if e['card_path'] == 'retro/snes-mvp/launch.sh')
    assert files['retro/snes-mvp/launch-game-1.8.sh']['sha256'] == old_wrapper['sha256']
    for relative, entry in files.items():
        if relative.startswith('retro/snes-mvp/') and relative.endswith('.so'):
            old = next(e for e in original['copied_and_hash_verified'] if e['card_path'] == relative)
            assert old['sha256'] == entry['sha256']
    runs = list((lab / 'results').iterdir()); assert len(runs) == 1 and runs[0].is_dir()
    run = runs[0]
    spec = importlib.util.spec_from_file_location('lab_analysis', ROOT / 'build/analyze-platform-lab.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    analysis = module.analyze(run)
    assert analysis['complete'] and not analysis['simulated']
    assert 'lab_exit=0' in (run / 'wrapper.log').read_text()
    assert 'worker joined' in (run / 'startup.log').read_text() and 'FreeVFB returned' in (run / 'startup.log').read_text()
    assert all(p['submitted_jobs'] == p['completed_vendor_flips'] == 240
               for p in analysis['pipelines'] if p['name'] != 'AUDIO ONLY')
    summary = {'version': 'lab1', 'physical_run_complete': True,
               'archive': archive.name, 'card_writes': 0, 'markers_consumed': True,
               'copied_mvp_files': len(current['copied_and_hash_verified']),
               'copied_lab_files': len(lab_collection['copied']),
               'protected_private_count': len(protected),
               'all_private_progress_unchanged': True,
               'stock_hook_game_runner_core_original_wrapper_unchanged': True,
               'exact_returned_lab_sha256': digest(lab / 'platform-lab'),
               'user_report': 'Completed; clicks between tests; text hard to read; returned to regular launcher.',
               'new_build_installed': False, 'test_rearmed': False}
    for name, value in [('lab-analysis.json', analysis), ('lab-verification.json', summary)]:
        (archive / name).write_text(json.dumps(value, indent=2) + '\n')
    target = ROOT / 'evidence/2026-10-04/platform-lab-1-return'; target.mkdir(exist_ok=True)
    selected = [(run / name, name) for name in ('results.log', 'startup.log', 'wrapper.log')]
    selected += [(p, p.name) for p in sorted(run.glob('audio-*.csv')) if p.name != 'audio-rate_probe.csv']
    selected += [(archive / name, name) for name in ('lab-analysis.json', 'lab-verification.json')]
    index = ROOT / 'evidence/manifest.json'; provenance = json.loads(index.read_text())
    for source, name in selected:
        destination = target / name
        assert not destination.exists() or digest(destination) == digest(source), 'Never replace published return bytes'
        shutil.copy2(source, destination)
        assert digest(source) == digest(destination)
        item = {'source': source.relative_to(ROOT).as_posix(),
                'published': destination.relative_to(ROOT).as_posix(),
                'source_sha256': digest(source), 'published_sha256': digest(destination),
                'bytes': destination.stat().st_size, 'normalized': False}
        if not any(e['published'] == item['published'] for e in provenance['entries']):
            provenance['entries'].append(item)
    index.write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--before', type=Path, required=True)
    args = parser.parse_args(); review(args.archive.resolve(), args.before.resolve())
