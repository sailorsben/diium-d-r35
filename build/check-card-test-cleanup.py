"""Exercise exact deletion boundary with fake cards; never touches I:."""
from pathlib import Path
from hashlib import sha256
import importlib.util,json,tempfile,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def main(archive):
 s=importlib.util.spec_from_file_location('clean',ROOT/'build/cleanup-card-test-packages.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);checks=[]
 for case in ['success','hash_mismatch','traversal','foreign_profile','save_refusal']:
  with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='cleanup-fixture-') as name:
   card=Path(name);base=card/'retro/snes-fivegame1/run-001';base.mkdir(parents=True);p=base/'pcm-full.txt';p.write_bytes(b'unique diagnostic');ip=card/'retro/snes-mvp/launch.sh';ip.parent.mkdir();ip.write_bytes(b'old dispatcher');save=card/'retro/snes-fivegame1/saves/progress.srm';save.parent.mkdir();save.write_bytes(b'user progress');trigger=card/'retro/update/Code.bkp';trigger.parent.mkdir();trigger.write_bytes(b'armed recovery')
   relative='retro/snes-fivegame1/run-001/pcm-full.txt';h=digest(p)
   if case=='hash_mismatch':h='0'*64
   if case=='traversal':relative='retro/snes-fivegame1/../../../outside'
   if case=='foreign_profile':relative='retro/uart-fix1/launch.sh'
   if case=='save_refusal':relative='retro/snes-fivegame1/saves/progress.srm';h=digest(save)
   wrapper=ROOT/'releases/snes-mvp-1.19/launch.sh';plan={'profiles':['snes-fivegame1'],'remove':{relative:{'sha256':h}},'restore_dispatcher':{'path':'retro/snes-mvp/launch.sh','host':wrapper.relative_to(ROOT).as_posix(),'before_sha256':digest(ip),'sha256':digest(wrapper)}}
   try:removed=m.apply(card,plan,lambda p,b:p.write_bytes(b))
   except AssertionError:assert case!='success' and p.exists() and ip.read_bytes()==b'old dispatcher'
   else:assert case=='success' and removed==[relative] and not p.exists() and ip.read_bytes()==wrapper.read_bytes()
   assert save.read_bytes()==b'user progress' and trigger.read_bytes()==b'armed recovery';checks.append(case)
 archive=archive.resolve();q={'passed':True,'checks':checks,'executor_sha256':digest(ROOT/'build/cleanup-card-test-packages.py'),'checker_sha256':digest(Path(__file__)),'plan_sha256':digest(archive/'cleanup-plan.json'),'no_card_access':True};(archive/'cleanup-qualification.json').write_text(json.dumps(q,indent=2)+'\n');print('PASS cleanup success/hash/path/foreign-profile/save boundaries')
if __name__=='__main__':main(Path(sys.argv[1]))
