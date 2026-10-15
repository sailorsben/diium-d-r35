"""Private temporary-card transaction tests; never accesses I:."""
from pathlib import Path
import importlib.util,json,tempfile
ROOT=Path(__file__).resolve().parent.parent
def load(n):
 s=importlib.util.spec_from_file_location(n,ROOT/'build'/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 installer=load('install-uart-fix.py');prepare=load('prepare-uart-fix.py')
 out=ROOT/'build/uart-fix-private';q=installer.artifacts();results=[]
 original=(ROOT/'device-evidence/a7-pair-before-20261015T062141Z/retro/init').read_bytes()
 payload={n:(out/'package'/n).read_bytes() for n in q['payloads']}
 assert prepare.boot_init(original)==payload['init']
 for label in ['success','before_activation','after_activation','existing_target','changed_init']:
  with tempfile.TemporaryDirectory(dir=out) as tmp:
   card=Path(tmp);retro=card/'retro';retro.mkdir();(retro/'init').write_bytes(original)
   (retro/'private-save').write_bytes(b'preserve private progress');(retro/'test-log').write_bytes(b'preserve previous evidence')
   if label=='existing_target':(retro/'uart-fix1').mkdir()
   if label=='changed_init':(retro/'init').write_bytes(b'another owner\n')
   before=(retro/'init').read_bytes();observed=[]
   def inject(phase):
    observed.append(phase)
    assert all((retro/'uart-fix1'/n).read_bytes()==b for n,b in payload.items() if n!='init')
    assert (retro/'init').read_bytes()==(original if phase=='before_activation' else payload['init'])
    if phase==label:raise RuntimeError('injected transaction interruption')
   try:
    installer.stage(card,payload,original,inject)
    assert label=='success' and observed==['before_activation','after_activation']
    assert (retro/'init').read_bytes()==payload['init']
    installer.atomic(retro/'uart-fix1/disabled',b'rollback\n')
    installer.atomic(retro/'init',(retro/'uart-fix1/original-init').read_bytes())
   except (AssertionError,RuntimeError):assert label!='success'
   expected={'success':['before_activation','after_activation'],'before_activation':['before_activation'],'after_activation':['before_activation','after_activation'],'existing_target':[],'changed_init':[]}
   assert observed==expected[label]
   assert (retro/'init').read_bytes()==before
   assert (retro/'private-save').read_bytes()==b'preserve private progress' and (retro/'test-log').read_bytes()==b'preserve previous evidence'
   results.append(label)
 report={'all_checks_passed':True,'cases':results,'card_access':False,
 'qualification_sha256':installer.digest(out/'qualification.json'),
 'sources':{n:installer.digest(ROOT/n) for n in ['build/install-uart-fix.py','build/check-uart-fix-install.py']}}
 (out/'installation-qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
