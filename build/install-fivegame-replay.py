"""Arm the replay-observable matched suite; keep flash/init/saves/evidence exact."""
from pathlib import Path
import importlib.util,json,shutil,sys
from attempt_archive import digest,verify_saved

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fivegame-kernel-private-v2'
TARGET='retro/snes-fivegame-kernel2'
MARKER=b'Matched five-game kernel UART replay-progress 20 epochs once\n'

def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'build'/name)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def stage(card,payload,dispatch,atomic,health,verify,inject=lambda _:None):
    target=card/TARGET;mvp=card/'retro/snes-mvp';old=(mvp/'launch.sh').read_bytes()
    assert not target.exists() and not list(card.rglob('armed')) and not list(card.rglob('Code.bkp'))
    target.mkdir()
    try:
        for name,data in payload.items():
            path=Path(name);assert not path.is_absolute() and '..' not in path.parts
            p=target/path;p.parent.mkdir(parents=True,exist_ok=True);atomic(p,data)
        inject('payload');verify();health('payload')
        atomic(mvp/'launch.sh',dispatch);inject('dispatcher')
        atomic(target/'armed',MARKER);inject('target_marker')
        atomic(mvp/'armed',MARKER);inject('mvp_marker');verify();health('armed')
        assert sorted(p.relative_to(card).as_posix() for p in card.rglob('armed'))==sorted([TARGET+'/armed','retro/snes-mvp/armed'])
    except BaseException:
        health('before-rollback')
        for p in [target/'armed',mvp/'armed']:
            if p.exists():assert p.read_bytes()==MARKER;p.unlink()
        assert (mvp/'launch.sh').read_bytes() in (old,dispatch)
        atomic(mvp/'launch.sh',old)
        raise
    return old

def main(archive):
    q=json.loads((OUT/'qualification.json').read_text())
    assert q['passed'] and q['measurement_only'] and not q['production_gate'] and len(q['actual_epochs'])==20 and q['native_policies']==[0,1]
    for n,h in q['sources'].items():assert digest(ROOT/n)==h,n
    for n,h in q['payload_hashes'].items():assert digest(OUT/n)==h,n
    iq=json.loads((OUT/'installation-qualification.json').read_text())
    assert iq['passed'] and iq['installer_sha256']==digest(Path(__file__)) and iq['qualification_sha256']==digest(OUT/'qualification.json')
    replay=json.loads((OUT/'replay-checks.json').read_text())
    assert replay['passed'] and len(replay['checks'])==9 and digest(OUT/'replay-checks.json')==iq['replay_checks_sha256']
    for n,h in replay['sources'].items():assert digest(ROOT/'build'/n)==h,n
    assert digest(OUT/'replay-checks.log')==replay['log_sha256']
    physical=ROOT/'evidence/2026-10-17/uart-kernel-reflash/verified-return.json'
    pv=json.loads(physical.read_text());assert all(pv[n] for n in ['two_pass_flash_exact','runtime_UART_module_absent','fresh_boot_verified','idle_IRQ_flood_acceptance_passed'])
    fix=load('install-uart-fix.py');assert not fix.git('status','--porcelain')
    commit=fix.git('rev-parse','HEAD');assert commit==fix.git('rev-parse','origin/codex/snes-mvp-foundation')
    archive=archive.resolve();assert archive.is_relative_to((ROOT/'device-evidence').resolve())
    a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text())
    assert a['fat_clean'] and a['card_writes']==o['card_writes']==0;verify_saved(archive,a)
    entries=a['all_retro_files']+o['files'];expected={e['path']:e['sha256'] for e in entries}
    card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\')
    assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}==set(expected)
    for e in entries:
        assert digest(card/e['path'])==e['sha256'],e['path']
        if e['stored']:assert digest(archive/e['path'])==e['sha256'],e['path']
    assert digest(card/'retro/init')=='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
    restore_dispatch=ROOT/'releases/snes-mvp-1.19/launch.sh'
    assert digest(card/'retro/snes-mvp/launch.sh')==digest(restore_dispatch)=='35b1c32fa5924e33a0f1da47833b6710e53dadc5ebd832a6b998a86236e2cc13'
    for n,h in load('package-snes-1.19.py').BOOT_EXPECTED.items():assert digest(card/n)==h,n
    payload={n:(OUT/n).read_bytes() for n in q['payload_hashes'] if n!='dispatch.sh'}
    for name in ['qualification.json','installation-qualification.json','replay-checks.json']:payload[name]=(OUT/name).read_bytes()
    assert shutil.disk_usage(card).free>sum(map(len,payload.values()))+64*1024*1024
    protected={n:h for n,h in expected.items() if n!='retro/snes-mvp/launch.sh'}
    def verify():
        for n,h in protected.items():assert digest(card/n)==h,n
        for n,data in payload.items():assert (card/TARGET/n).read_bytes()==data,n
    health=lambda label:fix.health(archive,'fivegame-replay-'+label)
    health('before')
    old=stage(card,payload,(OUT/'dispatch.sh').read_bytes(),fix.atomic,health,verify)
    r={'version':'fivegame-kernel2','source_commit':commit,'archive':archive.name,'target':TARGET,
       'one_shot_armed':True,'physical_result':'PENDING','kernel_UART_preserved':True,
       'kernel_verification_receipt_sha256':digest(physical),'normal_init_sha256':digest(card/'retro/init'),
       'protected_existing_files':len(protected),'all_existing_files_hashed':len(entries),
       'only_changed_existing_file':'retro/snes-mvp/launch.sh','previous_dispatch_sha256':__import__('hashlib').sha256(old).hexdigest(),
       'previous_dispatch_restore_source':restore_dispatch.relative_to(ROOT).as_posix(),
       'dispatch_sha256':digest(OUT/'dispatch.sh'),'marker_sha256':__import__('hashlib').sha256(MARKER).hexdigest(),
       'payload_hashes':{n:__import__('hashlib').sha256(data).hexdigest() for n,data in payload.items()},
       'clean_FAT':True,'no_full_backup':True,'firmware_update_absent':True}
    text=json.dumps(r,indent=2)+'\n';(archive/'fivegame-replay-installation.json').write_text(text)
    (ROOT/'evidence/2026-10-17/fivegame-replay/installation.json').write_text(text);print(text)

if __name__=='__main__':main(Path(sys.argv[1]))
