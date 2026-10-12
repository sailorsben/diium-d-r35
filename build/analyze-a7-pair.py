"""Analyze archived physical ABBA runs; keep unmatched coverage and epochs explicit."""
from pathlib import Path
from hashlib import sha256
import csv, json, re, statistics, sys
ROOT=Path(__file__).resolve().parent.parent
archive=Path(sys.argv[1]).resolve();base=archive/'retro/snes-pair1'
def stats(xs):
    xs=sorted(xs)
    if not xs:return {'n':0}
    def q(p):
        x=(len(xs)-1)*p;i=int(x);j=min(i+1,len(xs)-1)
        return xs[i]+(xs[j]-xs[i])*(x-i)
    return {'n':len(xs),'mean':statistics.mean(xs),'median':statistics.median(xs),'p95':q(.95),'p99':q(.99),'min':xs[0],'max':xs[-1]}
records=json.loads((archive/'archive.json').read_text());assert records['fat_clean'] and records['card_writes']==0
for e in records['all_retro_files']:assert sha256((archive/e['path']).read_bytes()).hexdigest()==e['sha256']
stage=ROOT/'device-evidence/a7-pair-before-20261012T032639Z'
installed=json.loads((stage/'pair-installation.json').read_text())
for name,h in installed['payload_hashes'].items():assert sha256((base/name).read_bytes()).hexdigest()==h,name
assert (base/'last-launch').read_bytes()==b'SNES-pair1 separate A7 measurement only; baseline/combined ABBA replay\n'
protected=json.loads((stage/'archive.json').read_text())['all_retro_files']
runtime_changed=[]
for e in protected:
    if e['path']=='retro/snes-mvp/launch.sh':continue
    if e['path']=='retro/swapfile':
        if sha256((archive/e['path']).read_bytes()).hexdigest()!=e['sha256']:runtime_changed.append(e['path'])
        continue
    assert sha256((archive/e['path']).read_bytes()).hexdigest()==e['sha256'],e['path']
assert not (archive/'retro/snes-mvp/armed').exists()
runs=[];data={}
metrics=('cpu_ns','wall_ns','admission_ns','observer_ns','step_ns')
for path in sorted(base.glob('pass-*')):
    m=re.fullmatch(r'pass-(\d+)-start-(\d+)-(baseline|combined)',path.name);assert m
    index,start,label=int(m[1]),int(m[2]),m[3]
    lines=(path/'pair.csv').read_text().splitlines()
    meta=dict(l[1:].split('=',1) for l in lines if l.startswith('#'))
    assert meta['mock']=='0' and meta['phase_clocks']=='disabled'
    rows=[{k:int(v) for k,v in r.items()} for r in csv.DictReader(l for l in lines if not l.startswith('#'))]
    assert [r['frame'] for r in rows]==list(range(start,start+len(rows)))
    session=dict(l.split('=',1) for l in (path/'last-session.txt').read_text().splitlines() if '=' in l)
    assert int(session['runs'])==len(rows)
    trusted=[r for r in rows if r['state']==3 and r['epoch']==1]
    phase=[r for r in rows if 277<=r['frame']<=438 and (start==0 or r['frame']>=start+16)]
    delta_native=rows[-1]['native_generated']/len(rows) if rows else 0
    # Use monotonic worker snapshots within a single RUNNING epoch. No priming
    # credit or post-stop drain enters this difference.
    production={}
    if len(trusted)>1:
        a,z=trusted[0],trusted[-1];dt=(z['observed_ns']-a['observed_ns'])/1e9
        if dt>0:production={'interval_s':dt,'accepted_delta':z['xfer']-a['xfer'],
            'accepted_frames_per_s':(z['xfer']-a['xfer'])/dt,'reserve_start':a['playable'],'reserve_end':z['playable']}
    trace=(path/'pcm-full.txt').read_text();events=[]
    for line in trace.splitlines():
        if line.startswith('seq='):
            e=dict(re.findall(r'(\w+)=([^ ]+)',line));events.append(e)
    failures=[e for e in events if int(e['result'])<0]
    steady=[e for e in events if e['state']=='3' and e['epoch']=='1' and int(e['result'])>=0]
    runs.append({'pass':index,'start':start,'variant':label,'calls':len(rows),'submitted':int(session['video_submitted']),
        'error':session['error'],'failed':bool(int(meta['failed'])),'effect_calls_after_warmup':len(phase),
        'all_frame_cost_us':{k:stats([r[k]/1000 for r in rows]) for k in metrics},
        'effect_cost_us':{k:stats([r[k]/1000 for r in phase]) for k in metrics},
        'effect_core_plus_admission_us':stats([(r['wall_ns']+r['admission_ns'])/1000 for r in phase]),
        'frame_frequency_values_khz':sorted({r[k] for r in rows for k in ('freq_before_khz','freq_after_khz')}),
        'mean_native_frames_per_call':delta_native,'held':int(session['held']),
        'accepted_including_prime':int(session['output_accepted_frames_including_priming']),
        'resampled_enqueued':int(session['resampled_enqueued_frames']),
        'priming':int(session['priming_silence_frames']),'remaining':int(session['audio_remaining_frames']),
        'running_production':production,'minimum_frame_observed_running_reserve':min((r['playable'] for r in trusted),default=None),
        'trace_entries':len(events),'trace_total':int(re.search(r'entries_total=(\d+)',trace)[1]),
        'trace_retained_from':int(re.search(r'retained_from=(\d+)',trace)[1]),
        'last_running_trace':steady[-1] if steady else None,'fault_events':failures,
        'last_running_pointer_bias':int(steady[-1]['appl'])-int(steady[-1]['xfer']) if steady else None,
        'pin':meta['pin'],'governor':meta['governor']})
    data[index]={r['frame']:r for r in rows}
assert len(runs)==12
pairs=[]
for a,b in ((0,1),(3,2),(4,5),(7,6),(8,9),(11,10)):
    start=runs[a]['start'];lo=max(277,start+16 if start else 277)
    common=sorted(f for f in data[a].keys() & data[b].keys() if lo<=f<=438 and data[a][f]['state']==data[b][f]['state']==3)
    pairs.append({'baseline_pass':a,'combined_pass':b,'first_frame':min(common,default=None),'last_frame':max(common,default=None),
        'common_running_effect_calls_after_warmup':len(common),
        'saving_us':{k:stats([(data[a][f][k]-data[b][f][k])/1000 for f in common]) for k in metrics},
        'core_plus_admission_saving_us':stats([((data[a][f]['wall_ns']+data[a][f]['admission_ns'])-(data[b][f]['wall_ns']+data[b][f]['admission_ns']))/1000 for f in common])})
summary={'version':'1.19-pair1','archive':archive.name,'hardware_measured':True,'production_accepted':False,
    'protected_original_retro_files':len(protected)-2,'runtime_mutable_files_changed':runtime_changed,'all_staged_payload_hashes_match':True,'fat_clean':True,'card_writes':0,
    'combined_complete_passes':sum(not r['failed'] for r in runs if r['variant']=='combined'),
    'baseline_failed_passes':sum(r['failed'] for r in runs if r['variant']=='baseline'),
    'runs':runs,'aligned_pairs':pairs,'late_floor_us':1514.283,'PCM_proxy_required_us':2436.981,
    'limits':['CPU frequency sysfs unavailable: paired frequency parity unproved',
    'later starts are independent audio epochs, not continuous effect/recovery',
    'baseline stops early: paired saving covers only overlapping RUNNING calls, not whole effect',
    'CPU and step timing include instrumentation; observer is never subtracted',
    'accepted rate over selected RUNNING endpoints is reserve-sensitive, not an unbounded sustained throughput measurement',
    'no physical pixel capture; visual observations separate from offline exact-output qualification']}
(archive/'pair-analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'combined_complete':summary['combined_complete_passes'],'baseline_failed':summary['baseline_failed_passes'],
    'runs':[{k:r[k] for k in ('pass','start','variant','calls','submitted','error','effect_calls_after_warmup','minimum_frame_observed_running_reserve')} for r in runs],
    'pairs':pairs},indent=2))
