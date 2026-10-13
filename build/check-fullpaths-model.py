"""Synthetic parser/model fixtures only. Never physical or QEMU performance data."""
from pathlib import Path
import contextlib,io,json,runpy
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fullpaths-private-v2'
def check():
 archive=OUT/'synthetic-model-fixture';assert not archive.exists();base=archive/'retro/snes-fullpaths1';base.mkdir(parents=True)
 (archive/'archive.json').write_text('{}\n')
 names=('baseline','fixed','subscreen','dsp','combined');costs=(18000000,16000000,17000000,17500000,15000000)
 runs=[{'run':repeat*5+i,'fixture':0,'variant':name,'repeat':repeat} for repeat in range(2) for i,name in enumerate(names)]
 plan={'version':'1.19-fullpaths1','measurement_only':True,'frameskip':False,'period_ns':16688154.5,'target_ns':13350523.6,'cases':[{'seq':0,'name':'SYNTHETIC_HOLY'}],'runs':runs,'cores':{n:{'crc32':'synthetic'} for n in names}}
 (base/'plan.json').write_text(json.dumps(plan))
 for r in runs:
  d=base/f"run-{r['run']:03d}";d.mkdir();cost=costs[names.index(r['variant'])]
  text='#mock=0\n#failed=0\nframe,cpu_ns,wall_ns,step_ns,pace_wait_ns,audio_worker_cpu_ns,video_worker_cpu_ns,pointer_valid,native_generated,freq_before_khz,freq_after_khz\n'
  text+=''.join(f'{i},{cost},{cost},{cost},0,0,0,1,{i*534},-1,-1\n' for i in range(1200))
  (d/'frames.csv').write_text(text)
  (d/'last-session.txt').write_text('core_crc32=synthetic\nbuild_version=1.19-fullpaths1\nruns=1200\nvideo_submitted=1200\ndisplay_flipped=1200\nheld=0\nerror=\n')
 # A completed callback count is not sufficient without actual flips.
 p=base/'run-009/last-session.txt';p.write_text(p.read_text().replace('display_flipped=1200','display_flipped=1199'))
 analyze=runpy.run_path(str(ROOT/'build/report-fullpaths-return.py'))['analyze']
 with contextlib.redirect_stdout(io.StringIO()):result=analyze(archive)
 c=next(c for c in result['matched_comparisons'] if c.get('variant')=='fixed' and c['repeat']==0)
 assert c['aligned_interval_complete'] and c['cpu_ns_saving_us']['mean']==2000
 assert next(c for c in result['matched_comparisons'] if 'CPU_combination_extra_vs_sum_us' in c)['CPU_combination_extra_vs_sum_us']==-500
 assert result['runs'][0]['all_recorded_call_20_percent_headroom']=='NOT_MET'
 assert result['runs'][9]['all_recorded_call_20_percent_headroom']=='INVALID_OR_INCOMPLETE'
 assert not result['production_gate_passed']
 # Missing tail frames must stay partial, never priced as zero-cost success.
 p=base/'run-001/frames.csv';lines=p.read_text().splitlines();p.write_text('\n'.join(lines[:253])+'\n')
 with contextlib.redirect_stdout(io.StringIO()):partial=analyze(archive)
 c=next(c for c in partial['matched_comparisons'] if c.get('variant')=='fixed' and c['repeat']==0)
 assert not c['aligned_interval_complete'] and not c['common_frames']
 print('PASS synthetic model only: matched 2000us difference, negative combination interaction, target miss, missing flip and incomplete heavy interval rejection; no physical performance claim')
if __name__=='__main__':check()
