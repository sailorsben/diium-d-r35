"""Reporter regressions: frozen proof reconstruction and invalid-tail censoring."""
from pathlib import Path
from hashlib import sha256
import csv,importlib.util,json,tempfile
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('reporter',ROOT/'build/report-presentation-ffvi.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def main():
 with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='presentation-report-check-') as name:
  base=Path(name);published=base/'published.json';proof={'passed':True,'installer_sha256':'original'}
  published.write_text(json.dumps({'installation_transaction':proof}));text=json.dumps(proof,indent=2)+'\n'
  for raw in (text.encode(),text.replace('\n','\r\n').encode()):m.original_installation_proof(sha256(raw).hexdigest(),published)
  try:m.original_installation_proof('0'*64,published)
  except AssertionError:pass
  else:raise AssertionError('Wrong original-proof hash accepted')
  expected=sha256(text.encode()).hexdigest();published.write_text(json.dumps({'installation_transaction':{'passed':True,'installer_sha256':'newer'}}))
  try:m.original_installation_proof(expected,published)
  except AssertionError:pass
  else:raise AssertionError('Changed proof accepted')
  def kv(p,values):p.write_text(''.join(f'{k}={v}\n' for k,v in values.items()))
  kv(base/'supervisor.txt',{'forced':0,'reaped':1});kv(base/'suite-result.txt',{'board_closed':1})
  d=base/'run-000';d.mkdir();run={'run':0,'fixture':0,'policy':1,'repeat':0,'load_ms':0}
  kv(d/'begin.txt',run);kv(d/'result.txt',{'runner_rc':0,'audio_worker_joined':1,'display_idle':1})
  kv(d/'last-session.txt',{'mock_backend':1,'runs':3,'rendered_frames':3,'video_submitted':2,'presentation_skipped':1,
                         'display_scaled':2,'display_flipped':2,'video_dupes':0,'held':0,'error':'','pcm_boundary_frames':1000,'pcm_buffer_frames':100})
  kv(d/'headroom.txt',{'final_PCM_software_accounting_exact':1,'final_remaining':0,'final_cleared':0,'final_audio_error':0})
  kv(d/'animation.csv',{'#matching_property_samples':1})
  rows=[]
  for i in range(3):rows.append(dict(frame=i,audio_worker_cpu_ns=i,video_worker_cpu_ns=i,appl=10+(i==1),xfer=10,hw=0,
   pointer_valid=int(i!=1),pace_wait_ns=0,step_ns=100,main_step_cpu_ns=10,load_events=0,rendered=i+1,skipped=int(i>0)))
  with (d/'frames.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
  lines=['entries_total=3','retained_from=0']
  for i,(appl,q) in enumerate(((10,10),(11,11),(99,99))):lines.append(f'seq={i} ns={i+1} op=SYNC_OK arg=7 result=0 state=3 queued={q} appl={appl} hw=0 epoch=1 xfer={10 if i<2 else 99}')
  (d/'pcm-full.txt').write_text('\n'.join(lines)+'\n')
  result=m.analyze(base,{'runs':[run]},True);r=result['epochs'][0]
  assert r['status']=='NOT_PHYSICAL' and r['valid_CPU_prefix_calls']==1 and r['valid_PCM_prefix_observations']==1 and r['minimum_valid_reserve_frames']==10
  try:m.analyze(base,{'runs':[run]})
  except AssertionError as e:assert 'Mock telemetry' in str(e)
  else:raise AssertionError('Mock accepted as physical')
 print('PASS original proof LF/CRLF, mismatched/changed proof rejection, invalid CPU/PCM tail censoring and mock rejection')
if __name__=='__main__':main()
