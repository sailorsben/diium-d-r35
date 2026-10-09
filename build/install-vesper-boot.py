"""Install only qualified boot artwork on the exact healthy, backed-up D: card.

No repair bypass: a reviewed read-only CHKDSK log must establish zero problems.
The entire private returned card is archived separately before filesystem
repair. This installer takes another complete MVP/lab/splash baseline after
repair and verifies MVP/progress/lab/stock/hook files. It never arms SNES.
--restore restores the known original artwork without touching other files.
"""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import argparse, importlib.util, json, os, subprocess

ROOT=Path(__file__).resolve().parent.parent
STOCK='436d8018808b150c926274575a195f664e61db646f44713371019e9ae10caf3b'
RELEASE=ROOT/'releases/vesper-boot-1'

def digest(path):return sha256(path.read_bytes()).hexdigest()
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'build'/file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def healthy(report):
    assert any(message in report for message in (
        'Windows has scanned the file system and found no problems.',
        'Windows has checked the file system and found no problems.'))
    assert 'No further action is required.' in report and 'FAT32' in report
    assert 'Volume Serial Number is 11EB-1465' in report

def install(card,health_log,stock,restore=False):
    card=card.resolve();stock=stock.resolve();health_log=health_log.resolve()
    assert str(card).lower() in ('d:\\','d:/')
    assert health_log.is_relative_to(ROOT/'device-evidence') and stock.is_relative_to(ROOT/'device-evidence')
    assert digest(stock)==STOCK
    health=health_log.read_text(encoding='utf-8')
    healthy(health)
    # A past healthy log cannot authorize writing to a newly damaged card.
    current=subprocess.run(['chkdsk','D:'],input=b'N\r\n',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    current_health=current.stdout.decode('cp437');assert current.returncode==0,current_health
    healthy(current_health)
    manifest=json.loads((RELEASE/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['stock_sha256']==STOCK and manifest['stock_loader_and_sprite_check'].startswith('passed exact original ARM')
    for name,wanted in manifest['verification_sources'].items():assert digest(ROOT/name)==wanted,name
    assert digest(RELEASE/'stock-seam-check.log')==manifest['check_sha256']
    assert digest(RELEASE/'logo.zip')==manifest['logo_zip_sha256']
    assert not (card/'retro/snes-mvp/armed').exists() and not (card/'retro/platform-lab/armed').exists()
    target=card/'retro/showlogo';original=stock.read_bytes()
    candidate=original[:manifest['zip_start']]+(RELEASE/'logo.zip').read_bytes()+original[manifest['zip_end']:]
    assert len(candidate)==len(original) and sha256(candidate).hexdigest()==manifest['patched_showlogo_sha256']
    wanted=candidate if not restore else original
    assert digest(target)==(STOCK if not restore else manifest['patched_showlogo_sha256'])
    # Strict collector stops on unreadable progress; never use tolerant salvage
    # as permission to overwrite a card whose filesystem remains damaged.
    collector=load('boot_baseline','collect-platform-lab.py');archive=collector.collect(card)
    (archive/'chkdsk-preinstall.txt').write_text(current_health,encoding='utf-8')
    collection=json.loads((archive/'collection.json').read_text(encoding='utf-8'));assert collection['complete']
    before=target.read_bytes();(archive/'stock-showlogo').write_bytes(before)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    temporary=card/'retro'/('showlogo.vesper-'+stamp+'.tmp');assert not temporary.exists()
    try:
        with temporary.open('xb') as stream:
            stream.write(wanted);stream.flush();os.fsync(stream.fileno())
        assert digest(temporary)==sha256(wanted).hexdigest()
        os.replace(temporary,target)
        assert target.read_bytes()==wanted
        for entry in collection['copied_and_hash_verified']:
            assert digest(card/entry['card_path'])==entry['sha256'],entry['card_path']
        for path,h in collection['production_hashes'].items():assert digest(card/path)==h,path
        for entry in json.loads((archive/'lab-collection.json').read_text())['copied']:
            assert digest(card/'retro/platform-lab'/entry['relative_path'])==entry['sha256']
    except BaseException:
        # If replacement happened, restore the exact archived bytes. Keep failed
        # temporary files for diagnosis instead of broad filesystem cleanup.
        if target.read_bytes()!=before:
            with temporary.open('wb') as stream:
                stream.write(before);stream.flush();os.fsync(stream.fileno())
            os.replace(temporary,target)
            assert target.read_bytes()==before
        raise
    retained_lab=json.loads((archive/'lab-collection.json').read_text())['copied']
    result={'version':'vesper-boot-1','restored':restore,'installed_utc':datetime.now(timezone.utc).isoformat(),
            'showlogo_sha256':digest(target),'stock_outside_zip_unchanged':True,
            'protected_mvp_and_progress_files':len(collection['copied_and_hash_verified']),
            'lab_files_unchanged':len(retained_lab),'snes_armed':False,'lab_armed':False,
            'stock_init_and_other_binaries_unchanged':True,'physical_appearance':'pending',
            'archive':archive.name}
    (archive/'boot-installation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2));return archive

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--card',type=Path,default=Path('D:/'))
    p.add_argument('--health-log',type=Path,required=True);p.add_argument('--stock',type=Path,required=True)
    p.add_argument('--restore',action='store_true');a=p.parse_args()
    install(a.card,a.health_log,a.stock,a.restore)
