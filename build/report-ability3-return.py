"""Reconcile measured net savings with prewritten thresholds; no fitted prices."""
from pathlib import Path
import csv,json,re,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
def rows(p):return list(csv.DictReader(l for l in p.read_text().splitlines() if not l.startswith('#')))
def report(archive):
    summary=json.loads((archive/'ability-analysis/summary.json').read_text())
    comparisons=json.loads((archive/'ability-analysis/aligned-comparison.json').read_text())
    predictions=json.loads((ROOT/'build/ability3-private-v1/predictions.json').read_text())['cases']
    assert summary['version']=='1.19-ability3' and summary['fat_clean'] and summary['marker_consumed']
    results=[]
    for m,p in zip(comparisons,predictions):
        assert m['case']==p['case'];n=m['case']
        records={int(v[0]):list(map(int,v[1:])) for l in (ROOT/f'build/ability3-private-v1/census/{n:03d}-math.log').read_text().splitlines() if l.startswith('MATH ') for v in [l[5:].split(',')]}
        common=m['matched_overlap_frames'];counts={k:statistics.mean(records[i][j] for i in common) for j,k in enumerate(('active_rows','fixed_rows','palette_hits','palette_builds'))}
        tail=m['new_tail'];step=tail['step_ns'];deficit=max(0,step-16688.1545)
        terminal=m['terminal'];match=re.search(r'appl=(\d+) hw=(\d+).*xfer=(\d+)',terminal or '')
        item={'case':n,'name':m['name'],'passed':m['passed'],'previous_calls':m['old_calls'],'current_calls':m['new_calls'],
              'matched_frame_indices':common,'matched_CPU_saving_us':m['overlap_cpu_saving_us'],
              'matched_work_counts':counts,'whole_original_tail_available':m['complete_baseline_tail_available'],
              'current_tail_step_us':step,'current_tail_deficit_us_before_headroom':deficit,
              'current_tail_cadence_sink_frames_per_second':735.94752e6/step,
              'current_tail_sink_deficit_frames_per_second':max(0,44100-735.94752e6/step),
              'prewritten_sensitivity_saving_us_not_measured':p['conditional_saving_us'],
              'native_error_detail':terminal,'terminal_pointer_excess_frames':int(match[1])-int(match[3]) if match else None,
              'unit_prices_inferred':False}
        results.append(item)
    # These are static instructions, not a microbenchmark or cycle model.
    assembly={'function':'DrawTile16Add1_2','ability2_stack_allocation_bytes':76,'ability3_stack_allocation_bytes':148,
              'observed_extra_loop_work':'Fixed-only eligibility test before original blend test; predicate vector-to-ARM transfers, palette selection, stack accesses.',
              'interpretation':'Plausible added overhead; this does not measure its A7 cost or prove cache misses dominate.'}
    outcome={'archive':archive.name,'version':summary['version'],'verdict':'REJECT_AS_DEFICIT_FIX',
             'physical_pass_set_unchanged':True,'bounded_cases_completed':summary['bounded_cases_completed'],
             'failures':len(summary['runtime_failed_cases']),'card_writes':0,'production_gate_passed':False,
             'baseline_for_further_work':'ability2; retain ability3 as a measured negative result',
             'assembly_evidence':assembly,'cases':results,
             'limits':['One paired run, unexposed frequency and contention limit attribution of small net differences.',
                       'Control tails save50..102us too; comparable gains cannot establish effect-specific cache savings.',
                       'Whole-call differences do not price row math, builds, hits or predicate cost.',
                       'Native application/transfer divergence makes late reported reserve inexact.']}
    (archive/'ability-analysis/verdict.json').write_text(json.dumps(outcome,indent=2)+'\n')
    print('Rejected as deficit fix:',outcome['bounded_cases_completed'],'complete,',outcome['failures'],'fail; no card writes')
    for r in results:
        print(r['name'],round(r['matched_CPU_saving_us']['mean']),round(r['current_tail_deficit_us_before_headroom']),r['terminal_pointer_excess_frames'])
if __name__=='__main__':report(Path(sys.argv[1]).resolve())
