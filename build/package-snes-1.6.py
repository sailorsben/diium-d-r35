"""Install verified full-render MVP in its owned folder; preserve stock/progress."""
from pathlib import Path
from datetime import datetime,timezone
from hashlib import sha256
import argparse,importlib.util,json,os,shutil,struct,zlib
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('baseline',ROOT/'build/package-snes-mvp.py')
baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
CHECKS=ROOT/'build/snes-mvp/out/verification.json'
PACKAGE=ROOT/'SNES-MVP-v1.6'
def digest(path): return sha256(path.read_bytes()).hexdigest()
def atomic(path,data):
    temporary=path.with_name(path.name+'.v16-tmp')
    assert not temporary.exists(),temporary
    with temporary.open('xb') as f: f.write(data);f.flush();os.fsync(f.fileno())
    assert digest(temporary)==sha256(data).hexdigest()
    os.replace(temporary,path)
def prepare():
    checks=json.loads(CHECKS.read_text());assert checks['passed'] and checks['version']=='1.6'
    payload=PACKAGE/'retro/snes-mvp';payload.mkdir(parents=True,exist_ok=True)
    for source,name,key in ((ROOT/'build/snes-mvp/out/snes-mvp','snes-mvp','binary_sha256'),
                            (ROOT/'build/plus-a7-out/plus-a7.so','plus-a7.so','core_sha256')):
        assert digest(source)==checks[key];shutil.copy2(source,payload/name)
    shutil.copy2(ROOT/'build/snes-mvp/launch.sh',payload/'launch.sh')
    instructions='''SNES MVP 1.6: full-render Cortex-A7 test

Same library, controls and pause menu. This boot uses an isolated A7 Plus core;
stock core/driver/launcher files remain intact. Every core frame is drawn:
adaptive holding is disabled, with no superseding queued frames.
Audio is delivered first and serviced independently. Display uses an ordered
three-source-buffer queue, releasing scaled source data before scanout waits.
The proven splash handshake, GPIO map and kernel-clock waits remain.

Launch Final Fantasy VI (not Rev1), MENU -> Load snapshot, then Resume.
Your last snapshot has a separate qualified copy for this core. Original state
and SRAM remain intact. Play opening/story or cave/map -> party menu -> map.
Try five minutes of normal play, Save/Load snapshot and Exit. Report lag,
crackles, picture corruption or any freeze. Shutdown and reconnect the card.
The returned report now records all drawings, display completion/queue waits,
both workers' CPU, pacing debt and exact software PCM clears/remainder.

The one-shot marker is consumed at boot; the following reboot takes stock.
Local ARM checks establish equivalence/ownership, not physical 60 FPS.
'''
    (payload/'TEST-ME.txt').write_text(instructions,newline='\n')
    (PACKAGE/'manifest.json').write_text(json.dumps(checks,indent=2)+'\n')
    return payload,checks
def update(card):
    card=card.resolve();assert str(card).lower() in ('d:\\','d:/')
    target=card/'retro/snes-mvp';assert target.is_dir() and not (target/'armed').exists()
    assert digest(card/'retro/init')=='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
    assert digest(target/'init.stock')==baseline.EXPECTED['retro/init']
    for name,wanted in baseline.EXPECTED.items():
        if name!='retro/init': assert digest(card/name)==wanted,name
    assert shutil.disk_usage(card).free>4*1024*1024
    payload,checks=prepare()
    states=list((target/'saves').glob('game-a27f1c7a-3145728-core-5ba71d2a-656816.state'))
    assert len(states)==1,'Expected exact returned FF6 snapshot'
    source=states[0];assert digest(source)==checks['qualified_snapshot_sha256'],'Snapshot changed since qualification'
    data=source.read_bytes();assert data[:8]==b'D35MVP01' and len(data)==40+531668
    assert struct.unpack_from('<I',data,32)[0]==zlib.crc32(data[40:])&0xffffffff
    migrated=bytearray(data);struct.pack_into('<II',migrated,20,int(checks['core_crc32'],16),checks['core_bytes'])
    new_state=target/'saves'/f"game-a27f1c7a-3145728-core-{checks['core_crc32']}-{checks['core_bytes']}.state"
    assert not new_state.exists() or new_state.read_bytes()==migrated,'Refusing to overwrite progressed new-core snapshot'
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    archive=ROOT/'device-evidence'/('snes-mvp-1.6-install-'+stamp);archive.mkdir()
    shutil.copytree(target,archive/'snes-mvp.before')
    shutil.copy2(card/'retro/init',archive/'init.before')
    protected={p.relative_to(card).as_posix():digest(p) for folder in
               ('retro/states','retro/saves','retro/snes-mvp/saves')
               for p in (card/folder).rglob('*') if p.is_file()}
    for folder in ('retro/states','retro/saves'):
        if (card/folder).is_dir(): shutil.copytree(card/folder,archive/'card'/folder)
    (archive/'protected.json').write_text(json.dumps(protected,indent=2)+'\n')
    changed=[];created_state=False
    try:
        for name in ('snes-mvp','plus-a7.so','launch.sh','TEST-ME.txt'):
            atomic(target/name,(payload/name).read_bytes());changed.append(name)
            assert digest(target/name)==digest(payload/name)
        if not new_state.exists(): atomic(new_state,migrated);created_state=True
        assert new_state.read_bytes()==migrated
        for name,wanted in protected.items(): assert digest(card/name)==wanted,name
        for name,wanted in baseline.EXPECTED.items():
            if name!='retro/init': assert digest(card/name)==wanted,name
        assert digest(card/'retro/init')==digest(archive/'init.before')
        atomic(target/'armed',b'SNES-MVP-v1.6 full-render A7 one-shot\n')
    except Exception:
        for name in changed:
            old=archive/'snes-mvp.before'/name
            if old.exists(): atomic(target/name,old.read_bytes())
            elif (target/name).exists(): (target/name).unlink()
        if created_state and new_state.exists() and new_state.read_bytes()==migrated: new_state.unlink()
        raise
    result={'version':'1.6','one_shot_armed':True,'stock_binaries_unchanged':True,
            'boot_hook_unchanged':True,'original_private_files_unchanged':len(protected),
            'snapshot_migration':'separate qualified FF6 copy; originals preserved',
            'binary_sha256':digest(target/'snes-mvp'),'core_sha256':digest(target/'plus-a7.so'),
            'wrapper_sha256':digest(target/'launch.sh'),'hardware_result':'pending'}
    (archive/'installation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return result
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--update',action='store_true')
    parser.add_argument('--card',default='D:/');args=parser.parse_args()
    if args.update:update(Path(args.card))
    else:prepare();print('Prepared verified local 1.6 payload; card unchanged')
