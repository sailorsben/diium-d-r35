"""Guarded I:-only installation of explicitly requested experimental subset."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ability-regression-private-v1'
MARKER=b'SNES ability2 automated18-case generalized renderer regression; experimental\n'
spec=importlib.util.spec_from_file_location('ability2_card_guard',ROOT/'build/package-snes-1.19.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
def digest(p):return sha256(p.read_bytes()).hexdigest()
def health(archive,name):
    r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True)
    (archive/name).write_text(r.stdout+r.stderr,encoding='utf-8')
    assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
def install(archive):
    archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
    a=json.loads((archive/'archive.json').read_text());q=json.loads((OUT/'verification.json').read_text())
    assert a['fat_clean'] and a['card_writes']==0 and q['passed'] and q['archive']==archive.name
    assert q['native_client_qualified'] and q['wrapper_qualified'] and q['renderer_changed'] and not q['production_gate_passed']
    assert q['authorization']=='Fix shared failure patterns and provide an automated subset of the largest set.'
    card=Path('I:/').resolve();old=card/'retro/snes-mvp';target=card/'retro/snes-ability2'
    assert str(card).lower() in ('i:/','i:\\') and target.resolve().is_relative_to(card) and not target.exists()
    assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
    for group in ('source_hashes','payload_hashes','proof_hashes'):
        for n,h in q[group].items():assert digest(ROOT/n)==h,n
    for e in a['all_retro_files']:assert digest(card/e['path'])==e['sha256'],e['path']
    for n,h in guard.BOOT_EXPECTED.items():assert digest(card/n)==h,n
    assert digest(card/'retro/init')==guard.baseline.HOOK
    assert digest(card/'retro/snes-ability1/plus-a7.so')=='d5761eacc68fbcba91052de19d37ca9f159fb2b40df7c9272f49398b9b4f880a'
    health(archive,'chkdsk-before-ability2.txt')
    payload={'ability-suite':OUT/'ability-suite','plus-a7.so':OUT/'plus-a7.so','launch.sh':OUT/'launch.sh',
        'ROM-PATH.txt':OUT/'ROM-PATH.txt','plan.json':OUT/'plan.json','suite-identity.json':OUT/'verification.json',
        'TEST-ME.txt':ROOT/'docs/snes-ability-regression-test.txt'}
    for p in (OUT/'cases').rglob('*'):
        if p.is_file():payload['cases/'+p.relative_to(OUT/'cases').as_posix()]=p
    assert len([n for n in payload if n.endswith('/scene.state')])==18
    assert shutil.disk_usage(card).free>sum(p.stat().st_size for p in payload.values())+256*1024*1024
    protected={e['path']:e['sha256'] for e in a['all_retro_files'] if e['path']!='retro/snes-mvp/launch.sh'}
    original=(old/'launch.sh').read_bytes();marker=old/'armed';created=[];dispatch=False
    target.mkdir();(target/'saves').mkdir()
    def verify():
        for n,h in protected.items():assert digest(card/n)==h,n
        for n,p in payload.items():assert digest(target/n)==digest(p),n
    try:
        for n,p in payload.items():
            dest=target/n;dest.parent.mkdir(parents=True,exist_ok=True);guard.atomic(dest,p.read_bytes(),target);created.append(dest)
        verify();health(archive,'chkdsk-after-ability2-payload.txt')
        guard.atomic(old/'launch.sh',(OUT/'dispatch.sh').read_bytes(),old);dispatch=True
        guard.atomic(marker,MARKER,old);assert marker.read_bytes()==MARKER
        assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/snes-mvp/armed']
        health(archive,'chkdsk-after-ability2-arm.txt');verify()
        assert (old/'launch.sh').read_bytes()==(OUT/'dispatch.sh').read_bytes()
    except Exception:
        # Never delete from a possibly damaged FAT. Preserve failed installation
        # and require collection if this fresh read-only health check fails.
        health(archive,'chkdsk-before-ability2-rollback.txt')
        if marker.exists():assert marker.read_bytes()==MARKER;marker.unlink()
        if dispatch:guard.atomic(old/'launch.sh',original,old)
        for p in reversed(created):p.unlink()
        for p in sorted((p for p in target.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):p.rmdir()
        target.rmdir();raise
    proof={'version':q['version'],'card':'I:','archive':archive.name,'one_shot_armed':True,'fat_checks_clean':True,
        'production_gate_passed':False,'renderer_changed':True,'hardware_result':'PENDING','cases':18,
        'original_retro_files_protected':len(protected),'original_progress_unchanged':True,'production_binaries_unchanged':True,
        'payload_files':len(payload),'payload_hashes':{n:digest(p) for n,p in payload.items()},'dispatch_sha256':digest(old/'launch.sh')}
    (archive/'ability2-installation.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='payload_hashes'},indent=2))
if __name__=='__main__':install(Path(sys.argv[1]))
