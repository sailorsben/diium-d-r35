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
print('PASS: hand-calculated percentiles, readiness/EAGAIN pair, odd shorts, drain zero, negative space and cursor reset')
