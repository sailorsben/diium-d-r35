"""Verify offline hypothesis evidence; publish counts, never QEMU timings."""
from pathlib import Path
from hashlib import sha256
from statistics import mean
import json,csv
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/bio-hypotheses-private'
fields=json.loads((OUT/'fields.json').read_text())
fields.update({'10':'palette_table_queries','80':'defer_queries','81':'prefix_queries',
               '82':'prefix_range_lengths_sum','83':'fallback_queries','84':'fallback_row_visits'})
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read_rows(p,prefix):
    result=[]
    for line in p.read_text().splitlines():
        if not line.startswith(prefix):continue
        f=line.split();assert f[1]==f'frame={len(result)+1}'
        row=list(map(int,f[2:]));assert len(row)==128;result.append(row)
    assert len(result)==1200;return result
result={'version':'bio-offline-hypotheses-1','hardware_performance_measured':False,
        'installed':False,'card_access':False,'qemu_cpu':'cortex-a7',
        'timings_used':False,'variants':{},'input_hashes':{},'source_hashes':{}}
base=None;wide=[]
for name in ['baseline','window','palette','palette-window','palette-fast-window','palette-fast-window-counts']:
    folder=OUT/name;h=read_rows(folder/'replay.log','HYP ')
    c=read_rows(folder/'capture/census.txt','CENSUS ')
    text=(folder/'equivalence-bio.log').read_text()
    assert 'PASS: 1200 frames exact visible pixels' in text and 'FAIL' not in text
    if base is None:base=c
    # Distinct call counters sum to the existing requested-row census, including
    # blank returns. Histogram zero is allowed but never silently drops >8 rows.
    for hc,cc in zip(h,c):
        assert sum(hc[17:25])==hc[0] and sum(hc[33:41])==hc[1]
        assert sum(i*hc[16+i] for i in range(1,9))==sum(cc[24:31])
        assert sum(i*hc[32+i] for i in range(1,9))==sum(cc[32:39])
    for cc,bc in zip(c[277:439],base[277:439]):
        assert all(cc[i]==bc[i] for i in range(1,46))
    stats={value:mean(row[int(key)] for row in h[277:439]) for key,value in fields.items()}
    stats.update(renderer_entries=mean(row[0] for row in c[277:439]),
                 color_materializations=mean(row[46] for row in c[277:439]),
                 color_reuses=mean(row[47] for row in c[277:439]))
    result['variants'][name]={'effect_means':stats,'full_effect_frames':162,
                             'bio_output_comparison_frames':1200,
                             'core_sha256':digest(folder/'core/snes9x2005_plus_libretro.so')}
    if (folder/'equivalence-general.log').exists():
        assert 'PASS: 2400 frames exact visible pixels' in (folder/'equivalence-general.log').read_text()
        result['variants'][name]['intro_returned_comparison_frames']=2400
    for rel in ['replay.log','capture/census.txt','equivalence-bio.log','core/source/tile.c',
                'core/source/a7_color_cache.h','core/source/gfx.c','core/source/ppu.c']:
        p=folder/rel;result['input_hashes'][p.relative_to(ROOT).as_posix()]=digest(p)
    if 'window' in name:
        p=folder/'core/source/a7_window.h';result['input_hashes'][p.relative_to(ROOT).as_posix()]=digest(p)
    for i in range(277,439):
        wide.append(dict(variant=name,frame=i,**{value:h[i][int(key)] for key,value in fields.items()},
                         renderer_entries=c[i][0],materializations=c[i][46],reuses=c[i][47]))
b=result['variants']['baseline']['effect_means'];w=result['variants']['window']['effect_means']
removed=b['tile_calls']-w['tile_calls']
assert abs(removed-8340.864197530866)<1e-8
result['dispatch_reduction']={'calls_per_effect_frame':removed,'percent':100*removed/b['tile_calls'],
    'rows_preserved':True,'price_missing':'removable dispatch/preamble per tile call, excluding row work',
    'by_mode':{str(i):b[f'full_mode_{i}_calls']-w[f'full_mode_{i}_calls'] for i in range(7)}}
setup=231.462235;rows=149.808224;short=114.5715625
result['sensitivity_not_a7_prediction']=[dict(dispatch_price_us=d,
    original_window_saving_us=removed*d+setup-rows-short,
    combined_if_palette_net_zero_and_helpers_equal_reference_us=removed*d+setup-short)
    for d in (.1,.2,.3)]
result['break_even_dispatch_us']={
    'original_window_late_floor':(1514.283-setup+rows+short)/removed,
    'original_window_pcm_proxy':(2436.980622-setup+rows+short)/removed,
    'combined_late_if_palette_net_zero_and_reference_helpers':(1514.283-setup+short)/removed,
    'combined_pcm_if_palette_net_zero_and_reference_helpers':(2436.980622-setup+short)/removed}
oracle=(OUT/'fast-window-check.log').read_text()
assert 'PASS: 524288 window states' in oracle and 'PASS: 38400 prefix queries' in oracle
result['fast_window_oracle']={'clip_states':524288,'validity_queries':38400,'passed':True,
    'fallback':'out-of-order captures use original scan','ordered_query':'two prefix reads and comparison'}
result['cache_storage_bytes']={'baseline_rgb_entries':36864,'palette_entries':3840,
                              'fast_validity_prefix_additional':1036}
manifest=json.loads((ROOT/'releases/snes-mvp-1.19/manifest.json').read_text())
assert digest(ROOT/'build/plus-a7-out/plus-a7.so')==manifest['core_sha256']
result['production_core_unchanged']=True
for rel in ['build/prepare-bio-hypotheses.py','build/prepare-bio-fast-window.py','build/prepare-bio-helper-counts.py',
            'build/bio-palette-cache.h','build/bio-palette-direct.h',
            'build/run-bio-hypotheses.sh','build/analyze-bio-hypotheses.py']:
    result['source_hashes'][rel]=digest(ROOT/rel)
result['limits']=['No A7 saving or installation qualification from QEMU counts.',
 'Direct palette path adds gathers on former cache hits; net cost unmeasured.',
 'Palette table builds and RGB-cache work are not independent additive credits.',
 'Derived battle is not the exact physical encounter; captures are instrumented.',
 'Original helper price does not price longer window spans or fast-prefix bookkeeping.',
 'ARM disassembly is instrumented and not a production instruction-cost estimate.']
(OUT/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
with (OUT/'effect-counts.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(wide[0]));writer.writeheader();writer.writerows(wide)
print(json.dumps({'passed':True,'variants':len(result['variants']),
    'bio_comparison_frames':7200,'broader_comparison_frames':4800,
    'removed_tile_dispatches_per_effect_frame':removed,
    'break_even_dispatch_us':result['break_even_dispatch_us']},indent=2))
