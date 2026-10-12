"""Explicit retry only: archive return, verify unchanged setup, write one marker."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,sys
ROOT=Path(__file__).resolve().parent.parent
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'build'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def digest(p):return sha256(p.read_bytes()).hexdigest()
def rearm():
    card=Path('I:/').resolve();old=card/'retro/snes-mvp';test=card/'retro/snes-combined-gameplay1'
    installer=module('manual_rearm_installer','install-combined-gameplay.py')
    q=json.loads((ROOT/'build/combined-gameplay-private-v1/verification.json').read_text())
    for n in ('snes-mvp','plus-a7.so','launch.sh','suite-identity.json'):
        expected=digest(ROOT/'build/combined-gameplay-private-v1'/('verification.json' if n=='suite-identity.json' else n))
        assert digest(test/n)==expected,n
    assert digest(old/'launch.sh')==digest(ROOT/'build/combined-gameplay-private-v1/dispatch.sh')
    for n,h in installer.baseline.BOOT_EXPECTED.items():assert digest(card/n)==h,n
    assert digest(card/'retro/init')==installer.baseline.baseline.HOOK
    assert (test/'last-launch').read_bytes()==installer.MARKER
    # Complete private archive and fresh read-only FAT health check. No replay,
    # benchmarks, builds, runtime analysis, save migration or payload replacement.
    collector=module('manual_rearm_collector','archive-a7-pair-card.py')
    archive=collector.archive(card)
    before=json.loads((archive/'archive.json').read_text())['all_retro_files']
    installer.baseline.atomic(old/'armed',installer.MARKER,old)
    assert (old/'armed').read_bytes()==installer.MARKER
    assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/snes-mvp/armed']
    for e in before:assert digest(card/e['path'])==e['sha256'],e['path']
    proof={'version':q['version'],'reason':'User explicitly requested unchanged retry after forgetting library B exit',
        'archive':archive.name,'one_shot_armed':True,'fat_clean':True,'only_card_write':'retro/snes-mvp/armed',
        'all_existing_files_unchanged':len(before),'extra_tests':0}
    (archive/'manual-gameplay-rearm.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
if __name__=='__main__':rearm()
