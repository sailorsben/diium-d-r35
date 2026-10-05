"""Bounded raw-contract analysis; synthetic/QEMU and hardware remain distinct."""
from pathlib import Path
from collections import defaultdict
import argparse
import csv
import json
import math
import shlex

METHODS=('libc_nanosleep','kernel_clock_nanosleep','poll_timeout','timerfd')
def rows(p):
    with p.open() as f: return [{k:int(v) for k,v in r.items()} for r in csv.DictReader(s for s in f if not s.startswith('#'))]
def distribution(values):
    if not values: return {'n':0}
    s=sorted(values)
    return {'n':len(s),'mean':sum(s)/len(s),'p50':s[math.ceil(len(s)*.50)-1],
            'p95':s[math.ceil(len(s)*.95)-1],'p99':s[math.ceil(len(s)*.99)-1],'maximum':s[-1]}
def audio(p):
    data=rows(p); writes=[s for s in data if s['operation']==1]; polls=[s for s in data if s['operation'] in (2,7)]
    success=[s for s in data if s['accepted_bytes']>0 and s['delay_rc']==0]
    pointers=[s for s in data if s['ptr_rc']==0]
    pairs=[]
    for i,s in enumerate(data):
        if s['operation']==2 and s['rc']>0 and s['revents']&4:
            following=next((r for r in data[i+1:] if r['operation'] in (1,4,5)),None)
            if following and following['operation']==1: pairs.append(following)
    return {'file':p.name,'samples':len(data),'successful_write_bytes':sum(max(0,s['rc']) for s in writes),
            'short_writes':sum(0<s['rc']<s['requested'] for s in writes),
            'write_eagain':sum(s['rc']<0 and s['errno']==11 for s in writes),
            'fatal_write_errors':sum(s['rc']<0 and s['errno'] not in (4,11) for s in writes),
            'poll_results':{'ready':sum(s['rc']>0 for s in polls),'timeout':sum(s['rc']==0 for s in polls),'error':sum(s['rc']<0 for s in polls)},
            'poll_bracket_ns':distribution([s['query_begin_ns']-s['begin_ns'] for s in polls]),
            'query_window_ns':distribution([s['end_ns']-s['query_begin_ns'] for s in data]),
            'readiness_followed_by_write_pairs':len(pairs),
            'readiness_followed_by_eagain':sum(s['rc']<0 and s['errno']==11 for s in pairs),
            'negative_free_space':sum(s['space_rc']==0 and s['free_bytes']<0 for s in data),
            'successful_delay_bytes':distribution([s['delay_bytes'] for s in success]),
            'pointer_backward_samples':sum(b['ptr_bytes']<a['ptr_bytes'] for a,b in zip(pointers,pointers[1:])),
            'query_errors':{k:sum(s[k+'_rc']<0 for s in data) for k in ('delay','space','ptr')},
            'physical_xruns_measured':False,'pointer_clock_qualified':False}
def analyze(folder):
    events=[dict(v.split('=',1) for v in shlex.split(s) if '=' in v) for s in (folder/'results.log').read_text().splitlines()]
    begin=next(r for r in events if r['event']=='run_begin')
    groups=defaultdict(list)
    if (folder/'timers.csv').exists():
        for s in rows(folder/'timers.csv'): groups[(s['method'],s['load'],s['requested_ns'],s['slack_ns'])].append(s)
    timers=[]
    for (method,load,requested,slack),samples in sorted(groups.items()):
        valid=[s for s in samples if s['rc']>=0]
        timers.append({'method':METHODS[method],'load':load,'requested_ns':requested,'slack_ns':slack,
                       'errors':len(samples)-len(valid),'duration_ns':distribution([s['end_ns']-s['begin_ns'] for s in valid]),
                       'lateness_ns':distribution([s['end_ns']-s['begin_ns']-requested for s in valid]),
                       'caller_cpu_ns':distribution([s['cpu_ns'] for s in valid])})
    drivers=[]; driver_dropped=0
    for p in folder.glob('driver-calls*.csv'):
        drivers.extend(rows(p))
        for line in p.read_text().splitlines():
            if line.startswith('# captured='):
                totals=dict(v.split('=',1) for v in line[2:].split())
                driver_dropped=max(driver_dropped,int(totals['dropped']))
    drivers.sort(key=lambda r:r['begin_ns']); commands=defaultdict(list)
    for s in drivers: commands[(s['phase'],s['kind'],s['operation'],s['command'])].append(s)
    costs=[{'phase':phase,'kind':kind,'operation':op,'command':hex(command),'errors':sum(s['rc']<0 for s in samples),
            'bracket_ns':distribution([s['end_ns']-s['begin_ns'] for s in samples])}
           for (phase,kind,op,command),samples in sorted(commands.items())]
    statuses=[s for s in drivers if s['kind']==1 and s['command']==0x80045005 and s['rc']>=0]
    fallback=[]
    for i,s in enumerate(drivers):
        if s['kind']==1 and s['command']==0x80045005 and s['rc']>=0 and not s['status']&2:
            following=next((r for r in drivers[i+1:] if r['fd']==s['fd'] and r['kind']==1),None)
            if following and following['command']==0x5003: fallback.append(following['begin_ns']-s['end_ns'])
    configs=[s for s in drivers if s['kind']==1 and s['command']==0x40e45000]
    producers=[]
    for p in sorted(folder.glob('producer-*.csv')):
        samples=rows(p)
        producers.append({'file':p.name,'calls':len(samples),
                          'admission_wait_ns':distribution([s['admitted_ns']-s['begin_ns'] for s in samples]),
                          'work_wall_ns':distribution([s['work_end_ns']-s['admitted_ns'] for s in samples]),
                          'work_cpu_ns':distribution([s['cpu_ns'] for s in samples]),
                          'audio_publish_ns':distribution([s['published_ns']-s['work_end_ns'] for s in samples]),
                          'image_and_submit_ns':distribution([s['submitted_ns']-s['published_ns'] for s in samples]),
                          'observed_lead_bytes':distribution([s['observed_lead_bytes'] for s in samples]),
                          'observation_age_ns':distribution([s['admitted_ns']-s['observation_ns'] for s in samples if s['observation_ns']])})
    return {'version':'lab2','simulated':begin['simulated']=='1',
            'complete':any(r['event']=='run_end' and r['status']=='complete' for r in events),
            'events':events,'timers':timers,'producers':producers,'audio':[audio(p) for p in sorted(folder.glob('*.csv')) if p.name.startswith(('transport-','controller-'))],
            'driver':{'calls':len(drivers),'dropped':driver_dropped,'costs':costs,'successful_status_values':sorted(set(s['status'] for s in statuses)),
                      'not_frame_done_statuses':len(fallback),'status_to_stop_fallback_gap_ns':distribution(fallback),
                      'observed_scaler_output_a':sorted(set(s['output_a'] for s in configs)),
                      'observed_scaler_output_b':sorted(set(s['output_b'] for s in configs)),
                      'observed_queue_drop_flags':sorted(set(s['queue_drop_flags'] for s in configs)),
                      'bitmap_addresses':sorted(set(s['bitmap_addr'] for s in drivers if s['command']==0x402c6413))},
            'limits':['Reported OSS rate/counters do not establish physical DAC rate or measured xruns.',
                      'Controller workload and memory fills are synthetic, not whole-game acceptance.',
                      'Timer getres alone does not establish wake precision or CONFIG_HZ.',
                      'Observation adds syscall/query CPU and can perturb latency.',
                      'Driver argument direction encoding is not a substitute for its recovered calling contract.',
                      'Queue fields and A/B flags do not qualify continuous scaling or cache coherency.']}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('folder',type=Path); args=parser.parse_args()
    print(json.dumps(analyze(args.folder),indent=2))
