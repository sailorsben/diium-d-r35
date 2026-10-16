"""Derive public metrics from immutable sparse FFVI return; no card access."""
from pathlib import Path
import argparse,csv,importlib.util,json,re,statistics
from hashlib import sha256
ROOT=Path(__file__).resolve().parent.parent
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def rows(p):return list(csv.DictReader(x for x in p.read_text().splitlines() if not x.startswith('#')))
def main():
 p=argparse.ArgumentParser();p.add_argument('archive',type=Path);a=p.parse_args();archive=a.archive.resolve()
 spec=importlib.util.spec_from_file_location('reporter',ROOT/'build/report-presentation-ffvi.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 meta=read(archive/'archive.json');m.verify_saved(archive,meta);assert meta['card_writes']==0 and meta['fat_clean']
 pub=ROOT/'evidence/2026-10-16/presentation-ffvi';installed=read(pub/'installation.json');qualification=read(pub/'qualification.json')
 before=ROOT/'device-evidence'/installed['archive'];assert digest(before/'archive.json')==qualification['archive_manifest_sha256']
 old={x['path']:x['sha256'] for x in read(before/'archive.json')['all_retro_files']};now={x['path']:x['sha256'] for x in meta['all_retro_files']}
 changes={k:{'before':v,'after':now.get(k)} for k,v in old.items() if now.get(k)!=v}
 assert set(changes)=={'retro/snes-mvp/launch.sh','retro/snes-mvp/last-launch-lab','retro/swapfile'}
 assert now['retro/snes-mvp/launch.sh']==installed['dispatch_sha256'] and now['retro/snes-mvp/last-launch-lab']==installed['marker_sha256']
 outside=read(archive/'outside-retro.json');oldoutside=read(before/'outside-retro.json');assert outside['card_writes']==0
 assert {x['path']:x['sha256'] for x in outside['files']}=={x['path']:x['sha256'] for x in oldoutside['files']}
 for n,h in installed['payload_hashes'].items():assert now['retro/snes-presentation-ffvi1/'+n]==h,n
 m.original_installation_proof(installed['payload_hashes']['installation-qualification.json'],pub/'qualification.json')
 assert not any(k.endswith('/armed') or k.endswith('/Code.bkp') for k in now),'Unexpected armed marker'
 assert now['retro/snes-presentation-ffvi1/last-launch']==installed['marker_sha256']
 plan=read(ROOT/'build/presentation-ffvi-private-v1/plan.json');base=list((archive/'retro/snes-presentation-ffvi1/results').glob('run-*'));assert len(base)==1;base=base[0]
 report=m.analyze(base,plan);assert report['physical'] and report['safe_teardown'] and len(report['epochs'])==80
 matched=[];recovery=[]
 for pair in report['comparisons']:
  x,y=[rows(base/f"run-{pair[k]:03d}"/'frames.csv') for k in ('control_run','candidate_run')]
  ax,ay=[rows(base/f"run-{pair[k]:03d}"/'animation.csv') for k in ('control_run','candidate_run')]
  n=min(len(x),len(y),len(ax),len(ay))
  logical=all({k:v for k,v in ax[i].items() if k!='observer_ns'}=={k:v for k,v in ay[i].items() if k!='observer_ns'} for i in range(n))
  generated=all(x[i]['native_generated']==y[i]['native_generated'] for i in range(n))
  matched.append({**pair,'compared_calls':n,'logical_effect_input_equal':logical,'generated_PCM_count_equal':generated})
  assert logical and generated
 for run in report['epochs']:
  if run['load_ms']==0 or run['status']!='CLEAN_BOUNDED_WINDOW':continue
  d=base/f"run-{run['run']:03d}";f=rows(d/'frames.csv');points=[]
  for line in (d/'pcm-full.txt').read_text().splitlines():
   v=dict(re.findall(r'(\w+)=([^ ]+)',line))
   if v.get('op')=='SYNC_OK' and v.get('state')=='3':points.append((int(v['ns']),int(v['queued'])))
  bursts=[]
  for frame in (239,359,479,599,719,839,959):
   start=int(f[frame-1]['observed_ns']);end=int(f[min(frame+119,1199)]['observed_ns'])
   bracket=[v for v in points if start<=v[0]<=end];assert bracket
   low=min(bracket,key=lambda v:v[1]);restored=next((v for v in bracket if v[0]>low[0] and v[1]>=2823),None)
   bursts.append({'load_frame':frame,'minimum_observed_frames':low[1],'returned_to_2823_frames_within_bracket':restored is not None,'minimum_to_reprime_ms':(restored[0]-low[0])/1e6 if restored else None})
  recovery.append({'run':run['run'],'policy':run['policy'],'load_ms':run['load_ms'],'bursts':bursts})
 def uart(name):return dict(re.findall(r'(\w+)=([^\s]+)',(base/name).read_text()))
 u0,u1=uart('uart-before.txt'),uart('uart-after.txt');assert all(u1[k]=='0' for k in ('full','fault','bypass','cap')) and u1['attached']=='1'
 assert int(u1['calls'])==int(u1['added'])+int(u1['fallback']) and int(u1['added'])==int(u1['writes'])+int(u1['empty_stop'])
 hashes={str(p.relative_to(archive)).replace('\\','/'):digest(p) for p in base.rglob('*') if p.is_file() and p.name!='presentation-analysis.json'}
 result={'version':'presentation-ffvi1-return','archive':archive.name,'archive_manifest_sha256':digest(archive/'archive.json'),'outside_manifest_sha256':digest(archive/'outside-retro.json'),'installation_sha256':digest(pub/'installation.json'),
  'card_writes':0,'fat_clean':True,'rearmed':False,'new_sparse_content_bytes':meta['new_content_bytes']+outside['new_content_bytes'],
  'preservation':{'prior_files':len(old)+len(outside['files']),'unchanged_prior_files':len(old)+len(outside['files'])-len(changes),'expected_changes':changes,'outside_files_unchanged':len(outside['files']),'installed_payload_hashes_verified':len(installed['payload_hashes']),'all_other_prior_files_including_saves_UART_init_unchanged':True},
  'clean_windows':sum(r['status']=='CLEAN_BOUNDED_WINDOW' for r in report['epochs']),'intentional_presentation_skips':sum(r['skipped'] for r in report['epochs']),
  'epochs':report['epochs'],'matched_comparisons':matched,'recovery':recovery,'UART_before':u0,'UART_after':u1,'raw_input_sha256':hashes,
  'user_observation':'No obvious issues','production_gate':False,
  'limits':['Bounded automatic physical test, not sustained interactive gameplay or independent optical/DAC capture.','Recovery brackets use fresh frame-boundary PCM observation timestamps; no exact load onset timestamp. Reserve minima are sampled.','Reprime is first observation at least 2823 frames after bracket minimum; it does not establish uninterrupted reserve.','CPU comparisons include observers and recorded main/audio/video threads only. Wall wait reduction is not CPU saving.','Failed control tails are censored by the reporter; failed windows never pass.']}
 out=pub/'return.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'output':str(out),'clean':result['clean_windows'],'skips':result['intentional_presentation_skips'],'matched_pairs':len(matched),'recovered_bursts':sum(b['returned_to_2823_frames_within_bracket'] for r in recovery for b in r['bursts'])}))
if __name__=='__main__':main()
