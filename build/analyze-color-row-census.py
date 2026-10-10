"""Demanded color work and exact rendered/audio CRCs; no hardware timing claim."""
from pathlib import Path
from hashlib import sha256
import json
ROOT=Path(__file__).resolve().parent
def read(name):
    p=ROOT/name
    rows=[list(map(int,l.split()[2:])) for l in (p/'census.txt').read_text().splitlines()]
    assert len(rows)==1200 and all(len(r)==128 for r in rows)
    return p,rows
a,old=read('magitek-lazy-baseline-private')
b,new=read('magitek-lazy-candidate-private')
historical=[list(map(int,l.split()[2:])) for l in (ROOT/'magitek-cache-census-private/census.txt').read_text().splitlines()]
assert old==historical, 'The independently repeated 1.18 baseline must reproduce its recorded work'
assert (a/'commands.txt').read_bytes()==(b/'commands.txt').read_bytes()
assert (a/'replay.log').read_bytes()==(b/'replay.log').read_bytes(), 'Pixels and PCM must match at every menu-command boundary'
assert all(x[:46]==y[:46] and x[48:]==y[48:] for x,y in zip(old,new)), 'Keep all raster/tile/visibility/flush work unchanged'
effect=[i for i,r in enumerate(old) if i>200 and r[0]>=80]
assert len(effect)==162 and (min(effect),max(effect))==(277,438)
before=sum(old[i][46]*8 for i in effect)
after=sum(new[i][46] for i in effect)
assert 0<after<before
result={'baseline_version':'1.18','candidate_version':'1.19','frames':1200,
    'effect_frames':len(effect),'effect_indices':[min(effect),max(effect)],
    'baseline_palette_lookup_rows':before,'candidate_palette_lookup_rows':after,
    'lookup_row_reduction_fraction':1-after/before,
    'baseline_tile_color_requests':sum(old[i][46]+old[i][47] for i in effect),
    'candidate_visible_row_color_requests':sum(new[i][46]+new[i][47] for i in effect),
    'empty_rows_without_color_request':sum(new[i][41] for i in effect),
    'cache_bytes':36864,'all_other_126_counters_identical':True,
    'baseline_reproduces_prior_1200_frame_census':True,'command_boundary_pixels_pcm_identical':True,
    'baseline_commands_sha256':sha256((a/'commands.txt').read_bytes()).hexdigest(),
    'source_hashes':{name:sha256((ROOT/name).read_bytes()).hexdigest() for name in
        ('apply-plus-a7.py','plus-a7-render.h','plus-a7-color-cache.h','prepare-render-census.py',
         'check-color-row-census.sh','analyze-color-row-census.py')},
    'private_fixture':'Same owner Narshe-derived Magitek battle entry and real menu inputs as 1.18; not the exact physical battle background.',
    'limits':'Work counts and CRC equality do not establish Cortex-A7 cycle savings or sustained physical sound. Shipping-core full-frame/native-PCM/logical-state equivalence is a separate check.'}
(b/'analysis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
