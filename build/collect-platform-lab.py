"""Archive lab results and all private progress read-only before any update."""
from pathlib import Path
from hashlib import sha256
import argparse
import importlib.util
import json
import shutil

ROOT = Path(__file__).resolve().parent.parent

def digest(p): return sha256(p.read_bytes()).hexdigest()

def collect(card):
    card = card.resolve(); lab = card / 'retro/platform-lab'
    assert lab.is_dir() and (lab / 'platform-lab').is_file()
    spec = importlib.util.spec_from_file_location('collect_mvp', ROOT / 'build/collect-snes-mvp.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    archive = module.collect(card)
    entries = []
    for source in sorted(lab.rglob('*')):
        if not source.is_file(): continue
        assert not source.is_symlink()
        relative = source.relative_to(lab)
        target = archive / 'platform-lab' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        before = digest(source); shutil.copy2(source, target)
        assert before == digest(source) == digest(target)
        entries.append({'relative_path': relative.as_posix(), 'sha256': before,
                        'bytes': source.stat().st_size})
    result = {'archive': str(archive), 'card_writes': 0,
              'lab_armed': (lab / 'armed').exists(), 'copied': entries}
    (archive / 'lab-collection.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'archive': str(archive), 'copied_lab_files': len(entries), 'card_writes': 0}, indent=2))
    return archive

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--card', type=Path, default=Path('D:/'))
    collect(parser.parse_args().card)
