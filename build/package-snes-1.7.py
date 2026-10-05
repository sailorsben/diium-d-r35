"""Install the authorized logging retry over the qualified 1.6 card, arm last."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,importlib.util,json,shutil
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('prior',ROOT/'build/package-snes-1.6.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
digest=prior.digest;atomic=prior.atomic

def update(card):
    card=card.resolve();assert str(card).lower() in ('d:\\','d:/')
    target=card/'retro/snes-mvp';assert target.is_dir() and not (target/'armed').exists()
    old=json.loads((ROOT/'releases/snes-mvp-1.6/manifest.json').read_text())
    checks=json.loads((ROOT/'build/snes-mvp/out/verification.json').read_text())
    assert checks['passed'] and checks['version']=='1.7'
    for name,key in (('snes-mvp','binary_sha256'),('launch.sh','wrapper_sha256'),('plus-a7.so','core_sha256')):
        assert digest(target/name)==old[key], 'Unexpected current owned file: '+name
    assert checks['core_sha256']==old['core_sha256'], 'Logging retry must retain the tested A7 core'
    assert digest(ROOT/'build/snes-mvp/out/snes-mvp')==checks['binary_sha256']
    assert digest(ROOT/'build/snes-mvp/launch.sh')==checks['wrapper_sha256']
    assert digest(card/'retro/init')=='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
    assert digest(target/'init.stock')==prior.baseline.EXPECTED['retro/init']
    for name,wanted in prior.baseline.EXPECTED.items():
        if name!='retro/init':assert digest(card/name)==wanted,name
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    archive=ROOT/'device-evidence'/('snes-mvp-1.7-install-'+stamp);archive.mkdir()
    shutil.copytree(target,archive/'snes-mvp.before')
    shutil.copy2(card/'retro/init',archive/'init.before')
    protected={p.relative_to(card).as_posix():digest(p) for folder in
               ('retro/states','retro/saves','retro/snes-mvp/saves')
               for p in (card/folder).rglob('*') if p.is_file()}
    for folder in ('retro/states','retro/saves'):
        if (card/folder).is_dir():shutil.copytree(card/folder,archive/'card'/folder)
    (archive/'protected.json').write_text(json.dumps(protected,indent=2)+'\n')
    instructions=b'''SNES MVP 1.7 logging retry

Same A7 core, full rendering, UI and display/audio pipeline as 1.6.
This adds fresh session progress once/second in RAM and bounded persisted
progress/thread/kernel/memory/helper snapshots about every five seconds.
Logging overhead is measured; it is not a promised speed repair.

Launch FF6 (not Rev1), MENU -> Load snapshot -> Resume. Play the same map/menu
and story workload. If badly laggy, try MENU -> Exit so final totals survive;
if it powers off again, reconnect the card. Existing state/SRAM are preserved.
About one minute of bad behavior is enough; five minutes if it runs normally.
The one-shot is consumed at boot; the following reboot takes stock.
'''
    payload={'snes-mvp':(ROOT/'build/snes-mvp/out/snes-mvp').read_bytes(),
             'launch.sh':(ROOT/'build/snes-mvp/launch.sh').read_bytes(),'TEST-ME.txt':instructions}
    changed=[]
    try:
        for name,data in payload.items():
            atomic(target/name,data);changed.append(name)
            assert (target/name).read_bytes()==data,name
        for name,wanted in protected.items():assert digest(card/name)==wanted,name
        for name,wanted in prior.baseline.EXPECTED.items():
            if name!='retro/init':assert digest(card/name)==wanted,name
        assert digest(card/'retro/init')==digest(archive/'init.before')
        assert digest(target/'plus-a7.so')==old['core_sha256']
        atomic(target/'armed',b'SNES-MVP-v1.7 bounded logging retry one-shot\n')
    except Exception:
        for name in changed:atomic(target/name,(archive/'snes-mvp.before'/name).read_bytes())
        raise
    result={'version':'1.7','one_shot_armed':True,'stock_binaries_unchanged':True,
            'boot_hook_unchanged':True,'original_private_files_unchanged':len(protected),
            'core_unchanged_from_1_6':True,'binary_sha256':digest(target/'snes-mvp'),
            'wrapper_sha256':digest(target/'launch.sh'),'core_sha256':digest(target/'plus-a7.so'),
            'hardware_result':'logging retry pending'}
    (archive/'installation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--card',default='D:/')
    args=parser.parse_args();update(Path(args.card))
