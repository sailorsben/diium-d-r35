"""Analyze an archived profile1 return. All timing remains observer-inclusive."""
from pathlib import Path
import csv,json,math,statistics,sys
def rows(p):return [{k:int(v) for k,v in r.items()} for r in csv.DictReader(s for s in p.read_text().splitlines() if not s.startswith('#'))]
def kv(p):return dict(s.split('=',1) for s in p.read_text().splitlines() if '=' in s)
def distribution(v):
 if not v:return {'n':0}
 a=sorted(v)
 return {'n':len(a),'mean_us':statistics.mean(a)/1000,'median_us':statistics.median(a)/1000,'p95_us':a[math.ceil(.95*len(a))-1]/1000,'p99_us':a[math.ceil(.99*len(a))-1]/1000,'max_us':a[-1]/1000}
def analyze(root):
 plan=json.loads((root/'plan.json').read_text());assert plan['version']=='1.19-profile1'
 answer={'version':plan['version'],'performance_evidence':'A7 only when mock_backend=0; reject otherwise','observer_costs':'included; no calibration subtraction','phase_overlap':'audio callback is nested inside APU; do not add it again','runs':[],'aligned_observer_disturbance':[]}
 allrows={}
 for run in plan['runs']:
  d=root/f"run-{run['run']:03d}";r={**run}
  if not (d/'phases.csv').exists():r['missing']='phases.csv';answer['runs'].append(r);continue
  phases=rows(d/'phases.csv');frames=rows(d/'frames.csv');s=kv(d/'last-session.txt')
  assert s['mock_backend']=='0','Offline/mock CPU times are not A7 evidence'
  assert s['core_crc32']==plan['cores'][run['variant']]['crc32']
  assert len(phases)==len(frames) and all(p['frame']==f['frame'] for p,f in zip(phases,frames))
  allrows[run['run']]=phases
  sampled=[p for p in phases if p['sampled'] and p['frame']>=120]
  r.update(calls=len(phases),error=s.get('error'),frequency_observations_khz=sorted({f[k] for f in frames for k in ('freq_before_khz','freq_after_khz')}),sampled_calls=len(sampled),clock_loop_mean_ns=kv(d/'phases.csv').get('#clock_loop_mean_ns'))
  r['whole_call_CPU']=distribution([p['core_cpu_ns'] for p in phases if p['frame']>=120])
  r['phase_groups']={}
  for label,subset in (('warm_all',sampled),('pre_effect_120_239',[p for p in sampled if p['frame']<240]),('known_expensive_384_423' if run['fixture']==1 else 'known_expensive_496_543',[p for p in sampled if (384<=p['frame']<=423 if run['fixture']==1 else 496<=p['frame']<=543)])):
   stats={key:distribution([p[key] for p in subset]) for key in ('core_cpu_ns','ppu_cpu_ns','apu_inclusive_cpu_ns','audio_callback_cpu_ns','video_callback_cpu_ns')}
   stats['residual_including_SNES_CPU_port_SPC_dispatch_observer']=distribution([p['core_cpu_ns']-p['ppu_cpu_ns']-p['apu_inclusive_cpu_ns'] for p in subset])
   stats['negative_residual_count']=sum(p['core_cpu_ns']<p['ppu_cpu_ns']+p['apu_inclusive_cpu_ns'] for p in subset)
   r['phase_groups'][label]=stats
  totals=[];pa=pv=0
  for f in frames:
   a,v=f['audio_worker_cpu_ns'],f['video_worker_cpu_ns'];valid=a>=pa and v>=pv
   totals.append(f['main_step_cpu_ns']+a-pa+v-pv if valid else None);pa,pv=a,v
  windows=[{'first':frames[i]['frame'],'last':frames[i+15]['frame'],'CPU_sum_mean_us':sum(totals[i:i+16])/16000,'invalid_PCM_pointer_frames':sum(not f['pointer_valid'] for f in frames[i:i+16])} for i in range(120,len(frames)-15) if all(x is not None for x in totals[i:i+16])]
  r['worst_16_call_CPU_window']=max(windows,key=lambda w:w['CPU_sum_mean_us']) if windows else None
  if r['worst_16_call_CPU_window']:
   w=r['worst_16_call_CPU_window'];w['deadline_overrun_us']=w['CPU_sum_mean_us']-16688.1545;w['saving_needed_for_20_percent_headroom_us']=w['CPU_sum_mean_us']-13350.5236
  answer['runs'].append(r)
 for c,p in ((0,1),(3,2)):
  if c not in allrows or p not in allrows:continue
  control={r['frame']:r for r in allrows[c]}
  for label,sampled in (('sampled_calls',1),('unsampled_calls',0)):
   diff=[r['core_cpu_ns']-control[r['frame']]['core_cpu_ns'] for r in allrows[p] if r['frame']>=120 and r['frame'] in control and bool(r['sampled'])==bool(sampled)]
   answer['aligned_observer_disturbance'].append({'control_run':c,'profile_run':p,'calls':label,'profile_minus_control_cpu':distribution(diff),'interpretation':'one pair; includes run noise/cache/scheduling; not a calibration subtraction or renderer saving'})
 return answer
def selftest():
 assert distribution([])=={'n':0}
 d=distribution(list(range(1,101)));assert d['median_us']==.0505 and d['p95_us']==.095 and d['p99_us']==.099
 print('PASS distribution ranks and empty-sample handling; synthetic only')
if __name__=='__main__':
 if sys.argv[1]=='--self-test':selftest()
 else:
  archive=Path(sys.argv[1]).resolve();assert (archive/'archive.json').exists(),'Use an archive, never the live card'
  result=analyze(archive/'retro/snes-profile1');out=archive/'profile-analysis.json';out.write_text(json.dumps(result,indent=2)+'\n');print(out)
