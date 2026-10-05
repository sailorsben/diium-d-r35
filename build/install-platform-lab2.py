"""Publish lab2 and atomically update the exact collected/unarmed lab1 card."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import os
import shutil

ROOT=Path(__file__).resolve().parent.parent
BUILD=ROOT/'build/platform-lab2-out'
RELEASE=ROOT/'releases/platform-lab-2'
def digest(p): return sha256(p.read_bytes()).hexdigest()
def load(name,leaf):
    spec=importlib.util.spec_from_file_location(name,ROOT/'build'/leaf)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def publish():
    checked=json.loads((BUILD/'verification.json').read_text())
    assert checked['passed'] and not checked['hardware_qualified'] and checked['version']=='lab2'
    assert checked['binary_sha256']==digest(BUILD/'platform-lab')
    assert all(digest(ROOT/p)==h for p,h in checked['source_hashes'].items()), 'Qualified source changed'
    payload={'platform-lab':BUILD/'platform-lab','launch.sh':ROOT/'build/launch-platform-lab2.sh',
             'dispatch.sh':ROOT/'build/dispatch-platform-lab.sh','verification.json':BUILD/'verification.json',
             'abi.txt':BUILD/'abi.txt','selftest.log':BUILD/'selftest.log',
             'driver-trace-check.log':BUILD/'driver-trace-check.log','TEST-ME.txt':ROOT/'docs/platform-lab2-test.txt'}
    RELEASE.mkdir(exist_ok=True)
    for name,source in payload.items():
        target=RELEASE/name
        assert not target.exists() or digest(target)==digest(source), 'Published releases are immutable'
        shutil.copy2(source,target)
    manifest={name:digest(RELEASE/name) for name in payload}
    (RELEASE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); return manifest

def install(card,arm):
    card=card.resolve(); assert str(card).lower() in ('d:\\','d:/')
    baseline=load('baseline','install-platform-lab.py')
    lab=card/'retro/platform-lab'; mvp=card/'retro/snes-mvp'
    assert not (lab/'armed').exists() and not (mvp/'armed').exists(), 'Collect the armed run first'
    old=json.loads((ROOT/'releases/platform-lab-1/manifest.json').read_text())
    for name in ('platform-lab','launch.sh','TEST-ME.txt','manifest.json'):
        assert digest(lab/name)==digest(ROOT/'releases/platform-lab-1'/name), name
    assert digest(mvp/'launch.sh')==old['dispatch.sh']
    assert digest(mvp/'launch-game-1.8.sh')==baseline.WRAPPER
    assert digest(mvp/'snes-mvp')==baseline.RUNNER and digest(card/'retro/init')==baseline.HOOK
    for name,h in baseline.EXPECTED.items(): assert digest(card/name)==h,name
    assert shutil.disk_usage(card).free>12*1024*1024
    collector=load('lab_collection','collect-platform-lab.py'); archive=collector.collect(card)
    protected={p.relative_to(card).as_posix():digest(p)
               for folder in ('retro/snes-mvp/saves','retro/saves','retro/states')
               for p in (card/folder).rglob('*') if p.is_file()}
    cores={p.relative_to(card).as_posix():digest(p) for p in mvp.glob('*.so')}
    (archive/'lab-protected.json').write_text(json.dumps(protected,indent=2)+'\n')
    payload=('platform-lab','launch.sh','TEST-ME.txt','manifest.json')
    for name in payload: assert not (lab/(name+'.lab2-tmp')).exists()
    try:
        for name in payload:
            stage=lab/(name+'.lab2-tmp'); shutil.copy2(RELEASE/name,stage)
            assert digest(stage)==digest(RELEASE/name); os.replace(stage,lab/name)
        for name,h in {**baseline.EXPECTED,**protected,**cores}.items(): assert digest(card/name)==h,name
        assert digest(card/'retro/init')==baseline.HOOK and digest(mvp/'snes-mvp')==baseline.RUNNER
        assert digest(mvp/'launch-game-1.8.sh')==baseline.WRAPPER and digest(mvp/'launch.sh')==old['dispatch.sh']
        if arm:
            stage=lab/'armed.lab2-tmp'; assert not stage.exists()
            stage.write_text('platform-lab-2 one shot\n',newline='\n'); os.replace(stage,lab/'armed')
            stage=mvp/'armed.lab2-tmp'; assert not stage.exists()
            stage.write_text('dispatch platform-lab-2 only\n',newline='\n'); os.replace(stage,mvp/'armed')
        for name in payload: assert digest(lab/name)==digest(RELEASE/name)
    except BaseException:
        (lab/'armed').unlink(missing_ok=True); (mvp/'armed').unlink(missing_ok=True)
        for name in payload:
            (lab/(name+'.lab2-tmp')).unlink(missing_ok=True)
            shutil.copy2(archive/'platform-lab'/name,lab/name)
            assert digest(lab/name)==digest(archive/'platform-lab'/name)
        (lab/'armed.lab2-tmp').unlink(missing_ok=True); (mvp/'armed.lab2-tmp').unlink(missing_ok=True)
        raise
    result={'version':'lab2','installed_utc':datetime.now(timezone.utc).isoformat(),'archive':archive.name,
            'armed':arm,'protected_private_count':len(protected),'stock_and_private_unchanged':True,
            'hook_dispatcher_game_runner_core_original_wrapper_unchanged':True,'previous_lab_archived':True,
            'lab_sha256':digest(lab/'platform-lab'),'card_payload_verified':True}
    (archive/'lab-installation.json').write_text(json.dumps(result,indent=2)+'\n')
    (BUILD/'installation.json').write_text(json.dumps(result,indent=2)+'\n'); return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install',action='store_true'); parser.add_argument('--arm',action='store_true')
    parser.add_argument('--card',type=Path,default=Path('D:/')); args=parser.parse_args()
    assert not args.arm or args.install
    manifest=publish(); print(json.dumps(install(args.card,args.arm) if args.install else manifest,indent=2))
