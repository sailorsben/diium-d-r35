"""Exact work populations and physical-baseline targets, with prices left open."""
from pathlib import Path
from hashlib import sha256
import csv,json,statistics
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fixed-rows-private-v3'
SUB=ROOT/'build/subscreen-rows-private-v1'
DSP=ROOT/'build/dsp-dead-work-private-v1'
RETURN=ROOT/'device-evidence/a7-pair-before-20261013T162915Z/retro/snes-ability2'
PERIOD_US=16688.154500
HEADROOM_FRACTION=0.20  # Explicit engineering proposal, not a measured capacity.
QUOTA=735.947520

def parse(p,prefix):return [list(map(int,s[len(prefix):].split(','))) for s in p.read_text().splitlines() if s.startswith(prefix)]
def mean(values):return statistics.mean(values)

def report():
    q=json.loads((OUT/'qualification.json').read_text())
    sq=json.loads((SUB/'qualification.json').read_text())
    dq=json.loads((DSP/'qualification.json').read_text())
    broad=json.loads((OUT/'screen.json').read_text())
    assert q['passed'] and sq['passed'] and dq['passed'] and broad['passed']
    original=(OUT/'clipping-original.crc').read_bytes()
    candidate=(OUT/'clipping-candidate.crc').read_bytes()
    assert original==candidate and len(original.splitlines())==16128
    assert 'signal 11' in (OUT/'clipping-old-counterexample.log').read_text()
    cases=[]
    for c in q['aligned_tail_work_census']:
        physical=list(csv.DictReader(s for s in (RETURN/f"run-{c['case']:03d}/frames.csv").read_text().splitlines() if not s.startswith('#')))
        by_frame={int(r['frame']):r for r in physical};tail=c['tail_frames']
        assert all(i in by_frame for i in tail)
        time_us=mean(int(by_frame[i]['step_ns'])/1000 for i in tail)
        cpu_us=mean(int(by_frame[i]['cpu_ns'])/1000 for i in tail)
        admission_us=mean(int(by_frame[i]['admission_ns'])/1000 for i in tail)
        fixed=parse(OUT/f"exact/{c['case']:03d}-fixed.log",'FIXED ')
        sub=parse(SUB/f"exact/{c['case']:03d}-fixed.log",'SUBSCREEN ')
        dsp=parse(DSP/f"exact/{c['case']:03d}-fixed.log",'DSP ')
        assert len(fixed)==len(sub)==len(dsp)==1200
        assert all([r[0] for r in data]==list(range(1200)) for data in (fixed,sub,dsp))
        assert all(r[1]==sum(r[2:]) for r in dsp)
        opportunities={k:mean(sub[i][j+1] for i in tail) for j,k in enumerate(('full_add','full_subtract','half_subtract'))}
        removed=c['removed'];d=removed['tile_calls']+removed['clipped_calls']
        deadline=max(0,time_us-PERIOD_US)
        margin=max(0,time_us-PERIOD_US*(1-HEADROOM_FRACTION))
        cases.append({**c,'baseline_step_us':time_us,'baseline_main_CPU_us':cpu_us,
            'baseline_admission_us':admission_us,'physical_fixture_failed':any(r=='#failed=1' for r in (RETURN/f"run-{c['case']:03d}/frames.csv").read_text().splitlines()),
            'baseline_local_cadence_proxy_frames_sec':QUOTA*1e6/time_us,
            'required_net_saving_us':deadline,'required_net_saving_for_20_percent_headroom_us':margin,
            'optimistic_equal_tile_dispatch_floor_us':deadline/d if d else None,
            'optimistic_equal_tile_dispatch_floor_for_headroom_us':margin/d if d else None,
            'fixed_queries_mean':mean(fixed[i][1] for i in tail),
            'batched_fixed_entries_mean':mean(fixed[i][2] for i in tail),
            'new_subscreen_fast_rows_mean':opportunities,
            'DSP_mean':{k:mean(dsp[i][j+1] for i in tail) for j,k in enumerate(('voice_calls','zero_envelope','noise_replacement','interpolated'))},
            'sensitivity_not_A7_prices':[{'d_us':price,'e_us':0,'b_us':0,
                'saving_us':d*price,'predicted_step_us':time_us-d*price,
                'cadence_proxy_frames_sec':QUOTA*1e6/(time_us-d*price)} for price in (0.1,0.25,0.5)],
            'scorecard':'S = removed_full*d_full + removed_clip*d_clip + removed_entries*e - b; all prices require aligned A7 measurement',
            'subscreen_scorecard':'S_sub = N_add*k_add + N_sub*k_sub + N_half_sub*k_half_sub - predicate_cost_on_all_other_rows - other_added_costs',
            'DSP_scorecard':'S_dsp = N_zero*g_zero + N_noise*g_noise - branch_cost_on_other_voices - other_added_costs; A7 prices remain unknown',
            'predicted_saving_measured':False})
    receipt={'baseline':'ability2, hash verified original-command fixtures and archived frame indices',
        'period_us':PERIOD_US,'proposed_headroom_fraction':HEADROOM_FRACTION,
        'proposed_total_step_target_us':PERIOD_US*(1-HEADROOM_FRACTION),
        'headroom_target_scope':'Unpaced service capacity. Matched expensive-step saving target is conservative and retains all observers/admission costs. Healthy intentional pacing must be identified separately; paced wall duration does not measure spare capacity.',
        'full_fidelity_required':True,'frameskip_authorized':False,
        'clipped_renderer_cases':16128,'clipped_renderer_matches_original_flushes':True,
        'old_fixed_v2_rejected_by_boundary_counterexample':True,
        'card_writes':0,'production_gate_passed':False,'A7_candidate_savings_measured':False,
        'cases':cases,'screen_cases':406,'screen_calls_per_case':600,
        'screen_context':broad['context'],'universal_coverage':False,
        'fixed_core_sha256':q['core_sha256'],'subscreen_core_sha256':sq['core_sha256'],'DSP_core_sha256':dq['core_sha256'],
        'evidence_boundaries':['Output equivalence and removed work do not establish performance.',
            '20 percent is a proposed engineering target, not proof across all legal PPU states.',
            'Native SETUP/errno77/pointer discrepancy remains a separate unresolved protocol cause.',
            'No measured lower bound proves full-frame emulation impossible on this A7.'],
        'checks':{p:sha256((ROOT/p).read_bytes()).hexdigest() for p in (
            'build/fixed-rows-private-v3/qualification.json','build/fixed-rows-private-v3/row-check.log',
            'build/fixed-rows-private-v3/screen.json','build/subscreen-rows-private-v1/qualification.json',
            'build/subscreen-rows-private-v1/check.log','build/dsp-dead-work-private-v1/qualification.json',
            'build/fixed-rows-private-v3/clipping-exact.log','build/fixed-rows-private-v3/clipping-old-counterexample.log')}}
    (OUT/'prediction.json').write_text(json.dumps(receipt,indent=2)+'\n')
    for c in cases:
        print(c['name'],round(c['baseline_step_us']/1000,3),round(c['required_net_saving_for_20_percent_headroom_us']/1000,3),
              c['removed']['tile_calls'],c['new_subscreen_fast_rows_mean'],flush=True)

if __name__=='__main__':report()
