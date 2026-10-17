"""Preserve only missing diagnostic text/metadata from a verified cleanup plan."""
from pathlib import Path
import json,sys,os,shutil,uuid
from attempt_archive import digest
ROOT=Path(__file__).resolve().parent.parent
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');planpath=archive/'cleanup-plan.json';plan=json.loads(planpath.read_text());assert plan['card_writes']==0
 card=Path('I:/').resolve();assert str(card).lower() in ('i:/','i:\\');store=ROOT/'device-evidence/attempt-objects';store.mkdir(exist_ok=True);records=[]
 assert not (archive/'cleanup-plan-initial.json').exists();retained=[];seen=set()
 for e in plan['unresolved_retained']:
  rel=Path(e['path']);assert len(rel.parts)>2 and rel.parts[0]=='retro' and rel.parts[1] in plan['profiles'] and '..' not in rel.parts
  if not (rel.suffix.lower() in {'.txt','.json'} or rel.name in {'consumed','last-launch','last-launch-lab'}):retained.append(e);continue
  source=(card/rel).resolve();assert source.is_relative_to((card/'retro'/rel.parts[1]).resolve()) and not source.is_symlink();assert digest(source)==e['sha256'],e['path']
  obj=store/e['sha256'];new=0
  if obj.exists():assert digest(obj)==e['sha256']
  else:
   temp=store/(e['sha256']+'.'+uuid.uuid4().hex+'.tmp')
   try:
    with source.open('rb') as inp,temp.open('xb') as out:shutil.copyfileobj(inp,out);out.flush();os.fsync(out.fileno())
    assert digest(temp)==digest(source)==e['sha256'];os.replace(temp,obj);new=e['bytes']
   finally:temp.unlink(missing_ok=True)
  target=archive/'supplement'/rel;target.parent.mkdir(parents=True,exist_ok=True)
  if not target.exists():os.link(obj,target)
  assert digest(target)==e['sha256']
  new=0 if e['sha256'] in seen else e['bytes'];seen.add(e['sha256'])
  proof={'host':target.relative_to(ROOT).as_posix(),'sha256':e['sha256'],'bytes':e['bytes'],'kind':'verified-supplemental-text-evidence'};plan['remove'][e['path']]=proof;plan['protected'].pop(e['path']);records.append({**proof,'card_path':e['path'],'new_content_bytes':new})
 plan['unresolved_retained']=retained;plan['remove_count']=len(plan['remove']);plan['remove_bytes']=sum(v['bytes'] for v in plan['remove'].values());plan['supplemental_evidence_files']=len(records);plan['supplemental_new_content_bytes']=sum(r['new_content_bytes'] for r in records)
 (archive/'supplement.json').write_text(json.dumps({'card_writes':0,'no_full_backup':True,'selected_missing_text_only':True,'records':records,'new_content_bytes':plan['supplemental_new_content_bytes']},indent=2)+'\n')
 planpath.rename(archive/'cleanup-plan-initial.json');planpath.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({k:plan[k] for k in ['remove_count','remove_bytes','supplemental_evidence_files','supplemental_new_content_bytes']},indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
