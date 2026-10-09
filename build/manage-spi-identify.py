"""Guarded one-shot read-only identification before the stock SPI owner starts."""
from pathlib import Path
from hashlib import sha256
import argparse,importlib.util,json,uuid
ROOT=Path(__file__).resolve().parent.parent
RELEASE=ROOT/'releases/spi-identify-1'
HOOK=b'# D35 SPI chip identification: synchronous fixed read-only commands.\nif [ -f /usr/retro/spi-identify/armed ]; then\n  /bin/sh /usr/retro/spi-identify/launch.sh\nfi\n'

def module():
    s=importlib.util.spec_from_file_location('survey_manager',ROOT/'build/manage-device-survey.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def digest(p):return sha256(p.read_bytes()).hexdigest()
def baseline(card,m):
    a=m.baseline(card);entries=m.archive_tree(card/'retro/spi-identify',a/'spi-identify')
    (a/'spi-extra-collection.json').write_text(json.dumps(entries,indent=2)+'\n',encoding='utf-8')
    return a
def analyze(base):
    p=base/'results/result.json'
    if not p.exists():return {'complete':False,'reason':'No result; inspect marker/startup'}
    r=json.loads(p.read_text());installation=json.loads((base/'installation.json').read_text())
    marker=(base/'consumed').exists() and not (base/'armed').exists() and (base/'consumed').read_text().strip()==installation['run_id']
    startup=(base/'startup.log').read_text(errors='replace') if (base/'startup.log').exists() else ''
    ids=r.get('ids',[])
    plausible=len(ids)==3 and len(set(ids))==1 and len(ids[0])==12 and ids[0][:2] not in ['00','ff']
    good=marker and 'identify_exit=0\n' in startup and r.get('errno')==0 and not r.get('timed_out') and not r.get('reap_pending') and r.get('operations')==5 and plausible and r.get('flash_writes') is False and r.get('global_config_writes') is False
    return {'complete':bool(good),'marker_matches':marker,'result':r,
        'limits':'ID exchange completion only; chip datasheet/capacity, full readback and recovery remain unqualified.'}

def install(card,m):
    base=card/'retro/spi-identify';target=card/'retro/init';assert not base.exists()
    assert digest(target)==m.INIT and digest(card/'retro/showlogo')==m.SPLASH
    for name in ['snes-mvp','platform-lab','device-survey','vesper-boot','vesper-boot-probe']:
        assert not (card/'retro'/name/'armed').exists(),name+' armed'
    q=json.loads((RELEASE/'manifest.json').read_text());assert q['software_checks_passed'] and q['physical_execution']=='pending'
    assert q['fixed_commands']==['05','9f'] and q['flash_writes'] is False and q['global_config_writes'] is False
    for n,h in q['source_hashes'].items():assert digest(ROOT/n)==h,n
    for n,h in q['release_hashes'].items():assert digest(RELEASE/n)==h,n
    health=m.healthy();a=baseline(card,m);(a/'chkdsk-prespi.txt').write_text(health,encoding='utf-8')
    original=target.read_bytes();assert original.startswith(b'#!/bin/sh\n') and HOOK not in original
    candidate=b'#!/bin/sh\n'+HOOK+original[len(b'#!/bin/sh\n'):];assert candidate.replace(HOOK,b'',1)==original
    (a/'init.before-spi').write_bytes(original);(a/'init.with-spi').write_bytes(candidate);base.mkdir()
    receipt={'version':1,'run_id':uuid.uuid4().hex,'archive':a.name,'init_before_sha256':m.INIT,
        'init_probe_sha256':sha256(candidate).hexdigest(),'binary_sha256':q['release_hashes']['spi-identify'],
        'wrapper_sha256':q['release_hashes']['launch.sh'],'hook':'synchronous before stock main',
        'fixed_commands':['05','9f'],'flash_writes':False,'global_config_writes':False,'physical_execution':'pending'}
    try:
        for n in ['spi-identify','launch.sh','manifest.json']:m.write_new(base/n,(RELEASE/n).read_bytes())
        m.write_new(base/'init.before',original)
        m.write_new(base/'installation.json',(json.dumps(receipt,indent=2)+'\n').encode())
        m.atomic_replace(target,candidate);m.verify_protected(card,a,receipt['init_probe_sha256'])
        m.write_new(base/'armed',(receipt['run_id']+'\n').encode())
    except BaseException:
        if (base/'armed').exists():(base/'armed').unlink()
        if target.read_bytes()!=original:m.atomic_replace(target,original)
        raise
    (a/'spi-installation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2));return a

def collect(card,m,restore=False):
    base=card/'retro/spi-identify';assert base.is_dir();a=baseline(card,m);result=analyze(a/'spi-identify')
    (a/'spi-analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    if restore:
        health=m.healthy();(a/'chkdsk-prerestore.txt').write_text(health,encoding='utf-8')
        assert not (base/'armed').exists(),'Still armed; collect only until run identity is resolved'
        installation=json.loads((base/'installation.json').read_text());target=card/'retro/init'
        assert digest(target)==installation['init_probe_sha256']
        assert digest(base/'init.before')==installation['init_before_sha256']==m.INIT
        m.atomic_replace(target,(base/'init.before').read_bytes());m.verify_protected(card,a,m.INIT)
        (a/'spi-restoration.json').write_text(json.dumps({'init_restored':True,'init_sha256':m.INIT},indent=2)+'\n')
    print(json.dumps({'archive':a.name,'analysis':result,'init_restored':restore},indent=2));return a

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['install','collect','restore'])
    p.add_argument('--card',type=Path,default=Path('D:/'));a=p.parse_args();card=a.card.resolve()
    assert str(card).lower() in ['d:\\','d:/'];m=module()
    if a.action=='install':install(card,m)
    else:collect(card,m,a.action=='restore')
