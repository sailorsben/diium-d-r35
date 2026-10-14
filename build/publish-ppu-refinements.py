"""Publish PPU qualification metadata; never distribute private cores or states."""
from pathlib import Path
from hashlib import sha256
import json,re
ROOT=Path(__file__).resolve().parent.parent
V4=ROOT/'build/ppu-refinements-private-v4'
V5=ROOT/'build/ppu-refinements-private-v5'
OUT=ROOT/'evidence/2026-10-14/ppu-refinements'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 assert not OUT.exists()
 manifest=ROOT/'evidence/manifest.json';m=read(manifest)
 for e in m['entries']:assert digest(ROOT/e['published'])==e['published_sha256'],e['published']
 for n,h in read(V5/'frozen.json').items():assert digest(ROOT/n)==h,n
 proofs=[V4/'seams.json',V4/'qualification.json',V4/'row-review/qualification.json',V5/'qualification.json']
 for base in (V4/'integration',V4/'row-integration',V5/'integration'):
  proofs.extend([base/'native-proof.json',base/'transitions-fixed.json'])
 for p in proofs:assert read(p)['passed'],p
 asm=(V5/'combined.asm').read_text();assert not re.search(r'\sbl\s.*<d35_sparse_math',asm)
 versions=[tuple(map(int,s.split('.'))) for s in re.findall(r'GLIBC_([\d.]+)',(V5/'abi.txt').read_text())]
 assert max(versions)<=(2,30)
 old=ROOT/'build/demand-visible-private-v3/core';new=V5/'combined'
 changed=[];unchanged=[]
 for p in (old/'source').rglob('*'):
  if p.is_file() and p.suffix in ('.c','.h'):
   rel=p.relative_to(old);assert (new/rel).exists()
   (unchanged if digest(p)==digest(new/rel) else changed).append(rel.as_posix())
 assert set(changed)<=set(['source/gfx.c','source/tile.c','source/a7_common_batch.h','source/a7_partial_kernels.h']),changed
 inputs={p.relative_to(ROOT).as_posix():digest(p) for p in proofs}
 for base in (V4,V5):
  for p in base.rglob('*'):
   if p.is_file() and p.suffix in ('.c','.h','.so','.json','.log','.txt','.asm'):
    inputs[p.relative_to(ROOT).as_posix()]=digest(p)
 for p in ROOT.glob('build/*ppu*'):
  if p.is_file():inputs[p.relative_to(ROOT).as_posix()]=digest(p)
 final=read(V5/'qualification.json')
 counted=[r for r in final['comparisons'] if r['label']=='combined-counted']
 score={'aggregate':{k:sum(r['work_counts'][k] for r in counted) for k in counted[0]['work_counts']},
        'peak_mean_requests':{r['name']:r['peak_mean_requests'] for r in counted if r['peak_mean_requests']},
        'counts_are_not_A7_time':True,'v4_legacy_FUSED_counters_not_used':True}
 analysis={'passed_offline':True,'raw_graphics_PCM_geometry_calls':sum(read(p)['raw_graphics_PCM_geometry_calls'] for p in [V4/'qualification.json',V4/'row-review/qualification.json',V5/'qualification.json']),
  'transition_calls':25200,'normalized_state_every':30,'core_sha256':digest(new/'snes9x2005_plus_libretro.so'),
  'core_bytes':(new/'snes9x2005_plus_libretro.so').stat().st_size,'changed_existing_source':changed,'unchanged_existing_source':unchanged,
  'source_row_cache_in_final':False,'sparse_math_out_of_line_calls':0,'max_GLIBC':list(max(versions)),
  'A7_saving_measured':False,'predicted_remaining_audio_deficit_ms':None,'production_gate_passed':False,'card_writes':0,
  'synthetic_239_caveat':'Shared TEST-ONLY HDMA host-pointer reset used in both clones; shipping HDMA unchanged. Baseline versus itself already diverges without this reset.',
  'saving_model':'Net saving = removed depth merge, initial OBJ seek, vector materialization and row-fill setup costs minus classifier misses, lookup/table construction, scalar/GPR transitions, spills and code footprint. Bulk clears retain every depth byte.',
  'break_even':'Measured matched net saving must exceed 0.231-0.270ms nominal CPU gap plus unpriced kernel/other costs and cumulative reserve debt; 20 percent quota margin requires about 3.59-3.61ms. All new prices and audio deficit remain unknown.',
  'next_physical_test':'After authorized archive/install, compare frozen demand-v3 with isolated obj/shapes/bulk and final combination on Meteor/Quasar in both orders; full 18-context paired regression and recovery. Ordinary cores, same owned runner, kernel clocks, complete PCM/pointer trace, no nested PPU timers. Price row cache separately only.',
  'prior_frozen_hashes_verified':True}
 OUT.mkdir(parents=True)
 packets={'analysis.json':analysis,'inputs.json':inputs,'work-counts.json':score}
 for p in proofs:packets[p.relative_to(ROOT/'build').as_posix().replace('/','--')]=read(p)
 for name,obj in packets.items():
  p=OUT/name;p.write_text(json.dumps(obj,indent=2)+'\n')
  m['entries'].append({'source':'build/publish-ppu-refinements.py','published':p.relative_to(ROOT).as_posix(),'source_sha256':digest(Path(__file__)),
    'published_sha256':digest(p),'bytes':p.stat().st_size,'normalized':True})
 manifest.write_text(json.dumps(m,indent=2)+'\n')
 print('Published exact offline PPU qualification; all prior hashes preserved; no physical performance claim or card writes')
if __name__=='__main__':main()
