"""Stage the explicitly authorized measurement one-shot on the reassigned I: card."""
from pathlib import Path
from hashlib import sha256
import importlib.util, json, subprocess, sys, zipfile, zlib
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/a7-pair-private-v1'
MARKER=b'SNES-pair1 separate A7 measurement only; baseline/combined ABBA replay\n'
def digest(p): return sha256(p.read_bytes()).hexdigest()
def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'build'/filename)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
baseline=module('pair_install_baseline','package-snes-1.19.py')
def health(archive,name):
    r=subprocess.run(['chkdsk','I:'],capture_output=True,text=True)
    (archive/name).write_text(r.stdout+r.stderr,encoding='utf-8')
    assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
def install(archive):
    archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
    a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
    card=Path('I:/').resolve();target=card/'retro/snes-pair1';old=card/'retro/snes-mvp'
    assert str(card).lower() in ('i:/','i:\\') and target.resolve().is_relative_to(card) and not target.exists()
    q=json.loads((OUT/'verification.json').read_text())
    assert q['passed'] and q['native_client_qualified'] and q['wrapper_qualified'] and not q['hardware_measured'] and not q['production_replacement']
    for n,h in q['source_hashes'].items(): assert digest(ROOT/n)==h,n
    for n,h in q['payload_hashes'].items(): assert digest(OUT/n)==h,n
    for n,h in q['proof_hashes'].items(): assert digest(OUT/n)==h,n
    for e in a['all_retro_files']:assert digest(card/e['path'])==e['sha256'],e['path']
    focus=json.loads((ROOT/'releases/snes-focus-1/manifest.json').read_text())
    for n,k in [('snes-mvp','binary_sha256'),('plus-a7.so','core_sha256')]:assert digest(old/n)==focus[k]
    assert digest(old/'launch.sh')==digest(ROOT/'build/a7-cost-private-v9/dispatch.sh')
    for n,h in baseline.BOOT_EXPECTED.items():assert digest(card/n)==h,n
    assert digest(card/'retro/init')==baseline.baseline.HOOK
    assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
    health(archive,'chkdsk-immediately-before-pair.txt')
    matches=[]
    for folder in (card/'002',card/'ROMs/SNES'):
        if not folder.exists():continue
        for p in folder.iterdir():
            if p.suffix.lower()=='.zip':
                with zipfile.ZipFile(p) as z:
                    if any(i.CRC==0xa27f1c7a and i.file_size==3145728 for i in z.infolist()):matches.append(p)
            elif p.suffix.lower() in ('.smc','.sfc') and p.stat().st_size==3145728 and zlib.crc32(p.read_bytes())==0xa27f1c7a:matches.append(p)
    assert matches,'Owner ROM absent'
    rom=sorted(matches)[0];rom_hash=digest(rom)
    payload={n:(OUT/n).read_bytes() for n in q['payload_hashes'] if n!='dispatch.sh'}
    payload.update({'ROM-PATH.txt':('/media/sdcardb1/'+rom.relative_to(card).as_posix()+'\n').encode(),
        'suite-identity.json':(OUT/'verification.json').read_bytes(),'TEST-ME.txt':(ROOT/'docs/snes-a7-pair-test.txt').read_bytes()})
    original=(old/'launch.sh').read_bytes();marker=old/'armed';created=[];dispatch=False
    protected={e['path']:e['sha256'] for e in a['all_retro_files'] if e['path']!='retro/snes-mvp/launch.sh'}
    def verify():
        for n,h in protected.items():assert digest(card/n)==h,n
        for n,raw in payload.items():assert (target/n).read_bytes()==raw,n
        assert digest(rom)==rom_hash
    target.mkdir()
    try:
        for n,raw in payload.items():baseline.atomic(target/n,raw,target);created.append(n)
        baseline.atomic(old/'launch.sh',(OUT/'dispatch.sh').read_bytes(),old);dispatch=True
        verify();health(archive,'chkdsk-after-pair-payload.txt')
        baseline.atomic(marker,MARKER,old)
        assert marker.read_bytes()==MARKER
        assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/snes-mvp/armed']
        health(archive,'chkdsk-after-pair-arm.txt');verify()
        assert (old/'launch.sh').read_bytes()==(OUT/'dispatch.sh').read_bytes()
    except Exception:
        health(archive,'chkdsk-before-pair-rollback.txt')
        if marker.exists():assert marker.read_bytes()==MARKER;marker.unlink()
        if dispatch:baseline.atomic(old/'launch.sh',original,old)
        for n in reversed(created):(target/n).unlink()
        target.rmdir();raise
    proof={'version':'1.19-pair1','card':'I:','archive':archive.name,'protected_retro_files':len(protected),
        'payload_hashes':{n:sha256(raw).hexdigest() for n,raw in payload.items()},'dispatch_sha256':digest(old/'launch.sh'),
        'production_replacement':False,'physical_result':'PENDING','one_shot_armed':True,'all_fat_checks_clean':True}
    (archive/'pair-installation.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
if __name__=='__main__': install(Path(sys.argv[1]))
