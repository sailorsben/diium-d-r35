"""Apply a hash-proven scoped obsolete-test cleanup; preserve armed rollback."""
from pathlib import Path
import importlib.util,json,sys,os,stat,shutil
from attempt_archive import digest
ROOT=Path(__file__).resolve().parent.parent
def load(name):
 s=importlib.util.spec_from_file_location(name,ROOT/'build'/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def scoped(card,relative,profiles):
 p=Path(relative);assert not p.is_absolute() and '..' not in p.parts and len(p.parts)>2 and p.parts[0]=='retro' and p.parts[1] in profiles
 root=card.resolve();target=(root/p).resolve();scope=(root/'retro'/p.parts[1]).resolve();assert target.is_relative_to(scope) and scope.parent==(root/'retro').resolve() and target!=scope
 cur=root
 for part in p.parts:
  cur=cur/part
  if cur.exists():assert not (cur.lstat().st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT) if os.name=='nt' else not cur.is_symlink()
 return target
def apply(card,plan,atomic,progress=lambda _:None):
 # Validate every resolved deletion before the first mutation. No recursive delete.
 planner=load('plan-card-test-cleanup.py');assert set(plan['profiles']).issubset(planner.PROFILES)
 for n in plan['remove']:assert not planner.keep_save(n)
 targets=[(n,scoped(card,n,set(plan['profiles'])),proof) for n,proof in plan['remove'].items()]
 for n,p,proof in targets:assert p.is_file() and digest(p)==proof['sha256'],n
 wrapper=plan['restore_dispatcher'];assert digest(card/wrapper['path'])==wrapper['before_sha256']
 atomic(card/wrapper['path'],(ROOT/wrapper['host']).read_bytes())
 removed=[]
 for n,p,proof in targets:
  assert digest(p)==proof['sha256'],n;p.unlink();removed.append(n)
  if len(removed)%128==0:progress(len(removed))
 for profile in plan['profiles']:
  scope=(card/'retro'/profile).resolve();assert scope.parent==(card/'retro').resolve()
  if not scope.exists():continue
  dirs=[]
  for parent,children,files in os.walk(scope,followlinks=False):
   for name in children:
    p=(Path(parent)/name).resolve();assert p.is_relative_to(scope) and not p.is_symlink();dirs.append(p)
  for p in sorted(dirs,key=lambda p:len(p.parts),reverse=True):
   if not any(p.iterdir()):p.rmdir()
  if not any(scope.iterdir()):scope.rmdir()
 return removed
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');plan=json.loads((archive/'cleanup-plan.json').read_text());planner=load('plan-card-test-cleanup.py');assert plan['planner_sha256']==digest(ROOT/'build/plan-card-test-cleanup.py')
 assert set(plan['profiles'])==planner.PROFILES and plan['no_new_full_backup'] and plan['card_writes']==0
 assert plan['archive_manifest_sha256']==digest(archive/'archive.json') and plan['outside_manifest_sha256']==digest(archive/'outside-retro.json')
 q=json.loads((archive/'cleanup-qualification.json').read_text());assert q['passed'] and q['executor_sha256']==digest(Path(__file__)) and q['plan_sha256']==digest(archive/'cleanup-plan.json')
 fix=load('install-uart-fix.py');assert not fix.git('status','--porcelain');commit=fix.git('rev-parse','HEAD');assert commit==fix.git('rev-parse','origin/codex/snes-mvp-foundation')
 a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());entries=a['all_retro_files']+o['files'];card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\')
 # Verify all host deletion proofs first, including full retained evidence bytes.
 cache={}
 for n,proof in plan['remove'].items():
  assert not planner.keep_save(n);host=(ROOT/proof['host']).resolve();assert host.is_relative_to(ROOT.resolve()) and host.is_file() and not host.is_symlink()
  if str(host) not in cache:cache[str(host)]=digest(host)
  assert cache[str(host)]==proof['sha256'] and host.stat().st_size==proof['bytes'],n
 wrapper=plan['restore_dispatcher'];assert digest(ROOT/wrapper['host'])==wrapper['sha256']
 for e in entries:assert digest(card/e['path'])==e['sha256'],e['path']
 assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}=={e['path'] for e in entries}
 assert not list(card.rglob('armed')) and digest(card/'retro/update/Code.bkp')==plan['rollback_trigger_sha256'];fix.health(archive,'test-cleanup-before')
 free_before=shutil.disk_usage(card).free
 journal=archive/'cleanup-progress.json'
 def progress(n):journal.write_text(json.dumps({'plan_sha256':digest(archive/'cleanup-plan.json'),'deleted_count':n})+'\n')
 removed=apply(card,plan,fix.atomic,progress)
 for n,h in plan['protected'].items():assert digest(card/n)==h,n
 assert digest(card/wrapper['path'])==wrapper['sha256']
 expected=set(plan['protected'])|{wrapper['path']};assert {p.relative_to(card).as_posix() for p in card.rglob('*') if p.is_file()}==expected
 assert not list(card.rglob('armed')) and digest(card/'retro/update/Code.bkp')==plan['rollback_trigger_sha256'];fix.health(archive,'test-cleanup-after')
 report={'source_commit':commit,'archive':archive.name,'plan_sha256':digest(archive/'cleanup-plan.json'),'removed_files':len(removed),'removed_logical_bytes':plan['remove_bytes'],'free_bytes_before':free_before,'free_bytes_after':shutil.disk_usage(card).free,'retained_files':len(expected),'retained_save_files':len(plan['kept_save_paths']),'unresolved_files_kept':len(plan['unresolved_retained']),'every_removed_file_has_verified_host_copy':True,'all_remaining_files_hash_verified':True,'rollback_package_and_UART_init_wrapper_exact':True,'normal_MVP_wrapper_restored_sha256':wrapper['sha256'],'no_game_test_armed':True,'FAT_clean':True,'no_new_full_backup':True}
 (archive/'cleanup-result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
