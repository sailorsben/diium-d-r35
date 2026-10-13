"""Calculate falsifiable math-reuse thresholds from the latest A7 tails."""
from pathlib import Path
import json,statistics
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ability3-private-v1'
RETURN=ROOT/'device-evidence/a7-pair-before-20261013T162915Z'
def report():
    q=json.loads((OUT/'qualification.json').read_text());assert q['passed']
    assert 'PASS: 2097152' in (OUT/'math-check.log').read_text()
    measured=json.loads((RETURN/'ability-analysis/aligned-comparison.json').read_text())
    cases=[]
    for census,m in zip(q['fixed_math_work_census'],measured):
        assert census['case']==m['case'];d=census['tail_means']
        removed=d['fixed_math_rows_removed'];builds=d['math_palette_builds'];hits=d['math_palette_hits'];active=d['active_NEON_rows']
        target=max(0,m['new_tail']['step_ns']-16688.1545) if not m['passed'] else 0
        p={'case':m['case'],'name':m['name'],'baseline_passed':m['passed'],'tail_frames':census['tail_frames'],
           'baseline_tail_us':m['new_tail'],'required_saving_us_before_headroom':target,**d,
           'equation_us':f'S = {removed:.6f} c - {builds:.6f} p - {hits:.6f} h - {active:.6f} q - u',
           'prices':'c=removed fixed-lane math; p=palette build; h=cache hit; q=eligibility overhead per active math/plain row (plain compiles away); u=other cache/contention cost',
           'optimistic_c_break_even_us_with_all_added_costs_zero':target/removed if target and removed else None,
           'unit_costs_measured':False,'production_gate_passed':False,'A7_prediction_is_conditional':True}
        # Example sensitivity, explicitly assumptions; no QEMU timings or old
        # unrelated prices are substituted for the new A7 paths.
        saving=removed*.2-builds*1-hits*.05-active*.01
        period=m['new_tail']['step_ns']-saving
        p['sensitivity_assumptions_us']={'c':.2,'p':1,'h':.05,'q':.01,'u':0}
        p['conditional_saving_us']=saving
        p['conditional_margin_us']=saving-target
        p['conditional_sink_production_frames_per_second']=735.94752e6/period
        p['conditional_remaining_deficit_frames_per_second']=max(0,44100-735.94752e6/period)
        cases.append(p)
    predictions={'budget_us':16688.1545,'sink_frames_per_call':735.94752,'production_gate_passed':False,
        'physical_test_authorized_experimental_only':True,'actual_new_math_A7_costs_measured':False,'cases':cases,
        'falsifiable_prediction':'Eligible math rows predict savings; absent eligible rows predict no benefit. All18 full1200-call cases must draw and maintain PCM without native errors; compare identical expensive frames and cumulative valid reserve, not pooled FPS.'}
    (OUT/'predictions.json').write_text(json.dumps(predictions,indent=2)+'\n')
    lines=['| Case | Previous result | Remaining tail deficit (ms) | Removed row math / palette builds / hits | Optimistic c break-even (us) |', '|---|---|---:|---:|---:|']
    for p in cases:
        threshold=p['optimistic_c_break_even_us_with_all_added_costs_zero']
        lines.append(f"| {p['name']} | {'pass' if p['baseline_passed'] else 'fail'} | {p['required_saving_us_before_headroom']/1000:.3f} | {p['fixed_math_rows_removed']:.1f} / {p['math_palette_builds']:.1f} / {p['math_palette_hits']:.1f} | {threshold:.3f} |" if threshold else f"| {p['name']} | {'pass' if p['baseline_passed'] else 'fail'} | {p['required_saving_us_before_headroom']/1000:.3f} | {p['fixed_math_rows_removed']:.1f} / {p['math_palette_builds']:.1f} / {p['math_palette_hits']:.1f} | {'control' if p['baseline_passed'] else 'no removed work'} |")
    (OUT/'prediction-table.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))
if __name__=='__main__':report()
