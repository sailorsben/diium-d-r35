"""Healthy-card, archive/hash guarded experimental one-shot only."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/confuser-gameplay-private-v1'
MARKER=b'SNES confuser-gameplay1 experimental manual qualification; separate core/saves\n'
spec=importlib.util.spec_from_file_location('confuser_card_guard',ROOT/'build/package-snes-1.19.py')
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
    assert q['manual_controls'] and not q['forced_replay'] and not q['production_gate_passed']
    assert q['authorization'].startswith('User explicitly requested Load it to I')
    assert (ROOT/'docs/snes-confuser-gameplay.md').is_file()
    card=Path('I:/').resolve();old=card/'retro/snes-mvp';target=card/'retro/snes-confuser-gameplay1'
    assert str(card).lower() in ('i:/','i:\\') and target.resolve().is_relative_to(card) and not target.exists()
    assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
    for n,h in q['source_hashes'].items():assert digest(ROOT/n)==h,n
    for n,h in q['payload_hashes'].items():assert digest(OUT/n)==h,n
    for n,h in q['proof_hashes'].items():assert digest(OUT/n)==h,n
    for e in a['all_retro_files']:assert digest(card/e['path'])==e['sha256'],e['path']
    for n,h in guard.BOOT_EXPECTED.items():assert digest(card/n)==h,n
    assert digest(card/'retro/init')==guard.baseline.HOOK
    assert digest(old/'launch.sh')==digest(ROOT/'build/combined-gameplay-private-v1/dispatch.sh')
    assert digest(card/'retro/snes-combined-gameplay1/plus-a7.so')=='ee0b241c3b7c561e76efbedbbdcf37bf8e104bb6754d7b0493c3ed4774172155'
    assert digest(card/'retro/snes-combined-gameplay1/snes-mvp')==q['regular_runner_sha256']
    health(archive,'chkdsk-before-confuser-gameplay.txt')
    payload={n:(OUT/n).read_bytes() for n in q['payload_hashes'] if n!='dispatch.sh'}
    payload['suite-identity.json']=(OUT/'verification.json').read_bytes()
    payload['TEST-ME.txt']=(ROOT/'docs/snes-confuser-gameplay-test.txt').read_bytes()
    protected={e['path']:e['sha256'] for e in a['all_retro_files'] if e['path']!='retro/snes-mvp/launch.sh'}
    original=(old/'launch.sh').read_bytes();marker=old/'armed';created=[];dispatch=False
    target.mkdir();(target/'saves').mkdir()
    def verify():
        for n,h in protected.items():assert digest(card/n)==h,n
        for n,raw in payload.items():assert (target/n).read_bytes()==raw,n
    try:
        for n,raw in payload.items():guard.atomic(target/n,raw,target);created.append(n)
        guard.atomic(old/'launch.sh',(OUT/'dispatch.sh').read_bytes(),old);dispatch=True
        verify();health(archive,'chkdsk-after-confuser-gameplay-payload.txt')
        guard.atomic(marker,MARKER,old);assert marker.read_bytes()==MARKER
        assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/snes-mvp/armed']
        health(archive,'chkdsk-after-confuser-gameplay-arm.txt');verify()
        assert (old/'launch.sh').read_bytes()==(OUT/'dispatch.sh').read_bytes()
    except Exception:
        health(archive,'chkdsk-before-confuser-gameplay-rollback.txt')
        if marker.exists():assert marker.read_bytes()==MARKER;marker.unlink()
        if dispatch:guard.atomic(old/'launch.sh',original,old)
        for n in reversed(created):(target/n).unlink()
        (target/'saves').rmdir();target.rmdir();raise
    proof={'version':q['version'],'card':'I:','archive':archive.name,'one_shot_armed':True,'fat_checks_clean':True,
     'experimental_qualification':True,'production_gate_passed':False,'hardware_saving_measured':False,
     'original_retro_files_protected':len(protected),'original_progress_unchanged':True,'new_test_saves_separate':True,
     'production_binaries_unchanged':True,'payload_hashes':{n:sha256(raw).hexdigest() for n,raw in payload.items()},
     'dispatch_sha256':digest(old/'launch.sh'),'long_gameplay_result':'PENDING'}
    (archive/'confuser-gameplay-installation.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
if __name__=='__main__':install(Path(sys.argv[1]))
