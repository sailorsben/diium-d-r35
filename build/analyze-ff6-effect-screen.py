"""Reproducible offline coverage/risk counts; no QEMU timing or A7 price claims."""
from pathlib import Path
from hashlib import sha256
from statistics import mean
import collections, csv, json, math

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/ff6-effect-screen-private-v1'
catalog=json.loads((OUT/'catalog.json').read_text())
proofs={}
def digest(p): return sha256(p.read_bytes()).hexdigest()
def parse(p):
    text=p.read_text()
    assert 'FAIL' not in text and 'IDENTITY init_hits=' in text
    columns=text.split('ROW columns=')[1].splitlines()[0].split(',')
    rows=[[int(x) for x in line[4:].split(',')] for line in text.splitlines()
          if line.startswith('ROW ') and not line.startswith('ROW columns=')]
    assert rows and [r[0] for r in rows]==list(range(len(rows)))
    assert all(len(r)==len(columns) for r in rows)
    assert f'PASS: {len(rows)} frames exact visible pixels' in text
    assert sum(r[16] for r in rows)>0 and sum(r[17] for r in rows)>0
    flushes=collections.Counter()
    for line in text.splitlines():
        if line.startswith('FLUSH '):
            flushes.update({k:int(v) for item in line.split()[2:] for k,v in [item.split('=')]})
    proofs[p.relative_to(ROOT).as_posix()]=digest(p)
    return rows,columns,flushes
def population(base,groups,expected):
    result={}
    for group in groups:
        for p in sorted((base/group).glob('*.json')):
            receipt=json.loads(p.read_text());index=receipt['index']
            assert receipt['exact_output_pass'] and receipt['identity_verified'] and not receipt['host_timeout']
            assert index not in result
            result[index]=parse(p.with_suffix('.log'))
            assert len(result[index][0])==receipt['frames_requested']
            proofs[p.relative_to(ROOT).as_posix()]=digest(p)
    assert set(result)==set(expected),(str(base),len(result))
    return result
current=population(OUT,['cases','broad'],range(406))
general=population(OUT/'general',['cases','broad'],range(406))
traced=population(OUT/'trace-current',['cases'],[14,19,20,33,57,65,66,73,96,100,113,136,134,195,198,204,224,138,329,222,183,69,161])
fixed=population(OUT/'fixed-unused',['cases'],[33,57,65,66,73,111,155,160,163,168,171,193,196,204,248,339,342,346,348])
natural={}
for case in json.loads((OUT/'natural/cases.json').read_text()):
    p=OUT/'natural'/f"{case['index']:03d}.log"
    natural[case['index']]=parse(p)
    assert 'overlay_bytes=0' in p.read_text() and 'deinit_hits=' in p.read_text()
    assert len(natural[case['index']][0])==1200
oracle=OUT/'multi-window-oracle.log'
assert '1572864 exhaustive single-layer and 524288 randomized multi-layer states' in oracle.read_text()
proofs[oracle.relative_to(ROOT).as_posix()]=digest(oracle)
def percentile(values,fraction):
    values=sorted(values);return values[max(0,math.ceil(len(values)*fraction)-1)]
def max_32(rows,column):
    v=[r[column] for r in rows];s=sum(v[:32]);best=s
    for i in range(32,len(v)):s+=v[i]-v[i-32];best=max(best,s)
    return best/32
summaries=[]
for index,entry in enumerate(catalog):
    row={'index':index,'name':entry['name'],'init':entry['init'],
         'current_frames':len(current[index][0]),'general_frames':len(general[index][0]),
         'exact_output':True,'normal_command_coverage':index in natural}
    for label,pop in [('current',current),('general',general)]:
        rows,columns,_=pop[index]
        for field in ('renderer_entries','tile_calls','clipped_calls','neon_rows','depth_rejected_rows','tile_decodes','window_fallback'):
            col=columns.index(field);values=[r[col] for r in rows]
            row[f'{label}_{field}_p95']=percentile(values,.95)
            row[f'{label}_{field}_max32_mean']=max_32(rows,col)
    summaries.append(row)
pairs=[]
for index in sorted(traced):
    old,columns,oldflush=traced[index];new,_,newflush=general[index]
    assert len(old)==len(new)==1200
    table_frame=next(r[0] for r in old if r[17])
    init_frame=next(r[0] for r in old if r[0]>=table_frame and r[16])
    interval=range(init_frame,min(len(old),init_frame+302))
    row={'index':index,'name':catalog[index]['name'],'first_init_frame':init_frame,
         'window_first':interval.start,'window_last':interval.stop-1,
         'window_definition':'first302 calls after verified init; not a claimed full effect duration'}
    for field in ('renderer_entries','tile_calls','clipped_calls','neon_rows','tile_decodes','palette_builds','window_fallback'):
        col=columns.index(field)
        row['current_'+field]=mean(old[f][col] for f in interval)
        row['general_'+field]=mean(new[f][col] for f in interval)
        row['removed_'+field]=row['current_'+field]-row['general_'+field]
    row['current_rendered_flush_registers_full_replay']=dict(oldflush)
    row['general_rendered_flush_registers_full_replay']=dict(newflush)
    row['sensitivity_us_at_dispatch_0_4_entry_0_new_cost_0']=(row['removed_tile_calls']+row['removed_clipped_calls'])*.4
    row['equation_us']=f"{row['removed_tile_calls']:.6f}d_full + {row['removed_clipped_calls']:.6f}d_clip + {row['removed_renderer_entries']:.6f}e - b - u"
    pairs.append(row)
negative=[]
for index,(new,columns,_) in sorted(fixed.items()):
    old,_,_=general[index];n=min(len(old),len(new))
    deltas={field:sum(old[f][columns.index(field)]-new[f][columns.index(field)] for f in range(n))
            for field in ('renderer_entries','tile_calls','clipped_calls','neon_rows')}
    negative.append({'index':index,'name':catalog[index]['name'],'common_calls':n,'total_removed':deltas})
assert all(not any(row['total_removed'].values()) for row in negative)
reference=ROOT/'build/plus-a7-out/plus-a7.so'
working=ROOT/'build/confuser-gameplay-private-v1/plus-a7.so'
assert digest(reference)=='80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'
assert digest(working)=='d5761eacc68fbcba91052de19d37ca9f159fb2b40df7c9272f49398b9b4f880a'
frames=sum(len(r[0]) for pop in (current,general,traced,fixed,natural) for r in pop.values())
result={'animation_records':406,'current_exact_records':406,'general_exact_records':406,
        'total_exact_comparison_calls':frames,'normal_magitek_abilities':len(natural),
        'normal_magitek_completion_verified':True,'clipping_oracle_cases':2097152,
        'new_actual_C_crashes_in_screen':0,'new_physical_crashes_confirmed':False,
        'A7_unit_prices_measured':False,'QEMU_timings_used':False,'card_writes':0,
        'working_core_preserved_sha256':digest(working),'original_reference_core_sha256':digest(reference),
        'generalization':'Mode1 Window2 snapshots on BG1/BG2/BG3 simultaneously, plus irrelevant Window2-edge deferral',
        'paired_register_and_work_analysis':pairs,'negative_fixed_unused_hypothesis':negative,
        'highest_remaining_tile_preamble_populations':sorted(summaries,key=lambda r:r['general_tile_calls_max32_mean'],reverse=True)[:20],
        'limits':[
          '406 records refer to AttackAnimProp; weapon/monster physical attacks use another property table.',
          'Substitution uses original Bio Blast attacker/target/mechanics, not ordinary casts for all records.',
          'Most screens are600 calls; selected cases1200. Completion is asserted only for eight natural casts.',
          'No multi-target/reflection/side/back attack/state matrix, full-game or physical performance certification.',
          'Operation counts rank mechanisms; unmeasured prices prevent numerical A7 cadence or crash-free guarantees.',
          'Legacy copied screen harness says Bio Blast in its final line; CASE/ROM table/init verification identifies substitutions.'
        ],'raw_proof_sha256':proofs}
(OUT/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
for name,rows in [('coverage.csv',summaries),('window-pairs.csv',[{k:v for k,v in r.items() if not isinstance(v,dict)} for r in pairs])]:
    with (OUT/name).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(json.dumps({k:v for k,v in result.items() if k not in ('raw_proof_sha256','paired_register_and_work_analysis','highest_remaining_tile_preamble_populations','negative_fixed_unused_hypothesis')},indent=2))
print('Leading window savings:')
for r in sorted(pairs,key=lambda r:r['removed_tile_calls']+r['removed_clipped_calls'],reverse=True)[:6]:
    print(r['name'],r['equation_us'], 'sensitivity',r['sensitivity_us_at_dispatch_0_4_entry_0_new_cost_0'])
print('Largest remaining populations:',[(r['name'],r['general_tile_calls_max32_mean']) for r in result['highest_remaining_tile_preamble_populations'][:8]])
