"""Offline inverse models: archived A7 clocks; census counts are not timings."""
from pathlib import Path
import csv, json, statistics as st, hashlib
ROOT = Path(__file__).resolve().parent.parent
def census(path):
    rows = [list(map(int, l.split()[2:])) for l in path.read_text().splitlines()]
    assert len(rows) == 1200 and all(len(r) == 128 for r in rows)
    return rows
paths = [ROOT/'build/magitek-lazy-candidate-private/census.txt', ROOT/'build/ff6-window-batch-private/census.txt']
base, candidate = map(census, paths)
def features(r):
    return dict(entries=r[0], full_rows=sum(r[24:31]), clipped_rows=sum(r[32:39]),
                full_math_rows=sum(r[25:31]), clipped_math_rows=sum(r[33:39]),
                neon_rows=r[40], empty_rows=r[41], all_active_rows=r[42],
                decodes=r[21], misses=r[46], hits=r[47], window_flushes=r[104]+r[105])
result = {'input_hashes': {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
          'count_windows': {}, 'controls': [], 'identifiability':'single-predictor fits are descriptive, not causal prices'}
for label, a, b in [('preceding',240,277), ('observed_effect',277,291), ('whole_effect',277,439)]:
    result['count_windows'][label] = {k:st.mean(features(r)[k] for r in base[a:b]) for k in features(base[0])}
result['candidate_delta_whole_effect'] = {k:st.mean(features(candidate[i])[k]-features(base[i])[k] for i in range(277,439)) for k in features(base[0]) if k != 'window_flushes'}
result['candidate_flush_counters_excluded'] = 'Pre-deferral register counters do not count actual candidate flushes.'
for file in sorted((ROOT/'evidence/2026-10-10/snes-a7-cost1-return').glob('pass-*-mode-0-unit-cost.csv')):
    rows = list(csv.DictReader(l for l in file.read_text().splitlines() if not l.startswith('#')))
    result['input_hashes'][file.relative_to(ROOT).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    clocks = {int(r['frame']):r for r in rows if r['type']=='frame' and int(r['frame'])<291}
    counts = {int(r['frame']):r for r in rows if r['type']=='counts'}
    assert all(int(counts[i]['iterations'])==base[i][0] and int(counts[i]['shape'])+int(counts[i]['warm'])==base[i][46]+base[i][47] for i in clocks)
    windows = {label:{k.replace('_ns','_us'):st.mean(int(clocks[i][k])/1000 for i in range(a,b)) for k in ('cpu_ns','wall_ns')} for label,a,b in [('preceding',240,277),('observed_effect',277,291)]}
    fits = {}
    # Adjacent held-out expensive calls: deliberately exposes extrapolation failure.
    train, test = range(240,284), range(284,291)
    for key in features(base[0]):
        x=[features(base[i])[key] for i in train]; y=[int(clocks[i]['cpu_ns'])/1000 for i in train]
        xm,ym=st.mean(x),st.mean(y); denom=sum((v-xm)**2 for v in x)
        if not denom: continue
        slope=sum((a-xm)*(b-ym) for a,b in zip(x,y))/denom; intercept=ym-slope*xm
        errors=[intercept+slope*features(base[i])[key]-int(clocks[i]['cpu_ns'])/1000 for i in test]
        fits[key]=dict(slope_us_per_count=slope, intercept_us=intercept,
                       heldout_mae_us=st.mean(abs(e) for e in errors),heldout_max_abs_us=max(map(abs,errors)))
    result['controls'].append(dict(file=file.name,windows=windows,fits=fits))
result['thresholds'] = dict(row_payload_whole_effect_us=4117.290123*.105208333333,
    extra_19_rows_payload_us=19*.105208333333,
    cache_saving_needed_per_request_us=1514.283/(4117.290123+7965.222222),
    clipped_saving_needed_per_row_us=1514.283/result['count_windows']['observed_effect']['clipped_rows'],
    reserve_loss_per_late_call_frames=44.1*1.514283,
    reserve_loss_per_pcm_proxy_call_frames=44.1*2.436980622)
early, late = result['count_windows']['preceding'], result['count_windows']['observed_effect']
result['inverse_requirements'] = dict(
    explain_focus1_ppu_growth_per_extra_neon_row_us=3163/(late['neon_rows']-early['neon_rows']),
    explain_focus1_ppu_growth_per_extra_clipped_row_us=3163/(late['clipped_rows']-early['clipped_rows']),
    explain_focus1_ppu_growth_per_extra_entry_us=3163/(late['entries']-early['entries']),
    added_miss_payload_us=(late['misses']-early['misses'])*.105208333333,
    gate_saving_per_whole_effect_clipped_row_us=1514.283/result['count_windows']['whole_effect']['clipped_rows'],
    gate_saving_per_whole_effect_neon_row_us=1514.283/result['count_windows']['whole_effect']['neon_rows'],
    gate_fraction_focus1_ppu=1514.283/8904,
    pcm_proxy_gate_fraction_focus1_ppu=2436.980622/8904)
for rel in ['build/snes9x2005/source/gfx.c','build/snes9x2005/source/tile.c',
            'build/snes9x2005/source/tile.h','build/snes9x2005/source/a7_tile.h',
            'build/snes9x2005/source/a7_color_cache.h','build/plus-a7-window.h']:
    result['input_hashes'][rel]=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
out=ROOT/'docs/bio-backward-analysis.json'; out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
