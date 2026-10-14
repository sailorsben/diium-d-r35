"""Evaluate strict archived PPU test evidence; never write the returned card."""
from pathlib import Path
import csv,json,runpy,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
def main(archive,live=False):
 archive=archive.resolve();assert archive.is_relative_to(ROOT/'device-evidence')
 a=json.loads((archive/'archive.json').read_text());assert a['fat_clean'] and a['card_writes']==0
 reporter=runpy.run_path(str(ROOT/'build/ppu-test-private-v1/report.py'))
 base=archive/'retro/snes-ppu-test1'
 report=reporter['analyze'](base,False)
 (base/'spell-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
 code=(ROOT/'build/evaluate-demand-spells-return.py').read_text()
 code=code.replace('demand-spells','ppu-test').replace("suite['runs']=='40'","suite['runs']=='56'")
 code=code.replace("'interim_user_observations':'Grand Train, Ultima and Pearl seemed to work; Meteor did not seem complete. Observations occurred during the suite, not an independent full40-epoch visual review.'","'interim_user_observations':'No independent visual or speaker report for this PPU test.'")
 ns={'__file__':str(Path(__file__).resolve()),'__name__':'ppu_return'}
 exec(compile(code,'ppu_return','exec'),ns);ns['main'](archive,live)
 p=archive/'ppu-test-return-evaluation.json';result=json.loads(p.read_text())
 result['optimization_prices_are_family_aggregate']=True
 result['prices_not_individual_clip_depth_math']=True
 result['limits']=[s for s in result['limits'] if not s.startswith('Only Meteor/Quasar have matched controls')]
 result['limits'].append('Isolated family controls exist only for Meteor/Quasar; shapes groups opacity, clipped and sparse plain/math. Prices are retained-prefix family costs, not universal unit prices.')
 # Compare every contiguous common warm 16-call window, not only the
 # control's most expensive window. Keep invalid-pointer samples excluded.
 records={}
 for epoch in result['epochs']:
  framepath=base/f"run-{epoch['run']:03d}/frames.csv"
  rows=list(csv.DictReader(l for l in framepath.read_text().splitlines() if not l.startswith('#')))
  pa=pv=0;valid={}
  for r in rows:
   ca,cv=int(r['audio_worker_cpu_ns']),int(r['video_worker_cpu_ns'])
   if r['pointer_valid']!='1' or ca<pa or cv<pv:break
   valid[int(r['frame'])]=int(r['main_step_cpu_ns'])+ca-pa+cv-pv;pa,pv=ca,cv
  records[(epoch['fixture'],epoch['repeat'],epoch['variant'])]=valid
 allwindows=[]
 for fixture in (1,8):
  for repeat in range(4):
   ref=records[(fixture,repeat,'reference')]
   for variant in (['demand'] if repeat<2 else ['obj','shapes','bulk']):
    new=records[(fixture,repeat,variant)];common=sorted(set(ref)&set(new));warm=[i for i in common if i>=120]
    windows=[warm[i:i+16] for i in range(max(0,len(warm)-15)) if warm[i+15]-warm[i]==15]
    deltas=[(statistics.mean(ref[j]-new[j] for j in w)/1e6,w) for w in windows]
    worst=min(deltas) if deltas else None;best=max(deltas) if deltas else None
    fixed={}
    for name,span in [('earlier_Meteor',range(384,416)),('late_Meteor',range(496,536))] if fixture==1 else [('Quasar',range(496,542))]:
     fixed[name]={'all_frames_valid_in_both':all(j in ref and j in new for j in span),
      'saving_ms':statistics.mean(ref[j]-new[j] for j in span)/1e6 if all(j in ref and j in new for j in span) else None}
    allwindows.append({'fixture':fixture,'repeat':repeat,'variant':variant,'common_valid_calls':len(common),
     'warm_common_mean_saving_ms':statistics.mean(ref[j]-new[j] for j in warm)/1e6 if warm else None,
     'worst_common16_saving_ms':worst[0] if worst else None,'worst_common16_frames':worst[1] if worst else [],
     'best_common16_saving_ms':best[0] if best else None,'fixed_intervals':fixed})
 result['all_common_valid_window_comparisons']=allwindows
 result['clean_all_epochs']=sum(r['status']=='CLEAN_BOUNDED_WINDOW' for r in result['epochs'])
 result['nominally_complete_but_invalid']=[r['run'] for r in result['epochs'] if r['completed_calls']==1200 and r['status']!='CLEAN_BOUNDED_WINDOW']
 p.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'comparisons':result['matched_comparisons'],'cases':result['cases']},indent=2))
if __name__=='__main__':main(Path(sys.argv[1]),'--verify-live' in sys.argv)
