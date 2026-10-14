"""Archive-only assessment plus optional read-only live identity check; no recoding."""
from pathlib import Path
from hashlib import sha256
import csv,importlib.util,json,re,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def rows(p):return list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')))
def main(archive,live=False):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
 for e in a['all_retro_files']:assert digest(archive/e['path'])==e['sha256'],e['path']
 base=archive/'retro/snes-demand-spells1';report=json.loads((base/'spell-analysis.json').read_text());plan=json.loads((base/'plan.json').read_text())
 inst=json.loads((ROOT/'evidence/2026-10-14/demand-spells/installation.json').read_text())
 for n,h in inst['payload_hashes'].items():assert digest(base/n)==h,n
 assert digest(archive/'retro/snes-mvp/launch.sh')==inst['dispatch_sha256']
 assert (base/'last-launch').read_bytes()==b'SNES demand-spells1 automatic18-context test, all frames; experimental\n'
 assert not list((archive/'retro').rglob('armed')) and not (archive/'retro/update/Code.bkp').exists()
 old=json.loads((ROOT/'device-evidence'/inst['archive']/'archive.json').read_text())
 changed=[];unchanged=0
 for e in old['all_retro_files']:
  if e['path']=='retro/snes-mvp/launch.sh':continue
  if (archive/e['path']).is_file() and digest(archive/e['path'])==e['sha256']:unchanged+=1
  else:changed.append(e['path'])
 assert not [n for n in changed if n!='retro/swapfile'],changed
 spec=importlib.util.spec_from_file_location('return_guard',ROOT/'build/package-snes-1.19.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
 protected={**guard.BOOT_EXPECTED,'retro/init':guard.baseline.HOOK,'retro/snes-mvp/plus-a7.so':'80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'}
 for n,h in protected.items():assert digest(archive/n)==h,n
 ROM_hash=None
 if live:
  card=Path('I:/');assert not list((card/'retro').rglob('armed'))
  for n,h in protected.items():assert digest(card/n)==h,n
  for n,h in inst['payload_hashes'].items():assert digest(card/'retro/snes-demand-spells1'/n)==h,n
  ROM_hash=digest(card/'002/Final Fantasy VI.zip');assert ROM_hash=='f61af2bd9e3f9b6a2bd543fb176af0b81fd9e5ba4ea0fa0f453371ccb45d3911'
 cases=[];details=[]
 for c in plan['cases']:
  runs=[r for r in report['epochs'] if r['fixture']==c['seq'] and r['variant']=='demand']
  clean=sum(r['status']=='CLEAN_BOUNDED_WINDOW' for r in runs)
  cases.append({'fixture':c['seq'],'name':c['name'],'recorded_effect_id':c['observed_effect_id'],'clean_windows':clean,'planned_windows':2,
   'worst16_recorded_CPU_ms':[r['worst16_recorded_threads_CPU_mean_ms'] for r in runs],
   'minimum_valid_running_reserve_frames':[r['minimum_valid_running_pointer_reserve_frames'] for r in runs]})
 for r in report['epochs']:
  d=base/f"run-{r['run']:03d}";s=kv(d/'last-session.txt');h=kv(d/'headroom.txt');f=rows(d/'frames.csv')
  invalid=next((x for x in f if x['pointer_valid']=='0'),None)
  ordinary=[];pa=pv=0
  for x in f:
   ca,cv=int(x['audio_worker_cpu_ns']),int(x['video_worker_cpu_ns'])
   if int(x['pointer_valid'])==0 or ca<pa or cv<pv:break
   x['thread_CPU']=int(x['main_step_cpu_ns'])+ca-pa+cv-pv
   x['service']=int(x['step_ns'])-int(x['pace_wait_ns'])+ca-pa+cv-pv
   pa,pv=ca,cv;ordinary.append(x)
  worstframes=r['worst16_valid_CPU_frames'];worst=[x for x in ordinary if int(x['frame']) in worstframes]
  properties=rows(d/'animation.csv');expected=(base/f"cases/{r['fixture']:03d}/expected.bin").read_bytes()
  patterns={expected[1+i*15+1:1+(i+1)*15].hex() for i in range(expected[0])}
  observed=sorted({int(x['attack'],16) for x in properties if x['properties'] in patterns})
  sync=[];boundary=int(s['pcm_boundary_frames']);pointer_bad_ns=None
  for m in re.finditer(r'seq=(\d+) ns=(\d+) op=(\S+) arg=(\d+) result=(-?\d+) state=(\d+) queued=(\d+) appl=(\d+) hw=(\d+) epoch=(\d+) xfer=(\d+)',(d/'pcm-full.txt').read_text()):
   seq,ns,op,arg,result,state,queued,appl,hw,epoch,xfer=m.groups()
   if op!='SYNC_OK' or int(state)!=3:continue
   good=int(appl)%boundary==int(xfer)%boundary and (int(appl)-int(hw))%boundary==int(queued)
   if not good:pointer_bad_ns=int(ns);break
   sync.append((int(ns),int(queued)))
  # Last trustworthy PCM observation before drift; no post-drift reserve claim.
  seconds_to_drift=(pointer_bad_ns-sync[0][0])/1e9 if pointer_bad_ns and sync else None
  details.append({**r,'completed_calls':int(s['runs']),'submitted':int(s['video_submitted']),'held':int(s['held']),'dupes':int(s['video_dupes']),
   'reported_xruns':int(s['xrun_count']),'write_errors':int(s['write_errors']),'final_pointer_bias_frames':int(s['pcm_appl_ptr'])-int(s['pcm_epoch_transferred_frames']),
   'first_invalid_frame':int(invalid['frame']) if invalid else None,'matching_property_attack_ids':observed,
   'running_seconds_before_pointer_drift':seconds_to_drift,'valid_prefix_reserve_min_frames':min((q for _,q in sync),default=None),
   'valid_prefix_reserve_min_ms':min((q for _,q in sync),default=0)/44100*1000,
   'worst16_same_interval_conservative_service_ms':statistics.mean(int(x['service']) for x in worst)/1e6 if worst else None,
   'final_PCM_software_accounting_exact':h['final_PCM_software_accounting_exact'],'final_remaining':int(h['final_remaining']),'final_cleared':int(h['final_cleared']),
   'final_residual_audio_CPU_ns':int(h['post_last_sample_audio_CPU_ns']),'final_residual_video_CPU_ns':int(h['post_last_sample_video_CPU_ns']),
   'phase_profile_available':int(s['phase_profile_available']),'frequency_values_khz':sorted({int(x[k]) for x in f for k in ('freq_before_khz','freq_after_khz')})})
 suite=kv(base/'suite-result.txt');assert suite['runs']=='40' and suite['stopped']=='0'
 log=(base/'startup.log').read_text();assert 'display worker joined' in log and 'FreeVFB returned' in log
 result={'archive':archive.name,'card_writes':0,'FAT_clean':True,'archive_files':len(a['all_retro_files']),'archive_bytes':sum(e['bytes'] for e in a['all_retro_files']),
 'installed_payloads_verified':len(inst['payload_hashes']),'protected_prior_files_unchanged':unchanged,'changed_prior_files':changed,'ROM_live_sha256':ROM_hash,
 'marker_consumed':True,'stock_next_boot':True,'suite':suite,'all_workers_joined_and_display_freed':True,'cases':cases,
 'clean_demand_windows':sum(c['clean_windows'] for c in cases),'planned_demand_windows':36,'cases_clean_both':sum(c['clean_windows']==2 for c in cases),
 'unresolved_contexts':[c['name'] for c in cases if c['clean_windows']!=2],'unresolved_recorded_effect_ids':sorted({c['recorded_effect_id'] for c in cases if c['clean_windows']!=2}),
 'epochs':details,'matched_comparisons':report['matched_Meteor_Quasar'],'production_gate_passed':False,'emulator_runtime_changes':False,
 'interim_user_observations':'Grand Train, Ultima and Pearl seemed to work; Meteor did not seem complete. Observations occurred during the suite, not an independent full40-epoch visual review.',
 'limits':report['limits']+['CPU deadline gap is a recorded-region gap, not a guaranteed sufficient optimization target; uncounted costs and cumulative reserve matter.','A late nominally complete epoch with pointer drift cannot pass despite exact software accounting and no reported underrun.'],
 'inputs':{p.relative_to(ROOT).as_posix():digest(p) for p in (archive/'archive.json',base/'spell-analysis.json',ROOT/'evidence/2026-10-14/demand-spells/installation.json',Path(__file__).resolve())}}
 (archive/'demand-spells-return-evaluation.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'cases_clean_both':result['cases_clean_both'],'clean_demand_windows':result['clean_demand_windows'],'unresolved':result['unresolved_contexts'],'effect_ids':result['unresolved_recorded_effect_ids'],'protected_unchanged':unchanged,'changed_prior':changed,'details':str(archive/'demand-spells-return-evaluation.json')},indent=2))
if __name__=='__main__':main(Path(sys.argv[1]),'--verify-live' in sys.argv)
