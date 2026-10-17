"""Exact staging seam success and write/FAT failure fixtures; no card access."""
from pathlib import Path
import importlib.util,json,tempfile
from hashlib import sha256
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'device-evidence/battery-rollback1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('stage',ROOT/'build/stage-battery-rollback.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);checks=[]
 for fault in ['none','launch','init','trigger','health-before','health-hooks','health-armed']:
  with tempfile.TemporaryDirectory(dir=OUT,prefix='stage-fixture-') as name:
   card=Path(name);(card/'retro/uart-fix1').mkdir(parents=True);(card/'retro/update').mkdir();ip=card/'retro/init';lp=card/'retro/uart-fix1/launch.sh';ip.write_bytes(b'normal');lp.write_bytes(b'compat');save=card/'retro/save.srm';save.write_bytes(b'progress')
   def atomic(p,b):p.write_bytes(b)
   def health(label):
    if fault=='health-'+label:raise RuntimeError('health gate')
   def inject(label):
    if fault==label:raise RuntimeError('injected write boundary')
   def verify():assert ip.read_bytes()==b'old init' and lp.read_bytes()==b'old launch' and save.read_bytes()==b'progress'
   try:m.stage(card,b'old init',b'old launch',b'package',atomic,health,verify,inject)
   except RuntimeError:assert fault!='none' and ip.read_bytes()==b'normal' and lp.read_bytes()==b'compat' and not (card/'retro/update/Code.bkp').exists()
   else:assert fault=='none' and (card/'retro/update/Code.bkp').read_bytes()==b'package'
   assert save.read_bytes()==b'progress' and not list(card.rglob('armed'));checks.append(fault)
 q={'passed':True,'checks':checks,'installer_sha256':digest(ROOT/'build/stage-battery-rollback.py'),'qualification_sha256':digest(OUT/'qualification.json'),'checker_sha256':digest(Path(__file__)),'card_access':False};(OUT/'staging-qualification.json').write_text(json.dumps(q,indent=2)+'\n');print('PASS seven rollback staging cases; no card access')
if __name__=='__main__':main()
