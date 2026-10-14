"""Publish bounded receipts and a saving model; never ROM/state/vendor bytes."""
from pathlib import Path
from hashlib import sha256
import json,re
ROOT=Path(__file__).resolve().parent.parent
V1=ROOT/'build/demand-private-v1';V2=ROOT/'build/demand-final-private-v2';V3=ROOT/'build/demand-visible-private-v3'
DEST=ROOT/'evidence/2026-10-14/demand-optimization'
def digest(p):return sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 assert not DEST.exists()
 qs=[load(p/'qualification.json') for p in (V1,V2,V3)];assert all(q['passed'] for q in qs)
 checks={'seams_v1':load(V1/'seams.json'),'OAM':load(V1/'oam-proof.json'),'runtime_FIFO':load(V1/'runtime-proof.json'),'seams_v2':load(V2/'seams.json'),'visibility_v3':load(V3/'visibility-seam.json'),'native_v2':load(V2/'native-proof.json'),'native_v3':load(V3/'native-proof.json'),'transitions_v2':load(V2/'transitions-fixed.json'),'transitions_v3':load(V3/'transitions-fixed.json'),'baseline_control':load(V2/'reference-control.json')}
 assert all(v['passed'] for k,v in checks.items() if k!='baseline_control')
 frozen=load(V3/'frozen.json');assert all(digest(ROOT/p)==h for p,h in frozen.items())
 assert digest(ROOT/'build/common-band-private-v3/plus-a7.so')=='e9c421e4e228a5c91eba112a8fd7ec9e0a3c66cc996ba6a6a86f995622ef8129'
 heavy={c['name']:{'work':c['heavy_mean'],'fused_by_index':c['fused_heavy_by_index']} for c in qs[2]['comparisons'] if c['label']=='counted-core' and c['case'] in (1,8)}
 earlier={c['name']:c['fused_heavy_by_index'] for c in qs[1]['comparisons'] if c['label']=='counted-core' and c['case'] in (1,8)}
 for name,r in heavy.items():
  w=r['work'];r['depth_vectors_before_clip_guard']=earlier[name][5];r['depth_vectors_after_including_clip_guard']=r['fused_by_index'][5]+w['clip_depth_vectors']
  r['new_clip_guard_index_row_saving']=earlier[name][10]-r['fused_by_index'][10]
 assert heavy['QUASAR']['work']['clip_cells_eliminated']==570 and heavy['QUASAR']['new_clip_guard_index_row_saving']==0
 assert heavy['QUASAR']['depth_vectors_before_clip_guard']==heavy['QUASAR']['depth_vectors_after_including_clip_guard']
 summary={'reference_sha256':digest(ROOT/'build/common-band-private-v3/plus-a7.so'),'preferred_offline_candidate':{'path':'build/demand-visible-private-v3/core/snes9x2005_plus_libretro.so','sha256':digest(V3/'core/snes9x2005_plus_libretro.so'),'reason':'Preserves Meteor sparse work and rejects Quasar hidden main clips before tile setup. Preferred by qualified work elimination; not established fastest on A7.','runner_path':'build/demand-private-v1/owned-output-runner','runner_sha256':digest(V1/'owned-output-runner')},'original_command_raw_comparison_calls':sum(q['calls'] for q in qs),'candidate_iterations':[{'name':p.name,'calls':q['calls'],'ordinary_core_sha256':digest(p/('combined/core/snes9x2005_plus_libretro.so' if p==V1 else 'core/snes9x2005_plus_libretro.so'))} for p,q in zip((V1,V2,V3),qs)],'final_combination_original_command_calls':43200,'final_synthetic_transition_calls':8400,'every_original_frame_raw_graphics_PCM_geometry':True,'normalized_state_every':30,'final_heavy_intervals_zero_based':{'METEOR':[384,415],'QUASAR':[496,529]},'heavy':heavy,'checks':checks,'frozen_files_verified':len(frozen),'card_access':False,'A7_savings_measured':False,'QEMU_timings_used':False,'production_gate_passed':False,'limits':['No new millisecond saving established. A7 chunk-memory access/cache/coherency cost and total thread CPU demand remain unknown.','Synthetic resolution tests use the same test-only HDMA base-pointer initialization in both source clones after identical unchanged baselines reproduce an allocator-derived register divergence. Final candidate HDMA code stays unchanged; no emulated state fields masked.','BG geometry producer shares one eligible layer per redraw. OBJ traversal remains; shared last-palette preparation covers OBJ and clipped callers. No RGB/source-row descriptor cache introduced.','Appearance writes avoided are not OBJ schedule rebuilds removed. Measured peaks previously had zero redundant rebuilds; no peak saving credited.','Work request bytes/vectors/stores are distinct from retired instructions, cache misses or physical DDR traffic.']}
 variants={'reference':ROOT/'build/common-band-private-v3/plus-a7.so','alignment':ROOT/'build/cache-alignment-private-v1/core/snes9x2005_plus_libretro.so','fused':ROOT/'build/fused-toolbox-private-v2/core/snes9x2005_plus_libretro.so'}
 variants.update({k:V1/k/'core/snes9x2005_plus_libretro.so' for k in ('dma','small','geometry','output')});variants.update({'combined_v2':V2/'core/snes9x2005_plus_libretro.so','combined_v3':V3/'core/snes9x2005_plus_libretro.so'})
 # One order and its reverse, repeated, on each exact archived context.
 keys=list(variants);runs=[]
 for case in (1,8):
  for order in (keys,list(reversed(keys)),list(reversed(keys)),keys):
   for key in order:runs.append({'epoch':len(runs),'case':case,'variant':key,'calls':1200})
 plan={'status':'LOCAL_PLAN_ONLY_NOT_STAGED_OR_ARMED','runs':runs,'variant_hashes':{k:{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)} for k,p in variants.items()},'deadline_ms':16.6881545,'headroom20pct_target_ms':13.3505236,'prior_failure_total_CPU_ms':{'METEOR':17.9965,'QUASAR':17.4914},'observer_policy':'Kernel syscall monotonic and thread CPU clocks around whole calls/steps; nested phase clocks and work counters off. Include observer/worker costs, never calibration-subtract. Record replay index and one-based run number. Frequency unavailable is not 666MHz.','capture':'Whole effect and recovery, every drawing/PCM callback, complete producer/consumer reserve, pointer validity, main/audio/display disjoint CPU and final worker joins. RAM records during epochs; diagnostic persistence after joins.','hardware_access_authorized_now':False,'before_future_writes':['Explicit new card-test authority','Fresh archive of all logs/private progress; source/copy/source and independent readback hashes','Card identity, FAT health, consumed-marker and stock/emu_sfc.so hashes','Exact source pushed, owned candidate directories and payload readback; never overwrite adapter','Declare candidate saving hypothesis/additional costs and failed-state falsification; measurement experiment is not production promotion'],'predictions':['Identical graphics/native PCM/state and every frame retained.','V3 Quasar rejects570 main cells per counted heavy call; geometry reads drop2280 logical bytes versusv2, with zero newly removed index rows and unchanged aggregate depth-vector count.','Meteor sparse one/two pixel hits remain3978.75 per heavy call in this specific interval; v3 adds one failed coverage vector, then vetoes.','Eligible direct callbacks copy zero visible bytes; fallback and promotion account migration/copy costs explicitly.','A candidate may measure zero gain or regress. Prefer only repeatable matched net main+worker CPU reduction with complete valid reserve and no new failures.']}
 model={'net_saving_ms':None,'A7_unit_prices':None,'deadline_gap_after_ms':None,'headroom_gap_after_ms':None,'audio_rate_after':None,'order':'reference -> fused/alignment -> DMA/small -> geometry -> owned output -> clip rejection; price complete incremental stages and interactions','formula':'S_total = S_fused + S_alignment + S_DMA + S_small + S_geometry + S_owned + S_clip - A_interactions, with each term a matched net incremental A7 measurement. Counts alone cannot price it.','geometry_formula':'Sub/main map/flip/grouping work avoided minus extra producer cells,132 bytes/band writes,4 bytes/consumer-cell reads, metadata/clip guards and footprint. Main hidden cells eliminated by S_clip receive no geometry-sharing credit.','clip_formula':'570*(removed tile setup + removed descriptor read) + old_depth_loop_cost - new_clip_depth_loop_cost -19*clip_guard_setup, in Quasar heavy interval. 4410 rows were already absent from index production; aggregate depth vectors remain5319.','owned_formula':'Strided copy cost removed - chunk PPU access delta - acquire/publication/restore/migration costs;224 rows*512 bytes read+write removed on successful direct frames, not the whole0.82-0.86ms callback.','reserve_formula':'For measured complete production/consumption, D(t)=consumed-produced; require maximum prefix deficit and maximum capped-reserve drawdown plus declared margin, using only valid pointers.','provisional_required_saving_ms':{'METEOR':{'deadline':1.3083455,'headroom20pct':4.6459764},'QUASAR':{'deadline':0.8032455,'headroom20pct':4.1408764}},'warning':'Prior failure windows, not healthy acceptance. These rounded totals may differ from exact earlier receipts. Use exact matched A7 return and cycle quota for the subsequent decision.'}
 # Bounded identities: only hashes and authored/owned source paths. No raw
 # ROM/private-state payloads, addresses, PCM, vendor libraries or attachments.
 inputs={}
 for folder in (V1,V2,V3):
  for p in folder.rglob('*'):
   if p.is_file() and (p.suffix in ('.c','.h','.so') or p.name.endswith('.json')):inputs[p.relative_to(ROOT).as_posix()]=digest(p)
 for p in (ROOT/'build').glob('*demand*'):
  if p.is_file():inputs[p.relative_to(ROOT).as_posix()]=digest(p)
 for p in (ROOT/'build/ability-regression-private-v1/plan.json',ROOT/'build/plus-a7-out/ff6.sfc'):inputs[p.relative_to(ROOT).as_posix()]=digest(p)
 for case in load(ROOT/'build/ability-regression-private-v1/plan.json')['cases']:
  for name in ('scene.state','input.txt'):
   p=ROOT/f"build/ability-regression-private-v1/cases/{case['seq']:03d}/{name}";inputs[p.relative_to(ROOT).as_posix()]=digest(p)
 # Keep old publications byte-exact and append only our new JSON receipts.
 manifest=ROOT/'evidence/manifest.json';raw=manifest.read_bytes();old=load(manifest)['entries']
 assert all(digest(ROOT/e['published'])==e['published_sha256'] for e in old)
 DEST.mkdir(parents=True);entries=[]
 for name,data in [('analysis.json',summary),('measurement-plan.json',plan),('saving-model.json',model),('inputs.json',{'hashes':inputs})]:
  p=DEST/name;p.write_text(json.dumps(data,indent=2)+'\n',newline='\n');entries.append({'source':p.relative_to(ROOT).as_posix(),'published':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'published_sha256':digest(p),'bytes':p.stat().st_size,'normalized':False})
 import importlib.util
 spec=importlib.util.spec_from_file_location('demand_pub',ROOT/'build/publish-snes-1.19.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
 manifest.write_bytes(pub.append_manifest(raw,entries));assert load(manifest)['entries'][:len(old)]==old
 print('Published',summary['original_command_raw_comparison_calls'],'original-command raw comparisons, final transition/native proofs and symbolic saving model; preserved',len(old),'prior entries')
if __name__=='__main__':main()
