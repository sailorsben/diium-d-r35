"""Independent synthetic analyzer cases. Never A7 or QEMU performance claims."""
from pathlib import Path
import json,runpy
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/combined-test-private-v1'
def main():
 archive=OUT/'synthetic-model';base=archive/'retro/snes-combined1';base.mkdir(parents=True,exist_ok=False);(archive/'archive.json').write_text('{}\n')
 runs=[{'run':rep*3+i,'fixture':0,'variant':v,'repeat':rep} for rep in range(2) for i,v in enumerate(('baseline','prior','combined'))]
 plan={'version':'1.19-combined1','measurement_only':True,'frameskip':False,'period_ns':16688154.5,'target_ns':13350523.6,'runs':runs,'cases':[{'seq':0,'name':'SYNTHETIC'}],'cores':{n:{'crc32':'synthetic'} for n in ('baseline','prior','combined')}};(base/'plan.json').write_text(json.dumps(plan))
 for run in runs:
  d=base/f"run-{run['run']:03d}";d.mkdir();cpu={'baseline':18000000,'prior':17000000,'combined':15000000}[run['variant']]
  text='#suite=1.19-combined1\n#mock=0\nframe,cpu_ns,wall_ns,step_ns,pace_wait_ns,audio_worker_cpu_ns,video_worker_cpu_ns,pointer_valid,native_generated,freq_before_khz,freq_after_khz\n'
  text+=''.join(f'{i},{cpu},{cpu},{cpu+8000000},8000000,0,0,1,{i*534},-1,-1\n' for i in range(1200));(d/'frames.csv').write_text(text)
  (d/'last-session.txt').write_text('core_crc32=synthetic\nbuild_version=1.19-combined1\nruns=1200\nvideo_submitted=1200\ndisplay_flipped=1200\nheld=0\nerror=\n')
  (d/'result.txt').write_text('runner_rc=0\naudio_worker_joined=1\ndisplay_idle=1\n')
  (d/'animation.csv').write_text('#matching_property_samples=1\n')
  (d/'headroom.txt').write_text('physical=1\nfinal_worker_counters_valid=1\nfinal_PCM_software_accounting_exact=1\nfinal_remaining=0\nfinal_cleared=0\nfinal_audio_error=0\ninvalid_accounting=0\npost_last_sample_audio_CPU_ns=200000\npost_last_sample_video_CPU_ns=0\n')
 analyze=runpy.run_path(str(ROOT/'build/report-combined-return.py'))['analyze'];r=analyze(archive)
 assert next(x for x in r['matched_comparisons'] if x['before']=='prior' and x['after']=='combined')['cpu_ns_saving_us']['mean']==2000
 assert r['runs'][2]['service_proxy_us']['max']==15200 and r['runs'][2]['status']=='NOT_MET'
 for name,file,old,new in [('flip','last-session.txt','display_flipped=1200','display_flipped=1199'),('drain','headroom.txt','final_remaining=0','final_remaining=1'),('discard','headroom.txt','final_cleared=0','final_cleared=1'),('observer-physical','headroom.txt','physical=1','physical=0')]:
  p=base/'run-002'/file;s=p.read_text();p.write_text(s.replace(old,new));bad=analyze(archive);assert bad['runs'][2]['status']=='INVALID_OR_INCOMPLETE',name;p.write_text(s)
 p=base/'run-002/frames.csv';s=p.read_text();p.write_text('\n'.join(s.splitlines()[:252])+'\n');r=analyze(archive)
 assert not next(x for x in r['matched_comparisons'] if x['before']=='prior' and x['after']=='combined')['aligned_interval_complete']
 print('PASS synthetic-only model: incremental2000us, included final200us worker tail, target miss, missing flip, undrained/discarded PCM, nonphysical flag and incomplete tail rejection; no physical claim')
if __name__=='__main__':main()
