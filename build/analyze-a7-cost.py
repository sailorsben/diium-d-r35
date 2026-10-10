"""Physical costs only with mock=0. Contracts mode discards all QEMU timings.

Keep individual observations and32-operation batch averages separate. Warm
setup, palette payload, valid-bit test and shadow helper costs are distinct;
neither an inclusive PPU/entry quotient nor a sum of unaligned path averages
is an installation prediction.
"""
from pathlib import Path
import argparse, csv, json, math, statistics, re
parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path)
parser.add_argument('--contracts-only',action='store_true');args=parser.parse_args()
paths=sorted(args.directory.rglob('unit-cost.csv'));assert paths,'No capture files'
KINDS=['entry_prefix','screen_setup','background_setup','object_setup_and_clip_list',
       'tile_renderer_select','row_materialization_payload','row_valid_bit_test',
       'mask_capture','deferral_shadow_span','clip_fetch','band_row_compare','mask_reset','empty_control']
PHASES=['entry_setup','pixel_tile_and_unselected_color_cache','sampled_color_row','window_clip_bounds','sampled_color_cache']
def distribution(values):
    if not values:return None
    s=sorted(values)
    return {'n':len(s),'mean':statistics.mean(s),'median':statistics.median(s),
            'p95':s[max(0,math.ceil(.95*len(s))-1)],'p99':s[max(0,math.ceil(.99*len(s))-1)],
            'min':s[0],'max':s[-1]}
all_benches={k:[] for k in range(len(KINDS))};phase_runs=[];captures=[]
for path in paths:
    lines=path.read_text().splitlines();meta={}
    for line in lines:
        if line.startswith('#'):
            k,v=line[1:].split('=',1);assert k not in meta;k and meta.update({k:v})
    assert meta['suite']=='1.19-cost1' and meta['overflow']=='0'
    assert args.contracts_only or meta['mock']=='0','QEMU/mock timings are not A7 costs'
    assert args.contracts_only or meta['contract_fixture']=='0','Synthetic native provider is not A7 evidence'
    rows=list(csv.DictReader(l for l in lines if not l.startswith('#')))
    types={'frame','checkpoint','ppu','timer_control','service','workers','phase','counts','calls','bench','row_sampling'}
    assert all(r['type'] in types for r in rows)
    assert all(all(re.fullmatch(r'-?\d+',v) for k,v in r.items() if k!='type') for r in rows)
    frames={int(r['frame']):r for r in rows if r['type']=='frame'}
    assert len(frames)==int(meta['runs']) and sorted(frames)==list(range(len(frames)))
    for r in rows:
        assert int(r['frame']) in frames
        if r['type']=='counts':assert r['wall_ns']=='0' and r['observer_ns']=='0','Clock error or record overflow'
        if r['type']=='bench':
            k=int(r['kind']);assert k<len(KINDS)
            assert int(r['iterations']) in (1,32) and r['warm']=='16'
            assert 277<=int(r['frame'])<=438
            if not args.contracts_only:all_benches[k].append(r)
    if not args.contracts_only:
        for f,frame in frames.items():
            if frame['kind'] not in ('1','3'):continue
            phases={int(r['kind']):r for r in rows if r['type']=='phase' and int(r['frame'])==f}
            assert set(phases)==set(range(len(PHASES)))
            ppu=next(r for r in rows if r['type']=='ppu' and int(r['frame'])==f)
            counts=next(r for r in rows if r['type']=='counts' and int(r['frame'])==f)
            phase_runs.append({'capture':path.parent.name,'frame':f,'dense':frame['kind']=='3',
                'ppu_inclusive_cpu_us':int(ppu['cpu_ns'])/1000,
                'phases_us':{PHASES[k]:int(v['cpu_ns'])/1000 for k,v in phases.items()},
                'ppu_entries':int(counts['iterations']),
                'exclusive_setup_us_per_observed_entry':int(phases[0]['cpu_ns'])/1000/int(counts['iterations']) if int(counts['iterations']) else None})
    captures.append({'directory':path.parent.name,'metadata':meta,'frames':len(frames)})
result={'version':'1.19-cost1','contracts_only':args.contracts_only,'captures':captures,
        'hardware_measured':not args.contracts_only,'timer_calibration_subtracted':False,
        'phase_runs':phase_runs,'unit_paths':{},'gate':'NOT MET',
        'scorecard':{'removed_entries':106.246914,'added_rows':1423.919753,'required_saving_us':1514.283,
                    'e_us':None,'r_us':None,'b_us':None,'S_us':None,'predicted_production_hz':None,
                    'formula':'S=106.246914e-1423.919753r-b; P_new=735.947520/(T-S/1000000)',
                    'current_production_frames_per_sec':38480.644205},
        'unmeasured':['weight entry subpaths by candidate-removed entries in this exact state',
                      'candidate longer deferral spans and changed band population',
                      'whole-candidate cache interaction beyond warm payload kernels',
                      'complete effect reserve if capture ends early or the PCM ring wraps'],
        'limits':['sparse phase runs time1/64 color requests: the pixel remainder contains the other63/64',
                  'dense frame320 has full row attribution and potentially large observer interference',
                  'batch-average p99 is not individual-call p99',
                  'row miss benchmark prices materialization payload; valid-bit benchmark is not the full cache-hit path',
                  'no installation verdict can be supplied by QEMU or the partial warm-path model']}
result['scorecard']['production_cadence_proxy_us']=735.947520/38480.644205*1e6
result['scorecard']['saving_to_close_that_pcm_cadence_us']=result['scorecard']['production_cadence_proxy_us']-16688.1545
if not args.contracts_only:
    for k,bench in all_benches.items():
        groups={}
        for width in (1,32):
            data=[b for b in bench if int(b['iterations'])==width]
            groups[str(width)]={'samples':len(data),'timed_iterations':len(data)*width,
                'cpu_us_per_operation':distribution([int(b['cpu_ns'])/width/1000 for b in data]),
                'wall_us_per_operation':distribution([int(b['wall_ns'])/width/1000 for b in data])}
        result['unit_paths'][KINDS[k]]={'distributions_by_batch_width':groups,
            'shapes_observed':sorted({int(b['shape']) for b in bench}),
            'frequency_pairs_khz':sorted({(int(b['freq_before_khz']),int(b['freq_after_khz'])) for b in bench})}
    result['phase_distributions']={label:distribution([p['phases_us'][label] for p in phase_runs if not p['dense']]) for label in PHASES}
(args.directory/'unit-cost-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'capture_files':len(paths),'hardware_measured':result['hardware_measured'],'gate':result['gate']},indent=2))
