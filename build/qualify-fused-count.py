"""Reuse unchanged comparator; qualify extra counters and unchanged old work."""
from pathlib import Path
from hashlib import sha256
import shutil,json
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/fused-count-private-v2'
def main():
 shutil.copy2(ROOT/'build/fused-toolbox-private-v1/census-compare',OUT/'census-compare')
 s=(ROOT/'build/qualify-fused-toolbox.py').read_text()
 anchor="OUT=ROOT/('build/fused-toolbox-private-v2' if V2 else 'build/fused-toolbox-private-v1')"
 assert s.count(anchor)==1
 s=s.replace(anchor,"OUT=ROOT/'build/fused-count-private-v2'")
 s=s.replace("OUT/('plus-a7.so' if label=='ordinary' else 'counted-core/snes9x2005_plus_libretro.so')","OUT/'core/snes9x2005_plus_libretro.so'")
 s=s.replace("for label in ('ordinary','census') for c in plan['cases']", "for label in ('census',) for c in plan['cases'] if c['seq'] in (0,1,8)")
 s=s.replace("'reserved27','reserved28','reserved29','reserved30'", "'prefix_rows_skipped_before_visible','band_cells','two_bpp_prefix_depth_loads','four_bpp_prefix_depth_loads'")
 ns={'__file__':__file__,'__name__':'fused_count_impl'};exec(compile(s,__file__,'exec'),ns);ns['main']()
 def read(p):return [list(map(int,l[6:].split(','))) for l in p.read_text().splitlines() if l.startswith('FUSED ')]
 q=json.loads((OUT/'qualification.json').read_text())
 for c in q['comparisons']:
  a=read(OUT/f"exact/{c['case']:03d}-census.log");b=read(ROOT/f"build/fused-toolbox-private-v1/exact/{c['case']:03d}-census.log")
  assert len(a)==len(b)==1200 and all(x[:28]==y[:28] and x[32]==y[32] for x,y in zip(a,b))
 q['prior_observer_fields_unchanged_every_call']=True;q['comparator_reused_sha256']=sha256((OUT/'census-compare').read_bytes()).hexdigest();(OUT/'qualification.json').write_text(json.dumps(q,indent=2)+'\n');print('PASS refined observer matches old event counts in all3600 calls; no timing claim')
if __name__=='__main__':main()
