"""Bound return preservation, matched-game results and passive UART evidence."""
from pathlib import Path
import json,sys,importlib.util
from attempt_archive import digest,verify_saved
ROOT=Path(__file__).resolve().parent.parent
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def main(archive):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence');a=json.loads((archive/'archive.json').read_text());o=json.loads((archive/'outside-retro.json').read_text());assert a['fat_clean'] and a['card_writes']==o['card_writes']==0;verify_saved(archive,a)
 installation=json.loads((ROOT/'evidence/2026-10-16/fivegame-kernel/installation.json').read_text());before=ROOT/'device-evidence'/installation['archive'];old=json.loads((before/'archive.json').read_text())['all_retro_files']+json.loads((before/'outside-retro.json').read_text())['files'];entries={e['path']:e for e in a['all_retro_files']+o['files']};changes={e['path']:entries.get(e['path'],{}).get('sha256') for e in old if entries.get(e['path'],{}).get('sha256')!=e['sha256']};assert set(changes)=={'retro/swapfile','retro/snes-mvp/launch.sh','retro/snes-mvp/last-launch-lab'}
 assert changes['retro/snes-mvp/launch.sh']==installation['dispatch_sha256'] and changes['retro/snes-mvp/last-launch-lab']==installation['marker_sha256'];assert entries['retro/init']['sha256']==installation['normal_init_sha256'];assert not any(n.endswith('/armed') or n.endswith('/Code.bkp') for n in entries)
 target=installation['target']
 for n,h in installation['payload_hashes'].items():assert entries[target+'/'+n]['sha256']==h,n
 assert entries[target+'/last-launch']['sha256']==installation['marker_sha256']
 base=list((archive/target/'results').glob('run-*'));assert len(base)==1;base=base[0]
 result=json.loads((archive/'fivegame-kernel-analysis.json').read_text());clean=[r for r in result['epochs'] if r['status']=='CLEAN_BOUNDED_WINDOW'];assert [r['fixture'] for r in clean]==[0,1,2] and result['safe_teardown']
 suite=kv(base/'suite-result.txt');supervisor=kv(base/'supervisor.txt');assert suite['runs']=='4' and suite['stopped']=='1' and supervisor['raw_status']=='1280' and supervisor['forced']=='0';assert 'lab_exit=5' in (base/'wrapper.log').read_text()
 windows=[];boot_ids=set()
 for label in ['before','after']:
  d=base/('uart-'+label);t={k:int(v) for k,v in kv(d/'timing.txt').items()};assert t['failed']==0 and t['relative_wait_ns']==5000000000;counts=[]
  for tag in ['before','after']:
   boot_ids.add((d/(tag+'-boot-id.txt')).read_text().strip());assert set(kv(d/(tag+'-presence.txt')).values())=={'0'};assert 'd35_uart_tx' not in (d/(tag+'-modules.txt')).read_text();counts.append(int(next(l.split()[1] for l in (d/(tag+'-interrupts.txt')).read_text().splitlines() if l.strip().startswith('19:'))))
  short=(t['end_snapshot_start_ns']-t['begin_snapshot_end_ns'])/1e9;long=(t['end_snapshot_end_ns']-t['begin_snapshot_start_ns'])/1e9;assert long>=short>=5 and counts[1]>=counts[0];rates=[(counts[1]-counts[0])/long,(counts[1]-counts[0])/short];assert rates[1]<500;windows.append({'phase':label,'counts':counts,'IRQ19_per_second_bracket':rates})
 assert len(boot_ids)==1 and base.name.startswith('run-'+next(iter(boot_ids)))
 session=kv(base/'run-003/last-session.txt');assert session['runs']=='0' and session['pcm_period_frames']=='0'
 v={'archive':archive.name,'all_files_hashed':len(entries),'new_sparse_content_bytes':a['new_content_bytes']+o['new_content_bytes'],'FAT_clean':True,'card_writes':0,'no_full_backup':True,'saves_stock_prior_evidence_normal_init_unchanged':True,'preinstall_files_unchanged':len(old)-len(changes),'expected_prior_changes':changes,'payload_hashes_verified':len(installation['payload_hashes']),'markers_consumed_no_rearm':True,'safe_teardown':True,'suite':suite,'supervisor':supervisor,'clean_blocking_windows':clean,'matched_policy_pairs':0,'Star_Fox_replay_elapsed_seconds':int(session['session_elapsed_ns'])/1e9,'Star_Fox_replay_call_count':'NOT_RECORDED','Star_Fox_measured_calls':0,'Rendering_Ranger':'NOT_STARTED','UART_windows':windows,'runtime_UART_module_absent':True,'battery_regression':'User reports low-power warning immediately after unplugging despite extended plugged-in time. Cause unresolved; no battery/charge telemetry was collected.','user_observation':'Plugged-in run appeared stopped at F-Zero image; user pressed Start+Select to return to launcher.','interpretation':'F-Zero completes; Star Fox silent cold replay is aborted. Cannot distinguish slow progress from stall without replay call counts. No native process crash or forced timeout recorded.','next_gate':'No unchanged rearm. Investigate battery warning and add visible replay progress with durable call/abort evidence before another suite.','limits':['Idle IRQ reduction does not qualify charging, electrical UART output, CPU savings or all-game performance.','Stale input/PCM buffers in failed-before-measurement Star Fox are excluded.']}
 (archive/'return-evaluation.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:v[k] for k in ['all_files_hashed','new_sparse_content_bytes','preinstall_files_unchanged','Star_Fox_replay_elapsed_seconds','UART_windows']},indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
