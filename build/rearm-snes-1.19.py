"""Archive a returned exact1.19 card, then re-arm only its owned one-shot."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util, json, subprocess

ROOT=Path(__file__).resolve().parent.parent
def module(name, filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'build'/filename)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value
install=module('snes_119_installer','package-snes-1.19.py')
def digest(path): return sha256(path.read_bytes()).hexdigest()

def rearm():
    card=Path('D:/').resolve(); target=card/'retro/snes-mvp'
    assert str(card).lower() in ('d:\\','d:/') and target.is_dir()
    # Preserve every returned diagnostic and private progress file first.
    archive=install.collector.collect(card)
    health=subprocess.run(['chkdsk','D:'],capture_output=True,text=True)
    (archive/'chkdsk-before-rearm.txt').write_text(health.stdout,encoding='utf-8')
    assert health.returncode==0 and '11EB-1465' in health.stdout and \
        'Windows has scanned the file system and found no problems.' in health.stdout
    expected=json.loads((ROOT/'releases/snes-mvp-1.19/manifest.json').read_text())
    for name,key in [('snes-mvp','binary_sha256'),('plus-a7.so','core_sha256'),('launch.sh','wrapper_sha256')]:
        assert digest(target/name)==expected[key],name
    assert (target/'TEST-ME.txt').read_bytes()==(ROOT/'releases/snes-mvp-1.19/TEST-ME.txt').read_bytes()
    protected={p:digest(card/p) for p in install.BOOT_EXPECTED}
    assert protected==install.BOOT_EXPECTED
    assert digest(card/'retro/init')==install.baseline.HOOK
    protected['retro/init']=install.baseline.HOOK
    collected=json.loads((archive/'collection.json').read_text())
    for e in collected['copied_and_hash_verified']:
        assert digest(archive/e['archive_path'])==e['sha256']
        protected[e['card_path']]=e['sha256']
    lab=json.loads((archive/'lab-collection.json').read_text())
    for e in lab['copied']:
        name='retro/platform-lab/'+e['relative_path']
        assert digest(archive/'platform-lab'/e['relative_path'])==e['sha256']
        protected[name]=e['sha256']
    for folder in (card/'retro').glob('spi-readback*'):
        if folder.is_dir():
            for p in folder.rglob('*'):
                if p.is_file(): protected[p.relative_to(card).as_posix()]=digest(p)
    assert not (card/'retro/update/Code.bkp').exists()
    marker=b'SNES-MVP-v1.19 lazy-row-rgb one-shot\n'
    armed=sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))
    assert armed in ([],['retro/snes-mvp/armed']),armed
    was_armed=(target/'armed').exists()
    if was_armed: assert (target/'armed').read_bytes()==marker
    for name,wanted in protected.items(): assert digest(card/name)==wanted,name
    if not was_armed: install.atomic(target/'armed',marker,target)
    # Independent rereads: every archived current byte remains intact.
    assert (target/'armed').read_bytes()==marker
    for name,wanted in protected.items(): assert digest(card/name)==wanted,name
    assert sorted(p.relative_to(card).as_posix() for p in (card/'retro').rglob('armed'))==['retro/snes-mvp/armed']
    report={'version':'1.19','rearmed_utc':datetime.now(timezone.utc).isoformat(),
        'archive_before_writes':archive.name,'fat_clean':True,'exact_release_verified':True,
        'only_snes_armed':True,'already_armed':was_armed,'card_writes':0 if was_armed else 1,
        'protected_current_files_verified':len(protected),'all_returned_progress_and_logs_preserved':True,
        'firmware_update_trigger_absent':True,'hardware_audio_result':'not inferred from rearm',
        'intent':'User requested another launch to exit properly; no payload or save changes'}
    (archive/'rearm-1.19.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__': rearm()
