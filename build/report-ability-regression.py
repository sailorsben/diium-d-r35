"""Reconcile labels/fixture metadata, and calculate bounded predictions before install."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ability-regression-private-v1'
RETURN=ROOT/'device-evidence/a7-pair-before-20261013T063819Z'
def report():
    qpath=OUT/'qualification.json';q=json.loads(qpath.read_text());plan=json.loads((OUT/'plan.json').read_text())
    assert q['passed'] and not (OUT/'verification.json').exists()
    # WORK records explicitly read $2126/$2127 (Window1), not Window2 edges.
    # Preserve the initial receipt and correct only labels, never counter data.
    old=OUT/'qualification-v0-labels.json'
    if not old.exists():old.write_bytes(qpath.read_bytes())
    for r in q['aligned_tail_work_census']:
        for group in ('current','general','removed'):
            for key in ('left','right'):
                prior=f'window_{key}_flush'
                if prior in r[group]:r[group][f'window1_{key}_flush']=r[group].pop(prior)
    qpath.write_text(json.dumps(q,indent=2)+'\n')
    for c in plan['cases']:(OUT/f"cases/{c['seq']:03d}/case.json").write_text(json.dumps(c,indent=2)+'\n')
    failures={c['case']:c for c in json.loads((RETURN/'ability-analysis/failure-analysis.json').read_text())['failures']}
    predictions=[]
    for r in q['aligned_tail_work_census']:
        f=failures[r['original_case']];d=r['removed'];target=(f['tail_mean_observed_step_ms']-16.6881545)*1000
        full,clip,entry=d['tile_calls'],d['clipped_calls'],d['renderer_entries']
        # Sensitivity only:0.4us is an assumed dispatch price;2.179us is an older
        # partial warm setup price, not a measurement of this candidate's e.
        saving=(full+clip)*.4+entry*2.179
        period=f['tail_mean_observed_step_ms']*1000-saving
        production=735.94752e6/period
        p={'effect':r['effect'],'original_case':r['original_case'],'tail_frames':r['tail_frames'],
           'baseline_tail_step_us':f['tail_mean_observed_step_ms']*1000,'required_saving_us_before_headroom':target,
           'removed_full_tile_calls':full,'removed_clipped_calls':clip,'removed_entries':entry,
           'equation_us':f'S = {full:.6f} d_full + {clip:.6f} d_clip + {entry:.6f} e - b - u',
           'optimistic_equal_dispatch_break_even_us_if_entry_and_added_costs_zero':target/(full+clip) if full+clip else None,
           'conditional_assumptions_not_measured':{'d_full_us':.4,'d_clip_us':.4,'e_us_old_partial_warm_price':2.179,'b_us':0,'u_us':0},
           'conditional_saving_us':saving,'conditional_margin_us_before_headroom':saving-target,
           'conditional_production_frames_per_second':production,'conditional_remaining_sink_deficit_frames_per_second':44100-production,
           'production_gate_passed':False,'candidate_A7_costs_measured':False}
        predictions.append(p)
    (OUT/'predictions.json').write_text(json.dumps({'budget_us':16688.1545,'sink_frames_per_call':735.94752,
        'A7_performance_evidence':False,'production_gate_passed':False,'cases':predictions},indent=2)+'\n')
    lines=['| Effect | Required saving in matched tail (ms) | Removed full / clipped calls | Removed entries | Optimistic equal dispatch break-even (us) |',
           '|---|---:|---:|---:|---:|']
    for p in predictions:
        threshold=p['optimistic_equal_dispatch_break_even_us_if_entry_and_added_costs_zero']
        lines.append(f"| {p['effect']} | {p['required_saving_us_before_headroom']/1000:.3f} | {p['removed_full_tile_calls']:.3f} / {p['removed_clipped_calls']:.3f} | {p['removed_entries']:.3f} | {threshold:.3f} |" if threshold else
                     f"| {p['effect']} | {p['required_saving_us_before_headroom']/1000:.3f} | 0 / 0 | 0 | No removed work |")
    (OUT/'prediction-table.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))
if __name__=='__main__':report()
