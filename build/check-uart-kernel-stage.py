"""Exact staging transaction fixtures, no device/card access."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,tempfile
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('stage',ROOT/'build/stage-uart-kernel-firmware.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);p,q,package,normal,old,oldinit=m.artifacts();cases=[]
 for fault in ['success','init','trigger','health-init','health-armed','changed-trigger','changed-init','armed-test']:
  with tempfile.TemporaryDirectory(dir=ROOT/'build') as t:
   card=Path(t);(card/'retro/update').mkdir(parents=True);init=card/'retro/init';trigger=card/'retro/update/Code.bkp';init.write_bytes(b'foreign' if fault=='changed-init' else oldinit);trigger.write_bytes(b'foreign' if fault=='changed-trigger' else old)
   (card/'save.srm').write_bytes(b'private progress');(card/'evidence.log').write_bytes(b'prior evidence');beforeinit=init.read_bytes();beforeupdate=trigger.read_bytes()
   if fault=='armed-test':(card/'retro/armed').write_bytes(b'other experiment')
   def atomic(path,data):
    tmp=path.with_suffix('.fixture-tmp');tmp.write_bytes(data);tmp.replace(path);assert path.read_bytes()==data
   def health(label):
    if fault=='health-'+label:raise RuntimeError('injected FAT failure')
   def inject(label):
    if fault==label:raise RuntimeError('injected write interruption')
   try:
    m.stage(card,package,normal,old,oldinit,atomic,health,lambda:None,inject);assert fault=='success' and init.read_bytes()==normal and trigger.read_bytes()==package
   except (AssertionError,RuntimeError):assert fault!='success' and init.read_bytes()==beforeinit and trigger.read_bytes()==beforeupdate
   assert (card/'save.srm').read_bytes()==b'private progress' and (card/'evidence.log').read_bytes()==b'prior evidence';cases.append(fault)
 report={'passed':True,'cases':cases,'installer_sha256':digest(ROOT/'build/stage-uart-kernel-firmware.py'),'checker_sha256':digest(Path(__file__)),'qualification_sha256':digest(m.OUT/'qualification.json'),'card_access':False}
 (m.OUT/'staging-qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
