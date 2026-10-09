"""Guarded passive survey install, read-only collection, and exact hook restore.

Only the inspected D: FAT32 card is accepted. Vendor captures remain private.
Install archives progress, verifies health and qualification, arms LAST.
Restore archives again before removing the hook; results stay on the card.
"""
from pathlib import Path
from hashlib import sha256
import argparse, importlib.util, json, os, shutil, subprocess, uuid

ROOT=Path(__file__).resolve().parent.parent
RELEASE=ROOT/'releases/device-survey-2'
INIT='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
SPLASH='ab56a67ae629e816a5752b1ad7cec2c335b46c82df84856f8a41376d2f919ebe'
HOOK=b'# D35 passive device survey: one boot, background, no hardware controls.\nif [ -f /usr/retro/device-survey/armed ]; then\n  /bin/sh /usr/retro/device-survey/launch.sh &\nfi\n'

def digest(p): return sha256(p.read_bytes()).hexdigest()
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'build'/file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def write_new(path,data):
    with path.open('xb') as f: f.write(data);f.flush();os.fsync(f.fileno())
    assert path.read_bytes()==data
def atomic_replace(path,data):
    temp=path.with_name(path.name+'.survey-'+uuid.uuid4().hex+'.tmp')
    write_new(temp,data);os.replace(temp,path);assert path.read_bytes()==data
def patched_init(original):
    assert original.startswith(b'#!/bin/sh\n') and HOOK not in original
    candidate=b'#!/bin/sh\n'+HOOK+original[len(b'#!/bin/sh\n'):]
    assert candidate.replace(HOOK,b'',1)==original
    return candidate
def archive_tree(source,dest):
    entries=[]
    if not source.exists(): return entries
    assert not source.is_symlink()
    for p in sorted(source.rglob('*')):
        assert not p.is_symlink(),p
        if not p.is_file(): continue
        relative=p.relative_to(source);target=dest/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        before=digest(p);shutil.copy2(p,target);assert before==digest(p)==digest(target)
        entries.append({'path':relative.as_posix(),'bytes':p.stat().st_size,'sha256':before})
    return entries
def healthy():
    check=subprocess.run(['chkdsk','D:'],input=b'N\r\n',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    text=check.stdout.decode('cp437');assert check.returncode==0,text
    module('survey_health','install-vesper-boot.py').healthy(text)
    return text
def baseline(card):
    archive=module('survey_collector','collect-platform-lab.py').collect(card)
    extra={}
    for name in ['device-survey','vesper-boot-probe','vesper-boot']:
        extra[name]=archive_tree(card/'retro'/name,archive/name)
    splash=card/'retro/showlogo';before=digest(splash)
    shutil.copy2(splash,archive/'showlogo');assert digest(archive/'showlogo')==before==digest(splash)
    (archive/'survey-extra-collection.json').write_text(json.dumps(extra,indent=2)+'\n',encoding='utf-8')
    return archive
def verify_protected(card,archive,init_hash):
    collection=json.loads((archive/'collection.json').read_text());assert collection['complete']
    for entry in collection['copied_and_hash_verified']:
        if entry['card_path']!='retro/init': assert digest(card/entry['card_path'])==entry['sha256'],entry['card_path']
    for path,h in collection['production_hashes'].items(): assert digest(card/path)==h,path
    for entry in json.loads((archive/'lab-collection.json').read_text())['copied']:
        assert digest(card/'retro/platform-lab'/entry['relative_path'])==entry['sha256']
    assert digest(card/'retro/showlogo')==digest(archive/'showlogo')
    assert digest(card/'retro/init')==init_hash
def qualification():
    r=json.loads((RELEASE/'manifest.json').read_text())
    assert r['software_checks_passed'] and r['physical_execution']=='pending'
    for name,h in r['source_hashes'].items(): assert digest(ROOT/name)==h,name
    for name,h in r['release_hashes'].items(): assert digest(RELEASE/name)==h,name
    return r
def install(card,rearm=False):
    target=card/'retro/init';base=card/'retro/device-survey'
    if not rearm: assert not base.exists(),'Survey directory already exists; collect/restore before rearm'
    else:
        assert base.is_dir() and not (base/'armed').exists(),'Survey must be collected/restored first'
    assert digest(target)==INIT,'Init differs from verified baseline; inspect it instead of overwriting'
    assert digest(card/'retro/showlogo')==SPLASH
    for name in ['snes-mvp','platform-lab','vesper-boot','vesper-boot-probe']:
        assert not (card/'retro'/name/'armed').exists(),name+' is armed'
    qualification();health=healthy();archive=baseline(card)
    (archive/'chkdsk-presurvey.txt').write_text(health,encoding='utf-8')
    original=target.read_bytes();candidate=patched_init(original)
    (archive/'init.before-survey').write_bytes(original)
    (archive/'init.with-survey').write_bytes(candidate)
    if rearm:
        # Delete only the owned, already hash-archived suite directory. Resolve
        # and check the final absolute target before any recursive operation.
        assert base.resolve()==(card/'retro/device-survey').resolve() and base.parent.resolve()==(card/'retro').resolve()
        archived=json.loads((archive/'survey-extra-collection.json').read_text())['device-survey']
        for e in archived: assert digest(base/e['path'])==e['sha256']
        assert len(archived)==sum(p.is_file() for p in base.rglob('*'))
        shutil.rmtree(base)
    base.mkdir()
    try:
        for source,name in [('device-survey','device-survey'),('launch.sh','launch.sh'),('manifest.json','manifest.json')]:
            write_new(base/name,(RELEASE/source).read_bytes())
        write_new(base/'init.before',original)
        receipt={'version':2,'mode':'passive','run_id':uuid.uuid4().hex,'archive':archive.name,
            'init_before_sha256':INIT,'init_survey_sha256':sha256(candidate).hexdigest(),
            'binary_sha256':digest(base/'device-survey'),'wrapper_sha256':digest(base/'launch.sh'),
            'snes_armed':False,'lab_armed':False,'survey_armed':True,
            'raw_device_reads':False,'firmware_writes':False,'physical_execution':'pending'}
        write_new(base/'installation.json',(json.dumps(receipt,indent=2)+'\n').encode())
        atomic_replace(target,candidate)
        verify_protected(card,archive,receipt['init_survey_sha256'])
        write_new(base/'armed',(receipt['run_id']+'\n').encode())
    except BaseException:
        if (base/'armed').exists(): (base/'armed').unlink()
        if target.read_bytes()!=original: atomic_replace(target,original)
        raise
    (archive/'survey-installation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2));return archive
def collect(card,restore=False):
    base=card/'retro/device-survey';assert base.is_dir()
    archive=baseline(card)
    result=module('survey_analysis','analyze-device-survey.py').analyze(archive/'device-survey')
    (archive/'survey-analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    if restore:
        # Preserve first, but never mutate an unhealthy volume just to remove
        # an already consumed hook. The next boot is stock without restoration.
        health=healthy()
        (archive/'chkdsk-prerestore.txt').write_text(health,encoding='utf-8')
        assert not (base/'armed').exists(),'Survey still armed: has it run? Collect only until identity is resolved'
        r=json.loads((base/'installation.json').read_text());target=card/'retro/init'
        assert digest(target)==r['init_survey_sha256'],'Init changed; preserve and inspect it'
        assert digest(base/'init.before')==r['init_before_sha256']==INIT
        atomic_replace(target,(base/'init.before').read_bytes())
        verify_protected(card,archive,INIT)
        (archive/'survey-restoration.json').write_text(json.dumps({'init_restored':True,'init_sha256':INIT},indent=2)+'\n')
    print(json.dumps({'archive':archive.name,'complete':result['complete'],'end':result.get('end'),
        'capture_files_verified':len(result.get('captured',[])),
        'capture_failures':len(result.get('failed_captures',[])),'init_restored':restore},indent=2));return archive
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['install','rearm','collect','restore']);p.add_argument('--card',type=Path,default=Path('D:/'))
    a=p.parse_args();card=a.card.resolve();assert str(card).lower() in ('d:\\','d:/')
    if a.action in ['install','rearm']: install(card,a.action=='rearm')
    else: collect(card,a.action=='restore')
