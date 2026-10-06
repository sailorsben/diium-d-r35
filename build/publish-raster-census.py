"""Publish work counts and exact-output results, never the replay inputs/core."""
from pathlib import Path
from hashlib import sha256
import json,importlib.util
ROOT=Path(__file__).resolve().parent.parent
PREFIX='evidence/2026-10-06/raster-work-census/'
before=ROOT/'build/render-census-color';after=ROOT/'build/render-census-fixed'
def read(path):
    text=(path/'replay.log').read_text()
    assert 'PASS: 40 frames exact visible pixels, native PCM, geometry and periodic state' in text
    rows=[list(map(int,line.split()[3:])) for line in text.splitlines() if line.startswith('CENSUS phase=1 ')]
    assert len(rows)==20 and all(len(r)==128 for r in rows)
    return rows
a=read(before);b=read(after)
assert all(x[64+0x32]==214 and x[44]==0 and x[45]==214 for x in a)
assert all(y[64+0x32]==0 for y in b)
assert all(x[2]==y[2]==423 and x[24]+x[25]==y[24]+y[25]==31520 for x,y in zip(a,b))
assert [r[0] for r in a]==[223 if i%2==0 else 217 for i in range(20)]
assert [r[0] for r in b]==[10 if i%2==0 else 4 for i in range(20)]
assert all(r[14]==r[15]==0 and sum(r[16:21])==0 and sum(r[32:39])==0 for r in a)
qualified=json.loads((ROOT/'build/snes-mvp/out/verification.json').read_text())
assert qualified['passed'] and qualified['version']=='1.16' and not qualified['hardware_qualified']
result={'pinned_core_commit':(ROOT/'build/core-source-commit.txt').read_text().strip(),
    'baseline_device_version':'1.15','patched_candidate_version':'1.16',
    'exact_returned_private_state_payload_verified':True,
    'loaded_frames':20,'before_ppu_updates':[r[0] for r in a],'after_ppu_updates':[r[0] for r in b],
    'same_layer_lines_per_frame':423,'same_requested_tile_rows_per_frame':31520,
    'mode7_clipped_offset_hires_calls':0,'baseline_pending_fixed_color_flushes_per_frame':214,
    'baseline_effective_fixed_color_changes_at_those_flushes':0,'patched_pending_fixed_color_flushes_per_frame':0,
    'baseline_tile_decodes':[r[21] for r in a],
    'replay_output':'Both isolated instrumented cores match clean stock-derived pixels, PCM, geometry and periodic logical state for40 frames; full shipping1.16 matches1200 frames.',
    'register_contract':qualified['raster_register_contract'],
    'interpretation':'Component-tag writes leave effective color unchanged; their raw-byte invalidation fragments raster jobs. Fix preserves actual changes, latch, every tile row, frame and native sound.',
    'performance_limit':'Counts establish removed setup/invalidation work, not physical cycle savings or sustainable native device speed.',
    'census_source_hashes':{label:{name:sha256((path/name).read_bytes()).hexdigest() for name in
        ('replay.c','core/source/gfx.c','core/source/tile.c','core/source/ppu.c','core/source/ppu.h','core/source/a7_tile.h','core/libretro.c','core/link.T')}
        for label,path in [('before',before),('after',after)]}}
out=ROOT/'build/render-census-fixed/analysis.json';out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();entries=json.loads(raw)['entries']
assert not any(e['published'].startswith(PREFIX) for e in entries)
for e in entries: assert sha256((ROOT/e['published']).read_bytes()).hexdigest()==e['published_sha256']
selected={'analysis.json':out,'before-replay.log':before/'replay.log','after-replay.log':after/'replay.log',
          'fields.json':after/'fields.json'}
additions=[]
for name,source in selected.items():
    data=source.read_bytes();assert b'C:\\Users' not in data and b'.codex' not in data
    target=ROOT/PREFIX/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    additions.append({'source':source.relative_to(ROOT).as_posix(),'published':target.relative_to(ROOT).as_posix(),
        'source_sha256':sha256(data).hexdigest(),'published_sha256':sha256(data).hexdigest(),'bytes':len(data),'normalized':False})
spec=importlib.util.spec_from_file_location('publisher',ROOT/'build/publish-snes-1.16.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
manifest.write_bytes(mod.append_manifest(raw,additions))
print('Published four nonprivate raster census artifacts; all prior evidence hashes verified')
