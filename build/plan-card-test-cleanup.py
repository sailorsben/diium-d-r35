"""Read-only host proof plan for explicitly retired card diagnostic profiles."""
from pathlib import Path
from collections import defaultdict
import json,os,sys
from attempt_archive import digest,verify_saved,PROGRESS
ROOT=Path(__file__).resolve().parent.parent
PROFILES=set("device-survey platform-lab render-pressure1 render-pressure2 render-pressure3 snes-ability1 snes-ability2 snes-ability3 snes-combined-gameplay1 snes-combined1 snes-confuser-gameplay1 snes-cost1 snes-demand-gameplay1 snes-demand-spells1 snes-draw-order1 snes-draw-uart1 snes-fivegame-kernel1 snes-fivegame1 snes-fullpaths1 snes-pair1 snes-pc-profile1 snes-ppu-test1 snes-presentation-ffvi1 snes-profile1 spi-identify spi-readback spi-readback.pre-vesper-2ef5b65b19664fbc934a7460000e8eee spi-readback.pre-vesper-e773f6fee1e94fd6b48ac326550280ec uart-kernel-verify1 uart-pair1 uart-state1 uart-status1 uart-tx1 vesper-boot-probe".split())
def keep_save(name):
 p=Path(name);n=p.name.lower()
 while n.endswith(('.bak','.bkp')):n=n.rsplit('.',1)[0]
 return Path(n).suffix in PROGRESS or bool({'saves','states','snapshots'}&{x.lower() for x in p.parts})
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());assert a['fat_clean'] and a['card_writes']==o['card_writes']==0;verify_saved(archive,a)
 entries=a['all_retro_files']+o['files'];proofs={};pending=[];saved=[]
 for e in entries:
  parts=e['path'].split('/')
  if len(parts)<3 or parts[0]!='retro' or parts[1] not in PROFILES:continue
  if keep_save(e['path']):saved.append(e['path']);continue
  if e['stored']:
   p=archive/e['path'];assert digest(p)==e['sha256'];proofs[e['path']]={'host':p.relative_to(ROOT).as_posix(),'sha256':e['sha256'],'bytes':e['bytes'],'kind':'verified-sparse-evidence'}
  else:pending.append(e)
 # Static package bytes must already exist on the host; no new bulk copy.
 lookup=defaultdict(list)
 for e in pending:lookup[(Path(e['path']).name,e['bytes'])].append(e)
 found={};store=ROOT/'device-evidence/attempt-objects'
 for e in pending:
  p=store/e['sha256']
  if p.is_file() and digest(p)==e['sha256']:found[e['sha256']]=p
 remaining={e['sha256'] for e in pending}-set(found)
 def fail(error):raise error
 for folder in ['releases','build','device-evidence']:
  for parent,dirs,files in os.walk(ROOT/folder,followlinks=False,onerror=fail):
   dirs[:]=[n for n in dirs if n not in {'.git','node_modules','sysroot','attempt-objects','__pycache__'} and not (Path(parent)/n).is_symlink()]
   for name in files:
    keys=[key for key in lookup if key[0]==name]
    if not keys:continue
    p=Path(parent)/name
    if p.is_symlink():continue
    size=p.stat().st_size;matches=lookup.get((name,size),[])
    if not any(e['sha256'] in remaining for e in matches):continue
    h=digest(p)
    if h in remaining and any(e['sha256']==h for e in matches):found[h]=p;remaining.remove(h)
  if not remaining:break
 unresolved=[]
 for e in pending:
  if e['sha256'] in found:proofs[e['path']]={'host':found[e['sha256']].relative_to(ROOT).as_posix(),'sha256':e['sha256'],'bytes':e['bytes'],'kind':'verified-existing-package-copy'}
  else:unresolved.append(e)
 wrapper=ROOT/'releases/snes-mvp-1.19/launch.sh';manifest=json.loads((wrapper.parent/'manifest.json').read_text());assert digest(wrapper)==manifest['wrapper_sha256']
 protected={e['path']:e['sha256'] for e in entries if e['path'] not in proofs and e['path']!='retro/snes-mvp/launch.sh'}
 rollback=json.loads((ROOT/'evidence/2026-10-16/battery-rollback/installation.json').read_text());assert protected['retro/update/Code.bkp']==rollback['package_sha256'] and protected['retro/init']==rollback['card_UART_payloads']['init'] and protected['retro/uart-fix1/launch.sh']==rollback['card_UART_payloads']['launch.sh']
 plan={'version':'retired-test-cleanup1','archive':archive.name,'archive_manifest_sha256':digest(archive/'archive.json'),'outside_manifest_sha256':digest(archive/'outside-retro.json'),'profiles':sorted(PROFILES),'before_file_count':len(entries),'remove':proofs,'remove_count':len(proofs),'remove_bytes':sum(v['bytes'] for v in proofs.values()),'kept_save_paths':saved,'unresolved_retained':unresolved,'protected':protected,'restore_dispatcher':{'path':'retro/snes-mvp/launch.sh','before_sha256':next(e['sha256'] for e in entries if e['path']=='retro/snes-mvp/launch.sh'),'host':wrapper.relative_to(ROOT).as_posix(),'sha256':digest(wrapper)},'rollback_trigger_sha256':rollback['package_sha256'],'planner_sha256':digest(Path(__file__)),'no_new_full_backup':True,'card_writes':0}
 dest=archive/'cleanup-plan.json';assert not dest.exists();dest.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({k:plan[k] for k in ['before_file_count','remove_count','remove_bytes']},indent=2));print('kept saves',len(saved),'unresolved retained',len(unresolved));print('plan',dest)
if __name__=='__main__':main(Path(sys.argv[1]))
