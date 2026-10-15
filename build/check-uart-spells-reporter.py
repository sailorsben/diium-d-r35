"""Reject mock/unsafe UART evidence and incomplete fixed-window speed claims."""
from pathlib import Path
import importlib.util,json,runpy,tempfile
ROOT=Path(__file__).resolve().parent.parent
def main():
 path=ROOT/'build/evaluate-uart-spells-return.py';spec=importlib.util.spec_from_file_location('uart_eval',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 checks=[];reporter=runpy.run_path(str(ROOT/'build/draw-order-test-private-v1/report.py'))['analyze']
 try:reporter(ROOT/'build/uart-spells-private',False)
 except AssertionError as e:assert 'Mock telemetry' in str(e)
 else:raise AssertionError('Mock physical acceptance')
 checks.append('unchanged physical reporter rejects retarget mock telemetry')
 original='version=4 result=0 irq=19 attached=1 calls=3 added=2 writes=2 full=0 empty_stop=0 stopped=0 urgent=0 fallback=1 fault=0 bypass=0 ctrl=0000b070 flags=05 fifo=8 head=0 tail=0 rx=0 tx=2 frame=0 parity=0 overrun=0 brk=0 cap=0\n'
 out=ROOT/'build/uart-spells-private'
 with tempfile.TemporaryDirectory(dir=out) as tmp:
  p=Path(tmp)/'status';p.write_text(original,encoding='utf-8',newline='\n');assert m.status(p)['calls']==3
  for old,new in [('attached=1','attached=0'),('cap=0','cap=200000'),('fault=0','fault=1'),('calls=3','calls=4'),('writes=2','writes=1')]:
   p.write_text(original.replace(old,new),encoding='utf-8',newline='\n')
   try:m.status(p)
   except AssertionError:pass
   else:raise AssertionError('Unsafe status accepted: '+new)
   checks.append('reject '+new)
 metrics={n:10 for n in ['thread_CPU_ns','core_CPU_ns','wall_service_ns','step_ns','pace_ns']}
 r=m.paired({0:metrics,1:metrics},{0:metrics},range(2));assert not r['complete'] and r['common_calls']==1 and all(v is None for v in r['saving_ms'].values())
 checks.append('incomplete fixed intervals have no invented saving')
 result={'passed':True,'checks':checks,'sources':{'build/evaluate-uart-spells-return.py':m.digest(path),'build/check-uart-spells-reporter.py':m.digest(Path(__file__))},'card_access':False}
 (out/'return-reporter-qualification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
