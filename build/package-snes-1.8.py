"""Install the forward A7 build over exact returned1.7; preserve new SRAM, arm last."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,importlib.util,json,shutil,struct,zlib
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('prior',ROOT/'build/package-snes-1.6.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
digest=prior.digest;atomic=prior.atomic

def update(card):
    card=card.resolve();assert str(card).lower() in ('d:\\','d:/')
    target=card/'retro/snes-mvp';assert target.is_dir() and not (target/'armed').exists()
    old=json.loads((ROOT/'releases/snes-mvp-1.7/manifest.json').read_text())
    checks=json.loads((ROOT/'build/snes-mvp/out/verification.json').read_text())
    assert checks['passed'] and checks['version']=='1.8'
    for name,key in (('snes-mvp','binary_sha256'),('launch.sh','wrapper_sha256'),('plus-a7.so','core_sha256')):
        assert digest(target/name)==old[key], 'Unexpected current owned file: '+name
    sources={'snes-mvp':ROOT/'build/snes-mvp/out/snes-mvp',
             'launch.sh':ROOT/'build/snes-mvp/launch.sh','plus-a7.so':ROOT/'build/plus-a7-out/plus-a7.so'}
    for name,key in (('snes-mvp','binary_sha256'),('launch.sh','wrapper_sha256'),('plus-a7.so','core_sha256')):
        assert digest(sources[name])==checks[key], 'Changed qualified build: '+name
    assert digest(card/'retro/init')=='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
    assert digest(target/'init.stock')==prior.baseline.EXPECTED['retro/init']
    for name,wanted in prior.baseline.EXPECTED.items():
        if name!='retro/init':assert digest(card/name)==wanted,name
    assert shutil.disk_usage(card).free>4*1024*1024
    source=target/'saves/game-a27f1c7a-3145728-core-5ba71d2a-656816.state'
    assert digest(source)==checks['qualified_snapshot_sha256'], 'Original qualified state changed'
    data=source.read_bytes();assert data[:8]==b'D35MVP01' and len(data)==531668+40
    assert struct.unpack_from('<I',data,32)[0]==zlib.crc32(data[40:])&0xffffffff
    migrated=bytearray(data);struct.pack_into('<II',migrated,20,int(checks['core_crc32'],16),checks['core_bytes'])
    new_state=target/'saves'/f"game-a27f1c7a-3145728-core-{checks['core_crc32']}-{checks['core_bytes']}.state"
    assert not new_state.exists() or new_state.read_bytes()==migrated, 'Progressed new-core state must be preserved'
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    archive=ROOT/'device-evidence'/('snes-mvp-1.8-install-'+stamp);archive.mkdir()
    shutil.copytree(target,archive/'snes-mvp.before')
    shutil.copy2(card/'retro/init',archive/'init.before')
    protected={p.relative_to(card).as_posix():digest(p) for folder in
               ('retro/states','retro/saves','retro/snes-mvp/saves')
               for p in (card/folder).rglob('*') if p.is_file()}
    for folder in ('retro/states','retro/saves'):
        if (card/folder).is_dir():shutil.copytree(card/folder,archive/'card'/folder)
    (archive/'protected.json').write_text(json.dumps(protected,indent=2)+'\n')
    instructions=b'''SNES MVP1.8: smarter Cortex-A7 rendering

Specialized NEON tile modes, cheaper palette lookups and vector backdrop/color
window passes. Full rendering, accurate Plus sound and ordered display remain.
Repeated shell/kernel captures and global sync are removed from gameplay.

Launch FF6 (not Rev1). Use the game's Continue to resume your NEW Save Point;
your latest in-game SRAM is preserved byte for byte. For the old location,
MENU -> Load snapshot has a separate qualified copy for this new core, but
that is older progress. Load snapshot can eventually save older SRAM on exit.

Play story/map -> FF6 party menu -> map and save/exit normally. Report speed,
crackles, corrupted graphics or a shutdown. No skipped/held drawings are enabled.
This is a forward optimized build; physical full speed is still to be tested.
The one-shot is consumed at boot; the following reboot takes stock.
'''
    payload={name:path.read_bytes() for name,path in sources.items()};payload['TEST-ME.txt']=instructions
    changed=[];created_state=False
    try:
        for name,raw in payload.items():
            atomic(target/name,raw);changed.append(name)
            assert (target/name).read_bytes()==raw,name
        if not new_state.exists():atomic(new_state,migrated);created_state=True
        for name,wanted in protected.items():assert digest(card/name)==wanted,name
        for name,wanted in prior.baseline.EXPECTED.items():
            if name!='retro/init':assert digest(card/name)==wanted,name
        assert digest(card/'retro/init')==digest(archive/'init.before')
        atomic(target/'armed',b'SNES-MVP-v1.8 smarter A7 one-shot\n')
    except Exception:
        for name in changed:atomic(target/name,(archive/'snes-mvp.before'/name).read_bytes())
        if created_state and new_state.exists() and new_state.read_bytes()==migrated:new_state.unlink()
        raise
    result={'version':'1.8','one_shot_armed':True,'stock_binaries_unchanged':True,
            'boot_hook_unchanged':True,'original_private_files_unchanged':len(protected),
            'new_save_point_sram_preserved':True,'snapshot_migration':'separate qualified older FF6 copy; Continue recommended',
            'binary_sha256':digest(target/'snes-mvp'),'wrapper_sha256':digest(target/'launch.sh'),
            'core_sha256':digest(target/'plus-a7.so'),'hardware_result':'pending'}
    (archive/'installation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--card',default='D:/')
    args=parser.parse_args();update(Path(args.card))
