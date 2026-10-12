"""Reproducible work counts and conditional A7 budget; never QEMU timings."""
from pathlib import Path
from hashlib import sha256
from statistics import mean
import csv,json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/confuser-private-v1'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p,prefix):
    rows=[]
    for l in p.read_text().splitlines():
        if not l.startswith(prefix+' '):continue
        parts=l.split();assert parts[1]==f'frame={len(rows)+1}'
        values=list(map(int,parts[2:]));assert len(values)==128
        rows.append(values)
    assert len(rows)==1200
    return rows
data={}
for n in ('baseline','bg3-window','bg3-blend','bg3-submask'):
    folder=OUT/n/'confuser'
    data[n]={k:read(folder/file,k) for k,file in [('CONF','replay.log'),('HYP','replay.log'),('CENSUS','census.txt')]}
ids=[i for i,r in enumerate(data['bg3-window']['CONF']) if r[13]]
assert ids==list(range(267,569))
assert [(i,r[11]) for i,r in enumerate(data['baseline']['CONF']) if r[11]]==[(267,1)]
assert not any(r[12] for r in data['baseline']['CONF'])
for n,d in data.items():
    assert sum(r[11] for r in d['CONF'])==1 and not any(r[12] for r in d['CONF'])
    for frame,(r,b) in enumerate(zip(d['CENSUS'],data['baseline']['CENSUS'])):
        assert r[1:46]==b[1:46],(n,frame,'requested/decode/pixel rows changed')
    assert all(r[7:10]==b[7:10] for r,b in zip(d['HYP'],data['baseline']['HYP']))
    for r,c in zip(d['HYP'],d['CENSUS']):
        assert sum(r[17:25])==r[0] and sum(r[33:41])==r[1]
        assert sum(i*r[16+i] for i in range(1,9))==sum(c[24:31])
        assert sum(i*r[32+i] for i in range(1,9))==sum(c[32:39])
def metric(n,p,i,indices=ids):return mean(data[n][p][f][i] for f in indices)
names={'renderer_entries':('CONF',0),'tile_calls':('HYP',0),'clipped_calls':('HYP',1),
 'plain_calls':('HYP',48),'half_add_calls':('HYP',50),'half_add_clipped_calls':('HYP',66),
 'plain_rows':('CENSUS',24),'half_add_rows':('CENSUS',26),'sub_rows':('CENSUS',27),
 'neon_rows':('CENSUS',40),'neon_empty_rows':('CENSUS',41),'neon_full_rows':('CENSUS',42),
 'neon_depth_rejected_rows':('CENSUS',43),'tile_decodes':('CENSUS',21),
 'palette_builds':('HYP',7),'direct_gathers':('HYP',8),'palette_queries':('HYP',10),
 'bg1_entries':('CONF',16),'bg2_entries':('CONF',17),'bg3_entries':('CONF',18),
 'bg1_rows':('CONF',24),'bg2_rows':('CONF',25),'bg3_rows':('CONF',26),
 'deferred_window_edges':('CONF',2),'fallback_window_edges':('CONF',3)}
stats={n:{k:metric(n,*v) for k,v in names.items()} for n in data}
ordinary={k:metric('baseline',*v,indices=range(100,200)) for k,v in names.items()}
removed={k:stats['baseline'][k]-stats['bg3-window'][k] for k in names}
fast_rows=metric('bg3-submask','CONF',102)
assert all(data['bg3-submask']['CONF'][f][96]==data['bg3-submask']['CONF'][f][102] for f in ids)
raw=ROOT/'device-evidence/a7-pair-before-20261012T043106Z/retro/snes-combined-gameplay1/last-progress.txt'
session=dict(x.split('=',1) for x in raw.read_text().splitlines() if '=' in x)
tail=[list(map(int,v.split(','))) for k,v in session.items() if k.startswith('frame_cost_') and k!='frame_cost_columns'][:-1]
deadline_ms=1000/float(session['fps'])
step_ms=mean(r[3]+r[9] for r in tail)/1e6
gap_us=(step_ms-deadline_ms)*1000
trace=[]
for line in (raw.parent/'last-pcm-fault.txt').read_text().splitlines():
    if not line.startswith('seq='):continue
    values=dict(x.split('=',1) for x in line.split() if '=' in x)
    if values.get('op')=='SYNC_OK' and values.get('state')=='3' and values.get('epoch')=='1':
        trace.append({k:int(values[k]) for k in ('seq','ns','xfer','appl','hw','queued')})
first,last=trace[0],trace[-1]
dt=(last['ns']-first['ns'])/1e9
accepted_rate=(last['xfer']-first['xfer'])/dt
native_gap_us=deadline_ms*1000*(44100/accepted_rate-1)
table=[]
removed_calls=removed['tile_calls']+removed['clipped_calls']
for d in (.2,.3,.4,.5):
    for f in (0,.02,.05,.10):
        saving=removed_calls*d+fast_rows*f
        predicted_ms=step_ms-saving/1000
        table.append({'dispatch_us':d,'blend_net_us_per_fast_row':f,'entry_credit_us':0,'new_bookkeeping_us':0,
          'predicted_saving_us':saving,'predicted_call_ms':predicted_ms,
          'local_pcm_proxy_frames_per_second':735.94752/(predicted_ms/1000),
          'budget_margin_before_other_costs_us':saving-gap_us})
# Whole-package transfer is a sensitivity check, never a tile unit price.
bio=list(csv.DictReader((ROOT/'evidence/2026-10-11/bio-offline-hypotheses/effect-counts.csv').open()))
bio={(r['variant'],int(r['frame'])):r for r in bio}
pair=json.loads((ROOT/'evidence/2026-10-11/a7-pair1-return/analysis.json').read_text())
transfer=[]
for p in pair['aligned_pairs']:
    if not p['common_running_effect_calls_after_warmup']:continue
    frames=range(p['first_frame'],p['last_frame']+1)
    r=mean(int(bio['baseline',i]['tile_calls'])-int(bio['palette-fast-window-counts',i]['tile_calls']) for i in frames)
    save=p['saving_us']['wall_ns']['mean']
    transfer.append({'baseline_pass':p['baseline_pass'],'aligned_bio_removed_calls':r,
                    'measured_bio_package_wall_saving_us':save,
                    'heuristic_confuser_saving_us':save/r*removed['tile_calls']})
proofs={}
for n in data:
    p=OUT/n/'equivalence-confuser.log'
    assert 'PASS: 1200 frames exact visible pixels' in p.read_text() and 'FAIL' not in p.read_text()
    proofs[p.relative_to(ROOT).as_posix()]=digest(p)
for n,label,frames in [('bg3-window','bio',1200),('bg3-window','general',2400),('bg3-blend','bio',1200),('bg3-submask','bio',1200)]:
    p=OUT/n/('equivalence-'+label+'.log');assert f'PASS: {frames} frames exact visible pixels' in p.read_text()
    proofs[p.relative_to(ROOT).as_posix()]=digest(p)
for name,phrase in [('window-oracle.log','PASS: 1048576'),('blend-oracle.log','PASS: 8388608'),('submask-oracle.log','PASS: 8388608')]:
    p=OUT/name;assert phrase in p.read_text();proofs[p.relative_to(ROOT).as_posix()]=digest(p)
assert digest(ROOT/'build/a7-pair-private-v1/core/snes9x2005_plus_libretro.so')=='ee0b241c3b7c561e76efbedbbdcf37bf8e104bb6754d7b0493c3ed4774172155'
assert digest(ROOT/'build/plus-a7-out/plus-a7.so')=='80b36f61971e4e649843ea23dc051cd185ba699c413ff9023c93f548e2c738b8'
result={'hardware_prices_measured':False,'qemu_timings_used':False,'card_access':False,'installed':False,
 'production_cores_unchanged':True,'confuser_init_zero_based_frame':267,
 'effect_window_zero_based_frames':[267,568],'effect_frames':302,'effect_identity_verified_from_rom':True,
 'replay_is_exact_physical_input_history':False,'stats':stats,'ordinary_replay_frames':[100,199],
 'ordinary_stats':ordinary,'removed':removed,'half_add_fast_rows':fast_rows,
 'physical_tail':{'core_plus_admission_ms':step_ms,'deadline_ms':deadline_ms,'gap_us':gap_us,
                  'reported_ppu_growth_ms':7.652-3.232,'sample_cpu_growth_ms':17.486-12.229,
                  'sample_apu_growth_ms':4.261-4.048,'source_sha256':digest(raw),
                  'native_trace_first':first,'native_trace_last':last,
                  'native_trace_seconds':dt,'accepted_rate_frames_per_second':accepted_rate,
                  'native_rate_equivalent_gap_us':native_gap_us,
                  'native_rate_limit':'215ms observation window; separate asynchronous endpoints, not identical to the23-call window'},
 'break_even':{'dispatch_only_us_per_removed_call':gap_us/removed_calls,
               'blend_only_net_us_per_fast_row':gap_us/fast_rows,
               'equation_us':'1772.066225d_plain + 255.639073d_half + 17.198675d_clip_half + 32.331126e + 4041.900662f - b - u',
               'required_us':gap_us,'gate_met':False,'reason':'aligned A7 incremental dispatch/blend/bookkeeping prices missing'},
 'sensitivity_not_measurement':table,'aligned_bio_package_transfer_not_unit_cost':transfer,
 'constant_tail_effect_prediction':{'lost_reserve_frames_per_call':gap_us/1e6*44100,
    'cumulative_deficit_frames_over_302_calls':gap_us/1e6*44100*302,
    'calls_until_2823_frame_reserve_exhaustion':2823/(gap_us/1e6*44100)},
 'output_comparison_frames':10800,'proofs':proofs,
 'compiler_sanity':{'counter_free':True,'timings_used':False,'first_blend_wrapper_saved_gprs':6,
                    'original_wrapper_saved_gprs':3,'refined_submask_wrapper_saved_gprs':3,
                    'preferred_blend':'bg3-submask; all active sd>1 lanes selected with one zero test'},
 'limits':['Derived Confuser encounter uses normal inputs after an earlier privately derived battle; it is not the physical failure state.',
   'Original harness label says Bio Blast for its shared A/A input mode; snapshot plus ROM init proves Confuser.',
   'Bio package transfer includes palette replacement and prefix changes, which Confuser baseline already has; it can overpredict incremental saving.',
   'f must be net of the new guard on both fast and fallback row shapes; b includes extra capture, clipping, traversal and cache costs.',
   '23-call hardware tail is not a full effect timeline; observer included, frequency unavailable, vendor pointer bias unresolved.',
   'Whole-phase or whole-package timing divided by counts is not a measured removable unit cost.']}
result['private_input_hashes']={p.relative_to(ROOT).as_posix():digest(p) for p in [OUT/'confuser-selection/scene.state',OUT/'confuser-selection/input.txt',OUT/'cast-input.txt']}
result['source_and_capture_hashes']={}
for n in data:
    for rel in ('core/source/gfx.c','core/source/ppu.c','core/source/tile.c','core/source/cpuexec.c',
                'core/source/a7_window.h','core/source/a7_tile.h','core/source/a7_color_cache.h',
                'core/libretro.c','core/link.T','core/snes9x2005_plus_libretro.so','confuser/replay.log','confuser/census.txt'):
        p=OUT/n/rel;result['source_and_capture_hashes'][p.relative_to(ROOT).as_posix()]=digest(p)
(OUT/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
with (OUT/'effect-counts.csv').open('w',newline='') as dst:
    columns=['variant','frame']+list(names)+['half_add_fast_rows']
    writer=csv.DictWriter(dst,fieldnames=columns);writer.writeheader()
    for n in data:
        for f in ids:
            row={k:data[n][p][i] for k,(p,i) in names.items()}
            row.update(variant=n,frame=f,half_add_fast_rows=data[n]['CONF'][f][102] if n in ('bg3-blend','bg3-submask') else '')
            writer.writerow(row)
print(json.dumps({'passed':True,'effect_frames':len(ids),'removed_tile_calls':removed['tile_calls'],
                 'fast_blend_rows':fast_rows,'gap_us':gap_us,'comparisons':10800,'gate_met':False},indent=2))
