"""Hand-calculated fixtures for timer percentiles and audio query/readiness semantics."""
from pathlib import Path
import csv
import importlib.util
import tempfile
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('analysis',ROOT/'build/analyze-platform-lab2.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
assert module.distribution([40,10,30,20])=={'n':4,'mean':25,'p50':20,'p95':40,'p99':40,'maximum':40}
fields=['operation','requested','rc','errno','revents','begin_ns','query_begin_ns','end_ns','accepted_bytes',
        'delay_rc','delay_errno','delay_bytes','space_rc','space_errno','free_bytes','ptr_rc','ptr_errno','ptr_bytes','ptr','blocks']
def row(**kwargs): return {k:kwargs.get(k,0) for k in fields}
samples=[row(operation=0,free_bytes=16),
         row(operation=2,rc=1,revents=4,begin_ns=10,query_begin_ns=20,end_ns=22,free_bytes=-4),
         row(operation=1,requested=8,rc=-1,errno=11,begin_ns=25,query_begin_ns=26,end_ns=28),
         row(operation=1,requested=8,rc=3,accepted_bytes=3,delay_bytes=3,ptr_bytes=4,query_begin_ns=30,end_ns=32),
         row(operation=3,accepted_bytes=3,delay_bytes=0,ptr_bytes=1,query_begin_ns=40,end_ns=42),
         row(operation=3,accepted_bytes=3,delay_rc=-1,space_rc=-1,ptr_rc=-1)]
with tempfile.TemporaryDirectory(dir=ROOT/'build/platform-lab2-out') as tmp:
    p=Path(tmp)/'transport-0.csv'
    with p.open('w',newline='') as f:
        writer=csv.DictWriter(f,fields); writer.writeheader(); writer.writerows(samples)
    result=module.audio(p)
assert result['successful_write_bytes']==3 and result['short_writes']==1
assert result['readiness_followed_by_eagain']==1 and result['write_eagain']==1
assert result['negative_free_space']==1 and result['pointer_backward_samples']==1
assert result['successful_delay_bytes']=={'n':2,'mean':1.5,'p50':0,'p95':3,'p99':3,'maximum':3}
assert result['query_errors']=={'delay':1,'space':1,'ptr':1}
assert not result['physical_xruns_measured'] and not result['pointer_clock_qualified']
assert not result['zero_delay_proves_all_accepted_played']

# At 1000 stereo frames/sec, 2ms consumes eight bytes: more than the five
# queued after the first write. Two bytes remain outside pointer+delay.
samples=[row(operation=1,requested=8,rc=8,begin_ns=1000000,query_begin_ns=1100000,end_ns=1100010,
             accepted_bytes=8,ptr_bytes=1,delay_bytes=5),
         row(operation=1,requested=4,rc=4,begin_ns=3100000,query_begin_ns=3200000,end_ns=3200010,
             accepted_bytes=12,ptr_bytes=3,delay_bytes=7),
         row(operation=3,accepted_bytes=12,ptr_bytes=10,delay_bytes=0)]
with tempfile.TemporaryDirectory(dir=ROOT/'build/platform-lab2-out') as tmp:
    p=Path(tmp)/'transport-0.csv'
    with p.open('w',newline='') as f:
        writer=csv.DictWriter(f,fields); writer.writeheader(); writer.writerows(samples)
    result=module.audio(p,1000)
assert result['accepted_write_gap_ns']['mean']==2000000
assert result['accepted_minus_pointer_minus_delay_bytes']['mean']==2
assert result['zero_delay_drain_accepted_minus_pointer_bytes']['mean']==2
assert result['nominal_rate_gap_exceedances']==[{'previous_query_ns':1100000,'next_write_ns':3100000,
                                               'gap_ns':2000000,'previous_delay_bytes':5}]

# Two independently constructed open/config/wait/status/close lifecycles:
# 72ns wall, 20ns wait and seven 2ns nonwait calls each. One wait fails.
drivers=[]
commands=[0,0x5003,0x40e45000,0x80045001,0x80045004,0x80045005,0x5003,0]
starts=[0,10,20,30,40,61,64,70]
for job in range(2):
    for i,(command,start) in enumerate(zip(commands,starts)):
        drivers.append({'kind':1,'fd':12,'operation':0 if i==0 else 2 if i==7 else 1,
                        'command':command,'rc':-1 if job==1 and i==4 else 0,'phase':20,
                        'input_wh':256<<16|224,'begin_ns':job*100+start,
                        'end_ns':job*100+start+(20 if i==4 else 2)})
jobs=module.scaler_jobs(drivers)
assert jobs['unclosed_jobs']==0 and len(jobs['groups'])==1
group=jobs['groups'][0]
assert (group['jobs'],group['errors'],group['input_width'],group['input_height'])==(2,1,256,224)
assert group['open_through_close_ns']['mean']==72
assert group['wait_command_ns']['mean']==20 and group['nonwait_syscall_ns']['mean']==14
print('PASS: hand-calculated percentiles, readiness/EAGAIN, odd shorts, drain residue, nominal lead gaps, cursor reset and FD-reused scaler lifecycles')
