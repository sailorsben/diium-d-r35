"""Temporary filesystem transaction qualification; never reads I:."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,tempfile
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main():
 s=importlib.util.spec_from_file_location('stage',ROOT/'build/stage-uart-firmware.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 p,q,package,compat=m.artifacts();old=(ROOT/'build/launch-uart-fix.sh').read_bytes();cases=[]
 for fault in ['success','compat','trigger','health-compat','health-armed','existing-trigger','armed-test','changed-hook']:
  with tempfile.TemporaryDirectory(dir=ROOT/'build') as tmp:
   card=Path(tmp);(card/'retro/uart-fix1').mkdir(parents=True);(card/'retro/update').mkdir();hook=card/'retro/uart-fix1/launch.sh';trigger=card/'retro/update/Code.bkp'
   hook.write_bytes(b'other owner' if fault=='changed-hook' else old);(card/'save.srm').write_bytes(b'private save');(card/'evidence.log').write_bytes(b'prior evidence')
   if fault=='existing-trigger':trigger.write_bytes(b'preexisting update')
   if fault=='armed-test':(card/'retro/armed').write_bytes(b'preexisting test')
   before=hook.read_bytes();calls=[]
   def atomic(path,data):
    t=path.with_name(path.name+'.test-tmp');t.write_bytes(data);t.replace(path);assert path.read_bytes()==data
   def inject(phase):
    calls.append(phase)
    if fault==phase:raise RuntimeError('injected '+phase)
   def health(phase):
    if fault=='health-'+phase:raise RuntimeError('injected FAT failure')
   def verify():assert hook.read_bytes()==compat
   try:
    m.stage(card,package,compat,atomic,health,verify,inject);assert fault=='success'
    assert hook.read_bytes()==compat and trigger.read_bytes()==package
   except (AssertionError,RuntimeError):
    assert fault!='success' and hook.read_bytes()==before
    assert trigger.exists()==(fault=='existing-trigger')
    if trigger.exists():assert trigger.read_bytes()==b'preexisting update'
   assert (card/'save.srm').read_bytes()==b'private save' and (card/'evidence.log').read_bytes()==b'prior evidence'
   cases.append(fault)
 report={'passed':True,'cases':cases,'installer_sha256':digest(ROOT/'build/stage-uart-firmware.py'),'checker_sha256':digest(Path(__file__)),'qualification_sha256':digest(m.OUT/'qualification.json'),'card_access':False}
 (m.OUT/'staging-qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
