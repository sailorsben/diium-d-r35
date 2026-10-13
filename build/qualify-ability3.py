"""Qualify exact fixed-math reuse and the actual independently versioned suite."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent.parent
def generate():
    s=(ROOT/'build/qualify-ability-regression.py').read_text()
    s=s.replace('ability-regression-private-v1','ability3-private-v1').replace('1.19-ability2','1.19-ability3').replace('snes-ability2','snes-ability3')
    # Keep original identity mapping while new physical measurements are in a
    # different archive. Both are explicitly named, never inferred from mtime.
    start=s.index('    for c in plan[\'cases\'][:11]:\n        jobs.extend')
    end=s.index('    # Exercise the actual new ELF',start)
    s=s[:start]+'''    jobs.extend((c,'math',OUT/'counted-core/snes9x2005_plus_libretro.so') for c in plan['cases'])
    with ThreadPoolExecutor(max_workers=2) as pool:comparisons=list(pool.map(compare,jobs))
    census=[]
    returned=ROOT/'device-evidence/a7-pair-before-20261013T162915Z/retro/snes-ability2'
    for c in plan['cases']:
        records=[list(map(int,l[5:].split(','))) for l in (OUT/f"census/{c['seq']:03d}-math.log").read_text().splitlines() if l.startswith('MATH ')]
        assert len(records)==1200 and [r[0] for r in records]==list(range(1200))
        physical=rows(returned/f"run-{c['seq']:03d}/frames.csv")
        tail=[int(x['frame']) for x in physical[-17:-1]]
        census.append({'case':c['seq'],'name':c['name'],'tail_frames':tail,
            'tail_means':{key:statistics.mean(records[i][k+1] for i in tail) for k,key in enumerate(('active_NEON_rows','fixed_math_rows_removed','math_palette_hits','math_palette_builds'))},
            'A7_unit_prices_measured':False})
''' +s[end:]
    s=s.replace("'aligned_tail_work_census':census", "'fixed_math_work_census':census")
    s=s.replace("assert 'PASS 1200 calls' in log.read_text();", "assert 'PASS 1200 calls' in log.read_text();\n        if label=='math':assert 'MATH 1199,' in log.read_text();")
    s=s.replace('PASS:18 exact new-core replays;22 aligned census replays;', 'PASS:18 exact new-core replays;18 counted math replays;')
    s=s.replace("'No physical candidate result; effect-specific savings are not priced.'", "'New math-reuse A7 saving is unmeasured; work counts are conditional predictions only.'")
    s=s.replace("'Window generalization does not claim to reduce unchanged fixed-color or Mode7 paths.'", "'Fixed-color register flushes and unsupported/mixed rows remain original.'")
    # Owned generated script is frozen with the exact artifact for review.
    p=ROOT/'build/ability3-private-v1/qualify.py';p.write_text(s,newline='\n')
    # Generated script parent differs; set the same explicit repository root.
    s=s.replace('ROOT=Path(__file__).resolve().parent.parent', 'ROOT=Path(__file__).resolve().parent.parent.parent')
    p.write_text(s,newline='\n')
    return p
if __name__=='__main__':
    import runpy
    runpy.run_path(str(generate()),run_name='__main__')
