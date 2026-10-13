"""Same emulated frames, kernel CPU/wall clocks; no timing calibration."""
from pathlib import Path
import importlib.util,json,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('analysis',ROOT/'build/analyze-ability2-return.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def compare(archive,suite='ability2'):
    assert suite in ('ability2','ability3')
    base=archive/f'retro/snes-{suite}';plan=json.loads((base/'plan.json').read_text())
    prior_suite='ability1' if suite=='ability2' else 'ability2'
    prior=ROOT/'device-evidence'/plan['returned_archive']/f'retro/snes-{prior_suite}'
    result=[]
    for c in plan['cases']:
        old_seq=c['original_case'] if prior_suite=='ability1' else c['seq']
        old=a.csv_rows(prior/f"run-{old_seq:03d}/frames.csv")
        new=a.csv_rows(base/f"run-{c['seq']:03d}/frames.csv")
        session=a.kv(base/f"run-{c['seq']:03d}/last-session.txt")
        # Avoid terminal calls, preserve baseline tail even if new case survives.
        tail=[int(x['frame']) for x in old[-17:-1]]
        n={int(x['frame']):x for x in new[:-1]};o={int(x['frame']):x for x in old[:-1]}
        common=[i for i in tail if i in n and i in o]
        matched_overlap=sorted(n.keys()&o.keys())[-16:]
        rec={'case':c['seq'],'original_case':c['original_case'],'name':c['name'],
             'old_calls':len(old),'new_calls':len(new),'passed':not session['error'],
             'terminal':session.get('pcm_error_detail'),'baseline_tail_frames':common,
             'baseline_suite':prior_suite,'candidate_suite':suite,
             'complete_baseline_tail_available':len(common)==16,
             'matched_overlap_frames':matched_overlap,
             'overlap_cpu_saving_us':a.dist([(int(o[i]['cpu_ns'])-int(n[i]['cpu_ns']))/1000 for i in matched_overlap])}
        for label,frames in [('baseline_tail',common),('new_tail',[int(x['frame']) for x in new[-17:-1]])]:
            if not frames:continue
            data=o if label=='baseline_tail' else {int(x['frame']):x for x in new}
            rec[label]={k:statistics.mean(int(data[i][k]) for i in frames)/1000 for k in ('cpu_ns','wall_ns','step_ns','admission_ns')}
        if common:
            rec['same_frame_saving_us']={k:a.dist([(int(o[i][k])-int(n[i][k]))/1000 for i in common]) for k in ('cpu_ns','wall_ns')}
            rec['candidate_on_baseline_tail_us']={k:statistics.mean(int(n[i][k]) for i in common)/1000 for k in ('cpu_ns','wall_ns','step_ns')}
        result.append(rec)
    (archive/'ability-analysis/aligned-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    for r in result:
        savings=r.get('same_frame_saving_us',{});tail=r['new_tail']
        print(r['case'],r['name'],'PASS' if r['passed'] else 'FAIL',r['old_calls'],r['new_calls'],
              'aligned CPU saving',round(savings['cpu_ns']['mean']) if savings else 'unavailable',
              'overlap saving',round(r['overlap_cpu_saving_us']['mean']),
              'new tail CPU/wall/step',*[round(tail[k]) for k in ('cpu_ns','wall_ns','step_ns')])
if __name__=='__main__':compare(Path(sys.argv[1]).resolve(),sys.argv[2] if len(sys.argv)>2 else 'ability2')
