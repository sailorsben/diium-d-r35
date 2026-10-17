"""Exercise the exact installer transaction with private temporary card fixtures."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,tempfile
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fivegame-kernel-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 path=ROOT/'build/install-fivegame-kernel.py'
 spec=importlib.util.spec_from_file_location('presentation_install',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 checks=[]
 for fault in ('none','payload','dispatcher','target_marker','mvp_marker','health_payload','health_armed'):
  with tempfile.TemporaryDirectory(dir=OUT,prefix='install-fixture-') as name:
   card=Path(name);mvp=card/'retro/snes-mvp';mvp.mkdir(parents=True)
   (mvp/'launch.sh').write_bytes(b'prior dispatcher\n');prior=card/'retro/saves/progress.srm';prior.parent.mkdir();prior.write_bytes(b'private progress retained')
   uart=card/'retro/uart-fix1/launch.sh';uart.parent.mkdir();uart.write_bytes(b'persistent fix')
   payload={'fivegame-suite':b'executable fixture','cases/000/scene.state':b'private fixture state'};events=[]
   def atomic(p,b):p.write_bytes(b)
   def health(label):
    events.append(label)
    if (fault=='health_payload' and label=='payload') or (fault=='health_armed' and label=='armed'):raise RuntimeError('injected FAT gate refusal')
   def verify():
    assert prior.read_bytes()==b'private progress retained' and uart.read_bytes()==b'persistent fix'
    for n,b in payload.items():assert (card/m.TARGET/n).read_bytes()==b
   def inject(where):
    if where==fault:raise RuntimeError('injected staging failure')
   try:m.stage(card,payload,b'new dispatch\n',atomic,health,verify,inject)
   except RuntimeError:
    assert fault!='none' and (mvp/'launch.sh').read_bytes()==b'prior dispatcher\n'
    assert not list((card/'retro').rglob('armed')) and events[-1]=='before-rollback'
   else:
    assert fault=='none' and (mvp/'launch.sh').read_bytes()==b'new dispatch\n'
    assert (mvp/'armed').read_bytes()==(card/m.TARGET/'armed').read_bytes()==m.MARKER
   assert prior.read_bytes()==b'private progress retained' and uart.read_bytes()==b'persistent fix'
   checks.append(fault)
 result={'passed':True,'checks':checks,'installer_sha256':digest(path),'checker_sha256':digest(Path(__file__)),
         'qualification_sha256':digest(OUT/'qualification.json'),'card_access':False}
 (OUT/'installation-qualification.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS exact installer success + six rollback/failure gates; prior progress/UART preserved')
if __name__=='__main__':main()
