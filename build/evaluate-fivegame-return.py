"""Publish bounded return metrics from a preserved sparse archive; no card access."""
from pathlib import Path
from hashlib import sha256
import argparse, importlib.util, json, re
ROOT=Path(__file__).resolve().parent.parent
def digest(p): return sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('archive',type=Path);a=p.parse_args();archive=a.archive.resolve()
 assert archive.is_relative_to(ROOT/'device-evidence')
 spec=importlib.util.spec_from_file_location('reporter',ROOT/'build/report-fivegame.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 meta=read(archive/'archive.json');outside=read(archive/'outside-retro.json');m.verify_saved(archive,meta)
 assert meta['fat_clean'] and meta['card_writes']==outside['card_writes']==0
 for e in outside['files']:
  if e['stored']:assert digest(archive/e['path'])==e['sha256']
 pub=ROOT/'evidence/2026-10-16/fivegame';installed=read(pub/'installation.json');q=read(pub/'qualification.json');before=ROOT/'device-evidence'/installed['archive']
 assert digest(before/'archive.json')==q['archive_manifest_sha256']
 old={e['path']:e['sha256'] for e in read(before/'archive.json')['all_retro_files']};now={e['path']:e['sha256'] for e in meta['all_retro_files']}
 changes={n:{'before':h,'after':now.get(n)} for n,h in old.items() if now.get(n)!=h}
 assert set(changes)=={'retro/snes-mvp/launch.sh','retro/snes-mvp/last-launch-lab','retro/swapfile','retro/uart-fix1/latest-boot.log'}
 assert {e['path']:e['sha256'] for e in outside['files']}=={e['path']:e['sha256'] for e in read(before/'outside-retro.json')['files']}
 assert now['retro/snes-mvp/launch.sh']==installed['dispatch_sha256']
 assert now['retro/snes-fivegame1/last-launch']==now['retro/snes-mvp/last-launch-lab']==installed['marker_sha256']
 assert not any(n.endswith('/armed') or n.endswith('/Code.bkp') for n in now)
 for n,h in installed['payload_hashes'].items():assert now['retro/snes-fivegame1/'+n]==h,n
 payload=ROOT/'build/fivegame-physical-private-v1';assert digest(payload/'plan.json')==installed['payload_hashes']['plan.json']
 bases=list((archive/'retro/snes-fivegame1/results').glob('run-*'));assert len(bases)==1;base=bases[0]
 report=m.analyze(base,read(payload/'plan.json'));supervisor=m.kv(base/'supervisor.txt');suite=m.kv(base/'suite-result.txt')
 assert report['safe_teardown'] and supervisor['raw_status']=='1280' and suite['stopped']=='1'
 assert [e['status'] for e in report['epochs']]==['CLEAN_BOUNDED_WINDOW']*3+['FAILED_BEFORE_MEASUREMENT']+['NOT_STARTED']*16
 def uart(name):return dict(re.findall(r'(\w+)=([^\s]+)',(base/name).read_text()))
 u0,u1=uart('uart-before.txt'),uart('uart-after.txt');assert u1['attached']=='1' and all(u1[k]=='0' for k in ('full','fault','bypass','cap'))
 assert int(u1['calls'])==int(u1['added'])+int(u1['fallback']) and int(u1['added'])==int(u1['writes'])+int(u1['empty_stop'])
 stale={n:digest(base/'run-002'/n)==digest(base/'run-003'/n) for n in ('input.csv','pcm-full.txt')};assert all(stale.values())
 result={**report,'archive':archive.name,'archive_manifest_sha256':digest(archive/'archive.json'),'outside_manifest_sha256':digest(archive/'outside-retro.json'),
  'installation_sha256':digest(pub/'installation.json'),'card_writes':0,'fat_clean':True,'rearmed':False,'new_sparse_content_bytes':meta['new_content_bytes']+outside['new_content_bytes'],
  'preservation':{'prior_files':len(old)+len(outside['files']),'unchanged_prior_files':len(old)+len(outside['files'])-len(changes),'expected_changes':changes,
   'outside_files_unchanged':len(outside['files']),'installed_payload_hashes_verified':len(installed['payload_hashes']),'all_other_prior_files_including_saves_UART_init_unchanged':True},
  'supervisor':supervisor,'suite':suite,'clean_windows':3,'matched_policy_pairs':0,'user_observation':'Initially reported crash during F-Zero; confirmed pressing Select+Start at the retained F-Zero picture.',
  'interpretation':'User abort during Star Fox cold replay, consistent with stopped=1 and normal child exit 5. F-Zero completed; no process crash or forced timeout is recorded. Exact replay call at abort was not logged.',
  'Star_Fox_failure':{'measured_calls':0,'native_PCM_opened':False,'session_elapsed_ns':m.kv(base/'run-003/last-session.txt')['session_elapsed_ns'],'stale_previous_epoch_buffers_excluded':stale},
  'UART_before':u0,'UART_after':u1,'raw_input_sha256':{p.relative_to(archive).as_posix():digest(p) for p in base.rglob('*') if p.is_file() and p.name!='fivegame-analysis.json'},
  'analysis_sources':{n:digest(ROOT/'build'/n) for n in ('report-fivegame.py','evaluate-fivegame-return.py')}}
 out=pub/'return.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
 manifest=ROOT/'evidence/manifest.json';data=manifest.read_bytes();values=json.loads(data)
 for e in values['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 values['entries'].append({'source':(base/'fivegame-analysis.json').relative_to(ROOT).as_posix(),'published':out.relative_to(ROOT).as_posix(),'source_sha256':digest(base/'fivegame-analysis.json'),'published_sha256':digest(out),'bytes':out.stat().st_size,'normalized':True})
 text=json.dumps(values,indent=2)+'\n';manifest.write_bytes(text.replace('\n','\r\n' if b'\r\n' in data else '\n').encode())
 print(json.dumps({'published':str(out),'clean_windows':3,'matched_pairs':0,'new_bytes':result['new_sparse_content_bytes'],'preserved_prior_files':result['preservation']['unchanged_prior_files']}))
if __name__=='__main__':main()
