"""Archive-only preservation and passive UART checks for the replay profile."""
from pathlib import Path
import json,sys
from attempt_archive import verify_saved
ROOT=Path(__file__).resolve().parent.parent
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());verify_saved(archive,a);verify_saved(archive,dict(o,all_retro_files=o['files']))
 i=json.loads((ROOT/'evidence/2026-10-17/fivegame-replay/installation.json').read_text());before=ROOT/'device-evidence'/i['archive']
 old=json.loads((before/'archive.json').read_text())['all_retro_files']+json.loads((before/'outside-retro.json').read_text())['files']
 entries={e['path']:e['sha256'] for e in a['all_retro_files']+o['files']}
 changes={e['path']:entries.get(e['path']) for e in old if entries.get(e['path'])!=e['sha256']}
 # Stock owns settings and swap; report their returned hashes without restoring them.
 allowed={'retro/setting.xml','retro/swapfile','retro/snes-mvp/launch.sh','retro/snes-mvp/last-launch-lab'}
 assert set(changes)<=allowed,changes
 assert entries['retro/snes-mvp/launch.sh']==i['dispatch_sha256'] and entries['retro/init']==i['normal_init_sha256']
 assert a['fat_clean'] and a['card_writes']==o['card_writes']==0
 result=json.loads((archive/'fivegame-replay-analysis.json').read_text());base=archive/i['target']/'results'/result['physical_run_directory']
 windows=[];boot_ids=set()
 for label in ['before','after']:
  d=base/('uart-'+label);t={k:int(v) for k,v in kv(d/'timing.txt').items()};assert t['failed']==0 and t['relative_wait_ns']==5000000000
  counts=[]
  for tag in ['before','after']:
   boot_ids.add((d/(tag+'-boot-id.txt')).read_text().strip());assert set(kv(d/(tag+'-presence.txt')).values())=={'0'}
   assert 'd35_uart_tx' not in (d/(tag+'-modules.txt')).read_text()
   counts.append(int(next(l.split()[1] for l in (d/(tag+'-interrupts.txt')).read_text().splitlines() if l.strip().startswith('19:'))))
  short=(t['end_snapshot_start_ns']-t['begin_snapshot_end_ns'])/1e9;long=(t['end_snapshot_end_ns']-t['begin_snapshot_start_ns'])/1e9
  assert long>=short>=5 and counts[1]>=counts[0]
  rates=[(counts[1]-counts[0])/long,(counts[1]-counts[0])/short];assert rates[1]<500
  windows.append({'phase':label,'IRQ19_per_second_bracket':rates})
 assert len(boot_ids)==1 and base.name.startswith('run-'+next(iter(boot_ids)))
 summary={'archive':archive.name,'files_hashed':len(entries),'new_content_bytes':a['new_content_bytes']+o['new_content_bytes'],'FAT_clean':True,'card_writes':0,'no_full_backup':True,'preinstall_changes':changes,'protected_preinstall_files_unchanged':len(old)-len(changes),'UART_windows':windows,'runtime_UART_module_absent':True,'suite':kv(base/'suite-result.txt'),'supervisor':result['replay_supervisor'],'safe_teardown':result['safe_teardown'],'clean_windows':sum(r['status']=='CLEAN_BOUNDED_WINDOW' for r in result['epochs']),'Star_Fox':[{'run':r['run'],'replay':r['replay_progress'],'session':kv(base/f"run-{r['run']:03d}"/'last-session.txt')} for r in result['epochs'] if r['fixture']==3],'battery_telemetry':'Not collected; red LED during powered test is user observation, not proof of charge failure.'}
 out=archive/'replay-return-evaluation.json';assert not out.exists();out.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='Star_Fox'},indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))

