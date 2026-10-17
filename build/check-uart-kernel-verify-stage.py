"""Fake-card transaction checks for the read-only verification installer."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,tempfile
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('stage',ROOT/'build/stage-uart-kernel-verify.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);q=m.artifacts();payload={n:(m.OUT/n).read_bytes() for n in q['payload_hashes']};normal=(ROOT/'device-evidence/uart-kernel-firmware1/normal-init').read_bytes();init=(m.OUT/'init').read_bytes();marker=(m.OUT/'armed').read_bytes();cases=[]
 for fault in ['success','payload','init','marker','health-payload','health-armed','foreign-trigger','foreign-init','existing-target']:
  with tempfile.TemporaryDirectory(dir=ROOT/'build') as tmp:
   card=Path(tmp);(card/'retro/update').mkdir(parents=True);trigger=card/'retro/update/Code.bkp';trigger.write_bytes(b'foreign' if fault=='foreign-trigger' else b'known');(card/'retro/init').write_bytes(b'foreign' if fault=='foreign-init' else normal)
   if fault=='existing-target':(card/m.TARGET).mkdir()
   (card/'save.srm').write_bytes(b'private progress');(card/'prior.log').write_bytes(b'prior evidence');old=(card/'retro/init').read_bytes()
   def atomic(p,b):p.write_bytes(b)
   def health(phase):
    if fault=='health-'+phase:raise RuntimeError('injected FAT failure')
   def inject(phase):
    if fault==phase:raise RuntimeError('injected phase failure')
   try:
    m.stage(card,payload,init,marker,sha256(b'known').hexdigest(),atomic,health,lambda:None,inject);assert fault=='success' and (card/'retro/init').read_bytes()==init and (card/m.TARGET/'armed').read_bytes()==marker
   except (AssertionError,RuntimeError):
    assert fault!='success' and (card/'retro/init').read_bytes()==old and not (card/m.TARGET/'armed').exists()
   if fault not in ('foreign-trigger','foreign-init','existing-target'):assert not trigger.exists()
   assert (card/'save.srm').read_bytes()==b'private progress' and (card/'prior.log').read_bytes()==b'prior evidence';cases.append(fault)
 report={'passed':True,'cases':cases,'installer_sha256':digest(ROOT/'build/stage-uart-kernel-verify.py'),'checker_sha256':digest(Path(__file__)),'qualification_sha256':digest(m.OUT/'qualification.json'),'card_access':False};(m.OUT/'staging-qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
