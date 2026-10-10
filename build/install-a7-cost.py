"""Archive-first one-shot measurement suite; never replace a production core."""
from pathlib import Path
from hashlib import sha256
import importlib.util, json, subprocess, sys
ROOT=Path(__file__).resolve().parent.parent
MARKER=b'SNES-cost1 diagnostic measurement suite; baseline renderer only; no production candidate\n'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/'build'/path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
baseline=module('cost_install_baseline','package-snes-1.19.py')
def health(archive,name):
    r=subprocess.run(['chkdsk','D:'],capture_output=True,text=True)
    (archive/name).write_text(r.stdout,encoding='utf-8')
    assert r.returncode==0 and '11EB-1465' in r.stdout and 'Windows has scanned the file system and found no problems.' in r.stdout
def install(tree):
    assert tree.startswith('a7-cost-private-') and '/' not in tree and '\\' not in tree
    out=ROOT/'build'/tree;card=Path('D:/').resolve();target=card/'retro/snes-cost1';old=card/'retro/snes-mvp'
    assert str(card).lower() in ('d:/','d:\\')
    assert target.resolve().is_relative_to(card) and not target.exists()
    q=json.loads((out/'verification.json').read_text());assert q['passed'] and not q['hardware_measured'] and not q['candidate_installed']
    for group in ('source_hashes','artifacts'):
        for name,wanted in q[group].items():assert digest(ROOT/name)==wanted,name
    for p,key in [('unit-suite','suite_sha256'),('core/snes9x2005_plus_libretro.so','core_sha256'),('replay.state','state_sha256')]:assert digest(out/p)==q[key],p
    old_release=json.loads((ROOT/'releases/snes-focus-1/manifest.json').read_text())
    for p,key in [('snes-mvp','binary_sha256'),('plus-a7.so','core_sha256'),('launch.sh','wrapper_sha256')]:assert digest(old/p)==old_release[key],p
    assert not list((card/'retro').rglob('armed')) and not (card/'retro/update/Code.bkp').exists()
    for p,wanted in baseline.BOOT_EXPECTED.items():assert digest(card/p)==wanted,p
    assert digest(card/'retro/init')==baseline.baseline.HOOK
    # Find the existing owner ROM by content, not a guessed game filename.
    import zipfile,zlib
    matches=[]
    for folder in (card/'002',card/'ROMs/SNES'):
        if not folder.exists():continue
        for p in folder.iterdir():
            if p.suffix.lower() not in ('.zip','.sfc','.smc'):continue
            if p.suffix.lower()=='.zip':
                with zipfile.ZipFile(p) as z:
                    if any(i.CRC==0xa27f1c7a and i.file_size==3145728 for i in z.infolist()):matches.append(p)
            elif p.stat().st_size==3145728 and zlib.crc32(p.read_bytes())==0xa27f1c7a:matches.append(p)
    assert matches,'Known owner ROM absent'
    rom=sorted(matches)[0]
    archive=baseline.collector.collect(card);health(archive,'chkdsk-before-cost.txt')
    records=json.loads((archive/'collection.json').read_text())['copied_and_hash_verified']
    protected={e['card_path']:e['sha256'] for e in records if e['card_path']!='retro/snes-mvp/launch.sh'}
    protected.update(baseline.BOOT_EXPECTED)
    lab=json.loads((archive/'lab-collection.json').read_text())
    protected.update({'retro/platform-lab/'+e['relative_path']:e['sha256'] for e in lab['copied']})
    for folder in (card/'retro').glob('spi-readback*'):
        for p in folder.rglob('*'):
            if p.is_file():protected[p.relative_to(card).as_posix()]=digest(p)
    payload={'unit-suite':(out/'unit-suite').read_bytes(),'measure-core.so':(out/'core/snes9x2005_plus_libretro.so').read_bytes(),
             'replay.state':(out/'replay.state').read_bytes(),'launch.sh':(out/'launch.sh').read_bytes(),
             'TEST-ME.txt':(ROOT/'docs/snes-a7-cost-test.txt').read_bytes(),
             'suite-identity.json':(json.dumps(q,indent=2)+'\n').encode()}
    # /usr/retro is the active card retro view; ROM paths use the known SD mount.
    payload['ROM-PATH.txt']=('/media/sdcardb1/'+rom.relative_to(card).as_posix()+'\n').encode()
    original=(old/'launch.sh').read_bytes();marker=old/'armed';created=[];dispatch=False
    target.mkdir()
    try:
        for name,raw in payload.items():baseline.atomic(target/name,raw,target);created.append(name)
        baseline.atomic(old/'launch.sh',(out/'dispatch.sh').read_bytes(),old);dispatch=True
        for name,wanted in protected.items():assert digest(card/name)==wanted,name
        for name,raw in payload.items():assert (target/name).read_bytes()==raw,name
        health(archive,'chkdsk-after-cost-payload.txt')
        baseline.atomic(marker,MARKER,old)
        assert marker.read_bytes()==MARKER
        assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/snes-mvp/armed']
        health(archive,'chkdsk-after-cost-arm.txt')
        for name,wanted in protected.items():assert digest(card/name)==wanted,name
        for name,raw in payload.items():assert (target/name).read_bytes()==raw,name
        assert (old/'launch.sh').read_bytes()==(out/'dispatch.sh').read_bytes()
    except Exception:
        health(archive,'chkdsk-before-cost-rollback.txt')
        if marker.exists():assert marker.read_bytes()==MARKER;marker.unlink()
        if dispatch:baseline.atomic(old/'launch.sh',original,old)
        for name in reversed(created):(target/name).unlink()
        target.rmdir();raise
    proof={'version':'1.19-cost1','archive_before_writes':archive.name,'protected_hashes_verified':len(protected),
           'only_measurement_one_shot_armed':True,'production_runner_core_adapter_stock_progress_unchanged':True,
           'candidate_installed':False,'payload_hashes':{n:sha256(raw).hexdigest() for n,raw in payload.items()},
           'dispatch_sha256':digest(old/'launch.sh'),'physical_measurements':'PENDING','all_three_fat_checks_clean':True}
    (archive/'cost-installation.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))
if __name__=='__main__':install(sys.argv[1])
