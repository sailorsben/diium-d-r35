"""Install a passive, consumed-once boot owner capture on the inspected card."""
from pathlib import Path
import importlib.util, json, os, subprocess
from hashlib import sha256
ROOT=Path(__file__).resolve().parent.parent
INIT='b89d080e324a518a516f12c470f790e8967626be0cca5db7149846b68319dce7'
SPLASH='ab56a67ae629e816a5752b1ad7cec2c335b46c82df84856f8a41376d2f919ebe'
HOOK=b'# Passive one-shot splash-owner capture; no display operations.\nif [ -f /usr/retro/vesper-boot-probe/armed ]; then\n  /bin/sh /usr/retro/vesper-boot-probe/probe.sh &\nfi\n'
def digest(p): return sha256(p.read_bytes()).hexdigest()
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'build'/file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def write(p,data):
    with p.open('xb') as f: f.write(data);f.flush();os.fsync(f.fileno())
    assert p.read_bytes()==data
if __name__=='__main__':
    card=Path('D:/');target=card/'retro/init';base=card/'retro/vesper-boot-probe'
    assert not base.exists() and digest(target)==INIT
    assert digest(card/'retro/showlogo')==SPLASH
    assert not (card/'retro/snes-mvp/armed').exists()
    assert not (card/'retro/platform-lab/armed').exists()
    check=subprocess.run(['chkdsk','D:'],input=b'N\r\n',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    health=check.stdout.decode('cp437');assert check.returncode==0
    module('boot_installer','install-vesper-boot.py').healthy(health)
    archive=module('probe_collector','collect-platform-lab.py').collect(card)
    (archive/'chkdsk-preprobe.txt').write_text(health,encoding='utf-8')
    (archive/'showlogo-returned').write_bytes((card/'retro/showlogo').read_bytes())
    original=target.read_bytes();assert original.startswith(b'#!/bin/sh\n')
    candidate=b'#!/bin/sh\n'+HOOK+original[len(b'#!/bin/sh\n'):]
    assert candidate.replace(HOOK,b'',1)==original
    (archive/'init.before-probe').write_bytes(original)
    (archive/'init.with-probe').write_bytes(candidate)
    script=(ROOT/'build/probe-firmware-route.sh').read_bytes();assert b'\r' not in script
    collection=json.loads((archive/'collection.json').read_text());assert collection['complete']
    base.mkdir();write(base/'probe.sh',script)
    temp=card/'retro/init.vesper-probe.tmp';assert not temp.exists()
    write(temp,candidate);os.replace(temp,target);assert target.read_bytes()==candidate
    for entry in collection['copied_and_hash_verified']:
        if entry['card_path']!='retro/init': assert digest(card/entry['card_path'])==entry['sha256']
    for path,h in collection['production_hashes'].items(): assert digest(card/path)==h
    for entry in json.loads((archive/'lab-collection.json').read_text())['copied']:
        assert digest(card/'retro/platform-lab'/entry['relative_path'])==entry['sha256']
    assert digest(card/'retro/showlogo')==SPLASH
    write(base/'armed',b'passive boot-owner capture v1\n')
    receipt={'archive':archive.name,'init_before_sha256':INIT,'init_probe_sha256':digest(target),
        'showlogo_sha256':SPLASH,'probe_sha256':digest(base/'probe.sh'),
        'snes_armed':False,'lab_armed':False,'probe_armed':True,'display_operations':False,
        'restore_init_from':str(archive.relative_to(ROOT)/'init.before-probe')}
    (archive/'probe-installation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
