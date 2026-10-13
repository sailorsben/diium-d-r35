"""Price failure tails and identify observed effects from the archived RAM records."""
from pathlib import Path
import csv,json,re,statistics,sys
ROOT=Path(__file__).resolve().parent.parent
def rows(p):return list(csv.DictReader(x for x in p.read_text().splitlines() if not x.startswith('#')))
def kv(p):return dict(x.split('=',1) for x in p.read_text().splitlines() if '=' in x)
def diagnose(archive):
    archive=archive.resolve();base=archive/'retro/snes-ability1';out=archive/'ability-analysis'
    summary=json.loads((out/'summary.json').read_text());cases=json.loads((out/'cases.json').read_text());plan=json.loads((base/'plan.json').read_text())
    catalog=json.loads((ROOT/'build/ff6-effect-screen-private-v1/catalog.json').read_text());details=[]
    for fail in summary['runtime_failed_cases']:
        n=fail['case'];d=base/f'run-{n:03d}';f=rows(d/'frames.csv');a=rows(d/'animation.csv');s=kv(d/'last-session.txt')
        c=plan['cases'][n];raw=(base/f'cases/{n:03d}/expected.bin').read_bytes();ids=[i for i in c['possible_attack_ids'] if i<238 or c['family']=='tools']
        mapping={(f'{raw[1+j*15]:02x}',raw[2+j*15:16+j*15].hex()):i for j,i in enumerate(ids)}
        observed=[mapping[(r['attack'],r['properties'])] for r in a if (r['attack'],r['properties']) in mapping]
        effect=observed[-1] if observed else None;name=catalog[effect]['name'] if effect is not None else 'unobserved'
        tail=f[-17:-1];wall=statistics.mean(int(r['wall_ns']) for r in tail)/1e6;cpu=statistics.mean(int(r['cpu_ns']) for r in tail)/1e6
        admission=statistics.mean(int(r['admission_ns']) for r in tail)/1e6;step=statistics.mean(int(r['step_ns']) for r in tail)/1e6
        deficit=max(0,step-16.6881545);core_deficit=max(0,wall-16.6881545)
        error=s.get('pcm_error_detail','');m=re.search(r'appl=(\d+) hw=(\d+).*xfer=(\d+)',error)
        details.append({'case':n,'case_name':fail['name'],'family':c['family'],'observed_effect_id':effect,'observed_effect_name':name,
            'calls_before_failure':fail['calls'],'terminal_pcm_detail':error,'terminal_pointer_excess_frames':int(m[1])-int(m[3]) if m else None,
            'tail_nonterminal_calls':len(tail),'tail_mean_core_cpu_ms':cpu,'tail_mean_core_wall_ms':wall,'tail_mean_admission_ms':admission,
            'tail_mean_observed_step_ms':step,'core_wall_saving_floor_ms':core_deficit,'full_observed_step_saving_floor_ms':deficit,
            'required_tail_step_throughput_gain_percent':100*deficit/16.6881545,
            'tail_reported_running_reserve_frames':[int(r['playable']) for r in tail if int(r['state'])==3],
            'tail_zero_pointer_bias_reserve_frames':[int(r['playable']) for r in tail if int(r['state'])==3 and int(r['appl'])==int(r['xfer'])],
            'admission_includes_intentional_pacing_not_pure_overhead':True,
            'no_incremental_renderer_unit_cost_inferred':True})
    groups={}
    for d in details:groups.setdefault(d['observed_effect_name'],[]).append(d['case'])
    clean_with_properties=sum(r['status']=='bounded_run_completed' and r['requested_property_samples']>0 for r in cases)
    completed_missing=[{'case':r['case'],'name':r['name'],'family':r['family'],'rage_ids':r['rage_ids']} for r in cases if r['status']=='bounded_run_completed' and not r['requested_property_samples']]
    result={'archive':archive.name,'failed_case_groups_by_last_observed_requested_effect':groups,
        'clean_bounded_cases_with_requested_properties':clean_with_properties,'clean_bounded_cases_without_requested_spell_properties':completed_missing,
        'failures':details,'headroom_prediction':'Tail floors require equal aligned savings to reach16.688ms, before safety margin; they do not price an optimization.',
        'physical_failure_mechanism':'All retained terminal messages must be checked; errno77 SETUP is not automatically evidence of memory corruption or a C crash.'}
    assert all('errno=77 state=1' in d['terminal_pcm_detail'] for d in details)
    result['terminal_operations']={op:sum(d['terminal_pcm_detail'].startswith(op+' ') for d in details) for op in ('SYNC_OBSERVE','WRITEI_FRAMES')}
    (out/'failure-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'groups':groups,'clean_with_properties':clean_with_properties,
        'tail_costs':[{k:v for k,v in d.items() if k in ['case','observed_effect_name','tail_mean_core_cpu_ms','tail_mean_core_wall_ms','tail_mean_observed_step_ms','full_observed_step_saving_floor_ms','terminal_pointer_excess_frames']} for d in details]},indent=2))
if __name__=='__main__':diagnose(Path(sys.argv[1]))
