"""Analyze isolated pressure cells, refusing mock or unarchived physical claims."""
from pathlib import Path
from hashlib import sha256
import argparse,csv,json,re,statistics
def digest(p):return sha256(p.read_bytes()).hexdigest()
def kv(p):return dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def analyze(base,allow_mock=False,installation=None):
 summary=kv(base/'summary.txt');assert summary['version']=='render-pressure2'
 simulated=summary['mock']=='1';assert allow_mock or not simulated,'Mock telemetry is not device performance'
 if not simulated:
  assert installation is not None,'Physical reporting requires an installation receipt and strict archive'
  i=json.loads(installation.read_text());assert i['version']=='render-pressure2'
  assert digest(base.parent.parent/'render-pressure')==i['payload_hashes']['render-pressure']
  archive=next((p for p in base.parents if (p/'archive.json').is_file()),None);assert archive is not None
  a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
  for e in a['all_retro_files']:assert digest(archive/e['path'])==e['sha256'],e['path']
 phases=[]
 for d in sorted(base.glob('phase-*')):
  p=kv(d/'begin.txt');r=kv(d/'result.txt');assert p['mock']==r['mock']==summary['mock']
  rows=list(csv.DictReader(l for l in (d/'samples.csv').read_text().splitlines() if not l.startswith('#')))
  done=int(r['completed']);requested=int(p['requested_frames']);detail=p['detailed']=='1'
  assert len(rows)==(done if detail else 0) and [int(x['frame']) for x in rows]==list(range(len(rows)))
  audio_ok=True;trace_complete=None;running=[]
  if int(r['pcm_trace_required']):
   t=kv(d/'pcm-full.txt');trace_complete=t['retained_from']=='0';boundary=int(r['pcm_boundary']);buffer=int(r['pcm_buffer'])
   records=list(re.finditer(r'seq=(\d+) ns=(\d+) op=(\S+) arg=(\d+) result=(-?\d+) state=(\d+) queued=(\d+) appl=(\d+) hw=(\d+) epoch=(\d+) xfer=(\d+)',(d/'pcm-full.txt').read_text()))
   assert len(records)==int(t['entries_total'])-int(t['retained_from'])
   for m in records:
    seq,ns,op,arg,result,state,q,appl,hw,epoch,xfer=m.groups()
    if op!='SYNC_OK' or state!='3':continue
    valid=boundary>0 and int(appl)%boundary==int(xfer)%boundary and (int(appl)-int(hw))%boundary==int(q) and int(q)<=buffer
    if not valid:audio_ok=False;break
    if int(r['begin_ns'])<=int(ns)<=int(r['end_ns']):running.append(int(q))
   audio_ok=audio_ok and trace_complete and r['audio_error']=='0' and int(r['audio_enqueued'])==int(r['audio_accepted'])+int(r['audio_remaining'])+int(r['audio_cleared']) and int(r['audio_enqueued'])==int(r['primed_frames'])+int(r['generated_frames']) and bool(running)
  video_ok=True
  if int(p['kind']) in (4,5) and not simulated:
   video_ok=int(r['submitted'])==int(r['scaled'])==int(r['flipped'])==done
   expected=done*int(p['width'])*int(p['height'])*2
   video_ok=video_ok and (int(r['direct_submitted'])==done and int(r['copied_bytes'])==0 if p['direct']=='1' else int(r['direct_submitted'])==0 and int(r['copied_bytes'])==expected)
  load_events=int(r['load_events']);expected_events=(done//int(p['load_every']) if int(p['load_ms']) else 0)
  if r['failed']=='0':assert load_events==expected_events
  accepted=not simulated and r['failed']=='0' and done==requested and audio_ok and video_ok
  warm=[x for x in rows if 8<=int(x['frame'])<requested-1]
  metrics=None
  if accepted:
   metrics={'completed_per_second':done*1e9/int(r['wall_ns']),
    'phase_wall_ms':int(r['wall_ns'])/1e6,'main_CPU_ms':int(r['main_cpu_ns'])/1e6,'display_worker_CPU_ms':int(r['worker_cpu_ns'])/1e6,'audio_worker_CPU_ms':int(r['audio_cpu_ns'])/1e6,
    'warm':{n:{'median_ms':statistics.median(int(x[n]) for x in warm)/1e6,'max_ms':max(int(x[n]) for x in warm)/1e6} for n in ['cpu_ns','render_ns','reserve_ns','admit_ns','submit_ns','join_ns'] if warm}}
  phases.append({'phase':d.name,'parameters':p,'result':r,'load_events_executed':load_events,'first_burst_executed':bool(load_events) if int(p['load_every'])>1 else None,'physical_cell_accepted':accepted,'PCM_history_complete':trace_complete,'PCM_pointer_prefix_valid':audio_ok,'minimum_valid_running_reserve':min(running) if running else None,'video_accounting_exact':video_ok,'metrics':metrics})
 assert len(phases)==int(summary['phases'])
 return {'version':'render-pressure2','mock':simulated,'physical':not simulated,'summary':summary,'phases':phases,
 'physical_device_ceiling_proven':False,'limits':['Synthetic command streams exercise row kernels, not the whole SNES PPU/CPU/APU.','Last-frame validation copy and first8 frames excluded from per-frame distributions; total phase time still includes the copy.','Scale and flip wall durations overlap producer work; never sum them as a serial CPU tax.','Aggregate controls remove additional frame clocks only; frozen board/PCM instrumentation remains.','An achieved throughput is not a proof of the theoretical device optimum.']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('--allow-mock',action='store_true');p.add_argument('--installation',type=Path);a=p.parse_args();r=analyze(a.base,a.allow_mock,a.installation);(a.base/'pressure-analysis.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'physical':r['physical'],'phases':len(r['phases']),'accepted':sum(x['physical_cell_accepted'] for x in r['phases']),'ceiling_proven':False}))
