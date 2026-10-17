"""Sparse-archive-bound five-game return analysis. Never reads/writes the card."""
from pathlib import Path
from hashlib import sha256
import argparse,csv,json,re
from attempt_archive import verify_saved
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l) if p.exists() else {}
def rows(p):return list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')))
def analyze(base,plan,allow_mock=False):
 supervisor=kv(base/'supervisor.txt');summary=kv(base/'suite-result.txt');safe=supervisor.get('reaped')=='1' and supervisor.get('forced')=='0' and summary.get('board_closed')=='1';reports=[]
 for r in plan['runs']:
  d=base/f"run-{r['run']:03d}";s=kv(d/'last-session.txt');begin=kv(d/'begin.txt');end=kv(d/'result.txt');head=kv(d/'headroom.txt');trace=kv(d/'pcm-full.txt')
  if not s or not (d/'frames.csv').exists():
   reports.append({**r,'status':'FAILED_BEFORE_MEASUREMENT' if begin and end.get('runner_rc') not in (None,'0') else 'INCOMPLETE' if begin else 'NOT_STARTED',
    'runner_rc':end.get('runner_rc'),'error':end.get('error'),'rendered':int(s.get('rendered_frames','0')),
    'aborted_or_stopped':summary.get('stopped')=='1' if begin else False,
    'audio_opened':int(s.get('pcm_period_frames','0'))>0,
    'limits':['No measured frame history; retained PCM/input buffers may belong to the preceding epoch and are not evidence for this run.'] if begin else []});continue
  mock=s.get('mock_backend')=='1';assert allow_mock or not mock,'Mock telemetry is not physical proof'
  f=rows(d/'frames.csv');input_rows=rows(d/'input.csv');correct=all(begin.get(k)==str(r[k]) for k in ('fixture','policy','repeat','load_ms'))
  complete=len(f)==1200 and [int(x['frame']) for x in f]==list(range(1200)) and len(input_rows)==1200 and s.get('runs')==s.get('rendered_frames')=='1200' and end.get('runner_rc')=='0' and not s.get('error')
  video=int(s['rendered_frames'])==int(s['video_submitted'])+int(s['presentation_skipped']) and s['display_scaled']==s['display_flipped']==s['video_submitted']
  video=video and s['video_dupes']==s['held']=='0' and (r['policy']!=0 or s['presentation_skipped']=='0')
  pcm=head.get('final_PCM_software_accounting_exact')=='1' and head.get('final_remaining')==head.get('final_cleared')==head.get('final_audio_error')=='0'
  pattern=r'seq=(\d+) ns=(\d+) op=(\S+) arg=(\d+) result=(-?\d+) state=(\d+) queued=(\d+) appl=(\d+) hw=(\d+) epoch=(\d+) xfer=(\d+)';parsed=list(re.finditer(pattern,(d/'pcm-full.txt').read_text()))
  all_trace=trace.get('retained_from')=='0' and len(parsed)==int(trace.get('entries_total','-1'));valid=True;reserves=[];invalid=[];boundary=int(s['pcm_boundary_frames']);buffer=int(s['pcm_buffer_frames'])
  for m in parsed:
   seq,ns,op,arg,result,state,q,appl,hw,epoch,xfer=m.groups()
   if int(result)<0 and int(result) not in (-11,-4):valid=False
   if op=='SYNC_OK' and state=='3':
    good=boundary>0 and int(appl)%boundary==int(xfer)%boundary and (int(appl)-int(hw))%boundary==int(q) and int(q)<=buffer
    if not good:valid=False;invalid.append(int(seq))
    if valid:reserves.append(int(q))
  prefix=0;prefix_valid=True;a0=v0=0
  for row in f:
   a,v=int(row['audio_worker_cpu_ns']),int(row['video_worker_cpu_ns']);prefix_valid=prefix_valid and row['pointer_valid']=='1' and boundary>0 and int(row['appl'])%boundary==int(row['xfer'])%boundary and (int(row['appl'])-int(row['hw']))%boundary<=buffer and a>=a0 and v>=v0 and int(row['pace_wait_ns'])<=int(row['step_ns'])
   if prefix_valid:prefix+=1
   a0,v0=a,v
  warm=r['fixture']!=3 or kv(d/'warmup.txt').get('cold_boot_calls')=='8656'
  joined=end.get('audio_worker_joined')==end.get('display_idle')=='1';accepted=not mock and safe and correct and complete and video and pcm and valid and all_trace and bool(reserves) and prefix==1200 and warm and joined
  reports.append({**r,'status':'NOT_PHYSICAL' if mock else 'CLEAN_BOUNDED_WINDOW' if accepted else 'INVALID_OR_INCOMPLETE','complete':complete,'rendered':int(s['rendered_frames']),'submitted':int(s['video_submitted']),'skipped':int(s['presentation_skipped']),'PCM_final_exact':pcm,'trace_complete':all_trace,'minimum_valid_sampled_reserve_frames':min(reserves,default=None),'valid_PCM_prefix_observations':len(reserves),'invalid_running_sequences':invalid,'valid_CPU_prefix_calls':prefix,'cold_boot_complete':warm,'core_error':s.get('error'),'headroom':head.get('sampled_warm_20_percent_headroom'),'period_ns':head.get('period_ns'),'end_state_sha256':digest(d/'end-state.bin') if (d/'end-state.bin').exists() else None})
 return {'version':'fivegame1-return','safe_teardown':safe,'epochs':reports,'production_gate':False,'limits':['Bounded physical windows do not establish sustained playability, optical/DAC continuity or GSU save/restore.','Sampled reserve is not continuous reserve. Censor native/CPU history after invalid pointers or fatal native errors.','Policy0 and1 share the corrected core; this isolates presentation scheduling, not old-core compatibility failures.']}
def main():
 p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--installation',type=Path,required=True);a=p.parse_args();archive=a.archive.resolve();meta=json.loads((archive/'archive.json').read_text());assert meta['fat_clean'] and meta['card_writes']==0;verify_saved(archive,meta)
 installed=json.loads(a.installation.read_text());assert installed['version']=='fivegame1';hashes={e['path']:e['sha256'] for e in meta['all_retro_files']};payload=ROOT/'build/fivegame-physical-private-v1'
 assert not any(p.endswith('/armed') for p in hashes)
 assert hashes['retro/snes-fivegame1/last-launch']==hashes['retro/snes-mvp/last-launch-lab']==installed['marker_sha256']
 for n,h in installed['payload_hashes'].items():assert hashes['retro/snes-fivegame1/'+n]==h,n
 assert digest(payload/'plan.json')==installed['payload_hashes']['plan.json']
 plan=json.loads((payload/'plan.json').read_text());runs=list((archive/'retro/snes-fivegame1/results').glob('run-*'));assert len(runs)==1,'Select the exact return if repeated';base=runs[0];result=analyze(base,plan)
 out=base/'fivegame-analysis.json';out.unlink(missing_ok=True);out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'epochs':len(result['epochs']),'clean':sum(r['status']=='CLEAN_BOUNDED_WINDOW' for r in result['epochs']),'report':str(out)}))
if __name__=='__main__':main()
